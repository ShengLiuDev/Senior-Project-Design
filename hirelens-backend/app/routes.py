from flask import Flask, Blueprint, jsonify, request
from app.sheets_api import get_static_sheet_data
from app.facial_recognition.interview_monitor import main as interview_monitor
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import cv2
import base64
import numpy as np
from flask_cors import CORS
import time
import mediapipe as mp
from .facial_recognition.eye_contact_analyzer import EyeContactAnalyzer
from .facial_recognition.posture_analyzer import PostureAnalyzer
from .facial_recognition.expression_analyzer import ExpressionAnalyzer
from datetime import datetime
from pymongo import MongoClient

import os
import sys
import threading
import wave
from RealtimeSTT import AudioToTextRecorder
import pyaudio
from app.answer_analysis.analyzer import AnswerAnalyzer
from app.sentiment_analysis.sentiment_analysis_functions import sentiment_analysis

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

routes = Blueprint('routes', __name__)
CORS(routes)  # Enable CORS for all routes

# Initialize MongoDB connection
client = MongoClient()
db = client.hirelens
interviews = db.interviews  # Create interviews collection

# Global variables to manage interview state
interview_sessions = {}  # Store multiple session states

# Initialize MediaPipe Face Mesh for expression analysis
mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

class InterviewSession:
    def __init__(self, session_id):
        self.session_id = session_id
        self.running = False
        self.frames = []  # Store frames only
        self.last_update = time.time()
        self.start_time = datetime.utcnow()
        self.email = ""
        self.name = ""
        self.current_question = None
        self.questions_asked = []  # Store all questions asked during the session
        self.answers = {}  # Store answers for each question
        
        # Initialize analyzers
        self.answer_analyzer = AnswerAnalyzer()
        self.sentiment_analyzer = sentiment_analysis()

    def add_frame(self, frame):
        """Add a frame to the session"""
        self.frames.append(frame)
        self.last_update = time.time()
        
    def add_question(self, question):
        """Add a question to the session history"""
        if question and question not in self.questions_asked:
            self.questions_asked.append(question)
            self.current_question = question
            self.answers[question] = {
                "audio_transcript": "",
                "analysis": None,
                "sentiment": None,
                "start_time": datetime.utcnow()
            }

    def process_interview(self):
        """Process all frames and return final scores"""
        if not self.frames:
            return {
                "posture_score": 0.0,
                "smile_percentage": 0.0,
                "eye_contact_score": 0.0,
                "overall_score": 0.0,
                "total_frames": 0,
                "answer_quality_score": 0.0,
                "overall_sentiment": 0.0
            }
            
        # Initialize analyzers
        eye_contact_analyzer = EyeContactAnalyzer()
        posture_analyzer = PostureAnalyzer()
        expression_analyzer = ExpressionAnalyzer()
        
        # Process each frame
        for frame in self.frames:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = mp_face_mesh.process(frame_rgb)
            
            # Analyze frame with each analyzer
            eye_contact_analyzer.analyze_frame(frame.copy())
            posture_analyzer.analyze_frame(frame.copy())
            expression_analyzer.analyze_frame(frame.copy(), results)

        # Get final scores
        eye_report = eye_contact_analyzer.get_eye_contact_score()
        posture_report = posture_analyzer.get_posture_score()
        _, _, expression_details = expression_analyzer.analyze_frame(frame.copy(), results)

        # Get smile percentage
        smile_percentage = 0.0
        if expression_details:
            smile_time = next((detail for detail in expression_details if "Time Spent Smiling" in detail), "0%")
            try:
                smile_percentage = float(smile_time.split(":")[1].strip().rstrip('%'))
            except:
                smile_percentage = 0.0
                
        # Process answers
        answer_scores = []
        sentiment_scores = []
        
        # Mock answer quality score for now - you can implement this based on actual answers
        # when you integrate speech-to-text
        answer_quality_score = 70.0  # Default dummy value
        overall_sentiment = 60.0  # Default dummy value

        # Calculate overall score
        overall_score = (
            (posture_report['posture_score'] * 0.3) +
            (smile_percentage * 0.2) +
            (eye_report['eye_contact_score'] * 0.2) +
            (answer_quality_score * 0.2) +
            (overall_sentiment * 0.1)
        )

        return {
            "posture_score": round(posture_report['posture_score'], 1),
            "smile_percentage": round(smile_percentage, 1),
            "eye_contact_score": round(eye_report['eye_contact_score'], 1),
            "answer_quality_score": round(answer_quality_score, 1),
            "overall_sentiment": round(overall_sentiment, 1),
            "overall_score": round(overall_score, 1),
            "total_frames": len(self.frames),
            "questions_asked": self.questions_asked
        }

@routes.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to HireLens API!"})

@routes.route('/api/static-sheet-data', methods=['GET'])
@jwt_required()
def static_sheet():
    """API route to return data from the specific hardcoded sheet."""
    current_user = get_jwt_identity()
    data, status_code = get_static_sheet_data()
    return jsonify(data), status_code

@routes.route('/api/interview/start', methods=['POST'])
@jwt_required()
def start_interview():
    """Start a new interview session"""
    current_user = get_jwt_identity()
    session_id = request.json.get('session_id')
    current_question = request.json.get('question')
    
    if not session_id:
        return jsonify({
            "status": "error",
            "message": "Session ID is required"
        }), 400
    
    if session_id in interview_sessions:
        return jsonify({
            "status": "error",
            "message": "Session already exists"
        }), 400
    
    try:
        # Create new session
        session = InterviewSession(session_id)
        session.user_id = current_user
        session.running = True
        
        # Add the question if provided
        if current_question:
            session.add_question(current_question)
        
        interview_sessions[session_id] = session
        
        return jsonify({
            "status": "success",
            "message": "Interview session started",
            "session_id": session_id,
            "current_question": current_question
        })
        
    except Exception as e:
        print(f"Error in start_interview: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error starting interview: {str(e)}"
        }), 500

@routes.route('/api/interview/record', methods=['POST'])
@jwt_required()
def record_frame():
    """Record a frame during the interview"""
    try:
        # Get JSON payload with force=True to handle malformed JSON
        payload = request.get_json(force=True)
        if not payload:
            return jsonify({
                "status": "error",
                "message": "Invalid JSON payload",
                "details": "No payload received"
            }), 400

        current_user = get_jwt_identity()
        session_id = payload.get('session_id')
        frame_data = payload.get('frame')
        current_question = payload.get('question')
        
        # Validate required fields
        if not session_id:
            return jsonify({
                "status": "error",
                "message": "Session ID is required",
                "details": "session_id field is missing"
            }), 400
            
        if not frame_data:
            return jsonify({
                "status": "error",
                "message": "Frame data is required",
                "details": "frame field is missing"
            }), 400
        
        # Get session
        session = interview_sessions.get(session_id)
        if not session:
            return jsonify({
                "status": "error",
                "message": "Session not found",
                "details": f"Session {session_id} does not exist"
            }), 404
        
        # Verify user owns this session
        if getattr(session, 'user_id', None) != current_user:
            return jsonify({
                "status": "error",
                "message": "Unauthorized access to session",
                "details": "User does not own this session"
            }), 403
            
        try:
            # Update current question if it has changed
            if current_question and current_question != getattr(session, 'current_question', None):
                session.add_question(current_question)
            
            # Validate frame data format
            if not isinstance(frame_data, str):
                return jsonify({
                    "status": "error",
                    "message": "Invalid frame data format",
                    "details": "Frame data must be a string"
                }), 400

            if not frame_data.startswith('data:image/jpeg;base64,'):
                return jsonify({
                    "status": "error",
                    "message": "Invalid frame data format",
                    "details": "Frame data must be a base64 encoded JPEG image"
                }), 400

            # Remove data URL prefix and decode base64
            try:
                frame_data = frame_data.split(',')[1]
                frame_bytes = base64.b64decode(frame_data)
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": "Invalid base64 data",
                    "details": str(e)
                }), 400
            
            # Convert to numpy array and decode image
            try:
                frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": "Failed to decode frame",
                    "details": str(e)
                }), 400
            
            if frame is None:
                return jsonify({
                    "status": "error",
                    "message": "Failed to decode frame",
                    "details": "OpenCV failed to decode the image"
                }), 400
            
            # Validate frame dimensions
            if frame.shape[0] == 0 or frame.shape[1] == 0:
                return jsonify({
                    "status": "error",
                    "message": "Invalid frame dimensions",
                    "details": f"Frame dimensions: {frame.shape}"
                }), 400
            
            # Store frame
            session.add_frame(frame)
            
            return jsonify({
                "status": "success",
                "message": "Frame recorded successfully",
                "frames_recorded": len(session.frames),
                "frame_dimensions": frame.shape,
                "current_question": session.current_question,
                "questions_asked": session.questions_asked
            })
            
        except Exception as e:
            print(f"Error processing frame: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Error processing frame",
                "details": str(e)
            }), 500
            
    except Exception as e:
        print(f"Error in record_frame route: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Server error",
            "details": str(e)
        }), 500

@routes.route('/api/interview/stop', methods=['POST'])
@jwt_required()
def stop_interview():
    """Stop recording and process the entire interview"""
    current_user = get_jwt_identity()
    session_id = request.json.get('session_id')
    
    if not session_id:
        return jsonify({
            "status": "error",
            "message": "Session ID is required"
        }), 400
    
    session = interview_sessions.get(session_id)
    if not session:
        return jsonify({
            "status": "error",
            "message": "Session not found"
        }), 404
    
    # Verify user owns this session
    if getattr(session, 'user_id', None) != current_user:
        return jsonify({
            "status": "error",
            "message": "Unauthorized access to session"
        }), 403
    
    try:
        # Stop recording
        session.running = False
        
        # Check if we have any frames to process
        if not session.frames:
            return jsonify({
                "status": "warning",
                "message": "No frames were recorded in this session",
                "final_scores": {
                    "posture_score": 0.0,
                    "smile_percentage": 0.0,
                    "eye_contact_score": 0.0,
                    "overall_score": 0.0,
                    "answer_quality_score": 0.0,
                    "overall_sentiment": 0.0,
                    "total_frames": 0
                }
            })
        
        # Process all frames
        print(f"Processing {len(session.frames)} frames...")
        final_scores = session.process_interview()
        
        # Calculate duration
        duration = (datetime.utcnow() - session.start_time).total_seconds()
        
        # Get user info from JWT token
        jwt_data = get_jwt()
        user_email = jwt_data.get('email', '')
        user_name = jwt_data.get('name', '')
        
        # Store results in MongoDB
        interview_result = {
            "userId": current_user,
            "email": user_email,
            "name": user_name,
            "date": datetime.utcnow(),
            "duration": duration,
            "scores": final_scores,
            "questions": session.questions_asked
        }
        
        result = interviews.insert_one(interview_result)
        
        # Cleanup session
        del interview_sessions[session_id]
        
        return jsonify({
            "status": "success",
            "message": "Interview results saved successfully",
            "interview_id": str(result.inserted_id),
            "final_scores": final_scores,
            "questions_asked": session.questions_asked
        })
        
    except Exception as e:
        print(f"Error in stop_interview: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error processing interview: {str(e)}"
        }), 500

@routes.route('/api/interview/test', methods=['POST'])
@jwt_required()
def test_interview():
    """Test endpoint that runs the interview monitor directly using the camera"""
    current_user = get_jwt_identity()
    session_id = request.json.get('session_id', 'test_session')
    
    try:
        # Create new session
        session = InterviewSession(session_id)
        session.user_id = current_user
        session.running = True
        interview_sessions[session_id] = session
        
        # Try different camera indices and backends
        camera_indices = [0, 1]  # Try first two camera indices
        backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]  # Try DirectShow and default backend
        
        cap = None
        for index in camera_indices:
            for backend in backends:
                try:
                    print(f"Trying camera index {index} with backend {backend}")
                    cap = cv2.VideoCapture(index + backend)
                    if cap.isOpened():
                        print(f"Successfully opened camera {index} with backend {backend}")
                        break
                except Exception as e:
                    print(f"Failed to open camera {index} with backend {backend}: {str(e)}")
                    if cap is not None:
                        cap.release()
            if cap is not None and cap.isOpened():
                break
        
        if not cap or not cap.isOpened():
            return jsonify({
                "status": "error",
                "message": "Could not open any camera. Please check if your camera is connected and not in use by another application."
            }), 500
            
        print("\nStarting test interview recording...")
        print("Recording frames for 10 seconds...")
        print("Press 'q' to stop recording early")
        
        # Record for 10 seconds (approximately 300 frames at 30 fps)
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < 10:  # 10 second recording
            ret, frame = cap.read()
            if not ret:
                print("Error reading frame from camera")
                break
                
            frame_count += 1
            
            # Store frame
            session.add_frame(frame.copy())
            
            # Display frame with recording indicator
            cv2.putText(frame, "Recording...", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, f"Frames: {frame_count}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.imshow('Test Interview', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        
        # Process results
        if not session.frames:
            return jsonify({
                "status": "warning",
                "message": "No frames were recorded",
                "final_scores": {
                    "posture_score": 0.0,
                    "smile_percentage": 0.0,
                    "eye_contact_score": 0.0,
                    "overall_score": 0.0,
                    "total_frames": 0
                }
            })
        
        print(f"\nProcessing {len(session.frames)} frames...")
        # Get final scores
        final_scores = session.process_interview()
        
        # Cleanup session
        del interview_sessions[session_id]
        
        return jsonify({
            "status": "success",
            "message": f"Test interview completed successfully. Processed {frame_count} frames.",
            "final_scores": final_scores
        })
        
    except Exception as e:
        print(f"Error in test_interview: {str(e)}")
        if 'cap' in locals():
            cap.release()
        cv2.destroyAllWindows()
        return jsonify({
            "status": "error",
            "message": f"Error during test interview: {str(e)}"
        }), 500

@routes.route('/api/interview/history', methods=['GET'])
@jwt_required()
def get_interview_history():
    """Get all interviews for the current user"""
    current_user = get_jwt_identity()
    
    try:
        # Get all interviews for the user, sorted by date
        user_interviews = list(interviews.find(
            {"userId": current_user}
        ).sort("date", -1))
        
        # Convert ObjectId to string for JSON serialization
        for interview in user_interviews:
            interview['_id'] = str(interview['_id'])
        
        return jsonify({
            "status": "success",
            "interviews": user_interviews
        })
        
    except Exception as e:
        print(f"Error getting interview history: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error retrieving interview history: {str(e)}"
        }), 500

@routes.route('/api/interview/results', methods=['GET'])
@jwt_required()
def get_all_results():
    try:
        current_user_id = get_jwt_identity()
        print(f"Fetching results for user: {current_user_id}")
        
        # Query all results for the user from MongoDB, ordered by date
        results = list(interviews.find(
            {"userId": current_user_id}
        ).sort("date", -1))
        
        print(f"Found {len(results)} results")
        
        # Format results
        formatted_results = [{
            'id': str(result['_id']),
            'created_at': result['date'].strftime('%Y-%m-%d %H:%M:%S'),
            'overall_score': result['scores']['overall_score'],
            'posture_score': result['scores']['posture_score'],
            'eye_contact_score': result['scores']['eye_contact_score'],
            'smile_percentage': result['scores']['smile_percentage']
        } for result in results]
        
        print("Formatted results:", formatted_results)
        
        return jsonify({
            'results': formatted_results
        }), 200
        
    except Exception as e:
        print(f"Error retrieving results: {str(e)}")
        return jsonify({'error': 'Failed to retrieve results'}), 500

@routes.route('/api/interview/questions', methods=['GET'])
@jwt_required()
def get_interview_questions():
    """Get random interview questions"""
    try:
        # Get query parameter for number of questions (default: 3)
        num_questions = request.args.get('count', 3, type=int)
        
        # Import the function from analyzer
        from app.answer_analysis.analyzer import AnswerAnalyzer
        
        # Get random questions
        analyzer = AnswerAnalyzer()
        questions = analyzer.get_random_questions(num_questions)
        
        print(f"Generated {len(questions)} random questions: {questions}")
        
        return jsonify({
            "status": "success",
            "questions": questions
        })
        
    except Exception as e:
        print(f"Error getting questions: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error getting questions: {str(e)}"
        }), 500

# Cleanup inactive sessions periodically
def cleanup_inactive_sessions():
    """Remove sessions that haven't been updated in 5 minutes"""
    current_time = time.time()
    inactive_sessions = [
        session_id for session_id, session in interview_sessions.items()
        if current_time - session.last_update > 300  # 5 minutes
    ]
    for session_id in inactive_sessions:
        del interview_sessions[session_id] 