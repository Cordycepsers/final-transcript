from flask import Blueprint, request, jsonify
from ..transcription.rev_ai import handle_transcription_job
from ..transcription.quality import get_transcript_quality

webhook_bp = Blueprint('webhook', __name__)

def find_question_text(questions, question_id):
    """Find the question text from question ID."""
    for question in questions:
        if question.get("question_id") == question_id:
            return question.get("metadata", {}).get("text", "Unknown Question")
    return "Unknown Question"

def process_media_answer(answer, contact, form_data, interaction_id):
    """Process a single video or audio answer from the webhook data."""
    media_url = answer["media_url"]
    question_id = answer.get("question_id", "Unknown")
    email = contact.get("email")
    name = contact.get("name", "Unknown")
    
    question_text = find_question_text(
        form_data.get("questions", []),
        question_id
    )
    
    return handle_transcription_job(
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

@webhook_bp.route('/webhook', methods=['POST'])
def videoask_webhook():
    """Receive VideoAsk webhook events."""
    data = request.json
    print("Received webhook:", data)
    
    response_data = {"status": "processed", "errors": []}
    
    # Handle VideoAsk form_response event
    if data.get("event_type") == "form_response":
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
                    response_data["errors"].append({
                        "media_url": answer["media_url"],
                        "error": result["error"]
                    })
    
    return jsonify(response_data)

@webhook_bp.route('/transcript/quality/<job_id>', methods=['GET'])
def check_transcript_quality(job_id):
    """Check the quality of a transcript."""
    try:
        quality_metrics = get_transcript_quality(job_id)
        return jsonify(quality_metrics)
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500
