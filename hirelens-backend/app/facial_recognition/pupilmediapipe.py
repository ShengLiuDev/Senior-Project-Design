import cv2
import mediapipe as mp
import numpy as np
from collections import deque

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True)

# Eye landmark indices for MediaPipe
LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]

# Pupil position smoothing buffer
BUFFER_SIZE = 5  # Keeps tracking stable but responsive
pupil_history = deque(maxlen=BUFFER_SIZE)

# Frame counters
total_frames = 0
looking_at_camera_frames = 0

# Function to extract eye region with padding
def get_eye_region(face_landmarks, eye_indices, frame, padding=5):
    eye = [(int(face_landmarks.landmark[i].x * frame.shape[1]), 
            int(face_landmarks.landmark[i].y * frame.shape[0])) for i in eye_indices]

    x_min, y_min = min(eye, key=lambda x: x[0])[0] - padding, min(eye, key=lambda x: x[1])[1] - padding
    x_max, y_max = max(eye, key=lambda x: x[0])[0] + padding, max(eye, key=lambda x: x[1])[1] + padding

    if x_max <= x_min or y_max <= y_min:
        return None, None  # Invalid eye region

    return frame[max(0, y_min):y_max, max(0, x_min):x_max], (x_min, y_min, x_max, y_max)

# Function to detect pupil using adaptive thresholding
def detect_pupil(eye_frame):
    if eye_frame is None or eye_frame.size == 0:
        return None  # Avoids crashing

    gray = cv2.cvtColor(eye_frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)  # Reduce noise

    # Adaptive thresholding for better lighting handling
    threshold = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY_INV, 11, 4)

    contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        (x, y, w, h) = cv2.boundingRect(largest_contour)
        return (x + w // 2, y + h // 2)  # Pupil center
    return None

# Function to determine gaze direction with increased sensitivity
def get_gaze_status(left_pupil_x, right_pupil_x, pupil_y, eye_width, eye_height, threshold_x=0.40, threshold_y=0.40):
    if left_pupil_x is None or right_pupil_x is None or pupil_y is None:
        return "Not Looking at Camera"

    # Compute average pupil position
    avg_pupil_x = (left_pupil_x + right_pupil_x) // 2

    # Define the "Looking at Camera" central range
    left_threshold = eye_width * threshold_x
    right_threshold = eye_width * (1 - threshold_x)
    up_threshold = eye_height * threshold_y
    down_threshold = eye_height * (1 - threshold_y)

    # If pupil is within central range → Looking at Camera
    if left_threshold <= avg_pupil_x <= right_threshold and up_threshold <= pupil_y <= down_threshold:
        return "Looking at Camera"
    return "Looking Away"




# Start video capture
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    total_frames += 1  # Count total frames

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(frame_rgb)

    gaze_status = "Not Looking at Camera"
    highlight_color = (0, 0, 255)  # Default: Red (Eyes not detected)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # Extract eye regions
            left_eye_frame, left_eye_coords = get_eye_region(face_landmarks, LEFT_EYE_INDICES, frame)
            right_eye_frame, right_eye_coords = get_eye_region(face_landmarks, RIGHT_EYE_INDICES, frame)

            # Validate eye regions before detecting pupils
            if left_eye_frame is not None and right_eye_frame is not None:
                left_pupil = detect_pupil(left_eye_frame)
                right_pupil = detect_pupil(right_eye_frame)

                # Ensure both pupils are considered, even if one is missing
                if left_pupil is None and right_pupil is not None:
                    left_pupil = right_pupil
                elif right_pupil is None and left_pupil is not None:
                    right_pupil = left_pupil

            # If pupils detected, update gaze status
            if left_pupil and right_pupil:
                eye_width = left_eye_coords[2] - left_eye_coords[0]
                eye_height = left_eye_coords[3] - left_eye_coords[1]
                gaze_status = get_gaze_status(left_pupil[0], right_pupil[0], left_pupil[1], eye_width, eye_height)

                # Set color based on gaze direction
                if gaze_status == "Looking at Camera":
                    highlight_color = (0, 255, 0)  # Green (Focused)
                    looking_at_camera_frames += 1
                else:
                    highlight_color = (0, 255, 255)  # Yellow (Looking Away)
            else:
                gaze_status = "Not Looking at Camera"
                highlight_color = (0, 0, 255)  # Red (Eyes not detected)

            # Draw pupil on the screen
            if left_pupil:
                cv2.circle(frame, (left_pupil[0] + left_eye_coords[0], left_pupil[1] + left_eye_coords[1]), 5, (255, 0, 0), -1)
            if right_pupil:
                cv2.circle(frame, (right_pupil[0] + right_eye_coords[0], right_pupil[1] + right_eye_coords[1]), 5, (255, 0, 0), -1)

    # Display status with color feedback
    cv2.putText(frame, gaze_status, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, highlight_color, 2)
    cv2.imshow("MediaPipe Pupil Tracking - Fixed", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# Calculate percentage
if total_frames > 0:
    looking_percentage = (looking_at_camera_frames / total_frames) * 100
else:
    looking_percentage = 0

# Save to file
with open("gaze_report.txt", "w") as file:
    file.write(f"Total Frames: {total_frames}\n")
    file.write(f"Frames Looking at Camera: {looking_at_camera_frames}\n")
    file.write(f"Percentage Looking at Camera: {looking_percentage:.2f}%\n")