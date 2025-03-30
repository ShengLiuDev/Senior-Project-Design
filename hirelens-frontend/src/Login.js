import React, { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './FrontPage.css';

function Login() {
	const location = useLocation();
	const navigate = useNavigate();

	useEffect(() => {
		const token = localStorage.getItem('jwt_token');
		if (token) {
			navigate('/score-homepage');
		}
	}, [navigate]);

	const handleGoogleLogin = async () => {
		try {
			const response = await fetch('http://localhost:5000/auth/login/google');
			const data = await response.json();
			if (data.auth_url) {
				window.location.href = data.auth_url;
			}
		} catch (error) {
			console.error('Error initiating Google login:', error);
		}
	};

	return (
		<div className="login-container">
			<div className="login-box">
				<h1>Welcome to HireLens</h1>
				<p>Sign in to start practicing your interview skills</p>
				<button 
					className="google-login-btn"
					onClick={handleGoogleLogin}
				>
					<img 
						src="https://www.google.com/favicon.ico" 
						alt="Google" 
						className="google-icon"
					/>
					Sign in with Google
				</button>
			</div>
		</div>
	);
}

export default Login;