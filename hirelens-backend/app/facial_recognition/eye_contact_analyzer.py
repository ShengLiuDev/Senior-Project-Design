import cv2
import mediapipe as mp
import numpy as np
from collections import deque

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh

class EyeContactAnalyzer:
    def __init__(self):
        # Detection confidence thresholds
        self.DETECTION_CONFIDENCE = 0.5
        self.TRACKING_CONFIDENCE = 0.5
        
        # Initialize MediaPipe Face Mesh with configurable parameters
        self.face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=self.DETECTION_CONFIDENCE,
            min_tracking_confidence=self.TRACKING_CONFIDENCE
        )
        
        # Eye landmark indices
        self.LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
        
        # Frame counters
        self.frame_count = 0
        self.looking_at_camera_frames = 0
        
        # Temporal smoothing parameters
        self.BUFFER_SIZE = 5
        self.GOOD_GAZE_RATIO = 0.6  # Ratio of good frames needed for positive detection
        self.gaze_history = deque(maxlen=self.BUFFER_SIZE)
        
        # Eye region parameters
        self.EYE_PADDING = 5  # Pixels to add around eye region
        
        # Gaze direction parameters
        self.HORIZONTAL_GAZE_THRESHOLD = 0.40  # How far horizontally pupils can move (proportion of eye width)
        self.VERTICAL_GAZE_THRESHOLD = 0.40    # How far vertically pupils can move (proportion of eye height)
        
        # Pupil detection parameters
        self.ADAPTIVE_THRESHOLD_BLOCK_SIZE = 11
        self.ADAPTIVE_THRESHOLD_C = 4

    def _get_eye_region(self, face_landmarks, eye_indices, frame):
        """Extract eye region with configurable padding"""
        eye = [(int(face_landmarks.landmark[i].x * frame.shape[1]), 
                int(face_landmarks.landmark[i].y * frame.shape[0])) for i in eye_indices]

        x_min, y_min = min(eye, key=lambda x: x[0])[0] - self.EYE_PADDING, min(eye, key=lambda x: x[1])[1] - self.EYE_PADDING
        x_max, y_max = max(eye, key=lambda x: x[0])[0] + self.EYE_PADDING, max(eye, key=lambda x: x[1])[1] + self.EYE_PADDING

        if x_max <= x_min or y_max <= y_min:
            return None, None

        return frame[max(0, y_min):y_max, max(0, x_min):x_max], (x_min, y_min, x_max, y_max)

    def _detect_pupil(self, eye_frame):
        """Enhanced pupil detection with configurable parameters"""
        if eye_frame is None or eye_frame.size == 0:
            return None

        # Convert to grayscale and reduce noise
        gray = cv2.cvtColor(eye_frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        # Adaptive thresholding with configurable parameters
        threshold = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            self.ADAPTIVE_THRESHOLD_BLOCK_SIZE,
            self.ADAPTIVE_THRESHOLD_C
        )

        # Find contours and get the largest one
        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            (x, y, w, h) = cv2.boundingRect(largest_contour)
            return (x + w // 2, y + h // 2)
            
        return None

    def _get_gaze_status(self, left_pupil_x, right_pupil_x, pupil_y, eye_width, eye_height):
        """Determine gaze direction with configurable thresholds"""
        if left_pupil_x is None or right_pupil_x is None or pupil_y is None:
            return "Not Looking at Camera"

        # Compute average pupil position
        avg_pupil_x = (left_pupil_x + right_pupil_x) // 2

        # Define thresholds based on eye dimensions
        left_threshold = eye_width * self.HORIZONTAL_GAZE_THRESHOLD
        right_threshold = eye_width * (1 - self.HORIZONTAL_GAZE_THRESHOLD)
        up_threshold = eye_height * self.VERTICAL_GAZE_THRESHOLD
        down_threshold = eye_height * (1 - self.VERTICAL_GAZE_THRESHOLD)

        if (left_threshold <= avg_pupil_x <= right_threshold and 
            up_threshold <= pupil_y <= down_threshold):
            return "Looking at Camera"
        return "Looking Away"

    def analyze_frame(self, frame):
        """Analyze eye contact in a single frame with temporal smoothing"""
        self.frame_count += 1
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)

        gaze_status = "Not Looking at Camera"
        highlight_color = (0, 0, 255)  # Default: Red

        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            
            # Extract eye regions
            left_eye_frame, left_eye_coords = self._get_eye_region(
                face_landmarks, self.LEFT_EYE_INDICES, frame
            )
            right_eye_frame, right_eye_coords = self._get_eye_region(
                face_landmarks, self.RIGHT_EYE_INDICES, frame
            )

            if left_eye_frame is not None and right_eye_frame is not None:
                left_pupil = self._detect_pupil(left_eye_frame)
                right_pupil = self._detect_pupil(right_eye_frame)

                # Fallback for single eye detection
                if left_pupil is None and right_pupil is not None:
                    left_pupil = right_pupil
                elif right_pupil is None and left_pupil is not None:
                    right_pupil = left_pupil

                if left_pupil and right_pupil:
                    # Draw pupils
                    cv2.circle(frame,
                            (left_pupil[0] + left_eye_coords[0],
                             left_pupil[1] + left_eye_coords[1]),
                            5, (255, 0, 0), -1)
                    cv2.circle(frame,
                            (right_pupil[0] + right_eye_coords[0],
                             right_pupil[1] + right_eye_coords[1]),
                            5, (255, 0, 0), -1)
                    
                    # Get gaze status
                    gaze_status = self._get_gaze_status(
                        left_pupil[0], right_pupil[0],
                        left_pupil[1],
                        left_eye_coords[2] - left_eye_coords[0],
                        left_eye_coords[3] - left_eye_coords[1]
                    )

                    # Update history and check ratio
                    self.gaze_history.append(gaze_status == "Looking at Camera")
                    good_gaze_ratio = sum(self.gaze_history) / len(self.gaze_history)

                    if good_gaze_ratio >= self.GOOD_GAZE_RATIO:
                        highlight_color = (0, 255, 0)  # Green
                        self.looking_at_camera_frames += 1
                        gaze_status = "Looking at Camera"
                    else:
                        highlight_color = (0, 255, 255)  # Yellow
                        gaze_status = "Looking Away"

        # Add status text
        cv2.putText(frame, f"Eye Contact: {gaze_status}", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, highlight_color, 2)

        return gaze_status, frame

    def get_eye_contact_score(self):
        """Calculate the overall eye contact score"""
        if self.frame_count == 0:
            return {
                "eye_contact_score": 0,
                "total_frames": 0
            }
        
        eye_contact_score = (self.looking_at_camera_frames / self.frame_count) * 100
        
        return {
            "eye_contact_score": round(eye_contact_score, 2),
            "total_frames": self.frame_count
        }

def main():
    """Main function for testing the EyeContactAnalyzer"""
    cap = cv2.VideoCapture(0)
    analyzer = EyeContactAnalyzer()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Process frame
        gaze_status, processed_frame = analyzer.analyze_frame(frame)
        
        # Display frame
        cv2.imshow('Eye Contact Analysis', processed_frame)
        
        # Break loop on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Generate and print final report
    report = analyzer.get_eye_contact_score()
    print("\nEye Contact Analysis Report:")
    print(f"Eye Contact Score: {report['eye_contact_score']}%")
    print(f"Total Frames Analyzed: {report['total_frames']}")
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 