from flask import Flask
from .extensions import db, ma, cors
from .routes.user_routes import user_bp
from .routes.transcription_routes import transcription_bp
from flask_jwt_extended import JWTManager
from .config import Config

jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    ma.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "http://localhost:4200"}}, supports_credentials=True)
    jwt.init_app(app)

    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(transcription_bp, url_prefix='/api')

    with app.app_context():
        db.create_all()
    
    return app