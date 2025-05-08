"""Rev.ai transcription service integration."""
import os
import requests
from urllib.parse import urlparse
from ..config import REV_AI_API_KEY, REV_AI_API_URL, SUPPORTED_AUDIO_FORMATS

def get_file_extension(url):
    """Extract file extension from URL."""
    path = urlparse(url).path
    return path.split('.')[-1].lower() if '.' in path else None

def validate_media_format(media_url):
    """
    Validate if the media file format is supported.
    
    Args:
        media_url (str): URL of the media file to check
        
    Returns:
        tuple: (is_valid, message)
    """
    ext = get_file_extension(media_url)
    
    if not ext:
        return False, "Could not determine file format"
        
    if ext not in SUPPORTED_AUDIO_FORMATS:
        return False, f"Unsupported file format: {ext}. Supported formats: {', '.join(SUPPORTED_AUDIO_FORMATS)}"
        
    return True, "File format is supported"

def handle_transcription_job(media_url, email, question):
    """
    Submit a transcription job to Rev.ai.
    
    Args:
        media_url (str): URL of the media file to transcribe
        email (str): Email address of the contact
        question (str): The question being answered in the video
        
    Returns:
        dict: Response from Rev.ai API or error information
    """
    if not REV_AI_API_KEY:
        print("Error: REV_AI_API_KEY not configured")
        return {"error": "API key not configured"}
    
    # Validate media format
    is_valid, message = validate_media_format(media_url)
    if not is_valid:
        print(f"Error: {message}")
        return {"error": message}
    
    # Rev.ai API endpoint for submitting jobs
    url = f"{REV_AI_API_URL}/jobs"
    
    headers = {
        "Authorization": f"Bearer {REV_AI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Submit job to Rev.ai
    payload = {
        "media_url": media_url,
        "metadata": {
            "email": email,
            "question": question
        },
        "notification_config": {
            "url": os.getenv("WEBHOOK_CALLBACK_URL"),
            "method": "POST"
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        print(f"Successfully submitted transcription job for {email}")
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error submitting transcription job: {e}")
        return None
