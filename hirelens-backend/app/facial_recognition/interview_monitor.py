import cv2
import numpy as np
import mediapipe as mp
from .posture_analyzer import PostureAnalyzer
from .eye_contact_analyzer import EyeContactAnalyzer
from .expression_analyzer import ExpressionAnalyzer

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def main():
    """
    Main function for running the interview monitor
    """
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    # Initialize analyzers
    eye_contact_analyzer = EyeContactAnalyzer()
    posture_analyzer = PostureAnalyzer()
    expression_analyzer = ExpressionAnalyzer()
    
    print("\nInterview monitoring started...")
    print("Recording your interview. Just act natural!")
    print("Press 'q' to stop and see your scores.\n")
    
    window_name = 'Interview Recording'
    cv2.namedWindow(window_name)
    
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Error reading from camera")
            break
            
        frame_count += 1
        
        # Show plain camera feed first, before any processing
        cv2.imshow(window_name, frame)
            
        # Process frame with face mesh
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(frame_rgb)
        
        # Process frame with each analyzer silently (without drawing)
        # Use deep copies to prevent any modifications to original frame
        eye_status, _ = eye_contact_analyzer.analyze_frame(frame.copy())
        posture_status, _ = posture_analyzer.analyze_frame(frame.copy())
        _, _, expression_details = expression_analyzer.analyze_frame(frame.copy(), results)
        
        # Break loop on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Clean up camera and windows
    cap.release()
    cv2.destroyAllWindows()
    cv2.waitKey(1)
    
    if frame_count == 0:
        print("No frames were processed. Please check if your camera is connected and not in use by another application.")
        return
    
    # Generate final report
    eye_contact_report = eye_contact_analyzer.get_eye_contact_score()
    posture_report = posture_analyzer.get_posture_score()
    
    # Get final expression details
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
        (eye_contact_report['eye_contact_score'] * 0.3)
    )
    
    # Print final scores with clear formatting
    print("\n" + "="*50)
    print("INTERVIEW ANALYSIS RESULTS")
    print("="*50)
    print(f"\nPOSTURE:")
    print(f"  Score: {posture_report['posture_score']:.1f}%")
    
    print(f"\nSMILING:")
    print(f"  Time Spent Smiling: {smile_percentage:.1f}%")
    
    print(f"\nEYE CONTACT:")
    print(f"  Score: {eye_contact_report['eye_contact_score']:.1f}%")
    
    print("\n" + "-"*50)
    print(f"OVERALL SCORE: {overall_score:.1f}%")
    print("-"*50)
    
    # Save detailed report to file
    with open("interview_report.txt", "w") as file:
        file.write("="*50 + "\n")
        file.write("INTERVIEW ANALYSIS RESULTS\n")
        file.write("="*50 + "\n\n")
        
        file.write("POSTURE:\n")
        file.write(f"  Score: {posture_report['posture_score']:.1f}%\n")
        
        file.write("\nSMILING:\n")
        file.write(f"  Time Spent Smiling: {smile_percentage:.1f}%\n")
        
        file.write("\nEYE CONTACT:\n")
        file.write(f"  Score: {eye_contact_report['eye_contact_score']:.1f}%\n")
        
        file.write("\n" + "-"*50 + "\n")
        file.write(f"OVERALL SCORE: {overall_score:.1f}%\n")
        file.write("-"*50 + "\n")
    
    print(f"\nDetailed report saved to interview_report.txt")

if __name__ == "__main__":
    main() 