from fastapi import APIRouter, HTTPException, Depends
from typing import List
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class Competitor(BaseModel):
    id: int
    name: str
    website: str
    description: str
    created_at: datetime
    updated_at: datetime

class CompetitorCreate(BaseModel):
    name: str
    website: str
    description: str

# Mock database
competitors_db = []
current_id = 1

@router.post("/", response_model=Competitor)
async def create_competitor(competitor: CompetitorCreate):
    global current_id
    new_competitor = Competitor(
        id=current_id,
        name=competitor.name,
        website=competitor.website,
        description=competitor.description,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    competitors_db.append(new_competitor)
    current_id += 1
    return new_competitor

@router.get("/", response_model=List[Competitor])
async def get_competitors():
    return competitors_db

@router.get("/{competitor_id}", response_model=Competitor)
async def get_competitor(competitor_id: int):
    competitor = next((c for c in competitors_db if c.id == competitor_id), None)
    if competitor is None:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return competitor

@router.put("/{competitor_id}", response_model=Competitor)
async def update_competitor(competitor_id: int, competitor: CompetitorCreate):
    index = next((i for i, c in enumerate(competitors_db) if c.id == competitor_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    updated_competitor = Competitor(
        id=competitor_id,
        name=competitor.name,
        website=competitor.website,
        description=competitor.description,
        created_at=competitors_db[index].created_at,
        updated_at=datetime.utcnow()
    )
    competitors_db[index] = updated_competitor
    return updated_competitor

@router.delete("/{competitor_id}")
async def delete_competitor(competitor_id: int):
    index = next((i for i, c in enumerate(competitors_db) if c.id == competitor_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail="Competitor not found")
    competitors_db.pop(index)
    return {"message": "Competitor deleted successfully"} 