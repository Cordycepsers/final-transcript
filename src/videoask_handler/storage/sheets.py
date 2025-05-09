"""Google Sheets integration for storing transcription results."""
import os
from typing import Dict, List, Optional
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from ..config import (
    SPREADSHEET_ID,
    SHEET_NAME,
    SCOPES,
    QUESTION_COLUMN_MAP,
    EMAIL_COLUMN_INDEX,
)

def get_credentials() -> Optional[Credentials]:
    """Get Google Sheets API credentials."""
    try:
        creds = None
        if os.path.exists('credentials.json'):
            creds = Credentials.from_service_account_file(
                'credentials.json',
                scopes=SCOPES
            )
        return creds
    except Exception as e:
        print(f"Error getting credentials: {e}")
        return None

def init_sheets_service():
    """Initialize Google Sheets service."""
    creds = get_credentials()
    if not creds:
        raise Exception("Could not get Google Sheets credentials")
    
    service = build('sheets', 'v4', credentials=creds)
    return service.spreadsheets()

def find_email_row(sheets, email: str) -> Optional[int]:
    """Find row number for an email address."""
    try:
        result = sheets.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!E:E"  # Email column
        ).execute()
        
        values = result.get('values', [])
        for i, row in enumerate(values):
            if row and row[0] == email:
                return i + 1  # 1-based row index
        return None
        
    except Exception as e:
        print(f"Error finding email row: {e}")
        return None

def update_transcript(
    email: str,
    question: str,
    media_url: str,
    transcript: str,
    quality_metrics: Dict
) -> bool:
    """
    Update transcript in Google Sheets.
    
    Args:
        email: Contact email
        question: Question text
        media_url: URL of the media file
        transcript: Transcribed text
        quality_metrics: Quality metrics dictionary
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        sheets = init_sheets_service()
        
        # Find or create row for email
        row_num = find_email_row(sheets, email)
        if not row_num:
            # If email not found, get last row and append
            result = sheets.values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A:A"
            ).execute()
            row_num = len(result.get('values', [])) + 1
        
        # Get column mapping for question
        cols = QUESTION_COLUMN_MAP.get(question, {})
        if not cols:
            print(f"No column mapping found for question: {question}")
            return False
            
        # Update media link
        sheets.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!{cols['link_col']}{row_num}",
            valueInputOption="RAW",
            body={"values": [[media_url]]}
        ).execute()
        
        # Update transcript with quality note
        quality_note = ""
        if quality_metrics:
            confidence = quality_metrics.get("overall_confidence", 0)
            warnings = quality_metrics.get("warnings", [])
            if warnings:
                quality_note = f"\n\nQuality Notes:\n- Confidence: {confidence:.2%}\n"
                quality_note += "\n".join(f"- {w}" for w in warnings)
                
        transcript_with_notes = f"{transcript}\n{quality_note}".strip()
        
        sheets.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!{cols['transcript_col']}{row_num}",
            valueInputOption="RAW",
            body={"values": [[transcript_with_notes]]}
        ).execute()
        
        return True
        
    except Exception as e:
        print(f"Error updating transcript in sheets: {e}")
        return False
