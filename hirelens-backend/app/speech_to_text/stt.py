import os
import sys
import time
import threading
import wave
from datetime import datetime
from RealtimeSTT import AudioToTextRecorder
import pyaudio
import platform
import secrets

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from app.answer_analysis.analyzer import AnswerAnalyzer
from app.sentiment_analysis.sentiment_analysis_functions import sentiment_analysis

class InterviewRecorder:
    def __init__(self):
        # Initialize RealtimeSTT recorder
        self.recorder = AudioToTextRecorder(
            model="base",
            language="en",
            silero_sensitivity=0.6,
            webrtc_sensitivity=3
        )
        
        # Audio configuration
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        
        # Initialize analyzers
        self.answer_analyzer = AnswerAnalyzer()
        self.sentiment_analyzer = sentiment_analysis()
        
        # Ensure recordings directory exists
        self.recordings_dir = os.path.join(project_root, '.recordings')
        os.makedirs(self.recordings_dir, exist_ok=True)

    def record_answer(self, question, duration=90):
        """
        Record and analyze an answer for a given question
        Returns transcription and analysis
        """
        try:
            # Record and transcribe audio
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.recordings_dir, f"recording_{timestamp}.wav")
            
            print(f"\nRecording answer for question: {question}")
            print(f"You have {duration} seconds to answer")
            print("Press Enter or Space to stop recording early")
            
            # Record audio
            text = self._record_audio(filename, duration)
            
            # Analyze the answer
            analysis = self._analyze_answer(text, question)
            
            return {
                'transcription': text,
                'analysis': analysis,
                'recording_path': filename
            }
            
        except Exception as e:
            print(f"Error recording answer: {e}")
            return None

    def _record_audio(self, filename, duration):
        """Internal method to record audio"""
        p = pyaudio.PyAudio()
        stream = p.open(format=self.FORMAT,
                       channels=self.CHANNELS,
                       rate=self.RATE,
                       input=True,
                       frames_per_buffer=self.CHUNK)
        
        # Start recording
        self.recorder.start()
        frames = []
        
        # Start timer thread
        stop_timer = threading.Event()
        timer_thread = threading.Thread(target=self._show_elapsed_time, args=(stop_timer,))
        timer_thread.start()
        
        # Start key press thread
        stop_recording = threading.Event()
        key_thread = threading.Thread(target=self._check_for_key, args=(stop_recording,))
        key_thread.start()
        
        # Record until duration or key press
        start_time = time.time()
        while time.time() - start_time < duration and not stop_recording.is_set():
            try:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                frames.append(data)
            except OSError as e:
                if e.errno == -9981:  # Input overflowed
                    continue
                raise
        
        # Clean up threads
        stop_timer.set()
        stop_recording.set()
        timer_thread.join()
        key_thread.join()
        
        # Stop recording and get text
        self.recorder.stop()
        text = self.recorder.text()
        
        # Save WAV file
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

    def _analyze_answer(self, text, question):
        """Internal method to analyze the answer"""
        # Get answer analysis
        analysis = self.answer_analyzer.analyze_answer(question, text)
        
        # Get sentiment analysis
        sentiment_result = self.sentiment_analyzer.predict(text)
        analysis['sentiment'] = sentiment_result
        
        # If sentiment is negative, provide positive reformulation
        if sentiment_result == 'negative':
            analysis['positive_reformulation'] = self.sentiment_analyzer.reformulate_positive(text)
        
        return analysis

    def _show_elapsed_time(self, stop_event):
        """Show elapsed time while recording"""
        start_time = time.time()
        while not stop_event.is_set():
            elapsed = int(time.time() - start_time)
            print(f"\rElapsed time: {elapsed} seconds", end="")
            time.sleep(1)

    def _check_for_key(self, stop_event):
        """Check for Enter or Space key press"""
        if platform.system() == 'Windows':
            import msvcrt
            while not stop_event.is_set():
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key in (b'\r', b' '):
                        stop_event.set()
                        break
                time.sleep(0.1)
        else:
            import select
            import termios
            import tty
            
            old_settings = termios.tcgetattr(sys.stdin)
            try:
                tty.setcbreak(sys.stdin.fileno())
                while not stop_event.is_set():
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        key = sys.stdin.read(1)
                        if key in ('\r', ' '):
                            stop_event.set()
                            break
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def get_random_questions(num_questions=3):
    """Get random interview questions"""
    try:
        analyzer = AnswerAnalyzer()
        return analyzer.get_random_questions(num_questions)
    except Exception as e:
        print(f"Error getting questions: {e}")
        return []

def main():
    """Main function to run the interview recorder"""
    print("\n=== Interview Recording System ===")
    
    # Get random questions
    questions = get_random_questions(3)
    if not questions:
        print("Error: Could not get questions")
        return
    
    # Initialize recorder
    recorder = InterviewRecorder()
    
    # Process each question
    for i, question in enumerate(questions):
        print(f"\nQuestion {i+1} of {len(questions)}")
        print(f"Question: {question}")
        
        # Allow 3 attempts
        for attempt in range(3):
            print(f"\nAttempt {attempt + 1} of 3")
            input("Press Enter to start recording...")
            
            # Record and analyze
            result = recorder.record_answer(question)
            
            if result:
                print("\nTranscription:")
                print(result['transcription'])
                print("\nAnalysis:")
                for key, value in result['analysis'].items():
                    print(f"{key}: {value}")
                print("-" * 50)
            
            # Ask if user wants to try again
            if attempt < 2:
                retry = input("Would you like to try again? (y/n): ").lower()
                if retry != 'y':
                    break

if __name__ == "__main__":
    main()