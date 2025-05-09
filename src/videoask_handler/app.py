from flask import Flask
from .webhooks.routes import webhook_bp
from .manual.routes import manual_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(webhook_bp)
    app.register_blueprint(manual_bp, url_prefix='/manual')
    return app

app = create_app()
