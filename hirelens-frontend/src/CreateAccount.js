import Header from './Header';
import { Link } from 'react-router-dom';
import './FrontPage.css';

/* 
	Might implement account creation here, but may stick to Google OAuth for security and simplicity
*/
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