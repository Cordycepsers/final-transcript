"""Manual transcription request endpoints."""
from flask import Blueprint, request, jsonify
from typing import Dict, Any, List, Optional
from ..transcription.rev_ai import (
    handle_transcription_job,
    check_job_status,
    get_transcript,
    validate_media_format
)
from ..transcription.nlp import get_transcript_analysis
from ..transcription.quality import get_transcript_quality
from ..storage.sheets import update_transcript

manual_bp = Blueprint('manual', __name__)

def validate_request(data: Dict) -> Optional[str]:
    """
    Validate manual transcription request.
    
    Args:
        data: Request data dictionary
        
    Returns:
        str: Error message if validation fails, None if valid
    """
    if not data.get("media_url"):
        return "media_url is required"
        
    is_valid, message = validate_media_format(data["media_url"])
    if not is_valid:
        return message
        
    if not data.get("email"):
        return "email is required"
        
    return None

@manual_bp.route('/transcribe', methods=['POST'])
def request_transcription():
    """
    Submit a manual transcription request.
    
    Request body:
    {
        "media_url": "https://example.com/video.mp4",
        "email": "user@example.com",
        "question": "Optional question context",
        "wait_for_completion": false,
        "max_wait_time": 300
    }
    """
    data = request.json
    error = validate_request(data)
    if error:
        return jsonify({"error": error}), 400
        
    try:
        result = handle_transcription_job(
            media_url=data["media_url"],
            email=data["email"],
            question=data.get("question", "Manual request"),
            wait_for_completion=data.get("wait_for_completion", False),
            max_wait_time=data.get("max_wait_time", 300)
        )
        
        if result.get("status") == "completed" and "transcript" in result:
            # Process transcript with NLP and quality checks
            transcript_text = result["transcript"].get("monologues", [{}])[0].get("elements", [{}])[0].get("value", "")
            if transcript_text:
                quality_metrics = get_transcript_quality(result["job_id"])
                nlp_analysis = get_transcript_analysis(transcript_text)
                
                # Update quality metrics
                quality_metrics.update({
                    "nlp_quality_score": nlp_analysis["quality_score"],
                    "enhancement_warnings": nlp_analysis["enhancement_warnings"],
                    "content_analysis": nlp_analysis["content_analysis"]
                })
                
                # Store in Google Sheets
                update_transcript(
                    email=data["email"],
                    question=data.get("question", "Manual request"),
                    media_url=data["media_url"],
                    transcript=nlp_analysis["enhanced_text"],
                    quality_metrics=quality_metrics
                )
                
                return jsonify({
                    "status": "completed",
                    "job_id": result["job_id"],
                    "transcript": nlp_analysis["enhanced_text"],
                    "quality_metrics": quality_metrics
                })
        
        # For non-completed jobs, return job details
        return jsonify({
            "status": result.get("status", "unknown"),
            "job_id": result.get("id"),
            "message": "Transcription job submitted successfully"
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@manual_bp.route('/status/<job_id>', methods=['GET'])
def check_status(job_id: str):
    """
    Check status of a transcription job.
    """
    try:
        status = check_job_status(job_id)
        if status.get("status") == "completed":
            # Get transcript and quality metrics
            transcript = get_transcript(job_id)
            transcript_text = transcript.get("monologues", [{}])[0].get("elements", [{}])[0].get("value", "")
            
            if transcript_text:
                quality_metrics = get_transcript_quality(job_id)
                nlp_analysis = get_transcript_analysis(transcript_text)
                quality_metrics.update({
                    "nlp_quality_score": nlp_analysis["quality_score"],
                    "content_analysis": nlp_analysis["content_analysis"]
                })
                
                return jsonify({
                    "status": "completed",
                    "transcript": nlp_analysis["enhanced_text"],
                    "quality_metrics": quality_metrics
                })
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@manual_bp.route('/batch', methods=['POST'])
def batch_transcribe():
    """
    Submit multiple transcription requests.
    
    Request body:
    {
        "requests": [
            {
                "media_url": "https://example.com/video1.mp4",
                "email": "user@example.com",
                "question": "Optional question 1"
            },
            ...
        ]
    }
    """
    data = request.json
    if not data.get("requests"):
        return jsonify({"error": "requests array is required"}), 400
        
    results = []
    for req in data["requests"]:
        error = validate_request(req)
        if error:
            results.append({
                "media_url": req.get("media_url"),
                "error": error,
                "status": "error"
            })
            continue
            
        try:
            result = handle_transcription_job(
                media_url=req["media_url"],
                email=req["email"],
                question=req.get("question", "Batch request")
            )
            
            results.append({
                "media_url": req["media_url"],
                "job_id": result.get("id"),
                "status": result.get("status", "unknown")
            })
            
        except Exception as e:
            results.append({
                "media_url": req["media_url"],
                "error": str(e),
                "status": "error"
            })
    
    return jsonify({
        "results": results,
        "total": len(results),
        "failed": len([r for r in results if r.get("status") == "error"])
    })
