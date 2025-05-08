from flask import Flask
from .webhooks.routes import webhook_bp

def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(webhook_bp)
    
    return app
