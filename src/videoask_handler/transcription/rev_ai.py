"""Rev.ai transcription service integration."""
import os
import time
import logging
import requests
from typing import Dict, Optional, Tuple, Union
from urllib.parse import urlparse
from ..config import (
    REV_AI_API_KEY,
    REV_AI_API_URL,
    SUPPORTED_AUDIO_FORMATS,
    WEBHOOK_CALLBACK_URL,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RevAiError(Exception):
    """Custom exception for Rev.ai API errors."""
    pass

def get_file_extension(url: str) -> Optional[str]:
    """Extract file extension from URL."""
    path = urlparse(url).path
    return path.split('.')[-1].lower() if '.' in path else None

def validate_media_format(media_url: str) -> Tuple[bool, str]:
    """
    Validate if the media file format is supported.
    
    Args:
        media_url (str): URL of the media file to check
        
    Returns:
        Tuple[bool, str]: A tuple containing (is_valid, message)
    """
    ext = get_file_extension(media_url)
    
    if not ext:
        return False, "Could not determine file format"
        
    if ext not in SUPPORTED_AUDIO_FORMATS:
        return False, f"Unsupported file format: {ext}. Supported formats: {', '.join(SUPPORTED_AUDIO_FORMATS)}"
        
    return True, "File format is supported"

def get_headers() -> Dict[str, str]:
    """
    Get headers for Rev.ai API requests.
    
    Returns:
        Dict[str, str]: Headers dictionary with authorization and content type
    """
    return {
        "Authorization": f"Bearer {REV_AI_API_KEY}",
        "Content-Type": "application/json"
    }

def check_job_status(job_id: str) -> Dict[str, any]:
    """
    Check the status of a transcription job.
    
    Args:
        job_id (str): The ID of the job to check
        
    Returns:
        Dict[str, any]: Job status information dictionary
        
    Raises:
        RevAiError: If there's an error checking the job status
    """
    try:
        response = requests.get(
            f"{REV_AI_API_URL}/jobs/{job_id}",
            headers=get_headers()
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking job status: {e}")
        raise RevAiError(f"Failed to check job status: {e}")

def get_transcript(job_id: str) -> Dict[str, any]:
    """
    Retrieve the transcript for a completed job.
    
    Args:
        job_id (str): The ID of the completed job
        
    Returns:
        Dict[str, any]: The transcript data dictionary
        
    Raises:
        RevAiError: If there's an error retrieving the transcript
    """
    try:
        response = requests.get(
            f"{REV_AI_API_URL}/jobs/{job_id}/transcript",
            headers=get_headers()
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error retrieving transcript: {e}")
        raise RevAiError(f"Failed to retrieve transcript: {e}")

def handle_transcription_job(
    media_url: str,
    email: str,
    question: str,
    wait_for_completion: bool = False,
    max_wait_time: int = 300
) -> Dict[str, any]:
    """
    Submit a transcription job to Rev.ai.
    
    Args:
        media_url (str): URL of the media file to transcribe
        email (str): Email address of the contact
        question (str): The question being answered in the video/audio
        wait_for_completion (bool): Whether to wait for job completion
        max_wait_time (int): Maximum time to wait in seconds
        
    Returns:
        Dict[str, any]: Response from Rev.ai API containing job information
        
    Raises:
        RevAiError: If there's an error with the transcription process
    """
    if not REV_AI_API_KEY:
        error_msg = "REV_AI_API_KEY not configured"
        logger.error(error_msg)
        raise RevAiError(error_msg)
    
    if not WEBHOOK_CALLBACK_URL and not wait_for_completion:
        error_msg = "WEBHOOK_CALLBACK_URL not configured"
        logger.error(error_msg)
        raise RevAiError(error_msg)
    
    # Validate media format
    is_valid, message = validate_media_format(media_url)
    if not is_valid:
        logger.error(message)
        raise RevAiError(message)
    
    # Prepare job submission payload
    payload = {
        "media_url": media_url,
        "metadata": {
            "email": email,
            "question": question
        }
    }
    
    # Add webhook config if URL is provided
    if WEBHOOK_CALLBACK_URL:
        payload["notification_config"] = {
            "url": WEBHOOK_CALLBACK_URL,
            "method": "POST"
        }
    
    try:
        # Submit job
        response = requests.post(
            f"{REV_AI_API_URL}/jobs",
            json=payload,
            headers=get_headers()
        )
        response.raise_for_status()
        job_data = response.json()
        job_id = job_data.get("id")
        
        logger.info(f"Successfully submitted transcription job {job_id} for {email}")
        
        # If waiting for completion is requested
        if wait_for_completion and job_id:
            start_time = time.time()
            while time.time() - start_time < max_wait_time:
                status = check_job_status(job_id)
                if status.get("status") == "completed":
                    transcript = get_transcript(job_id)
                    return {
                        "job_id": job_id,
                        "status": "completed",
                        "transcript": transcript
                    }
                elif status.get("status") == "failed":
                    error_msg = f"Transcription job {job_id} failed: {status.get('failure_detail')}"
                    logger.error(error_msg)
                    raise RevAiError(error_msg)
                time.sleep(10)  # Wait 10 seconds before checking again
                
            raise RevAiError(f"Transcription job {job_id} did not complete within {max_wait_time} seconds")
        
        return job_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error submitting transcription job: {e}")
        raise RevAiError(f"Failed to submit transcription job: {e}")

def handle_webhook_callback(callback_data: Dict[str, any]) -> Dict[str, any]:
    """
    Handle webhook callbacks from Rev.ai for completed transcriptions.
    
    Args:
        callback_data (Dict[str, any]): The webhook callback data from Rev.ai
        
    Returns:
        Dict[str, any]: Processed callback data with transcript if available
        
    Raises:
        RevAiError: If there's an error processing the callback
    """
    job_id = callback_data.get("job", {}).get("id")
    if not job_id:
        error_msg = "No job ID in callback data"
        logger.error(error_msg)
        raise RevAiError(error_msg)
    
    status = callback_data.get("job", {}).get("status")
    
    if status == "completed":
        try:
            transcript = get_transcript(job_id)
            return {
                "job_id": job_id,
                "status": "completed",
                "transcript": transcript,
                "metadata": callback_data.get("job", {}).get("metadata", {})
            }
        except RevAiError as e:
            logger.error(f"Error retrieving transcript for completed job {job_id}: {e}")
            raise
    elif status == "failed":
        error_msg = f"Job {job_id} failed: {callback_data.get('job', {}).get('failure_detail')}"
        logger.error(error_msg)
        raise RevAiError(error_msg)
    
    return {"job_id": job_id, "status": status}
