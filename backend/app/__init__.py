from flask import Flask
from extensions import db, ma, cors
from .routes.user_routes import user_bp

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

    db.init_app(app)
    ma.init_app(app)
    cors.init_app(app)

    app.register_blueprint(user_bp, url_prefix='/api/users')

    with app.app_context():
        db.create_all()
    
    return app