import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from './Header';
import './FrontPage.css';

function Interview() {
	const navigate = useNavigate();
	const [status, setStatus] = useState('ready'); // ready, recording, processing
	const [error, setError] = useState(null);
	const [results, setResults] = useState(null);
	const [frameCount, setFrameCount] = useState(0);
	
	const videoRef = useRef(null);
	const canvasRef = useRef(null);
	const streamRef = useRef(null);
	const sessionIdRef = useRef(null);
	const recordingIntervalRef = useRef(null);

	// Initialize camera
	const initializeCamera = async () => {
		try {
			const stream = await navigator.mediaDevices.getUserMedia({ 
				video: { 
					width: 640, 
					height: 480,
					facingMode: 'user'
				} 
			});
			
			streamRef.current = stream;
			if (videoRef.current) {
				videoRef.current.srcObject = stream;
			}
		} catch (err) {
			setError('Failed to access camera. Please ensure camera permissions are granted.');
			console.error('Camera error:', err);
		}
	};

	// Start interview session
	const startInterview = async () => {
		try {
			setStatus('recording');
			setError(null);
			setResults(null);
			setFrameCount(0);

			// Start camera if not already running
			if (!streamRef.current) {
				await initializeCamera();
			}

			// Create new session
			const sessionId = `session_${Date.now()}`;
			sessionIdRef.current = sessionId;

			const response = await fetch('http://localhost:5000/api/interview/start', {
				method: 'POST',
				headers: {
					'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ session_id: sessionId })
			});

			if (!response.ok) {
				throw new Error('Failed to start interview session');
			}

			// Start recording frames
			recordingIntervalRef.current = setInterval(recordFrame, 1000/30); // 30 FPS do not change this

		} catch (err) {
			setError('Failed to start interview');
			console.error('Start interview error:', err);
			stopInterview();
		}
	};

	// Record a single frame
	const recordFrame = async () => {
		try {
			if (!canvasRef.current || !videoRef.current || !sessionIdRef.current) {
				console.log('Missing required refs:', {
					canvas: !!canvasRef.current,
					video: !!videoRef.current,
					sessionId: !!sessionIdRef.current
				});
				return;
			}

			const canvas = canvasRef.current;
			const video = videoRef.current;
			const context = canvas.getContext('2d');

			// Set canvas size to match video
			canvas.width = video.videoWidth;
			canvas.height = video.videoHeight;

			// Draw current video frame to canvas
			context.drawImage(video, 0, 0, canvas.width, canvas.height);

			// Convert to base64 with proper format
			const frameData = canvas.toDataURL('image/jpeg', 0.8);
			
			// Validate frame data
			if (!frameData || !frameData.startsWith('data:image/jpeg;base64,')) {
				console.error('Invalid frame data format');
				return;
			}

			// Send frame to backend
			const response = await fetch('http://localhost:5000/api/interview/record', {
				method: 'POST',
				headers: {
					'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					session_id: sessionIdRef.current,
					frame: frameData
				})
			});

			if (!response.ok) {
				const errorData = await response.json();
				console.error('Frame recording error:', errorData);
				throw new Error(errorData.message || 'Failed to record frame');
			}

			const data = await response.json();
			console.log('Frame recorded successfully:', data);

		} catch (err) {
			console.error('Frame recording error:', err);
		}
	};

	// Stop interview session
	const stopInterview = async () => {
		try {
			setStatus('processing');

			// Clear recording interval
			if (recordingIntervalRef.current) {
				clearInterval(recordingIntervalRef.current);
				recordingIntervalRef.current = null;
			}

			// Stop camera
			if (streamRef.current) {
				streamRef.current.getTracks().forEach(track => track.stop());
				streamRef.current = null;
			}

			// Stop interview on backend
			if (sessionIdRef.current) {
				const response = await fetch('http://localhost:5000/api/interview/stop', {
					method: 'POST',
					headers: {
						'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
						'Content-Type': 'application/json'
					},
					body: JSON.stringify({ session_id: sessionIdRef.current })
				});

				if (!response.ok) {
					throw new Error('Failed to stop interview');
				}

				const data = await response.json();
				console.log('Interview results:', data); // Debug log
				
				// Set the results
				setResults({
					overall_score: data.final_scores?.overall_score || 0,
					posture_score: data.final_scores?.posture_score || 0,
					eye_contact_score: data.final_scores?.eye_contact_score || 0,
					smile_percentage: data.final_scores?.smile_percentage || 0
				});
				
				sessionIdRef.current = null;
			}

		} catch (err) {
			setError('Failed to stop interview');
			console.error('Stop interview error:', err);
			setStatus('ready');
		}
	};

	// Handle ESC key press
	const handleKeyPress = (event) => {
		if (event.key === 'Escape' && status === 'recording') {
			stopInterview();
		}
	};

	// Add ESC key listener when component mounts and status is recording
	useEffect(() => {
		if (status === 'recording') {
			window.addEventListener('keydown', handleKeyPress);
		}
		return () => {
			window.removeEventListener('keydown', handleKeyPress);
		};
	}, [status]);

	// Cleanup on component unmount
	useEffect(() => {
		return () => {
			if (recordingIntervalRef.current) {
				clearInterval(recordingIntervalRef.current);
			}
			if (streamRef.current) {
				streamRef.current.getTracks().forEach(track => track.stop());
			}
			window.removeEventListener('keydown', handleKeyPress);
		};
	}, []);

	return (
		<div>
			<Header />
			<div className="interview-container">
				{!results ? (
					<>
						{status === 'recording' && (
							<div className="video-container">
								<video 
									ref={videoRef} 
									autoPlay 
									playsInline 
									muted
									className="video-preview"
								/>
								<canvas 
									ref={canvasRef} 
									style={{ display: 'none' }}
								/>
							</div>
						)}

						<div className="controls">
							{status === 'ready' && (
								<div className="button-group">
									<button 
										className="start-btn"
										onClick={startInterview}
									>
										Begin Recording
									</button>
									<button 
										className="back-btn"
										onClick={() => navigate('/score-homepage')}
									>
										Back to Home
									</button>
								</div>
							)}

							{status === 'recording' && (
								<div className="recording-status">
									<div className="recording-indicator"></div>
									<span>Recording... Press ESC to stop</span>
									<button 
										className="stop-btn"
										onClick={stopInterview}
									>
										Stop Recording
									</button>
								</div>
							)}

							{status === 'processing' && (
								<div className="processing-status">
									<div className="spinner"></div>
									<p>Processing your interview...</p>
								</div>
							)}

							{error && (
								<div className="error-message">
									{error}
								</div>
							)}
						</div>
					</>
				) : (
					<div className="results-content">
						<h1>Interview Results</h1>
						<div className="score-grid">
							<div className="score-item">
								<span className="score-label">Overall Score</span>
								<span className="score-value">{results.overall_score}%</span>
							</div>
							<div className="score-item">
								<span className="score-label">Posture</span>
								<span className="score-value">{results.posture_score}%</span>
							</div>
							<div className="score-item">
								<span className="score-label">Eye Contact</span>
								<span className="score-value">{results.eye_contact_score}%</span>
							</div>
							<div className="score-item">
								<span className="score-label">Smile</span>
								<span className="score-value">{results.smile_percentage}%</span>
							</div>
						</div>
						<div className="action-buttons">
							<button 
								className="practice-btn"
								onClick={() => {
									setResults(null);
									setStatus('ready');
								}}
							>
								Practice Again
							</button>
							<button 
								className="home-btn"
								onClick={() => navigate('/score-homepage')}
							>
								Back to Home
							</button>
						</div>
					</div>
				)}
			</div>
		</div>
	);
}

export default Interview;