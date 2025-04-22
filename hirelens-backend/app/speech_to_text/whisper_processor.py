import os
import sys
import subprocess
import tempfile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s [%(levelname)s] - %(message)s')
logger = logging.getLogger("whisper_processor")

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

def transcribe_audio(audio_file_path):
    """
    Transcribe audio file using speech_recognition library.
    Falls back to a simple message if recognition fails.
    
    Args:
        audio_file_path: Path to the audio file to transcribe
        
    Returns:
        str: Transcribed text
    """
    # Check if file exists
    if not os.path.exists(audio_file_path):
        logger.error(f"Audio file not found: {audio_file_path}")
        return "[Audio file not found]"
    
    # Check file size
    file_size = os.path.getsize(audio_file_path)
    logger.info(f"Audio file size: {file_size} bytes")
    
    if file_size < 100:  # Very small file likely means no audio was recorded
        logger.warning("Audio file too small, likely no speech recorded")
        return "[No speech detected]"
    
    try:
        # Try using speech_recognition with Google's API
        import speech_recognition as sr
        
        # Convert webm to wav using pydub if possible
        if audio_file_path.endswith('.webm'):
            logger.info("Converting webm to wav using pydub...")
            try:
                from pydub import AudioSegment
                
                # Create a temporary wav file
                wav_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
                
                try:
                    # First try with pydub
                    try:
                        audio = AudioSegment.from_file(audio_file_path, format="webm")
                        audio.export(wav_file, format="wav")
                        logger.info(f"Converted to WAV using pydub: {wav_file}")
                    except Exception as e:
                        logger.warning(f"Pydub conversion failed: {str(e)}, trying ffmpeg...")
                        # Fallback to ffmpeg
                        command = ['ffmpeg', '-i', audio_file_path, '-ac', '1', '-ar', '16000', wav_file]
                        subprocess.run(command, check=True, capture_output=True)
                        logger.info(f"Converted to WAV using ffmpeg: {wav_file}")
                        
                    # Use the converted wav file for recognition
                    audio_file_path = wav_file
                except Exception as e:
                    logger.error(f"Error converting webm to wav: {str(e)}")
                    # Continue with the original file if conversion fails
            except ImportError:
                logger.warning("Pydub not installed, trying ffmpeg directly...")
                # Fallback to using ffmpeg directly
                try:
                    # Create a temporary wav file
                    wav_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
                    
                    # Use ffmpeg to convert
                    command = ['ffmpeg', '-i', audio_file_path, '-ac', '1', '-ar', '16000', wav_file]
                    subprocess.run(command, check=True, capture_output=True)
                    logger.info(f"Converted to WAV using ffmpeg: {wav_file}")
                    
                    # Use the converted wav file for recognition
                    audio_file_path = wav_file
                except Exception as e:
                    logger.error(f"Error using ffmpeg: {str(e)}")
        
        # Debug: list directory contents 
        directory = os.path.dirname(audio_file_path)
        logger.info(f"Directory contents of {directory}:")
        for file in os.listdir(directory):
            logger.info(f"  - {file} ({os.path.getsize(os.path.join(directory, file))} bytes)")
        
        # Initialize recognizer
        r = sr.Recognizer()
        
        # Adjust recognizer settings for better recognition
        r.energy_threshold = 300  # default is 300
        r.dynamic_energy_threshold = True
        r.pause_threshold = 0.8  # default is 0.8
        r.operation_timeout = 10  # seconds
        
        # Load the audio file
        logger.info(f"Loading audio file: {audio_file_path}")
        with sr.AudioFile(audio_file_path) as source:
            # Adjust for ambient noise
            r.adjust_for_ambient_noise(source, duration=0.5)
            
            # Read the audio data
            logger.info("Recording audio data from file")
            audio_data = r.record(source)
            
            logger.info(f"Audio duration: approximately {len(audio_data.frame_data) / (audio_data.sample_rate * audio_data.sample_width)} seconds")
            
            # Try multiple recognition engines
            try:
                # First try Google's speech recognition
                logger.info("Attempting Google Speech Recognition")
                text = r.recognize_google(audio_data)
                logger.info(f"Google Speech Recognition result: {text}")
                return text
            except sr.UnknownValueError:
                # Fallback to Sphinx if Google fails
                try:
                    logger.info("Google failed, attempting Sphinx Speech Recognition")
                    # Use CMU Sphinx if Google fails (offline)
                    text = r.recognize_sphinx(audio_data)
                    logger.info(f"Sphinx Speech Recognition result: {text}")
                    return text
                except Exception as sphinx_error:
                    logger.error(f"Sphinx recognition error: {str(sphinx_error)}")
                    return "[Speech unclear]"
    
    except ImportError as e:
        logger.error(f"Required library not installed: {str(e)}")
        return "[Speech recognition not available]"
    except sr.UnknownValueError:
        logger.error("Speech recognition could not understand audio")
        return "[Speech unclear]"
    except sr.RequestError as e:
        logger.error(f"Could not request results from speech recognition service; {e}")
        return "[Speech recognition service unavailable]"
    except Exception as e:
        logger.error(f"Error in transcription: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Return a simple message if recognition fails
        return "[Error during transcription]"
    finally:
        # Clean up temporary wav file if it was created
        if 'wav_file' in locals() and os.path.exists(wav_file):
            try:
                os.remove(wav_file)
                logger.info(f"Removed temporary WAV file: {wav_file}")
            except Exception as e:
                logger.error(f"Error removing temporary WAV file: {str(e)}")

# Simple test function
if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        logger.info(f"Transcribing {file_path}...")
        transcript = transcribe_audio(file_path)
        logger.info(f"Transcript: {transcript}")
    else:
        logger.info("Please provide an audio file path as an argument") 