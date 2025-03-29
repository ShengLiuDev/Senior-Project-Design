import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from './Header';
import './FrontPage.css';

function AllResults() {
    const navigate = useNavigate();
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchResults();
    }, []);

    const fetchResults = async () => {
        try {
            console.log('=== Starting fetchResults ===');
            const token = localStorage.getItem('jwt_token');
            console.log('Token:', token ? 'Present' : 'Missing');
            
            console.log('Making request to:', '/api/interview/results');
            const response = await fetch('/api/interview/results', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                credentials: 'include'
            });

            console.log('Response status:', response.status);
            console.log('Response headers:', Object.fromEntries(response.headers.entries()));
            
            if (!response.ok) {
                const errorData = await response.json();
                console.error('Error response:', errorData);
                throw new Error(errorData.error || 'Failed to fetch results');
            }

            const data = await response.json();
            console.log('Received data:', data);
            
            if (data.results) {
                console.log('Setting results:', data.results);
                setResults(data.results);
            } else {
                console.log('No results in data, setting empty array');
                setResults([]);
            }
        } catch (err) {
            console.error('Error in fetchResults:', err);
            console.error('Error stack:', err.stack);
            setError(err.message || 'Failed to load results');
        } finally {
            console.log('Setting loading to false');
            setLoading(false);
        }
    };

    return (
        <div>
            <Header />
            <div className="all-results-container">
                <div className="all-results-content">
                    <h1>Interview History</h1>
                    
                    {loading ? (
                        <div className="loading-state">
                            <div className="spinner"></div>
                            <p>Loading your interview history...</p>
                        </div>
                    ) : error ? (
                        <div className="error-message">
                            {error}
                        </div>
                    ) : results.length === 0 ? (
                        <p className="no-results">No interview results found.</p>
                    ) : (
                        <div className="results-list">
                            {results.map((result) => (
                                <div key={result.id} className="result-card">
                                    <div className="result-date">
                                        {new Date(result.created_at).toLocaleDateString()} at{' '}
                                        {new Date(result.created_at).toLocaleTimeString()}
                                    </div>
                                    <div className="score-grid">
                                        <div className="score-item">
                                            <span className="score-label">Overall Score</span>
                                            <span className="score-value">{result.overall_score}%</span>
                                        </div>
                                        <div className="score-item">
                                            <span className="score-label">Posture</span>
                                            <span className="score-value">{result.posture_score}%</span>
                                        </div>
                                        <div className="score-item">
                                            <span className="score-label">Eye Contact</span>
                                            <span className="score-value">{result.eye_contact_score}%</span>
                                        </div>
                                        <div className="score-item">
                                            <span className="score-label">Smile</span>
                                            <span className="score-value">{result.smile_percentage}%</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    <div className="action-buttons">
                        <button 
                            className="home-btn"
                            onClick={() => navigate('/score-homepage')}
                        >
                            Back to Home
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default AllResults; 