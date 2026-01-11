import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import { 
  Home, 
  Loader, 
  Calendar, 
  Clock,
  Target,
  Camera,
  Eye,
  Smile,
  AlertCircle,
  FileQuestion
} from 'lucide-react';

function Results() {
  const navigate = useNavigate();
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchResults();
  }, []);

  const fetchResults = async () => {
    try {
      const token = localStorage.getItem('jwt_token');
      const response = await fetch('/api/interview/results', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch results');
      }

      const data = await response.json();
      setResults(data.results || []);
    } catch (err) {
      console.error('Error fetching results:', err);
      setError(err.message || 'Failed to load results');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true
    });
  };

  return (
    <div className="page-wrapper">
      <Header />
      <main className="results-page">
        <div className="page-header">
          <h1>Interview History</h1>
          <p>Review your past interview sessions</p>
        </div>

        <div className="results-content">
          {loading ? (
            <div className="loading-state centered">
              <Loader className="spin" size={32} />
              <span>Loading your history...</span>
            </div>
          ) : error ? (
            <div className="error-card centered">
              <AlertCircle size={32} />
              <p>{error}</p>
              <button className="btn btn-secondary" onClick={fetchResults}>
                Try Again
              </button>
            </div>
          ) : results.length === 0 ? (
            <div className="empty-state">
              <FileQuestion size={64} />
              <h3>No interviews yet</h3>
              <p>Start practicing to see your results here</p>
              <button className="btn btn-primary" onClick={() => navigate('/interview')}>
                Start Practice
              </button>
            </div>
          ) : (
            <div className="results-list">
              {results.map((result, index) => (
                <div key={result.id || index} className="result-card">
                  <div className="result-header">
                    <div className="result-date">
                      <Calendar size={16} />
                      <span>{formatDate(result.created_at)}</span>
                    </div>
                    <div className="result-time">
                      <Clock size={16} />
                      <span>{formatTime(result.created_at)}</span>
                    </div>
                  </div>

                  <div className="result-scores">
                    <div className="score-item main">
                      <Target size={20} />
                      <div className="score-info">
                        <span className="value">{result.overall_score || 0}%</span>
                        <span className="label">Overall</span>
                      </div>
                    </div>
                    <div className="score-item">
                      <Camera size={18} />
                      <div className="score-info">
                        <span className="value">{result.posture_score || 0}%</span>
                        <span className="label">Posture</span>
                      </div>
                    </div>
                    <div className="score-item">
                      <Eye size={18} />
                      <div className="score-info">
                        <span className="value">{result.eye_contact_score || 0}%</span>
                        <span className="label">Eye Contact</span>
                      </div>
                    </div>
                    <div className="score-item">
                      <Smile size={18} />
                      <div className="score-info">
                        <span className="value">{result.smile_percentage || 0}%</span>
                        <span className="label">Expression</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="page-actions">
          <button className="btn btn-ghost" onClick={() => navigate('/score-homepage')}>
            <Home size={20} />
            <span>Back to Dashboard</span>
          </button>
        </div>
      </main>
    </div>
  );
}

export default Results;
