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
import os # Ensure this is also imported since you use os.getenv

class EmailConfig:
    
    GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.addons.current.message.readonly',
                     'https://www.googleapis.com/auth/gmail.modify',
                     'https://www.googleapis.com/auth/gmail.send']
   
    # gemini_model = "gemini-3-flash-preview"
    # gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class EmailConnector:
    def __init__(self,  credentials_path: str, token_path: str):
    
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = self._authenticate_gmail()
        
       

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
        return self.service
    def get_new_emails(self, query: str = 'is:unread', max_results: int = 10) -> List[Dict]:
        try:
            results= self.service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD'], q=query, maxResults=max_results).execute()
            messages = results.get('messages', [])
            return [self.get_message_details(msg['id']) for msg in messages]
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    def get_message_details(self, msg_id: str) -> Dict:
        try:
            message = self.service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            payload = message['payload']
            headers = payload.get('headers', [])
            subject = next((header['value'] for header in headers if header['name'] == 'Subject'), '')
            from_ = next((header['value'] for header in headers if header['name'] == 'From'), '')
            date = next((header['value'] for header in headers if header['name'] == 'Date'), '')
            body = self._get_email_body(payload)
            return {
                'id': msg_id,
                'subject': subject,
                'from': from_,
                'date': date,
                'body': body
            }
        except HttpError as error:
            print(f'An error occurred: {error}')
            return {}
    
    def _get_email_body(self, payload):
        if payload.get('mimeType') == 'text/plain':
            data = payload['body'].get('data')
        if data:
            return base64.urlsafe_b64decode(data).decode('utf-8')

        for part in payload.get('parts', []):
            text = self._get_email_body(part)
            if text:
                return text
        return ""

        def extract_attachments(self, msg_id: str) -> List[Tuple[str, bytes]]:
            attachments = []
            try:
                message = self.service.users().messages().get(userId='me', id=msg_id).execute()
                parts = message['payload'].get('parts', [])
                for part in parts:
                    if part['filename']:
                        att_id = part['body']['attachmentId']
                        att = self.service.users().messages().attachments().get(userId='me', messageId=msg_id, id=att_id).execute()
                        data = base64.urlsafe_b64decode(att['data'].encode('UTF-8'))
                        attachments.append((part['filename'], data))
                return attachments
            except HttpError as error:
                    print(f'An error occurred: {error}')
                    return []
    
if __name__ == "__main__":
        credential_path = 'D:\Helio\Helio\packages\src\email_service\client_secret_242213959124-6is5f6m49gi63kd67elcuk4tqbbbs0i0.apps.googleusercontent.com.json'
        connector = EmailConnector(credentials_path=credential_path, token_path='token.json')
        new_emails = connector.get_new_emails()
        for email in new_emails:
            print(f"Subject: {email['subject']}, From: {email['from']}, Date: {email['date']}")
            print(f"Body: {email['body'][:100]}...")  # Print first 100 characters of the body
                
        