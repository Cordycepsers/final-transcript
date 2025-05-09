from flask import Blueprint, request, jsonify
import time
from functools import wraps
from typing import Dict, Any, List
from ..transcription.rev_ai import handle_transcription_job, handle_webhook_callback, RevAiError
from ..transcription.quality import get_transcript_quality
from ..transcription.nlp import get_transcript_analysis
from ..storage.sheets import update_transcript

webhook_bp = Blueprint('webhook', __name__)

def retry_with_backoff(retries=3, backoff_in_seconds=1):
    """
    Retry decorator with exponential backoff.
    
    Args:
        retries: Number of times to retry the function
        backoff_in_seconds: Initial backoff time in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if i == retries - 1:  # Last attempt
                        raise
                    wait_time = (backoff_in_seconds * 2 ** i)  # Exponential backoff
                    time.sleep(wait_time)
            return func(*args, **kwargs)  # Final attempt
        return wrapper
    return decorator

def find_question_text(questions: List[Dict], question_id: str) -> str:
    """Find the question text from question ID."""
    for question in questions:
        if question.get("question_id") == question_id:
            return question.get("metadata", {}).get("text", "Unknown Question")
    return "Unknown Question"

def process_transcript(transcript_text: str, job_id: str) -> Dict[str, Any]:
    """Process transcript text with quality checks and NLP analysis."""
    quality_metrics = get_transcript_quality(job_id)
    
    if transcript_text:
        nlp_analysis = get_transcript_analysis(transcript_text)
        quality_metrics.update({
            "nlp_quality_score": nlp_analysis["quality_score"],
            "enhancement_warnings": nlp_analysis["enhancement_warnings"],
            "content_analysis": nlp_analysis["content_analysis"],
            "enhanced_text": nlp_analysis["enhanced_text"]
        })
    
    return quality_metrics

def handle_rev_ai_callback(data: Dict) -> Dict[str, Any]:
    """Handle Rev.ai webhook callback data."""
    try:
        callback_result = handle_webhook_callback(data)
        if callback_result.get("status") == "completed":
            # Process completed transcript
            job_id = callback_result["job_id"]
            transcript = callback_result["transcript"]
            metadata = callback_result["metadata"]
            
            transcript_text = transcript.get("monologues", [{}])[0].get("elements", [{}])[0].get("value", "")
            quality_metrics = process_transcript(transcript_text, job_id)
            
            if transcript_text:
                # Store in Google Sheets
                update_transcript(
                    email=metadata.get("email"),
                    question=metadata.get("question"),
                    media_url=metadata.get("media_url"),
                    transcript=quality_metrics["enhanced_text"],
                    quality_metrics=quality_metrics
                )
                
        return {"status": "processed"}
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

def handle_form_response(data: Dict) -> List[Dict[str, str]]:
    """Handle VideoAsk form response data."""
    errors = []
    contact = data.get("contact", {})
    answers = contact.get("answers", [])
    
    for answer in answers:
        if answer.get("media_url") and answer.get("type") in ["video", "audio"]:
            result = process_media_answer(
                answer,
                contact,
                data.get("form", {}),
                data.get("interaction_id")
            )
            
            if result and "error" in result:
                errors.append({
                    "media_url": result["media_url"],
                    "error": result["error"]
                })
                
    return errors

@retry_with_backoff(retries=3)
def process_media_answer(answer: Dict, contact: Dict, form_data: Dict, interaction_id: str) -> Dict[str, Any]:
    """Process a single video or audio answer from the webhook data."""
    media_url = answer["media_url"]
    question_id = answer.get("question_id", "Unknown")
    email = contact.get("email")
    name = contact.get("name", "Unknown")
    
    question_text = find_question_text(
        form_data.get("questions", []),
        question_id
    )
    
    try:
        # Submit transcription job
        job_result = handle_transcription_job(
            media_url=media_url,
            email=email,
            question=question_text,
            metadata={
                "name": name,
                "interaction_id": interaction_id,
                "answer_id": answer.get("answer_id"),
                "share_id": answer.get("share_id"),
                "answer_type": answer.get("type", "unknown")
            }
        )
        
        if job_result.get("status") == "completed" and "transcript" in job_result:
            transcript_text = job_result["transcript"].get("monologues", [{}])[0].get("elements", [{}])[0].get("value", "")
            quality_metrics = process_transcript(transcript_text, job_result["job_id"])
            
            if transcript_text:
                # Store in Google Sheets
                update_transcript(
                    email=email,
                    question=question_text,
                    media_url=media_url,
                    transcript=quality_metrics["enhanced_text"],
                    quality_metrics=quality_metrics
                )
        
        return job_result
        
    except RevAiError as e:
        return {"error": str(e), "media_url": media_url}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "media_url": media_url}

@webhook_bp.route('/webhook', methods=['POST'])
def videoask_webhook():
    """Receive VideoAsk webhook events."""
    data = request.json
    print("Received webhook:", data)
    
    response_data = {"status": "processed", "errors": []}
    
    try:
        if data.get("event_type") == "form_response":
            # Handle VideoAsk form response
            response_data["errors"].extend(handle_form_response(data))
            
        elif data.get("job"):
            # Handle Rev.ai callback
            callback_result = handle_rev_ai_callback(data)
            if "error" in callback_result:
                response_data["errors"].append({
                    "error": f"Callback processing error: {callback_result['error']}"
                })
                
    except Exception as e:
        response_data["errors"].append({
            "error": f"Webhook processing error: {str(e)}"
        })
    
    return jsonify(response_data)

@webhook_bp.route('/transcript/quality/<job_id>', methods=['GET'])
def check_transcript_quality(job_id: str):
    """Check the quality of a transcript."""
    try:
        # Get Rev.ai quality metrics
        quality_metrics = get_transcript_quality(job_id)
        
        if quality_metrics.get("status") == "completed":
            # Add NLP analysis if transcript is available
            transcript = quality_metrics.get("transcript", {})
            transcript_text = transcript.get("monologues", [{}])[0].get("elements", [{}])[0].get("value", "")
            quality_metrics = process_transcript(transcript_text, job_id)
        
        return jsonify(quality_metrics)
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500
