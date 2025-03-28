from RealtimeSTT import AudioToTextRecorder

if __name__ == '__main__':
    with AudioToTextRecorder() as recorder:
        print("Transcription: ", recorder.text())