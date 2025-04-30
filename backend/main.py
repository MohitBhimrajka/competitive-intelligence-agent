from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Competitive Intelligence Agent",
    description="AI-powered competitive intelligence platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from routers import company, news, insights, competitors, chat

# Include routers
app.include_router(company.router, prefix="/api/company", tags=["company"])
app.include_router(news.router, prefix="/api/news", tags=["news"])
app.include_router(insights.router, prefix="/api/insights", tags=["insights"])
app.include_router(competitors.router, prefix="/api/competitor", tags=["competitors"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

@app.get("/")
async def root():
    return {"message": "Welcome to Competitive Intelligence Agent API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True) 