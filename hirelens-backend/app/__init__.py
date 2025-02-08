from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    CORS(app)

    # Register Blueprints
    from app.routes import routes  # Import routes
    app.register_blueprint(routes)  # Register blueprint

    with app.app_context():
        db.create_all()

    return app
