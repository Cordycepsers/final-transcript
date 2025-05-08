"""Simple test for endpoint availability."""
from src.videoask_handler import create_app

def test_webhook_endpoint_exists():
    """Test that the webhook endpoint exists and accepts POST requests."""
    app = create_app()
    client = app.test_client()
    
    response = client.post('/webhook')
    # Should not be 404
    assert response.status_code != 404, "Webhook endpoint not found"
    print(f"Got response code: {response.status_code}")
