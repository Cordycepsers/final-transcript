from flask import Blueprint, request, jsonify
from ..transcription.rev_ai import handle_transcription_job
from ..transcription.quality import get_transcript_quality

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/webhook', methods=['POST'])
def videoask_webhook():
    """Receive VideoAsk webhook events."""
    data = request.json
    print("Received webhook:", data)
    
    response_data = {"status": "processed", "errors": []}
    
    # Extract media URL and other details
    for answer in data.get("answers", []):
        if "media_url" in answer:
            media_url = answer["media_url"]
            email = data["contact"]["email"]
            question = answer.get("poll_option_content", "Unknown Question")
            
            # Trigger transcription job
            result = handle_transcription_job(media_url, email, question)
            
            # Handle any errors
            if result and "error" in result:
                response_data["errors"].append({
                    "media_url": media_url,
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
    
    return jsonify({"status": "success"}), 200
