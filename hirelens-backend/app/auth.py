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
        'scope': 'https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    # Build the authorization URL
    auth_url = f"{GOOGLE_AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    
    print("\n=== Generated Auth URL ===")
    print(f"Scopes: {params['scope']}")
    print(f"Redirect URI: {params['redirect_uri']}")
    
    return jsonify({
        "auth_url": auth_url
    })

@auth.route('/login/google/callback', methods=['GET', 'POST'])
def google_callback():
    """
    Handles the Google OAuth2 callback.
    Exchanges the authorization code for tokens and creates a session.
    """
    print("\n=== Starting Google OAuth Callback ===")
    
    # Get the authorization code from either GET or POST
    code = request.args.get('code') or request.json.get('code')
    print(f"Received code: {code[:10]}...")  # Only print first 10 chars for security
    
    if not code:
        print("No code received")
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
        
        print("\nToken request data:")
        print(f"Client ID: {token_data['client_id'][:10]}...")
        print(f"Redirect URI: {token_data['redirect_uri']}")
        
        # Make the token request
        token_response = requests.post(token_url, data=token_data)
        print(f"\nToken response status: {token_response.status_code}")
        
        if not token_response.ok:
            print(f"Token response error: {token_response.text}")
            return jsonify({"error": "Failed to get token from Google"}), 400
            
        tokens = token_response.json()
        print("\nToken response keys:", list(tokens.keys()))
        
        if 'id_token' not in tokens:
            print("No ID token in response")
            return jsonify({"error": "No ID token received from Google"}), 400

        # Verify the ID token
        try:
            print("\nVerifying ID token...")
            idinfo = id_token.verify_oauth2_token(
                tokens['id_token'],
                google_requests.Request(),
                current_app.config['GOOGLE_CLIENT_ID']
            )
            print("\nID token info keys:", list(idinfo.keys()))
            print("ID token info:", idinfo)
        except Exception as e:
            print(f"\nError verifying ID token: {str(e)}")
            return jsonify({"error": "Failed to verify ID token"}), 400

        # Get user info from the ID token with fallbacks
        user_info = {
            'sub': idinfo.get('sub'),
            'email': idinfo.get('email'),
            'name': idinfo.get('name', idinfo.get('email', 'Unknown User'))
        }
        
        print("\nExtracted user info:", user_info)

        # Validate required fields
        if not user_info['sub'] or not user_info['email']:
            print("\nMissing required user info:", user_info)
            return jsonify({"error": "Missing required user information"}), 400

        # Create JWT access token
        access_token = create_access_token(
            identity=user_info['sub'],
            additional_claims={
                'email': user_info['email'],
                'name': user_info['name']
            }
        )

        print("\n=== OAuth Flow Completed Successfully ===")
        
        # Always return JSON response
        return jsonify({
            "access_token": access_token,
            "user": user_info
        })

    except Exception as e:
        print(f"\nError in google_callback: {str(e)}")
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