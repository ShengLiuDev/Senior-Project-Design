import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Header from './Header';
import './FrontPage.css';

function Results() {
    const location = useLocation();
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(true);
    const results = location.state?.results;

    useEffect(() => {
        if (!results) {
            navigate('/score-homepage');
            return;
        }

        const timer = setTimeout(() => {
            setIsLoading(false);
        }, 1500);

        return () => clearTimeout(timer);
    }, [results, navigate]);

    // Always render the container, even if loading or no results
    return (
        <div>
            <Header />
            <div className="results-container">
                <div className="results-content">
                    {isLoading ? (
                        <>
                            <h1>Processing Results</h1>
                            <div className="spinner"></div>
                            <p>Please wait while we analyze your interview...</p>
                        </>
                    ) : !results ? (
                        <>
                            <h1>No Results Available</h1>
                            <p>Please complete an interview to view your results.</p>
                            <div className="action-buttons">
                                <button 
                                    className="practice-btn"
                                    onClick={() => navigate('/interview')}
                                >
                                    Start Interview
                                </button>
                                <button 
                                    className="home-btn"
                                    onClick={() => navigate('/score-homepage')}
                                >
                                    Back to Home
                                </button>
                            </div>
                        </>
                    ) : (
                        <>
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
                                    onClick={() => navigate('/interview')}
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
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

export default Results; 