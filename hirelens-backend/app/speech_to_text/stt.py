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
        try:
            # Initialize RealtimeSTT recorder with improved parameters for web usage
            self.recorder = AudioToTextRecorder(
                model="base",                  # Use base model for faster processing
                language="en",                 # English language
                silero_sensitivity=0.7,        # Slightly higher sensitivity
                webrtc_sensitivity=4           # Increase sensitivity for web use
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
            
            # Print audio device info for debugging
            self._print_audio_devices()
            
            print("✅ AudioToTextRecorder initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing AudioToTextRecorder: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Create a fallback recorder that will return empty strings
            # This prevents the app from crashing if audio recording fails
            from types import SimpleNamespace
            self.recorder = SimpleNamespace()
            self.recorder.start = lambda: None
            self.recorder.stop = lambda: None
            self.recorder.text = lambda: ""
            
    def _print_audio_devices(self):
        """Print available audio devices for debugging"""
        try:
            p = pyaudio.PyAudio()
            info = p.get_host_api_info_by_index(0)
            num_devices = info.get('deviceCount')
            
            print(f"\n=== Available Audio Devices ({num_devices}) ===")
            for i in range(num_devices):
                device_info = p.get_device_info_by_host_api_device_index(0, i)
                name = device_info.get('name')
                inputs = device_info.get('maxInputChannels')
                if inputs > 0:  # Only show input devices
                    print(f"Device {i}: {name} (Inputs: {inputs})")
            print("="*40)
            
            p.terminate()
        except Exception as e:
            print(f"Error listing audio devices: {str(e)}")

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

    def transcribe_from_file(self, audio_file_path):
        """
        Transcribe audio from an existing file
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            str: Transcribed text
        """
        try:
            # Check if file exists
            if not os.path.exists(audio_file_path):
                print(f"Audio file not found: {audio_file_path}")
                return "[Audio file not found]"
            
            # Check file size
            file_size = os.path.getsize(audio_file_path)
            print(f"Audio file size: {file_size} bytes")
            
            if file_size < 100:  # Very small file likely means no audio was recorded
                print("Audio file too small, likely no speech recorded")
                return "[No speech detected]"
            
            # Simplified approach - try SpeechRecognition first
            try:
                import speech_recognition as sr
                r = sr.Recognizer()
                
                # Convert WebM to WAV if needed
                wav_file = audio_file_path
                if audio_file_path.endswith('.webm'):
                    try:
                        wav_file = os.path.join(os.path.dirname(audio_file_path), 
                                             f"{os.path.basename(audio_file_path).split('.')[0]}.wav")
                        
                        # Use ffmpeg to convert if available
                        import subprocess
                        print(f"Converting WebM to WAV: {audio_file_path} -> {wav_file}")
                        command = ['ffmpeg', '-i', audio_file_path, '-ac', '1', '-ar', '16000', wav_file]
                        subprocess.run(command, check=True, capture_output=True)
                        print(f"Conversion successful, using {wav_file}")
                    except Exception as e:
                        print(f"Error converting WebM to WAV: {e}")
                        print("Will try to process with original file")
                        wav_file = audio_file_path
                
                print(f"Processing with SpeechRecognition: {wav_file}")
                with sr.AudioFile(wav_file) as source:
                    # Adjust for ambient noise
                    r.adjust_for_ambient_noise(source, duration=0.5)
                    
                    # Record audio data
                    audio_data = r.record(source)
                    
                    # Use Google's speech recognition
                    text = r.recognize_google(audio_data)
                    print(f"Google Speech Recognition result: {text}")
                    return text
            except Exception as sr_error:
                print(f"SpeechRecognition error: {sr_error}")
                
                # Fallback to RealtimeSTT
                try:
                    # Create a fresh recorder instance to avoid any state issues
                    from RealtimeSTT import AudioToTextRecorder
                    file_recorder = AudioToTextRecorder(
                        model="base",
                        language="en"
                    )
                    
                    # Process the file
                    text = file_recorder.process_file(wav_file or audio_file_path)
                    print(f"RealtimeSTT result: {text}")
                    return text if text else "[No speech detected]"
                except Exception as rtstt_error:
                    print(f"RealtimeSTT error: {rtstt_error}")
                    return "[Error during transcription]"
            
        except Exception as e:
            print(f"Error in transcribe_from_file: {e}")
            import traceback
            traceback.print_exc()
            return f"[Error during transcription: {str(e)}]"

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