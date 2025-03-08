import cv2
import mediapipe as mp
import numpy as np
from collections import deque

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Initialize pose detector
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Buffer for smoothing measurements
BUFFER_SIZE = 5
posture_history = deque(maxlen=BUFFER_SIZE)

class PostureAnalyzer:
    def __init__(self):
        self.frame_count = 0
        self.good_posture_frames = 0
        self.BUFFER_SIZE = 5  # Reduced from 10 for even more lenient temporal evaluation
        self.posture_history = deque(maxlen=self.BUFFER_SIZE)
        
        # Initialize pose detector with very forgiving confidence thresholds
        self.pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            min_detection_confidence=0.5,  # Reduced from 0.6
            min_tracking_confidence=0.5    # Reduced from 0.6
        )
        
    def _calculate_angles(self, landmarks):
        """Calculate key angles for posture analysis"""
        # Get key landmarks
        left_shoulder = np.array([landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x,
                                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y])
        right_shoulder = np.array([landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x,
                                 landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y])
        nose = np.array([landmarks[mp_pose.PoseLandmark.NOSE].x,
                        landmarks[mp_pose.PoseLandmark.NOSE].y])
        left_hip = np.array([landmarks[mp_pose.PoseLandmark.LEFT_HIP].x,
                           landmarks[mp_pose.PoseLandmark.LEFT_HIP].y])
        right_hip = np.array([landmarks[mp_pose.PoseLandmark.RIGHT_HIP].x,
                            landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y])
        left_ear = np.array([landmarks[mp_pose.PoseLandmark.LEFT_EAR].x,
                           landmarks[mp_pose.PoseLandmark.LEFT_EAR].y])
        right_ear = np.array([landmarks[mp_pose.PoseLandmark.RIGHT_EAR].x,
                            landmarks[mp_pose.PoseLandmark.RIGHT_EAR].y])
        
        # Calculate shoulder slope with normalization by shoulder width
        shoulder_vector = right_shoulder - left_shoulder
        shoulder_width = np.linalg.norm(shoulder_vector)
        # Normalize shoulder slope by width to make it scale-invariant
        shoulder_slope = abs(shoulder_vector[1]) / (shoulder_width + 1e-6)
        
        # Calculate head tilt (nose should be centered between shoulders)
        shoulder_center = (left_shoulder + right_shoulder) / 2
        head_offset = abs(nose[0] - shoulder_center[0])
        
        # Calculate forward head posture using ear position
        ear_center = (left_ear + right_ear) / 2
        head_forward = nose[0] - ear_center[0]  # Positive means forward head
        
        # Calculate spine angle (should be close to vertical)
        hip_center = (left_hip + right_hip) / 2
        spine_vector = shoulder_center - hip_center
        spine_angle = abs(np.arctan2(spine_vector[0], -spine_vector[1]))  # Negative y for correct angle
        
        # Calculate shoulder rotation with improved normalization
        shoulder_depth = abs(left_shoulder[0] - right_shoulder[0])
        shoulder_rotation = 1.0 - (shoulder_depth / (shoulder_width + 1e-6))
        shoulder_rotation = max(0.0, min(1.0, shoulder_rotation))  # Clamp between 0 and 1
        
        return {
            'shoulder_slope': shoulder_slope,
            'head_offset': head_offset,
            'head_forward': head_forward,
            'spine_angle': spine_angle,
            'shoulder_rotation': shoulder_rotation
        }
        
    def _analyze_posture(self, angles):
        """Analyze posture based on calculated angles with very forgiving thresholds"""
        # Define very forgiving thresholds for good posture
        SHOULDER_THRESHOLD = 0.20  # Much more forgiving (was 0.12)
        HEAD_OFFSET_THRESHOLD = 0.10  # Unchanged
        HEAD_FORWARD_THRESHOLD = 0.15  # Unchanged
        SPINE_ANGLE_THRESHOLD = 0.25  # Unchanged
        SHOULDER_ROTATION_THRESHOLD = 0.30  # Much more forgiving (was 0.20)
        
        # Check each aspect of posture
        good_shoulders = angles['shoulder_slope'] < SHOULDER_THRESHOLD
        good_head_position = angles['head_offset'] < HEAD_OFFSET_THRESHOLD
        good_head_forward = abs(angles['head_forward']) < HEAD_FORWARD_THRESHOLD
        good_spine = angles['spine_angle'] < SPINE_ANGLE_THRESHOLD
        good_shoulder_rotation = angles['shoulder_rotation'] < SHOULDER_ROTATION_THRESHOLD
        
        # Calculate detailed status with very forgiving grading
        issues = []
        if not good_shoulders:
            severity = "Slightly" if angles['shoulder_slope'] < SHOULDER_THRESHOLD * 2.5 else "Significantly"  # Even more forgiving
            issues.append(f"{severity} Uneven Shoulders")
        if not good_head_position:
            severity = "Slightly" if angles['head_offset'] < HEAD_OFFSET_THRESHOLD * 2.0 else "Significantly"
            issues.append(f"{severity} Off-Center Head")
        if not good_head_forward:
            severity = "Slightly" if abs(angles['head_forward']) < HEAD_FORWARD_THRESHOLD * 2.0 else "Significantly"
            issues.append(f"{severity} Forward Head")
        if not good_spine:
            severity = "Slightly" if angles['spine_angle'] < SPINE_ANGLE_THRESHOLD * 2.0 else "Significantly"
            issues.append(f"{severity} Slouching")
        if not good_shoulder_rotation:
            severity = "Slightly" if angles['shoulder_rotation'] < SHOULDER_ROTATION_THRESHOLD * 2.5 else "Significantly"  # Even more forgiving
            issues.append(f"{severity} Poor Shoulder Alignment")
        
        # Calculate overall posture quality score with very forgiving weights
        posture_score = (
            (good_shoulders * 0.2) +       # Reduced from 0.25
            (good_head_position * 0.2) +
            (good_head_forward * 0.2) +
            (good_spine * 0.2) +
            (good_shoulder_rotation * 0.2)  # All equal weights
        )
        
        # Very forgiving thresholds for overall status
        if posture_score >= 0.70:  # Reduced from 0.80
            return True, "Excellent Posture", issues
        elif posture_score >= 0.50:  # Reduced from 0.65
            return True, "Good Posture", issues
        elif posture_score >= 0.35:  # Reduced from 0.50
            return False, "Fair Posture", issues
        else:
            return False, "Poor Posture", issues
        
    def analyze_frame(self, frame):
        """Analyze posture in a single frame with improved accuracy"""
        self.frame_count += 1
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(frame_rgb)
        
        if not results.pose_landmarks:
            return "No pose detected", frame
        
        # Calculate angles
        angles = self._calculate_angles(results.pose_landmarks.landmark)
        
        # Analyze posture
        is_good_posture, status, issues = self._analyze_posture(angles)
        
        # Add to history for temporal smoothing
        self.posture_history.append(is_good_posture)
        
        # Calculate the percentage of good posture frames in history
        good_posture_ratio = sum(self.posture_history) / len(self.posture_history)
        
        # Determine status and color based on both current issues and history (very forgiving)
        if good_posture_ratio >= 0.60 and not issues:  # Reduced from 0.75
            self.good_posture_frames += 1
            status = "Excellent Posture"
            highlight_color = (0, 255, 0)  # Green
        elif good_posture_ratio >= 0.40 and all("Significantly" not in issue for issue in issues):  # Reduced from 0.60
            self.good_posture_frames += 1
            status = "Good Posture"
            highlight_color = (0, 255, 255)  # Yellow
        else:
            status = "Poor Posture: " + ", ".join(issues)
            highlight_color = (0, 0, 255)  # Red
        
        # Draw pose landmarks and status
        mp_drawing.draw_landmarks(
            frame,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing.DrawingSpec(color=(255, 255, 0), thickness=2, circle_radius=2),
            connection_drawing_spec=mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2)
        )
        
        # Add status text
        cv2.putText(frame, status, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, highlight_color, 2)
        
        # Add detailed feedback if posture is poor
        if issues:
            y_pos = 60
            for issue in issues:
                cv2.putText(frame, f"- {issue}", (20, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, highlight_color, 1)
                y_pos += 25
        
        return status, frame

    def get_posture_score(self):
        """
        Calculate the overall posture score
        """
        if self.frame_count == 0:
            return {
                "posture_score": 0,
                "total_frames": 0
            }
        
        posture_score = (self.good_posture_frames / self.frame_count) * 100
        
        return {
            "posture_score": round(posture_score, 2),
            "total_frames": self.frame_count
        }

def main():
    """
    Main function for testing the PostureAnalyzer
    """
    cap = cv2.VideoCapture(0)
    analyzer = PostureAnalyzer()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Process frame
        posture_status, processed_frame = analyzer.analyze_frame(frame)
        
        # Display frame
        cv2.imshow('Posture Analysis', processed_frame)
        
        # Break loop on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Generate and print final report
    report = analyzer.get_posture_score()
    print("\nPosture Analysis Report:")
    print(f"Posture Score: {report['posture_score']}%")
    print(f"Total Frames Analyzed: {report['total_frames']}")
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 