import { useNavigate } from 'react-router-dom';
import Header from './Header';
import { Link } from 'react-router-dom';
import './FrontPage.css';

function ScoreHomepage() {
	const navigate = useNavigate();

	return (
		<div>
			<Header />
			<div className="score-homepage-container">
				<div className="score-homepage-content">
					<h1>Welcome to HireLens</h1>
					<div className="action-buttons">
						<Link className="interview-btn" to="/interview">
							Start Interview
						</Link>
						<button 
							className="results-btn"
							onClick={() => navigate('/all-results')}
						>
							View All Results
						</button>
					</div>
				</div>
			</div>
		</div>
	);
}

export default ScoreHomepage;