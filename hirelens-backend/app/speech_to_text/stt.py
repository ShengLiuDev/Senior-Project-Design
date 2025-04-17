import os
import sys
import time
import threading
import wave
from datetime import datetime
from RealtimeSTT import AudioToTextRecorder
import pyaudio
import platform
import random

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from app.answer_analysis.analyzer import AnswerAnalyzer
from app.sentiment_analysis.sentiment_analysis_functions import sentiment_analysis
from app.sentiment_analysis.csv_readin_functions import csv_read_in_functions

# Import appropriate module based on OS for key detection
if platform.system() == 'Windows':
    import msvcrt
else:
    import select
    import termios
    import tty

def ensure_recordings_dir():
    """
    Create .recordings directory if it doesn't exist
    """
    recordings_dir = os.path.join(project_root, '.recordings')
    os.makedirs(recordings_dir, exist_ok=True)
    return recordings_dir

class SpeechDetector:
    def __init__(self):
        # Initialize RealtimeSTT recorder with default settings
        self.recorder = AudioToTextRecorder(
            model="base",  # Use the base model for better performance
            language="en",  # Set language to English
            silero_sensitivity=0.6,  # Adjust sensitivity for voice detection
            webrtc_sensitivity=3  # Adjust WebRTC sensitivity
        )
        
        # Audio configuration for saving WAV files
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        
    def record_audio(self, filename, duration=20):
        """
        Record audio for specified duration using RealtimeSTT while saving WAV file
        Can be stopped early by pressing Enter or Space
        """
        print(f"Recording started... You have {duration} seconds")
        print("Press Enter or Space to stop recording early")
        
        # Initialize PyAudio for saving WAV file
        p = pyaudio.PyAudio()
        stream = p.open(format=self.FORMAT,
                       channels=self.CHANNELS,
                       rate=self.RATE,
                       input=True,
                       frames_per_buffer=self.CHUNK,
                       input_device_index=None)  # Use default input device
        
        # Start recording with RealtimeSTT
        self.recorder.start()
        frames = []
        
        # Start a thread to show elapsed time
        stop_timer = threading.Event()
        timer_thread = threading.Thread(target=show_elapsed_time, args=(stop_timer,))
        timer_thread.start()
        
        # Start a thread to check for key press
        stop_recording = threading.Event()
        key_thread = threading.Thread(target=check_for_key, args=(stop_recording,))
        key_thread.start()
        
        # Record until duration is reached or key is pressed
        start_time = time.time()
        while time.time() - start_time < duration and not stop_recording.is_set():
            try:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                frames.append(data)
            except OSError as e:
                if e.errno == -9981:  # Input overflowed
                    print("\nBuffer overflow detected, continuing recording...")
                    continue
                else:
                    raise
        
        # Stop the timer thread
        stop_timer.set()
        timer_thread.join()
        
        # Stop the key thread
        stop_recording.set()
        key_thread.join()
        
        # Stop recording and get the text
        self.recorder.stop()
        text = self.recorder.text()
        
        print("\nRecording finished!")
        
        # Save the recorded data as a WAV file
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        # Clean up
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        return text

def show_elapsed_time(stop_event):
    """
    Show elapsed time while recording
    """
    start_time = time.time()
    while not stop_event.is_set():
        elapsed = int(time.time() - start_time)
        print(f"\rElapsed time: {elapsed} seconds", end="")
        time.sleep(1)

def check_for_key(stop_event):
    """
    Check for Enter or Space key press to stop recording
    """
    if platform.system() == 'Windows':
        while not stop_event.is_set():
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in (b'\r', b' '):  # Enter or Space
                    stop_event.set()
                    break
            time.sleep(0.1)
    else:
        # Save terminal settings
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            while not stop_event.is_set():
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    key = sys.stdin.read(1)
                    if key in ('\r', ' '):  # Enter or Space
                        stop_event.set()
                        break
        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def analyze_answer(text, question):
    """
    Analyze the transcribed answer using the AnswerAnalyzer and sentiment_analysis classes
    """
    # Initialize analyzers
    answer_analyzer = AnswerAnalyzer()
    sentiment_analyzer = sentiment_analysis()
    
    # Get answer analysis
    analysis = answer_analyzer.analyze_answer(question, text)
    
    # Get sentiment analysis
    sentiment_result = sentiment_analyzer.predict(text)
    
    # Add sentiment information to the analysis
    analysis['sentiment'] = sentiment_result
    
    # If sentiment is negative, provide a positive reformulation
    if sentiment_result == 'negative':
        analysis['positive_reformulation'] = sentiment_analyzer.reformulate_positive(text)
    
    return analysis

def get_random_questions(num_questions=3):
    """Get a list of random interview questions from the dataset"""
    try:
        # Initialize the AnswerAnalyzer
        analyzer = AnswerAnalyzer()
        
        # Get questions from the dataset
        questions = analyzer.get_random_questions(num_questions)
        
        return questions
    except Exception as e:
        print(f"Error getting random questions: {e}")
        return []

def main():
    print("Speech-to-Text Analysis Program")
    print("You will be prompted to record answers to interview questions.")
    print("You will have 3 attempts for each question.")
    
    # Ensure recordings directory exists
    recordings_dir = ensure_recordings_dir()
    
    # Initialize analyzer and get random questions
    analyzer = AnswerAnalyzer()
    questions = analyzer.get_random_questions(num_questions=3)
    
    # Initialize speech detector
    detector = SpeechDetector()
    
    for i, question in enumerate(questions):
        print(f"\nQuestion {i+1} of {len(questions)}")
        print(f"Question: {question}")
        
        # Allow 3 attempts per question
        for attempt in range(3):
            print(f"\nAttempt {attempt + 1} of 3")
            input("Press Enter to start recording...")
            
            # Record and transcribe audio
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(recordings_dir, f"recording_{i+1}_attempt_{attempt+1}_{timestamp}.wav")
            print("\nRecording and transcribing...")
            text = detector.record_audio(filename, duration=20)
            
            print("\nTranscription:")
            print(text)
            
            # Analyze the answer
            print("\nAnalyzing answer...")
            analysis = analyze_answer(text, question)
            
            print("\nAnalysis Results:")
            for key, value in analysis.items():
                print(f"{key}: {value}\n")
            print("-" * 50)
            
            # Ask if user wants to try again
            if attempt < 2:  # Don't ask on the last attempt
                retry = input("Would you like to try again? (y/n): ").lower()
                if retry != 'y':
                    break

if __name__ == "__main__":
    main()