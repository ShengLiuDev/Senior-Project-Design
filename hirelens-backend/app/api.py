from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from datetime import datetime
from speech_to_text.stt import SpeechDetector, analyze_answer, get_random_questions
from answer_analysis.analyzer import AnswerAnalyzer
from sentiment_analysis.sentiment_analysis_functions import sentiment_analysis

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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
        recordings_dir = os.path.join(project_root, '.recordings')
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

@app.route('/api/interview/results', methods=['GET'])
def get_results():
    """Get all interview results"""
    try:
        # In production, this would fetch from a database
        # For now, we'll return a mock response
        return jsonify({
            'results': [
                {
                    'id': 1,
                    'created_at': datetime.now().isoformat(),
                    'overall_score': 85,
                    'posture_score': 90,
                    'eye_contact_score': 80,
                    'smile_percentage': 75
                }
            ]
        })
    except Exception as e:
        print(f"Error in get_results: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 