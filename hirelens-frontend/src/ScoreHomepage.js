import Header from './Header';
import { Link } from 'react-router-dom';
import './FrontPage.css';
function ScoreHomepage() {
	return (
		<div>
			<Header />
			<div className="app-content" style={{fontSize:'32px'}}>
			scorehomepage
		</div>
		<Link className="app-content" to="/Interview" style={{fontSize:'32px'}}>
            go to interview
		</Link>
		</div>
	);
}
export default ScoreHomepage;