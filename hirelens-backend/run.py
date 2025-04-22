import subprocess
import time
import os
import traceback
from app import create_app
from app.database import test_connection

def check_mongodb_connection():
    """Check if MongoDB is running and accessible"""
    max_retries = 5
    retry_delay = 2  # seconds
    
    for i in range(max_retries):
        if test_connection():
            print("✅ MongoDB connection successful")
            return True
        print(f"⏳ Waiting for MongoDB to be ready... (attempt {i+1}/{max_retries})")
        time.sleep(retry_delay)
    
    print("❌ Failed to connect to MongoDB after multiple attempts")
    return False

def main():
    print("\n=== Starting HireLens Backend ===")
    print("\nPlease ensure MongoDB is running:")
    print("1. Open MongoDB Compass")
    print("2. Or run 'net start MongoDB' in an Administrator PowerShell")
    print("3. Or start MongoDB service from Windows Services\n")
    
    # Wait for MongoDB to be ready
    if not check_mongodb_connection():
        print("\n❌ MongoDB is not accessible")
        print("Please start MongoDB manually and try again")
        return
    
    # Create and run Flask app
    app = create_app()
    
    # Load models with special error handling
    print("\n=== Preloading Models ===")
    try:
        # Try to import and initialize the sentiment analyzer
        from app.speech_to_text.sentiment_analysis import SentimentAnalyzer
        sentiment_analyzer = SentimentAnalyzer()
    except Exception as e:
        print(f"⚠️ Warning: Error initializing sentiment analyzer: {str(e)}")
        print("Continuing with fallback functionality")
    
    # Add a simple test route directly to the app
    @app.route('/api/test-connection', methods=['GET'])
    def test_connection():
        from flask import jsonify
        print("Test connection endpoint called!")
        return jsonify({"status": "success", "message": "Backend server is running"})
    
    # Add a route for testing transcription without authentication
    @app.route('/api/test-transcription', methods=['POST'])
    def test_transcription():
        from flask import request, jsonify
        import base64
        import os
        import uuid
        
        print("Test transcription endpoint called!")
        
        try:
            temp_dir = os.path.join(os.getcwd(), 'temp_audio')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate unique filename
            filename = f"test_audio_{uuid.uuid4().hex}.webm"
            filepath = os.path.join(temp_dir, filename)
            
            if request.is_json:
                data = request.get_json()
                
                if 'audio_data' not in data:
                    return jsonify({"error": "No audio data provided"}), 400
                    
                # Extract the base64 data
                base64_data = data['audio_data']
                if ',' in base64_data:
                    base64_data = base64_data.split(',', 1)[1]
                
                # Decode and save as binary file
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(base64_data))
                
                # Import STT module
                from app.speech_to_text.stt import InterviewRecorder
                recorder = InterviewRecorder()
                
                # Transcribe the audio
                transcription = recorder.transcribe_from_file(filepath)
                
                # Clean up
                if os.path.exists(filepath):
                    os.remove(filepath)
                    
                # Check for WAV file
                wav_path = filepath.replace('.webm', '.wav')
                if os.path.exists(wav_path):
                    os.remove(wav_path)
                
                return jsonify({
                    "status": "success",
                    "transcription": transcription
                })
                
            else:
                return jsonify({"error": "Request must be JSON"}), 400
                
        except Exception as e:
            print(f"Error testing transcription: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    
    # Add error handlers to prevent server crashes
    @app.errorhandler(500)
    def server_error(e):
        from flask import jsonify
        error_message = str(e)
        traceback.print_exc()
        print(f"⚠️ Server error: {error_message}")
        return jsonify({
            "error": "Internal server error",
            "details": error_message
        }), 500
        
    @app.errorhandler(Exception)
    def handle_exception(e):
        from flask import jsonify
        error_message = str(e)
        traceback.print_exc()
        print(f"⚠️ Unhandled exception: {error_message}")
        return jsonify({
            "error": "An unexpected error occurred",
            "details": error_message
        }), 500
    
    print("\n=== Starting Flask Server ===")
    print("Debug mode:", app.debug)
    print("Server will be available at: http://localhost:5000")
    print("Try opening http://localhost:5000/api/test-connection in your browser to verify")
    
    try:
        import werkzeug.serving
        werkzeug.serving.run_simple(
            '0.0.0.0', 5000, app, 
            use_reloader=False,  # disable reloader to prevent crashes
            threaded=True,       # enable threading
            use_debugger=app.debug
        )
    except KeyboardInterrupt:
        print("\n⚠️ Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting Flask server: {str(e)}")
        print("Please check if port 5000 is already in use")
        print("You can try running: lsof -i :5000 (on Mac/Linux) or netstat -ano | findstr :5000 (on Windows) to check what's using the port")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
