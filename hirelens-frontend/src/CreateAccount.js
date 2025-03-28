import Header from './Header';
import { Link } from 'react-router-dom';
import './FrontPage.css';
function CreateAccount() {
	return (
		<div>
			<Header />
			<div className="app-content" style={{fontSize:'32px'}}>
			send to google api ig
		</div>
		<Link className="app-content" to="/Login" style={{fontSize:'32px'}}>
            Create account and return to login
		</Link>
		</div>
	);
}
export default CreateAccount;