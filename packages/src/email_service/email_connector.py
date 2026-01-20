import os
import base64
import email
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
import re

# Gmail imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Outlook imports
import msal
import requests

# For AI processing (you'll need to install these)
# pip install openai python-dotenv
from google import genai

class EmailConfig:
    
    GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
                     'https://www.googleapis.com/auth/gmail.modify',
                     'https://www.googleapis.com/auth/gmail.send']
    OUTLOOK_SCOPES = ['https://graph.microsoft.com/Mail.ReadWrite',
                      'https://graph.microsoft.com/Mail.Send']
    gemini_model = "gemini-1.5-pro"
    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class EmailConnector:
    def __init__(self,  credentials_path: str, token_path: str):
    
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = self._authenticate_gmail(self)
        
       

    def _authenticate_gmail(self):
        creds=None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, EmailConfig.GMAIL_SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, EmailConfig.GMAIL_SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        self.service = build('gmail', 'v1', credentials=creds)
    
                
        