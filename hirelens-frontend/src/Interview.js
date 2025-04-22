import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from './Header';
import './FrontPage.css';

function Interview() {
	const navigate = useNavigate();
	const [status, setStatus] = useState('initializing'); // initializing, ready, recording, processing
	const [error, setError] = useState(null);
	const [results, setResults] = useState(null);
	const [frameCount, setFrameCount] = useState(0);
	const [questions, setQuestions] = useState([]);
	const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
	const [currentAttempt, setCurrentAttempt] = useState(1); // Track current attempt (1-3)
	const [questionResults, setQuestionResults] = useState({}); // Store results for each question
	const [isLoadingQuestions, setIsLoadingQuestions] = useState(false);
	
	const videoRef = useRef(null);
	const canvasRef = useRef(null);
	const streamRef = useRef(null);
	const sessionIdRef = useRef(null);
	const recordingIntervalRef = useRef(null);

	// Initialize camera when component mounts
	useEffect(() => {
		initializeCamera();
		fetchQuestions();
		
		// Cleanup on component unmount
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

	// Fetch random questions
	const fetchQuestions = async () => {
		try {
			setIsLoadingQuestions(true);
			const response = await fetch('http://localhost:5000/api/interview/questions?count=3', {
				method: 'GET',
				headers: {
					'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
				}
			});
			
			if (!response.ok) {
				throw new Error('Failed to fetch questions');
			}
			
			const data = await response.json();
			setQuestions(data.questions);
			setCurrentQuestionIndex(0);
			setCurrentAttempt(1);
			
			// Initialize results for each question
			const initialResults = {};
			data.questions.forEach(question => {
				initialResults[question] = {
					attempts: [],
					bestAttempt: null
				};
			});
			setQuestionResults(initialResults);
			
			setIsLoadingQuestions(false);
		} catch (err) {
			console.error('Error fetching questions:', err);
			setError('Failed to load interview questions. Please try again.');
			setIsLoadingQuestions(false);
		}
	};

	// Initialize camera
	const initializeCamera = async () => {
		try {
			setStatus('initializing');
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
			setStatus('ready');
		} catch (err) {
			setError('Failed to access camera. Please ensure camera permissions are granted.');
			console.error('Camera error:', err);
			setStatus('ready'); // Still set to ready so user can try again
		}
	};

	// Start interview session
	const startInterview = async () => {
		try {
			setStatus('recording');
			setError(null);
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
				body: JSON.stringify({ 
					session_id: sessionId,
					question: questions[currentQuestionIndex]
				})
			});

			if (!response.ok) {
				throw new Error('Failed to start interview session');
			}

			// Start recording frames
			recordingIntervalRef.current = setInterval(recordFrame, 1000/10); // 10 FPS

		} catch (err) {
			setError('Failed to start interview');
			console.error('Start interview error:', err);
			stopRecording();
		}
	};

	// Try again for the current question
	const tryAgain = () => {
		if (currentAttempt < 3) {
			setCurrentAttempt(currentAttempt + 1);
			startInterview();
		} else {
			// Move to next question if we've used all attempts
			nextQuestion();
		}
	};

	// Move to next question
	const nextQuestion = () => {
		if (currentQuestionIndex < questions.length - 1) {
			setCurrentQuestionIndex(currentQuestionIndex + 1);
			setCurrentAttempt(1);
			startInterview();
		} else {
			// All questions answered, end interview
			completeInterview();
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
					frame: frameData,
					question: questions[currentQuestionIndex]
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

	// Stop recording for current attempt
	const stopRecording = async () => {
		try {
			// Clear recording interval
			if (recordingIntervalRef.current) {
				clearInterval(recordingIntervalRef.current);
				recordingIntervalRef.current = null;
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
				console.log('Attempt results:', data);
				
				// Store results for this attempt
				const currentQuestion = questions[currentQuestionIndex];
				const attemptResults = {
					posture_score: data.final_scores?.posture_score || 0,
					eye_contact_score: data.final_scores?.eye_contact_score || 0,
					smile_percentage: data.final_scores?.smile_percentage || 0,
					answer_quality_score: data.final_scores?.answer_quality_score || 0,
					overall_sentiment: data.final_scores?.overall_sentiment || 0,
					overall_score: data.final_scores?.overall_score || 0,
					attempt: currentAttempt
				};
				
				// Update question results
				setQuestionResults(prev => {
					const questionData = prev[currentQuestion] || { attempts: [], bestAttempt: null };
					const attempts = [...questionData.attempts, attemptResults];
					
					// Determine best attempt based on overall score
					const bestAttempt = attempts.reduce((best, current) => 
						(best === null || current.overall_score > best.overall_score) ? current : best, null);
					
					return {
						...prev,
						[currentQuestion]: {
							attempts,
							bestAttempt
						}
					};
				});
				
				// Set status after recording stops
				setStatus('attempt_completed');
				sessionIdRef.current = null;
			}
		} catch (err) {
			setError('Failed to stop recording');
			console.error('Stop recording error:', err);
			setStatus('ready');
		}
	};

	// Complete the entire interview
	const completeInterview = async () => {
		try {
			setStatus('processing');

			// Stop camera
			if (streamRef.current) {
				streamRef.current.getTracks().forEach(track => track.stop());
				streamRef.current = null;
			}
			
			// Calculate final scores based on best attempts
			if (Object.keys(questionResults).length === 0) {
				throw new Error('No results recorded');
			}
			
			const bestScores = Object.values(questionResults).map(q => q.bestAttempt || {
				overall_score: 0,
				posture_score: 0,
				eye_contact_score: 0,
				smile_percentage: 0,
				answer_quality_score: 0,
				overall_sentiment: 0
			});
			
			// Average scores across all questions
			const finalResults = {
				overall_score: bestScores.reduce((sum, score) => sum + score.overall_score, 0) / bestScores.length,
				posture_score: bestScores.reduce((sum, score) => sum + score.posture_score, 0) / bestScores.length,
				eye_contact_score: bestScores.reduce((sum, score) => sum + score.eye_contact_score, 0) / bestScores.length,
				smile_percentage: bestScores.reduce((sum, score) => sum + score.smile_percentage, 0) / bestScores.length,
				answer_quality_score: bestScores.reduce((sum, score) => sum + score.answer_quality_score, 0) / bestScores.length,
				overall_sentiment: bestScores.reduce((sum, score) => sum + score.overall_sentiment, 0) / bestScores.length
			};
			
			setResults(finalResults);
		} catch (err) {
			setError('Failed to complete interview');
			console.error('Complete interview error:', err);
			setStatus('ready');
		}
	};

	// Handle ESC key press
	const handleKeyPress = (event) => {
		if (event.key === 'Escape' && status === 'recording') {
			stopRecording();
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

	return (
		<div>
			<Header />
			<div className="interview-container">
				{!results ? (
					<>
						{(status === 'initializing' || status === 'ready' || status === 'recording' || status === 'attempt_completed') && (
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
								{status === 'initializing' && (
									<div className="initializing-overlay">
										<div className="spinner"></div>
									</div>
								)}
							</div>
						)}

						{questions.length > 0 && (
							<div className="question-display">
								<h2>Question {currentQuestionIndex + 1} of {questions.length} (Attempt {currentAttempt} of 3)</h2>
								<p>{questions[currentQuestionIndex]}</p>
							</div>
						)}

						<div className="controls">
							{status === 'ready' && (
								<div className="button-group">
									{isLoadingQuestions ? (
										<div className="loading-questions">
											<div className="spinner"></div>
											<p>Loading questions...</p>
										</div>
									) : questions.length > 0 ? (
										<>
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
										</>
									) : (
										<>
											<div className="error-message">
												Failed to load interview questions.
											</div>
											<button 
												className="retry-btn"
												onClick={fetchQuestions}
											>
												Retry
											</button>
											<button 
												className="back-btn"
												onClick={() => navigate('/score-homepage')}
											>
												Back to Home
											</button>
										</>
									)}
								</div>
							)}

							{status === 'recording' && (
								<div className="recording-status">
									<div className="recording-indicator"></div>
									<span>Recording... Press ESC to stop</span>
									<button 
										className="stop-btn"
										onClick={stopRecording}
									>
										Stop Recording
									</button>
								</div>
							)}
							
							{status === 'attempt_completed' && (
								<div className="attempt-completed">
									<h3>Attempt {currentAttempt} of 3 completed</h3>
									{currentAttempt < 3 ? (
										<div className="attempt-buttons">
											<button 
												className="try-again-btn"
												onClick={tryAgain}
											>
												Try Again
											</button>
											<button 
												className="next-btn"
												onClick={nextQuestion}
											>
												Next Question
											</button>
										</div>
									) : (
										<button 
											className="next-btn"
											onClick={nextQuestion}
										>
											Next Question
										</button>
									)}
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
								<span className="score-value">{results.overall_score.toFixed(1)}%</span>
							</div>
							<div className="score-item">
								<span className="score-label">Posture</span>
								<span className="score-value">{results.posture_score.toFixed(1)}%</span>
							</div>
							<div className="score-item">
								<span className="score-label">Eye Contact</span>
								<span className="score-value">{results.eye_contact_score.toFixed(1)}%</span>
							</div>
							<div className="score-item">
								<span className="score-label">Smile</span>
								<span className="score-value">{results.smile_percentage.toFixed(1)}%</span>
							</div>
							<div className="score-item">
								<span className="score-label">Answer Quality</span>
								<span className="score-value">{results.answer_quality_score.toFixed(1)}%</span>
							</div>
							<div className="score-item">
								<span className="score-label">Overall Sentiment</span>
								<span className="score-value">{results.overall_sentiment.toFixed(1)}%</span>
							</div>
						</div>
						
						<div className="question-results">
							<h2>Question Breakdown</h2>
							{questions.map((question, index) => {
								const questionData = questionResults[question] || { bestAttempt: null };
								const bestAttempt = questionData.bestAttempt;
								
								return (
									<div key={index} className="question-result-item">
										<h3>Question {index + 1}: {question}</h3>
										{bestAttempt ? (
											<div className="best-attempt">
												<p>Best Score: {bestAttempt.overall_score.toFixed(1)}% (Attempt {bestAttempt.attempt})</p>
											</div>
										) : (
											<p className="no-data">No data recorded</p>
										)}
									</div>
								);
							})}
						</div>
						
						<div className="action-buttons">
							<button 
								className="practice-btn"
								onClick={() => {
									setResults(null);
									setStatus('ready');
									initializeCamera();
									fetchQuestions();
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