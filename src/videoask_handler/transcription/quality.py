"""Functions for checking transcript quality."""
import json
import time
import requests
from ..config import REV_AI_API_URL, REV_AI_API_KEY
from .media_quality import analyze_media_quality

def get_transcript_quality(job_id):
    """
    Get transcript quality metrics from Rev.ai.
    
    Args:
        job_id (str): The Rev.ai job ID
        
    Returns:
        dict: Quality metrics including confidence scores and warning flags
    """
    # Headers for Rev.ai API
    headers = {
        "Authorization": f"Bearer {REV_AI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Get job details first
    job_url = f"{REV_AI_API_URL}/jobs/{job_id}"
    job_response = requests.get(job_url, headers=headers)
    job_response.raise_for_status()
    job_status = job_response.json()
    
    # Get media quality metrics
    media_url = job_status.get("media_url")
    media_quality = analyze_media_quality(media_url, headers=headers) if media_url else {
        "quality_level": "unknown",
        "warning": "Media URL not found in job details"
    }
    
    if job_status["status"] != "completed":
        return {
            "status": job_status["status"],
            "message": "Transcript not ready yet",
            "media_quality": media_quality
        }
    
    # Get the transcript
    transcript_url = f"{REV_AI_API_URL}/jobs/{job_id}/transcript"
    transcript_response = requests.get(
        transcript_url,
        headers={"Authorization": f"Bearer {REV_AI_API_KEY}"}
    )
    transcript_response.raise_for_status()
    transcript = transcript_response.json()
    
    # Calculate quality metrics
    total_confidence = 0
    low_confidence_words = []
    monologues = transcript.get("monologues", [])
    total_words = 0
    
    for monologue in monologues:
        for element in monologue.get("elements", []):
            if element["type"] == "text":
                total_words += 1
                confidence = element.get("confidence", 0)
                total_confidence += confidence
                
                if confidence < 0.8:  # Flag words with less than 80% confidence
                    low_confidence_words.append({
                        "word": element["value"],
                        "confidence": confidence,
                        "timestamp": element["ts"]
                    })
    
    # Calculate overall metrics
    avg_confidence = total_confidence / total_words if total_words > 0 else 0
    quality_metrics = {
        "status": "completed",
        "overall_confidence": avg_confidence,
        "total_words": total_words,
        "low_confidence_count": len(low_confidence_words),
        "low_confidence_words": low_confidence_words,
        "quality_rating": "good" if avg_confidence > 0.9 else "fair" if avg_confidence > 0.8 else "poor",
        "warnings": []
    }
    
    # Add quality warnings
    if avg_confidence < 0.8:
        quality_metrics["warnings"].append("Low overall confidence score")
    if len(low_confidence_words) / total_words > 0.1:
        quality_metrics["warnings"].append("High number of uncertain words")
    
    return quality_metrics
