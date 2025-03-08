from flask import Flask, Blueprint, jsonify, request
from app.sheets_api import get_static_sheet_data
from app.facial_recognition.interview_monitor import main as interview_monitor
import cv2
import base64
import numpy as np
from flask_cors import CORS
import time

routes = Blueprint('routes', __name__)
CORS(routes)  # Enable CORS for all routes

# Global variables to manage interview state
interview_sessions = {}  # Store multiple session states

class InterviewSession:
    def __init__(self, session_id):
        self.session_id = session_id
        self.running = False
        self.frames = []  # Store frames for processing
        self.last_update = time.time()

    def add_frame(self, frame):
        """Add a frame to the session"""
        self.frames.append(frame)
        self.last_update = time.time()

    def process_interview(self):
        """Process all frames and return final scores"""
        # Initialize analyzers
        from app.facial_recognition.eye_contact_analyzer import EyeContactAnalyzer
        from app.facial_recognition.posture_analyzer import PostureAnalyzer
        from app.facial_recognition.expression_analyzer import ExpressionAnalyzer
        import mediapipe as mp
        
        eye_contact_analyzer = EyeContactAnalyzer()
        posture_analyzer = PostureAnalyzer()
        expression_analyzer = ExpressionAnalyzer()
        
        # Initialize MediaPipe Face Mesh
        face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Process each frame
        for frame in self.frames:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(frame_rgb)
            
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

        # Calculate overall score
        overall_score = (
            (posture_report['posture_score'] * 0.4) +
            (smile_percentage * 0.3) +
            (eye_report['eye_contact_score'] * 0.3)
        )

        return {
            "posture_score": round(posture_report['posture_score'], 1),
            "smile_percentage": round(smile_percentage, 1),
            "eye_contact_score": round(eye_report['eye_contact_score'], 1),
            "overall_score": round(overall_score, 1),
            "total_frames": len(self.frames)
        }

@routes.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to HireLens API!"})

@routes.route('/api/static-sheet-data', methods=['GET'])
def static_sheet():
    """API route to return data from the specific hardcoded sheet."""
    data, status_code = get_static_sheet_data()
    return jsonify(data), status_code

@routes.route('/api/interview/start', methods=['POST'])
def start_interview():
    """Initialize a new interview recording session"""
    session_id = request.json.get('session_id')
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
    
    # Create new session
    session = InterviewSession(session_id)
    session.running = True
    interview_sessions[session_id] = session
    
    return jsonify({
        "status": "success",
        "message": "Interview recording started",
        "session_id": session_id
    })

@routes.route('/api/interview/record', methods=['POST'])
def record_frame():
    """Record a frame from the interview"""
    session_id = request.json.get('session_id')
    frame_data = request.json.get('frame')  # Base64 encoded image
    
    if not session_id or not frame_data:
        return jsonify({
            "status": "error",
            "message": "Session ID and frame data are required"
        }), 400
    
    session = interview_sessions.get(session_id)
    if not session or not session.running:
        return jsonify({
            "status": "error",
            "message": "Invalid or inactive session"
        }), 400
    
    try:
        # Decode base64 image
        frame_bytes = base64.b64decode(frame_data.split(',')[1])
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Add frame to session
        session.add_frame(frame)
        
        return jsonify({
            "status": "success",
            "frames_recorded": len(session.frames)
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error recording frame: {str(e)}"
        }), 500

@routes.route('/api/interview/stop', methods=['POST'])
def stop_interview():
    """Stop recording and process the entire interview"""
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
    
    try:
        # Stop recording
        session.running = False
        
        # Process all frames
        print(f"Processing {len(session.frames)} frames...")
        final_scores = session.process_interview()
        
        # Cleanup
        del interview_sessions[session_id]
        
        return jsonify({
            "status": "success",
            "message": "Interview processed successfully",
            "final_scores": final_scores
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error processing interview: {str(e)}"
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