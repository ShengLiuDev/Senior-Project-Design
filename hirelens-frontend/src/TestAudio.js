import React, { useState, useRef } from 'react';

function TestAudio() {
    const [recording, setRecording] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [status, setStatus] = useState('ready');
    const [error, setError] = useState(null);
    
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);
    const audioStreamRef = useRef(null);
    
    const startRecording = async () => {
        try {
            setStatus('recording');
            setError(null);
            
            // Get audio stream
            const audioStream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                } 
            });
            audioStreamRef.current = audioStream;
            
            // Initialize MediaRecorder
            const options = { mimeType: 'audio/wav' };
            
            // Check if WAV is supported, fallback to WebM
            if (!MediaRecorder.isTypeSupported('audio/wav')) {
                console.log("WAV recording not supported, using WebM as fallback");
                options.mimeType = 'audio/webm;codecs=opus';
            }
            
            const mediaRecorder = new MediaRecorder(audioStream, options);
            mediaRecorderRef.current = mediaRecorder;
            
            // Clear previous audio chunks
            audioChunksRef.current = [];
            
            // Handle dataavailable event
            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                    console.log(`Audio chunk captured, size: ${event.data.size} bytes`);
                }
            };
            
            // Start recording
            mediaRecorder.start(2000); // Collect data every 2 seconds
            console.log('MediaRecorder started with format:', mediaRecorder.mimeType);
            
            setRecording(true);
        } catch (err) {
            console.error('Error starting recording:', err);
            setError('Failed to start recording: ' + err.message);
            setStatus('ready');
        }
    };
    
    const stopRecording = async () => {
        try {
            if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') {
                console.warn('MediaRecorder not active, nothing to stop');
                setRecording(false);
                setStatus('ready');
                return;
            }
            
            setStatus('processing');
            
            // Define event for when recording stops
            mediaRecorderRef.current.onstop = async () => {
                try {
                    const audioBlob = new Blob(audioChunksRef.current, { type: mediaRecorderRef.current.mimeType });
                    console.log(`Audio recording completed, size: ${audioBlob.size} bytes`);
                    
                    // Stop all audio tracks
                    if (audioStreamRef.current) {
                        audioStreamRef.current.getTracks().forEach(track => track.stop());
                    }
                    
                    // Process audio using backend transcription
                    if (audioBlob.size > 0) {
                        // Convert blob to base64
                        const reader = new FileReader();
                        reader.readAsDataURL(audioBlob);
                        
                        // Wait for file reading to complete
                        const base64Audio = await new Promise((resolve) => {
                            reader.onloadend = () => resolve(reader.result);
                        });
                        
                        // Send to backend test-transcription endpoint
                        console.log("Sending audio to backend for transcription testing");
                        
                        const response = await fetch('http://localhost:5000/api/test-transcription', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                audio_data: base64Audio
                            })
                        });
                        
                        if (response.ok) {
                            const data = await response.json();
                            console.log('Transcription result:', data);
                            setTranscript(data.transcription || '[No transcription returned]');
                        } else {
                            const errorData = await response.json();
                            setError(`Server error: ${errorData.error || 'Unknown error'}`);
                            console.error('Server error:', errorData);
                        }
                    } else {
                        setError('No audio data recorded');
                    }
                    
                    setRecording(false);
                    setStatus('ready');
                    
                } catch (error) {
                    console.error('Error processing recording:', error);
                    setError('Error processing recording: ' + error.message);
                    setRecording(false);
                    setStatus('ready');
                }
            };
            
            // Stop the recorder
            mediaRecorderRef.current.stop();
            console.log('MediaRecorder stopped');
            
        } catch (err) {
            console.error('Error stopping recording:', err);
            setError('Error stopping recording: ' + err.message);
            setRecording(false);
            setStatus('ready');
        }
    };
    
    return (
        <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
            <h1>Audio Transcription Test</h1>
            <p>Use this page to test the audio transcription functionality without needing to log in.</p>
            
            <div style={{ margin: '20px 0' }}>
                {status === 'ready' ? (
                    <button 
                        onClick={startRecording}
                        style={{
                            padding: '10px 20px',
                            fontSize: '16px',
                            backgroundColor: '#4CAF50',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer'
                        }}
                    >
                        Start Recording
                    </button>
                ) : status === 'recording' ? (
                    <button 
                        onClick={stopRecording}
                        style={{
                            padding: '10px 20px',
                            fontSize: '16px',
                            backgroundColor: '#f44336',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer'
                        }}
                    >
                        Stop Recording
                    </button>
                ) : (
                    <div>
                        <p>Processing audio...</p>
                        <div style={{ 
                            border: '4px solid #f3f3f3',
                            borderRadius: '50%',
                            borderTop: '4px solid #3498db',
                            width: '30px',
                            height: '30px',
                            animation: 'spin 2s linear infinite',
                            marginTop: '10px'
                        }}></div>
                        <style>{`
                            @keyframes spin {
                                0% { transform: rotate(0deg); }
                                100% { transform: rotate(360deg); }
                            }
                        `}</style>
                    </div>
                )}
            </div>
            
            {recording && (
                <div style={{ 
                    marginTop: '20px',
                    padding: '10px',
                    backgroundColor: '#ffcccc',
                    borderRadius: '4px',
                    display: 'flex',
                    alignItems: 'center'
                }}>
                    <div style={{
                        width: '12px',
                        height: '12px',
                        backgroundColor: '#f44336',
                        borderRadius: '50%',
                        marginRight: '10px',
                        animation: 'pulse 1s infinite'
                    }}></div>
                    <span>Recording in progress...</span>
                    <style>{`
                        @keyframes pulse {
                            0% { opacity: 1; }
                            50% { opacity: 0.5; }
                            100% { opacity: 1; }
                        }
                    `}</style>
                </div>
            )}
            
            {error && (
                <div style={{ 
                    marginTop: '20px',
                    padding: '10px',
                    backgroundColor: '#ffcccc',
                    borderRadius: '4px'
                }}>
                    <strong>Error:</strong> {error}
                </div>
            )}
            
            {transcript && (
                <div style={{ 
                    marginTop: '20px',
                    padding: '15px',
                    backgroundColor: '#e8f5e9',
                    borderRadius: '4px',
                    border: '1px solid #c8e6c9'
                }}>
                    <h2>Transcription Result:</h2>
                    <p style={{ 
                        fontSize: '16px',
                        lineHeight: '1.5'
                    }}>{transcript}</p>
                </div>
            )}
            
            <div style={{ marginTop: '30px' }}>
                <h3>Debugging Info:</h3>
                <ul>
                    <li>Status: {status}</li>
                    <li>Recording: {recording ? 'Yes' : 'No'}</li>
                    <li>
                        <a href="http://localhost:5000/api/test-connection" target="_blank" rel="noopener noreferrer">
                            Test Backend Connection
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    );
}

export default TestAudio; 