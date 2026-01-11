import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import { 
  Video, 
  History, 
  TrendingUp, 
  Award,
  ArrowRight,
  Sparkles
} from 'lucide-react';

function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalInterviews: 0,
    averageScore: 0,
    bestScore: 0
  });
  // eslint-disable-next-line no-unused-vars
  const [recentResults, setRecentResults] = useState([]);
  // eslint-disable-next-line no-unused-vars
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('jwt_token');
      console.log('Dashboard: Fetching stats with token:', token ? 'present' : 'missing');
      
      const response = await fetch('/api/interview/results', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('Dashboard: Response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('Dashboard: Received data:', data);
        if (data.results && data.results.length > 0) {
          const scores = data.results.map(r => r.overall_score || 0);
          setStats({
            totalInterviews: data.results.length,
            averageScore: Math.round(scores.reduce((a, b) => a + b, 0) / scores.length),
            bestScore: Math.round(Math.max(...scores))
          });
          setRecentResults(data.results.slice(0, 3));
        }
      } else if (response.status === 401) {
        console.log('Dashboard: Unauthorized, redirecting to login');
        localStorage.removeItem('jwt_token');
        navigate('/login');
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error('Dashboard: API error:', errorData);
      }
    } catch (err) {
      console.error('Error fetching stats:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-wrapper">
      <Header />
      <main className="dashboard">
        <div className="dashboard-header">
          <div className="welcome-section">
            <h1>Welcome Back</h1>
            <p>Ready to ace your next interview?</p>
          </div>
        </div>

        <div className="dashboard-grid">
          {/* Quick Actions */}
          <section className="action-cards">
            <div 
              className="action-card primary"
              onClick={() => navigate('/interview')}
            >
              <div className="card-icon">
                <Video size={32} />
              </div>
              <div className="card-content">
                <h3>Start Practice</h3>
                <p>Begin a new interview session</p>
              </div>
              <ArrowRight className="card-arrow" size={24} />
            </div>

            <div 
              className="action-card secondary"
              onClick={() => navigate('/all-results')}
            >
              <div className="card-icon">
                <History size={32} />
              </div>
              <div className="card-content">
                <h3>View History</h3>
                <p>Review your past interviews</p>
              </div>
              <ArrowRight className="card-arrow" size={24} />
            </div>
          </section>

          {/* Stats Cards */}
          <section className="stats-section">
            <h2>Your Progress</h2>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">
                  <Video size={24} />
                </div>
                <div className="stat-info">
                  <span className="stat-value">{stats.totalInterviews}</span>
                  <span className="stat-label">Total Sessions</span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon">
                  <TrendingUp size={24} />
                </div>
                <div className="stat-info">
                  <span className="stat-value">{stats.averageScore}%</span>
                  <span className="stat-label">Average Score</span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon">
                  <Award size={24} />
                </div>
                <div className="stat-info">
                  <span className="stat-value">{stats.bestScore}%</span>
                  <span className="stat-label">Best Score</span>
                </div>
              </div>
            </div>
          </section>

          {/* Tips Section */}
          <section className="tips-section">
            <div className="tips-card">
              <Sparkles size={24} />
              <div className="tips-content">
                <h3>Quick Tips</h3>
                <ul>
                  <li>Maintain eye contact with the camera</li>
                  <li>Speak clearly and at a moderate pace</li>
                  <li>Use the STAR method for behavioral questions</li>
                  <li>Practice in a well-lit, quiet environment</li>
                </ul>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

export default Dashboard;
