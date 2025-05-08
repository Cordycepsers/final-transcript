"""Test VideoAsk webhook integration."""
import unittest
import json
from src.videoask_handler import create_app

class TestVideoAskWebhook(unittest.TestCase):
    """Test cases for VideoAsk webhook endpoint."""
    
    def setUp(self):
        """Set up test client."""
        self.app = create_app()
        self.client = self.app.test_client()
        
    def test_webhook_endpoint(self):
        """Test webhook endpoint with sample VideoAsk payload."""
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
        
        response = self.client.post(
            '/webhook',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        # Since we don't have REV_AI_API_KEY in test, it should still accept the webhook
        # but log that the key is not configured
