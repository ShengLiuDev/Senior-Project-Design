import pyaudio
import wave
import speech_recognition as sr
import time
import threading
import os
import sys
from datetime import datetime

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))  # This goes up to hirelens-backend
sys.path.append(parent_dir)

from app.answer_analysis.analyzer import AnswerAnalyzer

def ensure_recordings_dir():
    """
    Create .recordings directory if it doesn't exist
    """
    recordings_dir = os.path.join(current_dir, '.recordings')
    os.makedirs(recordings_dir, exist_ok=True)
    return recordings_dir

# set to 90 second duration for production, testing for now with 20 second duration
def record_audio(filename, duration=20):
    """
    Record audio for specified duration
    """
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    
    p = pyaudio.PyAudio()
    
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    
    print(f"Recording started... You have {duration} seconds")
    frames = []
    
    # Start a thread to show elapsed time
    stop_timer = threading.Event()
    timer_thread = threading.Thread(target=show_elapsed_time, args=(stop_timer,))
    timer_thread.start()
    
    # Record for specified duration
    for i in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)
    
    # Stop the timer thread
    stop_timer.set()
    timer_thread.join()
    
    print("\nRecording finished!")
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Save the recorded data as a WAV file
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def show_elapsed_time(stop_event):
    """
    Show elapsed time while recording
    """
    start_time = time.time()
    while not stop_event.is_set():
        elapsed = int(time.time() - start_time)
        print(f"\rElapsed time: {elapsed} seconds", end="")
        time.sleep(1)

def transcribe_audio(filename):
    """
    Transcribe the recorded audio file
    """
    recognizer = sr.Recognizer()
    
    with sr.AudioFile(filename) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError as e:
            return f"Error with the speech recognition service; {e}"

def analyze_answer(text, question):
    """
    Analyze the transcribed answer using the AnswerAnalyzer
    """
    analyzer = AnswerAnalyzer()
    analysis = analyzer.analyze_answer(question, text)  # Note: parameters swapped to match analyzer.py
    return analysis

def main():
    print("Speech-to-Text Sample Program")
    print("You will be prompted to record 3 times, 90 seconds each time.")
    
    # Ensure recordings directory exists
    recordings_dir = ensure_recordings_dir()
    
    # Sample questions for testing
    questions = [
        "Tell me about a time when you faced a difficult challenge at work and how you handled it.",
        "Describe a situation where you had to work with a difficult team member.",
        "What are your greatest strengths and how have they helped you in your career?"
    ]
    
    for i in range(2):
        print(f"\nRecording {i+1} of 2")
        print(f"Question: {questions[i]}")
        input("Press Enter to start recording...")
        
        # Record audio
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(recordings_dir, f"recording_{i+1}_{timestamp}.wav")
        record_audio(filename)
        
        # Transcribe audio
        print("\nTranscribing...")
        text = transcribe_audio(filename)
        
        print("\nTranscription:")
        print(text)
        
        # Analyze the answer
        print("\nAnalyzing answer...")
        analysis = analyze_answer(text, questions[i])
        
        print("\nAnalysis Results:")
        print(analysis)
        print("-" * 50)

if __name__ == "__main__":
    main()
