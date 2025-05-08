"""Test Rev.ai integration."""
import json
import responses
import pytest
from unittest.mock import patch
from src.videoask_handler.config import REV_AI_API_URL
from src.videoask_handler.transcription.rev_ai import validate_media_format

@pytest.fixture
def mock_rev_ai_response():
    """Mock successful Rev.ai API response."""
    return {
        "id": "test_job_123",
        "status": "in_progress",
        "created_on": "2025-05-08T12:00:00Z"
    }

def test_media_format_validation():
    """Test media format validation."""
    # Test valid formats
    valid_formats = [
        "https://example.com/audio.mp3",
        "https://example.com/video.mp4",
        "https://example.com/audio.flac",
        "https://example.com/audio.wav",
    ]
    for url in valid_formats:
        is_valid, message = validate_media_format(url)
        assert is_valid, f"Should accept {url}"
    
    # Test invalid formats
    invalid_formats = [
        "https://example.com/doc.pdf",
        "https://example.com/file.txt",
        "https://example.com/noextension",
    ]
    for url in invalid_formats:
        is_valid, message = validate_media_format(url)
        assert not is_valid, f"Should reject {url}"

@responses.activate
def test_transcription_job_submission(client, mock_rev_ai_response):
    """Test submitting a transcription job to Rev.ai."""
    # Mock Rev.ai API endpoint
    responses.add(
        responses.POST,
        REV_AI_API_URL,
        json=mock_rev_ai_response,
        status=200
    )
    
    # Test data
    payload = {
        "contact": {
            "email": "test@example.com"
        },
        "answers": [
            {
                "media_url": "https://example.com/test-video.mp4",
                "poll_option_content": "Test Question"
            }
        ]
    }
    
    # Send webhook request
    response = client.post(
        '/webhook',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    
    # Verify Rev.ai API was called correctly
    assert len(responses.calls) == 1
    rev_ai_request = json.loads(responses.calls[0].request.body)
    assert rev_ai_request["media_url"] == "https://example.com/test-video.mp4"
    assert rev_ai_request["metadata"]["email"] == "test@example.com"

@responses.activate
def test_transcription_job_error_handling(client):
    """Test handling Rev.ai API errors."""
    # Mock Rev.ai API endpoint with error
    responses.add(
        responses.POST,
        REV_AI_API_URL,
        json={"error": "Invalid API key"},
        status=401
    )
    
    payload = {
        "contact": {
            "email": "test@example.com"
        },
        "answers": [
            {
                "media_url": "https://example.com/test-video.mp4",
                "poll_option_content": "Test Question"
            }
        ]
    }
    
    # Send webhook request
    response = client.post(
        '/webhook',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    # Even if Rev.ai fails, webhook should still return 200
    # as we don't want VideoAsk to retry
    assert response.status_code == 200
