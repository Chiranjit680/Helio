from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.responses import JSONResponse, StreamingResponse
from email_service.models import (
    EmailSearchQuery,
    EmailSendRequest,
    EmailReplyRequest,
    EmailMarkReadRequest,
    EmailDetailsResponse,
    EmailOperationResponse
)
import io
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

        
router = APIRouter(
    prefix="/api/v1/email",
    tags=["Email"],
    responses={404: {"description": "Not found"}}
)

# Global connector instance (you might want to use dependency injection instead)
email_connector = None

def get_email_connector():
    """Dependency to get email connector instance"""
    global email_connector
    if email_connector is None:
        raise HTTPException(
            status_code=503,
            detail="Email connector not initialized. Please configure credentials."
        )
    return email_connector

def init_connector(credentials_path: str, token_path: str):
    """Initialize the email connector - call this at app startup"""
    global email_connector
    from email_connector import EmailConnector  # Import your connector
    email_connector = EmailConnector(credentials_path, token_path)
    logger.info("Email connector initialized")

# ================== Email Reading Endpoints ==================

@router.get("/unread", response_model=List[EmailDetailsResponse])
async def get_unread_emails(
    max_results: int = Query(default=10, ge=1, le=100, description="Maximum number of emails to fetch")
):
    """
    Retrieve unread emails from inbox
    
    Returns a list of unread email details including subject, sender, date, and body preview.
    """
    try:
        connector = get_email_connector()
        emails = connector.get_new_emails(query='is:unread', max_results=max_results)
        return emails
    except Exception as e:
        logger.error(f"Error fetching unread emails: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {str(e)}")

@router.get("/search", response_model=List[EmailDetailsResponse])
async def search_emails(
    query: str = Query(..., description="Gmail search query (e.g., 'from:example@gmail.com after:2024/1/1')"),
    max_results: int = Query(default=10, ge=1, le=100, description="Maximum number of results")
):
    """
    Search emails with custom Gmail query
    
    Supports Gmail search operators:
    - from:email@example.com
    - to:email@example.com
    - subject:keyword
    - has:attachment
    - is:unread, is:read
    - after:2024/1/1, before:2024/12/31
    - newer_than:7d, older_than:30d
    """
    try:
        connector = get_email_connector()
        emails = connector.search_emails(query=query, max_results=max_results)
        return emails
    except Exception as e:
        logger.error(f"Error searching emails: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/message/{message_id}", response_model=EmailDetailsResponse)
async def get_email_details(
    message_id: str
):
    """
    Get detailed information about a specific email
    
    Returns full email details including complete body and metadata.
    """
    try:
        connector = get_email_connector()
        email_details = connector.get_message_details(message_id)
        
        if not email_details:
            raise HTTPException(status_code=404, detail="Email not found")
        
        return email_details
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching email details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch email: {str(e)}")

# ================== Attachment Endpoints ==================

@router.get("/message/{message_id}/attachments")
async def list_attachments(message_id: str):
    """
    List all attachments for a specific email
    
    Returns attachment filenames and sizes without downloading the files.
    """
    try:
        connector = get_email_connector()
        attachments = connector.extract_attachments(message_id)
        
        attachment_list = [
            {
                "filename": filename,
                "size": len(data)
            }
            for filename, data in attachments
        ]
        
        return {
            "message_id": message_id,
            "attachment_count": len(attachment_list),
            "attachments": attachment_list
        }
    except Exception as e:
        logger.error(f"Error listing attachments: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list attachments: {str(e)}")

@router.get("/message/{message_id}/attachments/{filename}")
async def download_attachment(
    message_id: str,
    filename: str
):
    """
    Download a specific attachment from an email
    
    Returns the attachment file as a downloadable response.
    """
    try:
        connector = get_email_connector()
        attachments = connector.extract_attachments(message_id)
        
        # Find the requested attachment
        for att_filename, att_data in attachments:
            if att_filename == filename:
                return StreamingResponse(
                    io.BytesIO(att_data),
                    media_type="application/octet-stream",
                    headers={
                        "Content-Disposition": f"attachment; filename={filename}"
                    }
                )
        
        raise HTTPException(status_code=404, detail=f"Attachment '{filename}' not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading attachment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download attachment: {str(e)}")

# ================== Email Actions Endpoints ==================

@router.post("/mark-read", response_model=EmailOperationResponse)
async def mark_email_as_read(request: EmailMarkReadRequest):
    """
    Mark an email as read
    
    Removes the UNREAD label from the specified message.
    """
    try:
        connector = get_email_connector()
        success = connector.mark_as_read(request.message_id)
        
        if success:
            return EmailOperationResponse(
                success=True,
                message=f"Email {request.message_id} marked as read",
                data={"message_id": request.message_id}
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to mark email as read")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking email as read: {e}")
        raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")

@router.post("/send", response_model=EmailOperationResponse)
async def send_email(request: EmailSendRequest):
    """
    Send a new email
    
    Sends an email with the specified recipient, subject, and body.
    Optionally includes CC and BCC recipients.
    """
    try:
        connector = get_email_connector()
        success = connector.send_email(
            to=request.to,
            subject=request.subject,
            body=request.body,
            cc=request.cc,
            bcc=request.bcc
        )
        
        if success:
            return EmailOperationResponse(
                success=True,
                message=f"Email sent successfully to {request.to}",
                data={
                    "to": request.to,
                    "subject": request.subject
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@router.post("/reply", response_model=EmailOperationResponse)
async def reply_to_email(request: EmailReplyRequest):
    """
    Reply to an existing email
    
    Sends a reply to the specified message, maintaining the thread.
    """
    try:
        connector = get_email_connector()
        success = connector.reply_to_email(
            msg_id=request.message_id,
            body=request.body
        )
        
        if success:
            return EmailOperationResponse(
                success=True,
                message=f"Reply sent successfully",
                data={"original_message_id": request.message_id}
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to send reply")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error replying to email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send reply: {str(e)}")

# ================== Batch Operations ==================

@router.post("/batch/mark-read", response_model=EmailOperationResponse)
async def batch_mark_as_read(
    message_ids: List[str] = Body(..., embed=True)
):
    """
    Mark multiple emails as read in batch
    
    Processes multiple message IDs and marks them all as read.
    """
    try:
        connector = get_email_connector()
        results = []
        
        for msg_id in message_ids:
            success = connector.mark_as_read(msg_id)
            results.append({"message_id": msg_id, "success": success})
        
        successful = sum(1 for r in results if r["success"])
        
        return EmailOperationResponse(
            success=True,
            message=f"Marked {successful}/{len(message_ids)} emails as read",
            data={"results": results}
        )
        
    except Exception as e:
        logger.error(f"Error in batch mark as read: {e}")
        raise HTTPException(status_code=500, detail=f"Batch operation failed: {str(e)}")

# ================== Health Check ==================

@router.get("/health")
async def health_check():
    """
    Check if the email service is operational
    
    Returns the status of the email connector and API.
    """
    try:
        connector = get_email_connector()
        return {
            "status": "healthy",
            "service": "email",
            "timestamp": datetime.utcnow().isoformat(),
            "connector_initialized": connector is not None
        }
    except HTTPException as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "email",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e.detail)
            }
        )
