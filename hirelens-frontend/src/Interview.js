import Header from './Header';
import { Link } from 'react-router-dom';
import './FrontPage.css';
function Interview() {
	return (
		<div>
			<Header />
		<Link className="app-content" to="/ScoreHomepage" style={{fontSize:'32px'}}>
            go back to score homepage after finishing
		</Link>
		</div>
	);
}
export default Interview;