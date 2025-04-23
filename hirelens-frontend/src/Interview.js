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
	const [isProcessingAnswer, setIsProcessingAnswer] = useState(false); // Processing state
	const [currentTranscript, setCurrentTranscript] = useState(''); // Store the current transcript
	const [timeRemaining, setTimeRemaining] = useState(90); // 90 seconds timer
	const [microphonePermission, setMicrophonePermission] = useState(false); // Track microphone permission status
	
	const videoRef = useRef(null);
	const canvasRef = useRef(null);
	const streamRef = useRef(null);
	const audioStreamRef = useRef(null); // For audio stream
	const mediaRecorderRef = useRef(null); // For MediaRecorder instance
	const audioChunksRef = useRef([]); // To store audio chunks
	const sessionIdRef = useRef(null);
	const recordingIntervalRef = useRef(null);
	const audioRecordingRef = useRef(false); // Track if audio recording is active
	const timerIntervalRef = useRef(null); // Track timer interval

	// Sets up camera, mic, and questions when component loads
	useEffect(() => {
		initializeCamera();
		requestMicrophonePermission(); // Request microphone permission
		fetchQuestions();
		
		// Cleanup on component unmount
		return () => {
			if (recordingIntervalRef.current) {
				clearInterval(recordingIntervalRef.current);
			}
			if (timerIntervalRef.current) {
				clearInterval(timerIntervalRef.current);
			}
			if (streamRef.current) {
				streamRef.current.getTracks().forEach(track => track.stop());
			}
			if (audioStreamRef.current) {
				audioStreamRef.current.getTracks().forEach(track => track.stop());
			}
			window.removeEventListener('keydown', handleKeyPress);
		};
	}, []);

	// Requests microphone access from the browser
	const requestMicrophonePermission = async () => {
		try {
			const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
			audioStreamRef.current = audioStream;
			setMicrophonePermission(true);
			console.log('Microphone permission granted');
			
			// Stop the stream for now, we'll start it again when recording begins
			audioStream.getTracks().forEach(track => track.stop());
		} catch (err) {
			console.error('Microphone permission denied:', err);
			setError('Microphone permission denied. Please grant permission to use the microphone.');
			setMicrophonePermission(false);
		}
	};

	// Initializes and starts audio recording
	const startAudioRecording = async () => {
		try {
			// Get audio stream
			const audioStream = await navigator.mediaDevices.getUserMedia({ 
				audio: {
					echoCancellation: true,
					noiseSuppression: true,
					autoGainControl: true
				} 
			});
			audioStreamRef.current = audioStream;
			
			// Initialize MediaRecorder with WAV codec using PCM format
			// This creates files that are easier to process without conversion
			const options = { 
				mimeType: 'audio/wav' 
			};
			
			// Check if WAV recording is supported, fallback to WebM
			if (!MediaRecorder.isTypeSupported('audio/wav')) {
				console.log("WAV recording not supported, using WebM as fallback");
				options.mimeType = 'audio/webm;codecs=opus';
			} else {
				console.log("Using WAV recording format");
			}
			
			const mediaRecorder = new MediaRecorder(audioStream, options);
			mediaRecorderRef.current = mediaRecorder;
			
			// Clear previous audio chunks
			audioChunksRef.current = [];
			
			// Handle dataavailable event
			mediaRecorder.ondataavailable = (event) => {
				if (event.data.size > 0) {
					audioChunksRef.current.push(event.data);
					console.log(`Audio chunk captured, size: ${event.data.size} bytes, type: ${event.data.type}`);
				}
			};
			
			// Start recording
			mediaRecorder.start(3000); // Collect data every 3 seconds
			console.log('MediaRecorder started with format:', mediaRecorder.mimeType);
			
			audioRecordingRef.current = true;
		} catch (err) {
			console.error('Error starting audio recording:', err);
			setError('Failed to start audio recording. Please ensure microphone permissions are granted.');
		}
	};

	// Stops audio recording and sends data to backend for transcription
	const stopAudioRecording = async () => {
		return new Promise((resolve, reject) => {
			try {
				if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') {
					console.warn('MediaRecorder not active, nothing to stop');
					resolve(null);
					return;
				}
				
				// Define event for when recording stops
				mediaRecorderRef.current.onstop = async () => {
					try {
						const audioBlob = new Blob(audioChunksRef.current, { type: mediaRecorderRef.current.mimeType });
						console.log(`Audio recording completed, size: ${audioBlob.size} bytes, type: ${mediaRecorderRef.current.mimeType}`);
						
						// Stop all audio tracks
						if (audioStreamRef.current) {
							audioStreamRef.current.getTracks().forEach(track => track.stop());
						}
						
						// Process audio using backend transcription
						if (audioBlob.size > 0) {
							console.log("Sending audio to backend for processing...");
							setIsProcessingAnswer(true);
							setCurrentTranscript("Processing your answer...");
							
							try {
								// Convert blob to base64
								const reader = new FileReader();
								reader.readAsDataURL(audioBlob);
								
								// Wait for file reading to complete
								const base64Audio = await new Promise((resolve) => {
									reader.onloadend = () => resolve(reader.result);
								});
								
								// Send to backend process-audio endpoint with retry capability
								let retryCount = 0;
								const maxRetries = 2;
								let audioResponse = null;
								let audioData = null;

								while (retryCount <= maxRetries) {
									try {
										console.log(`Sending audio to backend (attempt ${retryCount + 1}/${maxRetries + 1}), size: ${audioBlob.size} bytes`);
										
										// Update UI during retry
										if (retryCount > 0) {
											setCurrentTranscript(`Processing your answer... (retry ${retryCount}/${maxRetries})`);
										}
										
										// Make request to backend
										audioResponse = await fetch('http://localhost:5000/api/interview/process-audio', {
											method: 'POST',
											headers: {
												'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
												'Content-Type': 'application/json'
											},
											body: JSON.stringify({
												session_id: sessionIdRef.current,
												audio_data: base64Audio,
												question: questions[currentQuestionIndex]
											})
										});
										
										if (audioResponse.ok) {
											audioData = await audioResponse.json();
											if (audioData && audioData.transcription) {
												break; // Successful response, exit retry loop
											}
										}
										
										// If we get here, response wasn't successful. Wait before retrying.
										retryCount++;
										if (retryCount <= maxRetries) {
											await new Promise(r => setTimeout(r, 1000 * retryCount)); // Exponential backoff
										}
									} catch (fetchError) {
										console.error(`Fetch error on attempt ${retryCount + 1}:`, fetchError);
										retryCount++;
										if (retryCount <= maxRetries) {
											await new Promise(r => setTimeout(r, 1000 * retryCount));
										}
									}
								}
								
								// Check final results after all retry attempts
								if (!audioResponse || !audioResponse.ok || !audioData) {
									throw new Error("Failed to process audio after multiple attempts");
								}
								
								// Process the transcription result
								const backendTranscript = audioData.transcription || '';
								console.log('Backend transcription result:', backendTranscript);
								
								// Define transcription variable before using it
								let transcription;
								
								// If the backend returns a message in brackets, it's likely an error or status message
								if (backendTranscript.startsWith('[') && 
									(backendTranscript.includes('Error') || 
									backendTranscript.includes('No speech') ||
									backendTranscript.includes('too quiet') ||
									backendTranscript.includes('too small') ||
									backendTranscript.includes('too short'))) {
									
									// Show user-friendly version of the error
									if (backendTranscript.includes('too quiet')) {
										setCurrentTranscript("Your audio was too quiet. Please speak louder or move closer to the microphone.");
									} else if (backendTranscript.includes('No speech')) {
										setCurrentTranscript("No speech was detected. Please speak clearly into your microphone.");
									} else if (backendTranscript.includes('too short') || backendTranscript.includes('too small')) {
										setCurrentTranscript("The recording was too short. Please speak for a longer period.");
									} else {
										setCurrentTranscript("Speech transcription failed. Please try again and speak clearly.");
									}
									
									// Use the backend message as the transcript for processing
									transcription = backendTranscript;
								} else {
									// We got a valid transcription
									transcription = backendTranscript;
									setCurrentTranscript(transcription);
								}
								
								// Only try to analyze if we have a real transcription
								if (transcription && 
									!transcription.startsWith('[') && 
									transcription.trim().length > 0) {
									
									try {
										// Simple check if server is still responding
										const pingResponse = await fetch('http://localhost:5000', { 
											method: 'GET' 
										}).catch(() => null);
										
										if (pingResponse && pingResponse.ok) {
											// Server is responding, try to analyze
											const analysisResponse = await fetch('http://localhost:5000/api/interview/analyze-transcript', {
												method: 'POST',
												headers: {
													'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
													'Content-Type': 'application/json'
												},
												body: JSON.stringify({
													session_id: sessionIdRef.current,
													transcript: transcription,
													question: questions[currentQuestionIndex]
												})
											});
											
											if (analysisResponse.ok) {
												const analysisResult = await analysisResponse.json();
												console.log("Analysis result:", analysisResult);
												
												// Check if we have a positive reformulation to show
												if (analysisResult.positive_reformulation && analysisResult.sentiment === 'negative') {
													console.log("Positive reformulation available");
												}
											} else {
												console.error("Error analyzing transcript:", await analysisResponse.text());
											}
										} else {
											console.log("Server not responding for analysis, skipping analyze-transcript call");
										}
									} catch (analysisError) {
										console.error("Network error when analyzing transcript:", analysisError);
									}
								}
							} catch (backendError) {
								console.error("Error with backend transcription:", backendError);
								setCurrentTranscript("Error processing audio. Please try again.");
							} finally {
								// Ensure processing state is cleared
								setIsProcessingAnswer(false);
							}
						} else {
							console.warn("Audio blob is empty, skipping transcription");
							setCurrentTranscript("No audio recorded. Please try again.");
							setIsProcessingAnswer(false);
						}
						
						resolve(audioBlob);
					} catch (error) {
						console.error("Error in onstop handler:", error);
						setCurrentTranscript("Error processing recording. Please try again.");
						setIsProcessingAnswer(false);
						reject(error);
					}
				};
				
				// Stop the recorder
				mediaRecorderRef.current.stop();
				console.log('MediaRecorder stopped');
				
			} catch (err) {
				console.error('Error stopping audio recording:', err);
				setIsProcessingAnswer(false);
				reject(err);
			}
		});
	};

	// Starts the interview timer countdown
	const startTimer = () => {
		// Reset timer to 90 seconds
		setTimeRemaining(90);
		
		// Clear any existing timer
		if (timerIntervalRef.current) {
			clearInterval(timerIntervalRef.current);
		}
		
		// Start a new timer
		timerIntervalRef.current = setInterval(() => {
			setTimeRemaining(prevTime => {
				if (prevTime <= 1) {
					// Stop timer and recording when time is up
					clearInterval(timerIntervalRef.current);
					stopRecording();
					return 0;
				}
				return prevTime - 1;
			});
		}, 1000);
	};
	
	// Stops the interview timer
	const stopTimer = () => {
		if (timerIntervalRef.current) {
			clearInterval(timerIntervalRef.current);
			timerIntervalRef.current = null;
		}
	};
	
	// Calculates the timer progress percentage for UI display
	const getTimerProgress = () => {
		return (timeRemaining / 90) * 100;
	};
	
	// Returns appropriate color for timer based on time left
	const getTimerColor = () => {
		if (timeRemaining <= 10) return '#dc3545'; // Red when 10 seconds or less
		if (timeRemaining <= 30) return '#ffc107'; // Yellow when 30 seconds or less
		return '#0d6efd'; // Default blue
	};
	
	// Renders the transcript with appropriate styling based on state
	const renderTranscript = () => {
		if (isProcessingAnswer) {
			return (
				<div className="transcription-box processing">
					<div className="processing-indicator">
						<div className="spinner"></div>
					</div>
					<p>{currentTranscript || "Processing your answer..."}</p>
				</div>
			);
		}
		
		// Check if the transcript contains an error message (starts with '[')
		if (currentTranscript && currentTranscript.startsWith('[')) {
			return (
				<div className="transcription-box error">
					<div className="error-icon">⚠️</div>
					<p>{currentTranscript.replace(/^\[|\]$/g, '')}</p>
				</div>
			);
		}
		
		// Regular transcript
		return currentTranscript ? (
			<div className="transcription-box">
				<strong>Your answer:</strong> {currentTranscript}
			</div>
		) : null;
	};
	
	// Converts sentiment score to user-friendly display text and icon
	const getSentimentDisplay = (sentimentScore) => {
		// 0 is negative, 100 is positive based on our backend logic
		const isPositive = sentimentScore >= 50;
		
		return {
			text: isPositive ? "Positive" : "Negative",
			className: isPositive ? "positive-sentiment" : "negative-sentiment",
			icon: isPositive ? "✓" : "✗"
		};
	};
	
	// Fetches interview questions from the backend
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

	// Initializes the camera for video capture
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

	// Starts a new interview session
	const startInterview = async () => {
		try {
			setStatus('recording');
			setError(null);
			setFrameCount(0);
			setCurrentTranscript(''); // Clear current transcript

			// Start camera if not already running
			if (!streamRef.current) {
				await initializeCamera();
			}

			// Create new session
			const sessionId = `session_${Date.now()}`;
			sessionIdRef.current = sessionId;

			// Start session with current question
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
			
			// Start audio recording
			await startAudioRecording();
			
			// Start the timer
			startTimer();

		} catch (err) {
			setError('Failed to start interview');
			console.error('Start interview error:', err);
			stopRecording();
		}
	};

	// Allows user to try answering the current question again
	const tryAgain = () => {
		if (currentAttempt < 3) {
			setCurrentAttempt(currentAttempt + 1);
			startInterview();
		} else {
			// Move to next question if we've used all attempts
			nextQuestion();
		}
	};

	// Moves to the next question or completes interview
	const nextQuestion = () => {
		if (currentQuestionIndex < questions.length - 1) {
			setCurrentQuestionIndex(currentQuestionIndex + 1);
			setCurrentAttempt(1);
			setStatus('ready');
		} else {
			// All questions answered, end interview
			completeInterview();
		}
	};

	// Captures and sends a video frame to the backend
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
			setFrameCount(prevCount => prevCount + 1);

		} catch (err) {
			console.error('Frame recording error:', err);
		}
	};

	// Stops recording and processes current question attempt results
	const stopRecording = async () => {
		try {
			// Stop the timer
			stopTimer();
			
			// Set processing state first
			setIsProcessingAnswer(true);
			
			// Clear recording interval
			if (recordingIntervalRef.current) {
				clearInterval(recordingIntervalRef.current);
				recordingIntervalRef.current = null;
			}

			// Stop interview on backend
			if (sessionIdRef.current) {
				let transcriptResult = '';
				
				// Stop audio recording if it was started
				if (audioRecordingRef.current) {
					try {
						// Stop local MediaRecorder
						const audioBlob = await stopAudioRecording();
						
						if (audioBlob && audioBlob.size > 0) {
							console.log(`Audio recorded successfully: ${audioBlob.size} bytes, type: ${audioBlob.type}`);
							
							// The transcript is already set by the stopAudioRecording function
							transcriptResult = currentTranscript;
							
							// Add a small delay to ensure the transcript is processed
							await new Promise(resolve => setTimeout(resolve, 1000));
						}
						
						// Now just update the flag
						audioRecordingRef.current = false;
					} catch (audioErr) {
						console.error('Error stopping audio recording:', audioErr);
					}
				}
				
				let backendSuccess = false;
				
				// Try to send data to backend
				try {
					// Try to connect to backend with a simple OPTIONS request
					const pingSuccess = await fetch('http://localhost:5000/api/test-connection', { 
						method: 'GET'
					})
					.then(res => res.ok)
					.catch(() => false);
					
					if (pingSuccess) {
						// If backend is available, send stop command
						const response = await fetch('http://localhost:5000/api/interview/stop', {
							method: 'POST',
							headers: {
								'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
								'Content-Type': 'application/json'
							},
							body: JSON.stringify({ 
								session_id: sessionIdRef.current,
								transcript: transcriptResult
							})
						});
		
						if (response.ok) {
							backendSuccess = true;
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
								attempt: currentAttempt,
								transcript: transcriptResult,
								answer_analysis: {
									...data.answer_analysis,
									analysis: data.answer_analysis?.analysis || {},
									positive_reformulation: data.answer_analysis?.positive_reformulation || null
								}
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
						} else {
							throw new Error('Failed to stop interview, backend returned error');
						}
					} else {
						throw new Error('Backend server not responding');
					}
				} catch (fetchError) {
					console.error('Backend communication error:', fetchError);
					
					if (!backendSuccess) {
						// Create fallback results using only local data
						const currentQuestion = questions[currentQuestionIndex];
						const fallbackResults = {
							posture_score: 50, // Default fallback values
							eye_contact_score: 50,
							smile_percentage: 50,
							answer_quality_score: 50,
							overall_sentiment: 50,
							overall_score: 50,
							attempt: currentAttempt,
							transcript: transcriptResult,
							answer_analysis: {
								feedback: "Your answer was recorded successfully, but we couldn't analyze it due to server issues."
							}
						};
						
						// Show an error message but don't make it seem too serious
						setError('Analysis is unavailable due to length of your answer, but your answer was recorded successfully. Please try to answer the question more thoroughly');
						
						// Update question results with fallback data
						setQuestionResults(prev => {
							const questionData = prev[currentQuestion] || { attempts: [], bestAttempt: null };
							const attempts = [...questionData.attempts, fallbackResults];
							
							return {
								...prev,
								[currentQuestion]: {
									attempts,
									bestAttempt: attempts[0] // Set first attempt as best since we have no scores
								}
							};
						});
					}
				}
				
				// Set status after recording stops
				setIsProcessingAnswer(false);
				setStatus('attempt_completed');
				sessionIdRef.current = null;
			}
		} catch (err) {
			setIsProcessingAnswer(false);
			setError('Failed to stop recording: ' + err.message);
			console.error('Stop recording error:', err);
			setStatus('ready');
		}
	};

	// Finalizes interview and calculates overall results
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

	// Handles ESC key press to stop recording
	const handleKeyPress = (event) => {
		if (event.key === 'Escape' && status === 'recording') {
			stopRecording();
		}
	};

	return (
		<div>
			<Header />
			<div className="interview-container">
				{!results ? (
					<>
						{questions.length > 0 && (
							<div className="question-display">
								<h2>Question {currentQuestionIndex + 1} of {questions.length} (Attempt {currentAttempt} of 3)</h2>
								<p>{questions[currentQuestionIndex]}</p>
							</div>
						)}
						<div className="timer-container">
									<div className="timer-label">Time remaining: {timeRemaining}s</div>
									<div className="timer-bar-container">
										<div 
											className="timer-bar" 
											style={{ 
												width: `${getTimerProgress()}%`,
												backgroundColor: getTimerColor(),
												boxShadow: `0 0 5px ${getTimerColor()}`
											}}
										></div>
							</div>
						</div>
						
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
								{isProcessingAnswer && (
									<div className="processing-overlay">
										<div className="spinner"></div>
										<p>Please wait while we process your answer...</p>
									</div>
								)}
							</div>
						)}
						
						{/* Display microphone permission status */}
						{status === 'ready' && (
							<div className={`mic-status ${microphonePermission ? 'granted' : 'denied'}`}>
								<i></i>
								{microphonePermission 
									? 'Microphone access granted' 
									: 'Microphone access denied. Please grant microphone permission.'}
							</div>
						)}
						
						{status === 'recording' && (
							<>
								<div className="recording-instructions">
									<h3>Recording in progress</h3>
									<p>Speak clearly into your microphone. Click "Stop Recording" when you're done.</p>
								</div>
							</>
						)}
						
						{/* Always display transcription when available */}
						{(status === 'recording' || status === 'attempt_completed' || isProcessingAnswer) && renderTranscript()}

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
							{/* <div className="score-item">
								<span className="score-label">Answer Quality</span>
								<span className="score-value">{results.answer_quality_score.toFixed(1)}%</span>
							</div> */}
							<div className="score-item">
								<span className="score-label">Overall Sentiment</span>
								<span className={`score-value ${getSentimentDisplay(results.overall_sentiment).className}`}>
									{getSentimentDisplay(results.overall_sentiment).icon} {getSentimentDisplay(results.overall_sentiment).text}
								</span>
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
												{/* Show transcript */}
												<div className="transcript-section">
													<h4>Your Answer:</h4>
													<p className="transcript">{bestAttempt.transcript}</p>
												</div>
												
												{/* Show positive reformulation if available */}
												{bestAttempt.answer_analysis && bestAttempt.answer_analysis.positive_reformulation && (
													<div className="reformulation-section">
														<h4>Improved Version:</h4>
														<p className="reformulation">{bestAttempt.answer_analysis.positive_reformulation}</p>
													</div>
												)}
												
												{bestAttempt.answer_analysis && bestAttempt.answer_analysis.analysis && (
													<div className="feedback-section">
														<h4>Analysis:</h4>
														<div className="feedback-item strengths-weaknesses">
															<h5>Strengths & Areas for Improvement</h5>
															<div className="two-column-feedback">
																<div className="feedback-column">
																	<h6>Strengths:</h6>
																	<ul>
																		{bestAttempt.answer_analysis.analysis.strengths?.map((strengths, i) => (
																			<li key={i}>{strengths}</li>
																		))}
																	</ul>
																</div>
																<div className="feedback-column">
																	<h6>Areas to Improve:</h6>
																	<ul>
																		{bestAttempt.answer_analysis.analysis.improvements?.map((improvement, i) => (
																			<li key={i}>{improvement}</li>
																		))}
																	</ul>
																</div>
															</div>
														</div>
														
														{/* Show competencies if available */}
														{bestAttempt.answer_analysis.analysis.competencies && bestAttempt.answer_analysis.analysis.competencies.length > 0 && (
															<div className="feedback-item">
																<h5>Key Competencies Demonstrated:</h5>
																<ul>
																	{bestAttempt.answer_analysis.analysis.competencies.map((competency, i) => (
																		<li key={i}>{competency}</li>
																	))}
																</ul>
															</div>
														)}
														
														{/* Show weaknesses section */}
														<div className="feedback-item weaknesses-section">
															<h5>Weaknesses:</h5>
															<ul>
																{bestAttempt.answer_analysis.analysis.weaknesses?.map((weakness, i) => (
																	<li key={i}>{weakness}</li>
																)) || bestAttempt.answer_analysis.analysis.improvements?.map((improvement, i) => (
																	<li key={i}>{improvement}</li>
																)) || <li>No specific weaknesses identified</li>}
															</ul>
														</div>
														
														{/* Show score if available */}
														<div className="feedback-item">
															<h5>Answer Quality Score:</h5>
															<p className="score-value">{bestAttempt.answer_analysis.analysis.score}/100</p>
														</div>
														
														{/* Show suggestions as Feedback */}
														{bestAttempt.answer_analysis.analysis.suggestions && bestAttempt.answer_analysis.analysis.suggestions.length > 0 && (
															<div className="feedback-item">
																<h5>Specific Suggestions:</h5>
																<ul>
																	{bestAttempt.answer_analysis.analysis.suggestions.map((suggestion, i) => (
																		<li key={i}>{suggestion}</li>
																	))}
																</ul>
															</div>
														)}
													</div>
												)}
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