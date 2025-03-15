import Header from './Header';
import { Link } from 'react-router-dom';
import './FrontPage.css';
function Login() {
	return (
		<div>
			<Header />
			<Link className="app-content" to="/ScoreHomepage" style={{fontSize:'32px'}}>
            placeholder for actual login stuff
		</Link>
			<Link className="app-content" to="/CreateAccount" style={{fontSize:'32px'}}>
            Create Account
		</Link>
		</div>
	);
}
export default Login;