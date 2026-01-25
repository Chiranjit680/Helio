import os
import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
import re
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[3]
class EmailConfig:
    """Configuration for Gmail API"""
    GMAIL_SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.send'
    ]


class EmailConnector:
    """Gmail connector for reading, processing, and sending emails"""
    
    def __init__(self, credentials_path: str, token_path: str):
        """
        Initialize the Gmail connector
        
        Args:
            credentials_path: Path to OAuth credentials JSON file
            token_path: Path to store/load authentication token
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self._authenticate_gmail()

    def _authenticate_gmail(self):
        """Authenticate with Gmail API using OAuth 2.0"""
        creds = None
        
        # Load existing credentials if available
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(
                    self.token_path, 
                    EmailConfig.GMAIL_SCOPES
                )
            except Exception as e:
                logger.warning(f"Could not load token file: {e}")
        
        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Token refresh failed: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_path}"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, 
                    EmailConfig.GMAIL_SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail authentication successful")

    def get_new_emails(self, query: str = 'is:unread', max_results: int = 10) -> List[Dict]:
        """
        Retrieve new/unread emails
        
        Args:
            query: Gmail search query (default: unread emails)
            max_results: Maximum number of emails to retrieve
            
        Returns:
            List of email dictionaries with details
        """
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                logger.info("No messages found")
                return []
            
            emails = []
            for msg in messages:
                email_details = self.get_message_details(msg['id'])
                if email_details:
                    emails.append(email_details)
            
            logger.info(f"Retrieved {len(emails)} emails")
            return emails
            
        except HttpError as error:
            logger.error(f'Gmail API error: {error}')
            return []

    def get_message_details(self, msg_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific email
        
        Args:
            msg_id: Gmail message ID
            
        Returns:
            Dictionary with email details or None if error
        """
        try:
            message = self.service.users().messages().get(
                userId='me', 
                id=msg_id, 
                format='full'
            ).execute()
            
            payload = message['payload']
            headers = payload.get('headers', [])
            
            # Extract key headers
            subject = self._get_header(headers, 'Subject')
            from_ = self._get_header(headers, 'From')
            to = self._get_header(headers, 'To')
            date = self._get_header(headers, 'Date')
            
            # Extract email body
            body = self._get_email_body(payload)
            
            # Check if email has attachments
            has_attachments = self._has_attachments(payload)
            
            return {
                'id': msg_id,
                'subject': subject,
                'from': from_,
                'to': to,
                'date': date,
                'body': body,
                'has_attachments': has_attachments,
                'labels': message.get('labelIds', [])
            }
            
        except HttpError as error:
            logger.error(f'Error getting message details: {error}')
            return None

    def _get_header(self, headers: List[Dict], name: str) -> str:
        """Extract specific header value from headers list"""
        return next(
            (header['value'] for header in headers if header['name'] == name), 
            ''
        )

    def _get_email_body(self, payload: Dict) -> str:
        """
        Extract email body, preferring plain text over HTML
        
        Args:
            payload: Email payload from Gmail API
            
        Returns:
            Email body as string
        """
        # Handle single-part messages
        if payload.get('mimeType') == 'text/plain':
            data = payload.get('body', {}).get('data')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8')
        
        # Handle multipart messages
        if 'parts' in payload:
            # First try to find plain text
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    data = part.get('body', {}).get('data')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8')
            
            # Fallback to HTML if no plain text
            for part in payload['parts']:
                if part.get('mimeType') == 'text/html':
                    data = part.get('body', {}).get('data')
                    if data:
                        html_content = base64.urlsafe_b64decode(data).decode('utf-8')
                        # Strip HTML tags for basic text extraction
                        return self._strip_html(html_content)
            
            # Recursively check nested parts
            for part in payload['parts']:
                if 'parts' in part:
                    body = self._get_email_body(part)
                    if body:
                        return body
        
        return ""

    def _strip_html(self, html: str) -> str:
        """Basic HTML tag removal"""
        text = re.sub('<[^<]+?>', '', html)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _has_attachments(self, payload: Dict) -> bool:
        """Check if email has attachments"""
        parts = payload.get('parts', [])
        for part in parts:
            if part.get('filename'):
                return True
        return False

    def extract_attachments(self, msg_id: str) -> List[Tuple[str, bytes]]:
        """
        Extract all attachments from an email
        
        Args:
            msg_id: Gmail message ID
            
        Returns:
            List of tuples (filename, file_data)
        """
        attachments = []
        try:
            message = self.service.users().messages().get(
                userId='me', 
                id=msg_id
            ).execute()
            
            parts = message['payload'].get('parts', [])
            
            for part in parts:
                filename = part.get('filename')
                if filename:
                    att_id = part['body'].get('attachmentId')
                    if att_id:
                        att = self.service.users().messages().attachments().get(
                            userId='me', 
                            messageId=msg_id, 
                            id=att_id
                        ).execute()
                        data = base64.urlsafe_b64decode(att['data'].encode('UTF-8'))
                        attachments.append((filename, data))
            
            logger.info(f"Extracted {len(attachments)} attachments from message {msg_id}")
            return attachments
            
        except HttpError as error:
            logger.error(f'Error extracting attachments: {error}')
            return []

    def mark_as_read(self, msg_id: str) -> bool:
        """
        Mark an email as read
        
        Args:
            msg_id: Gmail message ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            logger.info(f"Marked message {msg_id} as read")
            return True
        except HttpError as error:
            logger.error(f'Error marking message as read: {error}')
            return False

    def send_email(self, to: str, subject: str, body: str, 
                   cc: Optional[str] = None, 
                   bcc: Optional[str] = None) -> bool:
        """
        Send an email
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
            
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')
            
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email sent to {to}")
            return True
            
        except HttpError as error:
            logger.error(f'Error sending email: {error}')
            return False

    def reply_to_email(self, msg_id: str, body: str) -> bool:
        """
        Reply to an email
        
        Args:
            msg_id: Original message ID
            body: Reply body text
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get original message
            original = self.service.users().messages().get(
                userId='me', 
                id=msg_id
            ).execute()
            
            headers = original['payload']['headers']
            subject = self._get_header(headers, 'Subject')
            from_ = self._get_header(headers, 'From')
            message_id = self._get_header(headers, 'Message-ID')
            
            # Create reply
            reply = MIMEText(body)
            reply['to'] = from_
            reply['subject'] = f"Re: {subject}" if not subject.startswith('Re:') else subject
            reply['In-Reply-To'] = message_id
            reply['References'] = message_id
            
            raw_message = base64.urlsafe_b64encode(
                reply.as_bytes()
            ).decode('utf-8')
            
            self.service.users().messages().send(
                userId='me',
                body={
                    'raw': raw_message,
                    'threadId': original['threadId']
                }
            ).execute()
            
            logger.info(f"Reply sent for message {msg_id}")
            return True
            
        except HttpError as error:
            logger.error(f'Error replying to email: {error}')
            return False

    def search_emails(self, query: str, max_results: int = 100) -> List[Dict]:
        """
        Search emails with custom query
        
        Args:
            query: Gmail search query (e.g., 'from:example@gmail.com after:2024/1/1')
            max_results: Maximum results to return
            
        Returns:
            List of matching emails
        """
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            emails = []
            for msg in messages:
                email_details = self.get_message_details(msg['id'])
                if email_details:
                    emails.append(email_details)
            
            logger.info(f"Search '{query}' returned {len(emails)} results")
            return emails
            
        except HttpError as error:
            logger.error(f'Search error: {error}')
            return []


def main():
    """Example usage"""
    # Use environment variables or update these paths
    
    
    BASE_DIR = Path(__file__).resolve().parents[3]
    credentials_path = Path(
    os.getenv("GMAIL_CREDENTIALS_PATH", BASE_DIR / "credentials.json")
).resolve()

    token_path = Path(
    os.getenv("GMAIL_TOKEN_PATH", BASE_DIR / "storage" / "token.json")
).resolve()

    logging.info("Credentials Path: %s", credentials_path)
    logging.info("Token Path: %s", token_path)
    
    try:
        # Initialize connector
        connector = EmailConnector(
            credentials_path=credentials_path,
            token_path=token_path
        )
        
        # Get unread emails
        print("\n=== Fetching Unread Emails ===")
        new_emails = connector.get_new_emails(max_results=5)
        
        for email_data in new_emails:
            print(f"\nSubject: {email_data['subject']}")
            print(f"From: {email_data['from']}")
            print(f"Date: {email_data['date']}")
            print(f"Has Attachments: {email_data['has_attachments']}")
            print(f"Body Preview: {email_data['body'][:150]}...")
            
            # Example: Mark as read
            # connector.mark_as_read(email_data['id'])
            
            # Example: Extract attachments
            if email_data['has_attachments']:
                attachments = connector.extract_attachments(email_data['id'])
                print(f"Attachments: {[name for name, _ in attachments]}")
        
        # Example: Search emails
        print("\n=== Searching Emails ===")
        search_results = connector.search_emails(
            query='from:noreply@github.com newer_than:7d',
            max_results=5
        )
        print(f"Found {len(search_results)} emails from GitHub in the last 7 days")
        
        # Example: Send email
        # connector.send_email(
        #     to='recipient@example.com',
        #     subject='Test Email',
        #     body='This is a test email sent via Gmail API'
        # )
        
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()