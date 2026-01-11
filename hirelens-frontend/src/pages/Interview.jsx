import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import { 
  Play, 
  Square, 
  RotateCcw, 
  ArrowRight, 
  Home,
  Mic,
  MicOff,
  Camera,
  Clock,
  CheckCircle,
  Loader,
  AlertCircle,
  ThumbsUp,
  ThumbsDown,
  Target,
  Eye,
  Smile
} from 'lucide-react';

function Interview() {
  const navigate = useNavigate();
  const [status, setStatus] = useState('initializing');
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);
  // eslint-disable-next-line no-unused-vars
  const [frameCount, setFrameCount] = useState(0);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [currentAttempt, setCurrentAttempt] = useState(1);
  const [questionResults, setQuestionResults] = useState({});
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(false);
  const [isProcessingAnswer, setIsProcessingAnswer] = useState(false);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [timeRemaining, setTimeRemaining] = useState(90);
  const [microphonePermission, setMicrophonePermission] = useState(false);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const audioStreamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const sessionIdRef = useRef(null);
  const recordingIntervalRef = useRef(null);
  const audioRecordingRef = useRef(false);
  const timerIntervalRef = useRef(null);

  useEffect(() => {
    initializeCamera();
    requestMicrophonePermission();
    fetchQuestions();

    return () => {
      if (recordingIntervalRef.current) clearInterval(recordingIntervalRef.current);
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
      if (streamRef.current) streamRef.current.getTracks().forEach(track => track.stop());
      if (audioStreamRef.current) audioStreamRef.current.getTracks().forEach(track => track.stop());
      // Keyboard event listeners are handled in the status-specific useEffect
    };
  }, []);

  const requestMicrophonePermission = async () => {
    try {
      const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStreamRef.current = audioStream;
      setMicrophonePermission(true);
      audioStream.getTracks().forEach(track => track.stop());
    } catch (err) {
      console.error('Microphone permission denied:', err);
      setError('Microphone permission denied. Please grant permission to use the microphone.');
      setMicrophonePermission(false);
    }
  };

  const startAudioRecording = async () => {
    try {
      const audioStream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }
      });
      audioStreamRef.current = audioStream;

      const options = { mimeType: 'audio/webm;codecs=opus' };
      const mediaRecorder = new MediaRecorder(audioStream, options);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      mediaRecorder.start(3000);
      audioRecordingRef.current = true;
    } catch (err) {
      console.error('Error starting audio recording:', err);
      setError('Failed to start audio recording.');
    }
  };

  const stopAudioRecording = async () => {
    return new Promise((resolve, reject) => {
      try {
        if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') {
          resolve(null);
          return;
        }

        mediaRecorderRef.current.onstop = async () => {
          try {
            const audioBlob = new Blob(audioChunksRef.current, { type: mediaRecorderRef.current.mimeType });
            if (audioStreamRef.current) {
              audioStreamRef.current.getTracks().forEach(track => track.stop());
            }

            if (audioBlob.size > 0) {
              setIsProcessingAnswer(true);
              setCurrentTranscript("Processing your answer...");

              try {
                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                const base64Audio = await new Promise((resolve) => {
                  reader.onloadend = () => resolve(reader.result);
                });

                const audioResponse = await fetch('http://localhost:5000/api/interview/process-audio', {
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
                  const audioData = await audioResponse.json();
                  const transcription = audioData.transcription || '';
                  setCurrentTranscript(transcription);
                }
              } catch (backendError) {
                console.error("Error with backend transcription:", backendError);
                setCurrentTranscript("Error processing audio. Please try again.");
              } finally {
                setIsProcessingAnswer(false);
              }
            }
            resolve(audioBlob);
          } catch (error) {
            setIsProcessingAnswer(false);
            reject(error);
          }
        };

        mediaRecorderRef.current.stop();
      } catch (err) {
        setIsProcessingAnswer(false);
        reject(err);
      }
    });
  };

  const startTimer = () => {
    setTimeRemaining(90);
    if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);

    timerIntervalRef.current = setInterval(() => {
      setTimeRemaining(prevTime => {
        if (prevTime <= 1) {
          clearInterval(timerIntervalRef.current);
          stopRecording();
          return 0;
        }
        return prevTime - 1;
      });
    }, 1000);
  };

  const stopTimer = () => {
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
  };

  const getTimerProgress = () => (timeRemaining / 90) * 100;
  
  const getTimerColor = () => {
    if (timeRemaining <= 10) return 'var(--color-error)';
    if (timeRemaining <= 30) return 'var(--color-warning)';
    return 'var(--color-primary)';
  };

  const fetchQuestions = async () => {
    try {
      setIsLoadingQuestions(true);
      const response = await fetch('http://localhost:5000/api/interview/questions?count=3', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('jwt_token')}` }
      });

      if (!response.ok) throw new Error('Failed to fetch questions');

      const data = await response.json();
      setQuestions(data.questions);
      setCurrentQuestionIndex(0);
      setCurrentAttempt(1);

      const initialResults = {};
      data.questions.forEach(question => {
        initialResults[question] = { attempts: [], bestAttempt: null };
      });
      setQuestionResults(initialResults);
      setIsLoadingQuestions(false);
    } catch (err) {
      console.error('Error fetching questions:', err);
      setError('Failed to load interview questions. Please try again.');
      setIsLoadingQuestions(false);
    }
  };

  const initializeCamera = async () => {
    try {
      setStatus('initializing');
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' }
      });
      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
      setStatus('ready');
    } catch (err) {
      setError('Failed to access camera. Please ensure camera permissions are granted.');
      setStatus('ready');
    }
  };

  const startInterview = async () => {
    try {
      setStatus('recording');
      setError(null);
      setFrameCount(0);
      setCurrentTranscript('');

      if (!streamRef.current) await initializeCamera();

      const sessionId = `session_${Date.now()}`;
      sessionIdRef.current = sessionId;

      await fetch('http://localhost:5000/api/interview/start', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ session_id: sessionId, question: questions[currentQuestionIndex] })
      });

      recordingIntervalRef.current = setInterval(recordFrame, 100);
      await startAudioRecording();
      startTimer();
    } catch (err) {
      setError('Failed to start interview');
      stopRecording();
    }
  };

  const recordFrame = async () => {
    try {
      if (!canvasRef.current || !videoRef.current || !sessionIdRef.current) return;

      const canvas = canvasRef.current;
      const video = videoRef.current;
      const context = canvas.getContext('2d');

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      const frameData = canvas.toDataURL('image/jpeg', 0.8);
      if (!frameData || !frameData.startsWith('data:image/jpeg;base64,')) return;

      await fetch('http://localhost:5000/api/interview/record', {
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

      setFrameCount(prev => prev + 1);
    } catch (err) {
      console.error('Frame recording error:', err);
    }
  };

  const stopRecording = async () => {
    try {
      stopTimer();
      setIsProcessingAnswer(true);

      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
        recordingIntervalRef.current = null;
      }

      if (sessionIdRef.current) {
        let transcriptResult = '';

        if (audioRecordingRef.current) {
          try {
            await stopAudioRecording();
            transcriptResult = currentTranscript;
            await new Promise(resolve => setTimeout(resolve, 1000));
            audioRecordingRef.current = false;
          } catch (audioErr) {
            console.error('Error stopping audio recording:', audioErr);
          }
        }

        try {
          const response = await fetch('http://localhost:5000/api/interview/stop', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ session_id: sessionIdRef.current, transcript: transcriptResult })
          });

          if (response.ok) {
            const data = await response.json();
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
              answer_analysis: data.answer_analysis || {}
            };

            setQuestionResults(prev => {
              const questionData = prev[currentQuestion] || { attempts: [], bestAttempt: null };
              const attempts = [...questionData.attempts, attemptResults];
              const bestAttempt = attempts.reduce((best, current) =>
                (best === null || current.overall_score > best.overall_score) ? current : best, null);
              return { ...prev, [currentQuestion]: { attempts, bestAttempt } };
            });
          }
        } catch (fetchError) {
          console.error('Backend communication error:', fetchError);
        }

        setIsProcessingAnswer(false);
        setStatus('attempt_completed');
        sessionIdRef.current = null;
      }
    } catch (err) {
      setIsProcessingAnswer(false);
      setError('Failed to stop recording: ' + err.message);
      setStatus('ready');
    }
  };

  const tryAgain = () => {
    if (currentAttempt < 3) {
      setCurrentAttempt(currentAttempt + 1);
      startInterview();
    } else {
      nextQuestion();
    }
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      setCurrentAttempt(1);
      setStatus('ready');
    } else {
      completeInterview();
    }
  };

  const completeInterview = async () => {
    setStatus('processing');
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    const bestScores = Object.values(questionResults).map(q => q.bestAttempt || {
      overall_score: 0, posture_score: 0, eye_contact_score: 0,
      smile_percentage: 0, answer_quality_score: 0, overall_sentiment: 0
    });

    const finalResults = {
      overall_score: bestScores.reduce((sum, s) => sum + s.overall_score, 0) / bestScores.length,
      posture_score: bestScores.reduce((sum, s) => sum + s.posture_score, 0) / bestScores.length,
      eye_contact_score: bestScores.reduce((sum, s) => sum + s.eye_contact_score, 0) / bestScores.length,
      smile_percentage: bestScores.reduce((sum, s) => sum + s.smile_percentage, 0) / bestScores.length,
      answer_quality_score: bestScores.reduce((sum, s) => sum + s.answer_quality_score, 0) / bestScores.length,
      overall_sentiment: bestScores.reduce((sum, s) => sum + s.overall_sentiment, 0) / bestScores.length
    };

    setResults(finalResults);
  };

  useEffect(() => {
    const onKeyPress = (event) => {
      if (event.key === 'Escape' && status === 'recording') stopRecording();
    };
    if (status === 'recording') window.addEventListener('keydown', onKeyPress);
    return () => window.removeEventListener('keydown', onKeyPress);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  const getSentimentDisplay = (score) => ({
    isPositive: score >= 50,
    text: score >= 50 ? "Positive" : "Negative",
    icon: score >= 50 ? <ThumbsUp size={16} /> : <ThumbsDown size={16} />
  });

  return (
    <div className="page-wrapper">
      <Header />
      <main className="interview-page">
        {!results ? (
          <div className="interview-container">
            {/* Question Display */}
            {questions.length > 0 && (
              <div className="question-card">
                <div className="question-header">
                  <span className="question-badge">
                    Question {currentQuestionIndex + 1} of {questions.length}
                  </span>
                  <span className="attempt-badge">
                    Attempt {currentAttempt}/3
                  </span>
                </div>
                <p className="question-text">{questions[currentQuestionIndex]}</p>
              </div>
            )}

            {/* Timer */}
            {status === 'recording' && (
              <div className="timer-card">
                <Clock size={20} />
                <span className="timer-text">{timeRemaining}s remaining</span>
                <div className="timer-bar">
                  <div 
                    className="timer-progress"
                    style={{ 
                      width: `${getTimerProgress()}%`,
                      backgroundColor: getTimerColor()
                    }}
                  />
                </div>
              </div>
            )}

            {/* Video Preview */}
            <div className="video-section">
              <div className="video-container">
                <video ref={videoRef} autoPlay playsInline muted className="video-preview" />
                <canvas ref={canvasRef} style={{ display: 'none' }} />
                
                {status === 'initializing' && (
                  <div className="video-overlay">
                    <Loader className="spin" size={48} />
                    <p>Initializing camera...</p>
                  </div>
                )}

                {isProcessingAnswer && (
                  <div className="video-overlay">
                    <Loader className="spin" size={48} />
                    <p>Processing your answer...</p>
                  </div>
                )}

                {status === 'recording' && (
                  <div className="recording-badge">
                    <span className="recording-dot" />
                    Recording
                  </div>
                )}
              </div>

              {/* Microphone Status */}
              {status === 'ready' && (
                <div className={`mic-status ${microphonePermission ? 'granted' : 'denied'}`}>
                  {microphonePermission ? <Mic size={16} /> : <MicOff size={16} />}
                  <span>{microphonePermission ? 'Microphone ready' : 'Microphone access denied'}</span>
                </div>
              )}
            </div>

            {/* Transcript */}
            {currentTranscript && (status === 'recording' || status === 'attempt_completed') && (
              <div className="transcript-card">
                <h4>Your Response</h4>
                <p>{currentTranscript}</p>
              </div>
            )}

            {/* Controls */}
            <div className="controls-section">
              {status === 'ready' && (
                <div className="control-buttons">
                  {isLoadingQuestions ? (
                    <div className="loading-state">
                      <Loader className="spin" size={24} />
                      <span>Loading questions...</span>
                    </div>
                  ) : questions.length > 0 ? (
                    <>
                      <button className="btn btn-primary btn-lg" onClick={startInterview}>
                        <Play size={20} />
                        <span>Start Recording</span>
                      </button>
                      <button className="btn btn-ghost" onClick={() => navigate('/score-homepage')}>
                        <Home size={20} />
                        <span>Back to Home</span>
                      </button>
                    </>
                  ) : (
                    <>
                      <p className="error-text">Failed to load questions</p>
                      <button className="btn btn-secondary" onClick={fetchQuestions}>
                        <RotateCcw size={20} />
                        <span>Retry</span>
                      </button>
                    </>
                  )}
                </div>
              )}

              {status === 'recording' && (
                <div className="control-buttons">
                  <button className="btn btn-danger btn-lg" onClick={stopRecording}>
                    <Square size={20} />
                    <span>Stop Recording</span>
                  </button>
                  <span className="hint-text">Press ESC to stop</span>
                </div>
              )}

              {status === 'attempt_completed' && (
                <div className="attempt-complete-card">
                  <CheckCircle size={32} className="success-icon" />
                  <h3>Attempt {currentAttempt} Complete</h3>
                  <div className="control-buttons">
                    {currentAttempt < 3 && (
                      <button className="btn btn-secondary" onClick={tryAgain}>
                        <RotateCcw size={20} />
                        <span>Try Again</span>
                      </button>
                    )}
                    <button className="btn btn-primary" onClick={nextQuestion}>
                      <ArrowRight size={20} />
                      <span>{currentQuestionIndex < questions.length - 1 ? 'Next Question' : 'View Results'}</span>
                    </button>
                  </div>
                </div>
              )}

              {status === 'processing' && (
                <div className="loading-state">
                  <Loader className="spin" size={32} />
                  <span>Processing your interview...</span>
                </div>
              )}
            </div>

            {error && (
              <div className="error-card">
                <AlertCircle size={20} />
                <span>{error}</span>
              </div>
            )}
          </div>
        ) : (
          /* Results View */
          <div className="results-container">
            <div className="results-header">
              <h1>Interview Complete!</h1>
              <p>Here's how you did</p>
            </div>

            <div className="scores-grid">
              <div className="score-card main">
                <div className="score-icon"><Target size={32} /></div>
                <span className="score-value">{results.overall_score.toFixed(0)}%</span>
                <span className="score-label">Overall Score</span>
              </div>
              <div className="score-card">
                <div className="score-icon"><Camera size={24} /></div>
                <span className="score-value">{results.posture_score.toFixed(0)}%</span>
                <span className="score-label">Posture</span>
              </div>
              <div className="score-card">
                <div className="score-icon"><Eye size={24} /></div>
                <span className="score-value">{results.eye_contact_score.toFixed(0)}%</span>
                <span className="score-label">Eye Contact</span>
              </div>
              <div className="score-card">
                <div className="score-icon"><Smile size={24} /></div>
                <span className="score-value">{results.smile_percentage.toFixed(0)}%</span>
                <span className="score-label">Expression</span>
              </div>
              <div className="score-card">
                <div className={`score-icon ${getSentimentDisplay(results.overall_sentiment).isPositive ? 'positive' : 'negative'}`}>
                  {getSentimentDisplay(results.overall_sentiment).icon}
                </div>
                <span className="score-value">{getSentimentDisplay(results.overall_sentiment).text}</span>
                <span className="score-label">Sentiment</span>
              </div>
            </div>

            {/* Question Breakdown */}
            <div className="breakdown-section">
              <h2>Question Breakdown</h2>
              {questions.map((question, index) => {
                const qData = questionResults[question] || { bestAttempt: null };
                const best = qData.bestAttempt;
                return (
                  <div key={index} className="breakdown-card">
                    <h4>Q{index + 1}: {question}</h4>
                    {best ? (
                      <div className="breakdown-content">
                        {best.transcript && (
                          <div className="response-section">
                            <strong>Your Answer:</strong>
                            <p>{best.transcript}</p>
                          </div>
                        )}
                        {best.answer_analysis?.positive_reformulation && (
                          <div className="improvement-section">
                            <strong>Suggested Improvement:</strong>
                            <p>{best.answer_analysis.positive_reformulation}</p>
                          </div>
                        )}
                        {best.answer_analysis?.analysis && (
                          <div className="analysis-grid">
                            {best.answer_analysis.analysis.strengths?.length > 0 && (
                              <div className="analysis-item strengths">
                                <h5><CheckCircle size={16} /> Strengths</h5>
                                <ul>
                                  {best.answer_analysis.analysis.strengths.map((s, i) => (
                                    <li key={i}>{s}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {best.answer_analysis.analysis.improvements?.length > 0 && (
                              <div className="analysis-item improvements">
                                <h5><AlertCircle size={16} /> Areas to Improve</h5>
                                <ul>
                                  {best.answer_analysis.analysis.improvements.map((imp, i) => (
                                    <li key={i}>{imp}</li>
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

            <div className="results-actions">
              <button className="btn btn-primary" onClick={() => {
                setResults(null);
                setStatus('ready');
                initializeCamera();
                fetchQuestions();
              }}>
                <RotateCcw size={20} />
                <span>Practice Again</span>
              </button>
              <button className="btn btn-ghost" onClick={() => navigate('/score-homepage')}>
                <Home size={20} />
                <span>Back to Home</span>
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default Interview;
