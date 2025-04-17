import subprocess
import time
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from app.database import test_connection
from app.speech_to_text.stt import SpeechDetector, analyze_answer, get_random_questions
from app.answer_analysis.analyzer import AnswerAnalyzer
from app.sentiment_analysis.sentiment_analysis_functions import sentiment_analysis

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

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    # Configure CORS with specific allowed origins and methods
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000"],  # Only allow requests from your frontend
            "methods": ["GET", "POST", "OPTIONS"],  # Only allow specific HTTP methods
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    # Initialize components
    speech_detector = SpeechDetector()
    answer_analyzer = AnswerAnalyzer()
    sentiment_analyzer = sentiment_analysis()

    @app.route('/api/interview/questions', methods=['GET'])
    def get_questions():
        """Get random interview questions from the dataset"""
        try:
            questions = get_random_questions(num_questions=3)
            if not questions:
                return jsonify({'error': 'No questions available'}), 500
            return jsonify({'questions': questions})
        except Exception as e:
            print(f"Error in get_questions: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/interview/record', methods=['POST'])
    def record_answer():
        """Record and analyze an answer"""
        try:
            data = request.json
            question = data.get('question')
            
            # Create recordings directory if it doesn't exist
            recordings_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.recordings')
            os.makedirs(recordings_dir, exist_ok=True)
            
            # Record audio
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(recordings_dir, f"recording_{timestamp}.wav")
            
            # Record and transcribe
            text = speech_detector.record_audio(filename, duration=90)
            
            # Analyze the answer using both analyzers
            answer_analysis = analyze_answer(text, question)
            sentiment_result = sentiment_analyzer.predict(text)
            
            # Combine analyses
            analysis = {
                'answer_analysis': answer_analysis,
                'sentiment': sentiment_result
            }
            
            return jsonify({
                'transcription': text,
                'analysis': analysis,
                'recording_path': filename
            })
            
        except Exception as e:
            print(f"Error in record_answer: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/interview/analyze-video', methods=['POST'])
    def analyze_video():
        """Analyze video for posture, eye contact, and smile"""
        try:
            # For now, return mock data
            # In a real implementation, this would analyze the video stream
            return jsonify({
                'overall_score': 85,
                'posture_score': 90,
                'eye_contact_score': 80,
                'smile_percentage': 75
            })
        except Exception as e:
            print(f"Error in analyze_video: {e}")
            return jsonify({'error': str(e)}), 500

    return app

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
    print("\n=== Starting Flask Server ===")
    app.run(debug=True, port=5000)

if __name__ == '__main__':
    main()
