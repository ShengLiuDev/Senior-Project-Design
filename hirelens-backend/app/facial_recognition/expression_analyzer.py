import cv2
import mediapipe as mp
import numpy as np
from collections import deque

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

# Initialize face mesh detector
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Facial landmarks for improved expression detection
MOUTH_CORNERS = [61, 291]  # Left and right mouth corners
UPPER_LIP = [13]  # Upper lip center
LOWER_LIP = [14]  # Lower lip center
EYEBROWS = [107, 336]  # Left and right eyebrow centers
INNER_EYEBROWS = [55, 285]  # Inner eyebrow points
OUTER_EYEBROWS = [70, 300]  # Outer eyebrow points

# Buffer for smoothing measurements
BUFFER_SIZE = 10
expression_history = deque(maxlen=BUFFER_SIZE)

class ExpressionAnalyzer:
    def __init__(self):
        self.emotion_history = deque(maxlen=30)  # Store last 30 frames of emotions
        self.expression_scores = {
            'smile_score': 0.0,      # Current smile intensity
            'smile_percent': 0.0,     # Percentage of time spent smiling
        }
        self.total_frames = 0        # Total frames processed
        self.smiling_frames = 0      # Frames where smile was detected
        
    def _calculate_facial_metrics(self, landmarks):
        """Direct smile detection based on mouth shape"""
        # Get all mouth points
        left_corner = np.array([landmarks[61].x, landmarks[61].y])
        right_corner = np.array([landmarks[291].x, landmarks[291].y])
        upper_lip = np.array([landmarks[13].x, landmarks[13].y])
        lower_lip = np.array([landmarks[14].x, landmarks[14].y])
        
        # Calculate mouth shape
        mouth_width = abs(right_corner[0] - left_corner[0])  # Horizontal width
        mouth_height = abs(upper_lip[1] - lower_lip[1])      # Vertical height
        
        # Calculate corner positions relative to center
        mouth_center_y = (upper_lip[1] + lower_lip[1]) / 2
        left_lift = mouth_center_y - left_corner[1]
        right_lift = mouth_center_y - right_corner[1]
        
        # More sensitive smile metrics
        width_score = mouth_width * 8.0  # Increased width scaling
        lift_score = (left_lift + right_lift) * 3.0  # Increased lift scaling
        
        return {
            'width': width_score,
            'lift': lift_score,
            'mouth_height': mouth_height
        }
        
    def _detect_emotions(self, metrics):
        """Simple smile detection based on width and lift"""
        emotions = {
            'smile_score': 0.0,
            'smile_percent': 0.0
        }
        
        # More sensitive smile detection with larger neutral window
        width_component = max(0, metrics['width'] - 0.25)  # Increased width threshold
        lift_component = max(0, metrics['lift'] * 3.0)    # Keep lift scaling
        
        # Combined score with higher weight on lift
        smile_score = (width_component * 0.4 + lift_component * 0.6)  # Emphasize lift more
        emotions['smile_score'] = min(1.0, max(0.0, smile_score))
        
        # Count frame as smiling only if the score exceeds our "Slight Smile" threshold (0.15)
        if smile_score > 0.15:  # Match the threshold from _analyze_expression
            self.smiling_frames += 1
            
        # Update total frames and calculate percentage
        self.total_frames += 1
        if self.total_frames > 0:
            emotions['smile_percent'] = (self.smiling_frames / self.total_frames) * 100
            
        return emotions

    def analyze_frame(self, frame, face_mesh_results):
        if not face_mesh_results.multi_face_landmarks:
            cv2.putText(frame, "No face detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return None, "No face detected", []
            
        landmarks = face_mesh_results.multi_face_landmarks[0].landmark
        metrics = self._calculate_facial_metrics(landmarks)
        
        # Debug info focusing on current state
        debug_info = [
            f"Width Score: {metrics['width']:.3f}",
            f"Lift Score: {metrics['lift']:.3f}",
            f"Current Smile: {self._detect_emotions(metrics)['smile_score']:.1%}"
        ]
        
        y_offset = frame.shape[0] - 80
        for info in debug_info:
            cv2.putText(frame, info, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_offset += 20
        
        emotions = self._detect_emotions(metrics)
        self.emotion_history.append(emotions)
        smoothed_emotions = self._smooth_emotions()
        status, message, details = self._analyze_expression(smoothed_emotions)
        self._draw_face_mesh(frame, face_mesh_results.multi_face_landmarks[0])
        self._draw_expression_feedback(frame, status, message, smoothed_emotions, details)
        return status, message, details

    def _smooth_emotions(self):
        """Apply temporal smoothing to emotion detection"""
        if not self.emotion_history:
            return self.expression_scores
            
        # Calculate weighted average of recent emotions
        weights = np.linspace(0.5, 1.0, len(self.emotion_history))
        weights = weights / np.sum(weights)  # Normalize weights
        
        smoothed = {emotion: 0.0 for emotion in self.expression_scores}
        
        for i, emotions in enumerate(self.emotion_history):
            for emotion, score in emotions.items():
                smoothed[emotion] += score * weights[i]
                
        return smoothed
        
    def _analyze_expression(self, emotions):
        """Analyze current smile state and overall performance"""
        details = []
        current_score = emotions['smile_score']
        smile_percent = emotions['smile_percent']
        
        # Adjusted thresholds for larger neutral window
        if current_score > 0.3:  # Lowered from 0.35
            details.append("Big Smile")
        elif current_score > 0.2:  # Keep regular smile the same
            details.append("Smile")
        elif current_score > 0.15:  # Increased from 0.1
            details.append("Slight Smile")
        else:
            details.append("Not Smiling")
            
        # Add current smile intensity
        smile_intensity = int(current_score * 100)
        details.append(f"Current Intensity: {smile_intensity}%")
        
        # Overall message based on total time spent smiling
        if smile_percent >= 40:
            message = "Excellent Engagement!"
        elif smile_percent >= 25:
            message = "Good Engagement"
        elif smile_percent >= 10:
            message = "Fair Engagement"
        else:
            message = "Try to Smile More"
            
        details.append(f"Time Spent Smiling: {smile_percent:.1f}%")
        
        return True, message, details

    def _draw_face_mesh(self, frame, landmarks):
        """Draw face mesh landmarks and key points"""
        h, w, _ = frame.shape
        for landmark in landmarks.landmark:
            x, y = int(landmark.x * w), int(landmark.y * h)
            cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)
            
        # Draw key points in different colors
        for idx in MOUTH_CORNERS + UPPER_LIP + LOWER_LIP:
            x = int(landmarks.landmark[idx].x * w)
            y = int(landmarks.landmark[idx].y * h)
            cv2.circle(frame, (x, y), 3, (0, 255, 255), -1)  # Yellow for mouth
            
        for idx in EYEBROWS + INNER_EYEBROWS + OUTER_EYEBROWS:
            x = int(landmarks.landmark[idx].x * w)
            y = int(landmarks.landmark[idx].y * h)
            cv2.circle(frame, (x, y), 3, (255, 0, 0), -1)  # Blue for eyebrows

    def _draw_expression_feedback(self, frame, status, message, emotions, details):
        """Enhanced feedback display focusing only on current smile intensity"""
        current_score = emotions['smile_score']
        
        # Draw current smile intensity bar and label
        y_offset = 60
        bar_width = 150
        
        # Current smile intensity bar
        cv2.putText(frame, "Smile Intensity:", (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 1)
        
        # Draw background bar for current smile
        cv2.rectangle(frame, (120, y_offset-15), (120+bar_width, y_offset-5),
                    (100, 100, 100), -1)
        # Draw filled portion based on current smile
        filled_width = int(bar_width * current_score)
        cv2.rectangle(frame, (120, y_offset-15), (120+filled_width, y_offset-5),
                    (0, 255, 255), -1)  # Cyan for current smile
        
        # Draw current smile state
        y_offset += 35
        current_state = next((detail for detail in details if any(state in detail for state in ["Big Smile", "Smile", "Slight Smile", "Not Smiling"])), "")
        if current_state:
            cv2.putText(frame, current_state, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 1)
            y_offset += 25
        
        # Draw current intensity percentage
        intensity_text = next((detail for detail in details if "Current Intensity" in detail), "")
        if intensity_text:
            cv2.putText(frame, intensity_text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 1)

    def _get_emotion_color(self, emotion):
        """Simple color getter for smile score"""
        if emotion == 'smile_score':
            return (0, 255, 0)  # Green
        return (200, 200, 200)  # Gray default

def main():
    """
    Main function for testing the ExpressionAnalyzer
    """
    cap = cv2.VideoCapture(0)
    analyzer = ExpressionAnalyzer()
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    print("\nStarting Expression Analysis...")
    print("Press 'q' to end the session and see your final score.\n")
    
    # Initialize variables to store the last valid results
    last_status = None
    last_message = None
    last_details = []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Convert to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        face_mesh_results = face_mesh.process(frame_rgb)
        status, message, details = analyzer.analyze_frame(frame, face_mesh_results)
        
        # Update last valid results if we got valid ones
        if status is not None:
            last_status = status
            last_message = message
            last_details = details
        
        # Display frame
        cv2.imshow('Expression Analysis', frame)
        
        # Break loop on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Generate and print final report only if we have valid results
    if last_status is not None:
        print("\n=== Final Expression Analysis Report ===")
        print(f"Overall Performance: {last_message}")
        # Extract smile time percentage from details
        smile_time = next((detail for detail in last_details if "Time Spent Smiling" in detail), "0%")
        print(f"Total {smile_time}")
        print("\nThank you for participating!")
    else:
        print("\nNo valid expression analysis results were obtained.")
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 