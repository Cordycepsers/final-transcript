"""Test transcript quality checking."""
import json
import pytest
import responses
from src.videoask_handler.config import REV_AI_API_URL

@pytest.fixture
def mock_completed_job_response():
    """Mock response for a completed transcription job."""
    return {
        "id": "test_job_123",
        "status": "completed",
        "created_on": "2025-05-08T12:00:00Z"
    }

@pytest.fixture
def mock_transcript_response():
    """Mock transcript response with quality data."""
    return {
        "monologues": [
            {
                "speaker": 1,
                "elements": [
                    {
                        "type": "text",
                        "value": "Hello",
                        "ts": 0.5,
                        "confidence": 0.95
                    },
                    {
                        "type": "text",
                        "value": "world",
                        "ts": 1.0,
                        "confidence": 0.75
                    }
                ]
            }
        ]
    }

@responses.activate
def test_transcript_quality_check(client, mock_completed_job_response, mock_transcript_response):
    """Test checking transcript quality."""
    job_id = "test_job_123"
    
    # Mock the job status endpoint
    responses.add(
        responses.GET,
        f"{REV_AI_API_URL}/jobs/{job_id}",
        json=mock_completed_job_response,
        status=200
    )
    
    # Mock the transcript endpoint
    responses.add(
        responses.GET,
        f"{REV_AI_API_URL}/jobs/{job_id}/transcript",
        json=mock_transcript_response,
        status=200
    )
    
    # Check quality
    response = client.get(f'/transcript/quality/{job_id}')
    assert response.status_code == 200
    
    quality_data = json.loads(response.data)
    assert quality_data["status"] == "completed"
    assert "overall_confidence" in quality_data
    assert "quality_rating" in quality_data
    assert "low_confidence_words" in quality_data
    
    # Verify quality metrics
    assert len(quality_data["low_confidence_words"]) == 1  # "world" has low confidence
    assert quality_data["total_words"] == 2
    
@responses.activate
def test_incomplete_transcript_quality(client):
    """Test checking quality of incomplete transcript."""
    job_id = "test_job_456"
    
    # Mock job status endpoint for incomplete job
    responses.add(
        responses.GET,
        f"{REV_AI_API_URL}/jobs/{job_id}",
        json={
            "id": job_id,
            "status": "in_progress"
        },
        status=200
    )
    
    # Check quality
    response = client.get(f'/transcript/quality/{job_id}')
    assert response.status_code == 200
    
    quality_data = json.loads(response.data)
    assert quality_data["status"] == "in_progress"
    assert quality_data["message"] == "Transcript not ready yet"
