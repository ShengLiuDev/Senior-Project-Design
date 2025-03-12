from functools import wraps
from flask import Blueprint, request, jsonify, current_app, url_for, redirect
from flask_jwt_extended import (
    create_access_token,
    jwt_required, get_jwt_identity
)
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

auth = Blueprint('auth', __name__)

@auth.route('/login/google', methods=['GET'])
def google_login():
    """
    Initiates the Google OAuth2 login flow.
    Returns the Google OAuth URL that the client should redirect to.
    """
    # Google OAuth2 configuration
    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    
    # Parameters for Google OAuth
    params = {
        'client_id': current_app.config['GOOGLE_CLIENT_ID'],
        'redirect_uri': url_for('auth.google_callback', _external=True),
        'response_type': 'code',
        'scope': 'openid email profile',
        'prompt': 'select_account'
    }
    
    # Build the authorization URL
    auth_url = f"{GOOGLE_AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    
    return jsonify({
        "auth_url": auth_url
    })

@auth.route('/login/google/callback')
def google_callback():
    """
    Handles the Google OAuth2 callback.
    Exchanges the authorization code for tokens and creates a session.
    """
    # Get the authorization code from the callback
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "Authorization code not found"}), 400

    try:
        # Exchange the authorization code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'code': code,
            'client_id': current_app.config['GOOGLE_CLIENT_ID'],
            'client_secret': current_app.config['GOOGLE_CLIENT_SECRET'],
            'redirect_uri': url_for('auth.google_callback', _external=True),
            'grant_type': 'authorization_code'
        }
        
        # Make the token request
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        tokens = token_response.json()

        # Verify the ID token
        idinfo = id_token.verify_oauth2_token(
            tokens['id_token'],
            google_requests.Request(),
            current_app.config['GOOGLE_CLIENT_ID']
        )

        # Get user info from the ID token
        user_info = {
            'sub': idinfo['sub'],
            'email': idinfo['email'],
            'name': idinfo.get('name', idinfo['email'])
        }

        # Create JWT access token
        access_token = create_access_token(
            identity=user_info['sub'],
            additional_claims={
                'email': user_info['email'],
                'name': user_info['name']
            }
        )

        return jsonify({
            "access_token": access_token,
            "user": user_info
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auth.route('/me')
@jwt_required()
def get_user():
    """
    Returns the current user's information from the JWT token.
    Requires a valid JWT token in the Authorization header.
    """
    current_user = get_jwt_identity()
    return jsonify({
        "user_id": current_user,
        "claims": get_jwt_identity()
    }) 