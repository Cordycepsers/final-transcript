"""Test configuration and fixtures."""
import os
import pytest
from src.videoask_handler import create_app

@pytest.fixture
def app():
    """Create application for testing."""
    # Set test environment variables
    os.environ['REV_AI_ACCESS_TOKEN'] = 'test-token'
    os.environ['WEBHOOK_CALLBACK_URL'] = 'https://test-webhook.example.com/callback'
    
    app = create_app()
    return app

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()
