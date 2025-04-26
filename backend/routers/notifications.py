from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

router = APIRouter()

class NotificationConfig(BaseModel):
    email: str
    frequency: str  # "daily" or "weekly"
    competitor_ids: List[int]

class Notification(BaseModel):
    id: int
    competitor_id: int
    type: str
    content: str
    timestamp: datetime
    sent: bool

# Mock database
notifications_db = []
current_id = 1

# Google API credentials
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/spreadsheets'
]

def get_credentials():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = Flow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

@router.post("/config", response_model=NotificationConfig)
async def configure_notifications(config: NotificationConfig):
    # In a real app, this would save to a database
    return config

@router.post("/send-email")
async def send_email_notification(notification: Notification):
    try:
        creds = get_credentials()
        service = build('gmail', 'v1', credentials=creds)
        
        message = MIMEMultipart()
        message['to'] = notification.email
        message['subject'] = f"Competitive Intelligence Update: {notification.type}"
        
        msg = MIMEText(notification.content)
        message.attach(msg)
        
        raw = base64.urlsafe_b64encode(message.as_bytes())
        raw = raw.decode()
        
        service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()
        
        notification.sent = True
        return {"message": "Email sent successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-sheet")
async def update_google_sheet(notification: Notification):
    try:
        creds = get_credentials()
        service = build('sheets', 'v4', credentials=creds)
        
        # In a real app, this would update a specific spreadsheet
        # For now, just returning success
        return {"message": "Sheet updated successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[Notification])
async def get_notifications():
    return notifications_db

@router.get("/{notification_id}", response_model=Notification)
async def get_notification(notification_id: int):
    notification = next((n for n in notifications_db if n.id == notification_id), None)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification 