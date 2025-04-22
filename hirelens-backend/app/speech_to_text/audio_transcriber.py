import os
import sys
import base64
import time
import uuid
import requests
from datetime import datetime
import tempfile

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

# Setup logging
import logging
logger = logging.getLogger("audio_transcriber")
logger.setLevel(logging.INFO)

class AudioTranscriber:
    """Simplified AudioTranscriber that doesn't require librosa"""
    
    def __init__(self):
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.openrouter_api_key:
            logger.warning("OpenRouter API key not found. Transcription will use Google Speech Recognition only.")
            
        # Initialize logger for tracking issues
        self.logger = logging.getLogger("audio_transcriber")
        self.logger.setLevel(logging.INFO)
        
    def transcribe_audio(self, audio_file_path):
        """
        Transcribe audio file using either OpenRouter API or Google Speech Recognition
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            str: Transcribed text
        """
        try:
            # Check if file exists and has content
            if not os.path.exists(audio_file_path):
                return "[Error: Audio file not found]"
                
            file_size = os.path.getsize(audio_file_path)
            if file_size < 1000:  # Less than 1KB
                return "[Error: Audio file too small]"
                
            self.logger.info(f"Processing audio file: {audio_file_path} (size: {file_size} bytes)")
            
            # Try Google Speech Recognition
            import speech_recognition as sr
            r = sr.Recognizer()
            
            # Convert WebM to WAV if needed
            wav_file = audio_file_path
            if audio_file_path.endswith('.webm'):
                try:
                    # Use the directory of the original file
                    wav_file = os.path.join(os.path.dirname(audio_file_path), 
                                        f"{os.path.basename(audio_file_path).split('.')[0]}.wav")
                    
                    # Use ffmpeg for conversion
                    import subprocess
                    self.logger.info(f"Converting WebM to WAV: {audio_file_path} -> {wav_file}")
                    command = ['ffmpeg', '-i', audio_file_path, '-ac', '1', '-ar', '16000', wav_file]
                    subprocess.run(command, check=True, capture_output=True)
                    self.logger.info(f"Conversion successful, using {wav_file}")
                except Exception as e:
                    self.logger.error(f"Error converting WebM to WAV: {e}")
                    self.logger.info("Using original file for transcription")
                    wav_file = audio_file_path
            
            try:
                with sr.AudioFile(wav_file) as source:
                    self.logger.info(f"Reading audio from {wav_file}")
                    audio_data = r.record(source)
                    
                    # Use Google's speech recognition
                    self.logger.info("Transcribing with Google Speech Recognition")
                    text = r.recognize_google(audio_data)
                    self.logger.info(f"Transcription successful: {text[:50]}...")
                    return text
            except Exception as e:
                self.logger.error(f"Google Speech Recognition failed: {e}")
                
                # Try OpenRouter if API key is available
                if self.openrouter_api_key:
                    try:
                        text = self._transcribe_with_openrouter(wav_file)
                        if text:
                            return text
                    except Exception as e:
                        self.logger.error(f"OpenRouter transcription failed: {e}")
                
                return "[Error: Could not transcribe audio]"
                
        except Exception as e:
            self.logger.error(f"Transcription error: {e}")
            import traceback
            traceback.print_exc()
            return f"[Error: {str(e)}]"
            
    def transcribe_base64(self, base64_audio, question=None):
        """
        Transcribe audio from base64 string
        
        Args:
            base64_audio: Base64 encoded audio data
            question: Optional question for context
            
        Returns:
            str: Transcribed text
        """
        try:
            # Create temp directory for audio files
            temp_dir = tempfile.mkdtemp()
            self.logger.info(f"Created temp directory: {temp_dir}")
            
            # Generate unique filename
            filename = f"audio_{uuid.uuid4().hex}.webm"
            filepath = os.path.join(temp_dir, filename)
            
            # Remove data URL prefix if present
            if ',' in base64_audio:
                base64_audio = base64_audio.split(',', 1)[1]
                
            # Decode and save as binary file
            self.logger.info(f"Saving base64 audio to {filepath}")
            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(base64_audio))
                
            # Transcribe and cleanup
            try:
                transcription = self.transcribe_audio(filepath)
                
                # Log question and answer for debugging
                if question:
                    self.logger.info(f"Question: {question}")
                    self.logger.info(f"Transcription: {transcription}")
                
                return transcription
            finally:
                # Clean up files
                if os.path.exists(filepath):
                    os.remove(filepath)
                    
                # Check for WAV file
                wav_path = filepath.replace('.webm', '.wav')
                if os.path.exists(wav_path):
                    os.remove(wav_path)
                    
        except Exception as e:
            self.logger.error(f"Error transcribing base64 audio: {e}")
            import traceback
            traceback.print_exc()
            return f"[Error: {str(e)}]"
            
    def _transcribe_with_openrouter(self, audio_file_path):
        """
        Transcribe audio using OpenRouter API
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            str: Transcribed text
        """
        try:
            # Read file as base64
            with open(audio_file_path, 'rb') as f:
                audio_bytes = f.read()
                
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Set up API request
            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "anthropic/claude-3-opus:free",
                "messages": [
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": "Please transcribe this audio recording accurately."},
                            {"type": "image_url", "image_url": {"url": f"data:audio/wav;base64,{audio_base64}"}}
                        ]
                    }
                ]
            }
            
            # Make request
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            response.raise_for_status()
            
            # Extract transcription
            text = response.json()["choices"][0]["message"]["content"]
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"OpenRouter transcription failed: {e}")
            raise 