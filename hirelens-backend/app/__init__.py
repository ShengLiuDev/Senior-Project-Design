from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config

jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    jwt.init_app(app)
    CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://localhost:3000"}})

    # Register Blueprints
    from app.routes import routes
    from app.auth import auth
    app.register_blueprint(routes)
    app.register_blueprint(auth, url_prefix='/auth')

    return app
