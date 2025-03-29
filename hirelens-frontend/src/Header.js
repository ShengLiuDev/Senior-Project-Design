import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './Header.css';

function Header() {
	const [username, setUsername] = useState('');
	const [showDropdown, setShowDropdown] = useState(false);
	const navigate = useNavigate();

	useEffect(() => {
		// Get the token from localStorage
		const token = localStorage.getItem('jwt_token');
		if (token) {
			try {
				// Decode the JWT token to get user info
				const payload = JSON.parse(atob(token.split('.')[1]));
				setUsername(payload.name);
			} catch (error) {
				console.error('Error decoding token:', error);
			}
		}
	}, []);

	const handleLogout = () => {
		localStorage.removeItem('jwt_token');
		navigate('/login');
	};

	return (
		<header className="header">
			<div className="header-content">
				<div className="header-left">
					<span className="logo">HireLens</span>
					<nav className="nav-links">
						<Link to="/score-homepage">Practice</Link>
						<Link to="/score-homepage">Review</Link>
					</nav>
				</div>
				{username && (
					<div className="user-menu">
						<button 
							className="username-button"
							onClick={() => setShowDropdown(!showDropdown)}
						>
							{username}
							<span className="dropdown-arrow">▼</span>
						</button>
						{showDropdown && (
							<div className="dropdown-menu">
								<button onClick={handleLogout} className="dropdown-item">
									Logout
								</button>
							</div>
						)}
					</div>
				)}
			</div>
		</header>
	);
}

export default Header;