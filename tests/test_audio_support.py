"""Test handling of audio responses from VideoAsk."""
import unittest
import json
from src.videoask_handler import create_app

class TestAudioSupport(unittest.TestCase):
    """Test cases for audio response handling."""
    
    def setUp(self):
        """Set up test client."""
        self.app = create_app()
        self.client = self.app.test_client()
        
    def test_audio_response(self):
        """Test webhook endpoint with audio response."""
        payload = {
            "event_type": "form_response",
            "contact": {
                "email": "test@example.com",
                "name": "Test User",
                "answers": [
                    {
                        "type": "audio",
                        "media_url": "https://example.com/test-audio.mp3",
                        "question_id": "q123",
                        "answer_id": "a123",
                        "share_id": "s123"
                    }
                ]
            },
            "form": {
                "questions": [
                    {
                        "question_id": "q123",
                        "metadata": {
                            "text": "What is your experience?"
                        }
                    }
                ]
            },
            "interaction_id": "int123"
        }
        
        response = self.client.post(
            '/webhook',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["status"], "processed")
        self.assertEqual(len(response_data["errors"]), 0)
