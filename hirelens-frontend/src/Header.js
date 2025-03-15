import React from 'react';
import { Link } from 'react-router-dom';
import './Header.css';
function Header() {
	return (
		<header className="header">{
			//links to go here eventually
			<div className="header-content">
                <span>(Logo here)</span>
                <span>Practice</span>
                <span>Review</span>
                <span>
					<Link to="/Login">
					(Username here)
					</Link>
				</span>
            </div>
		}</header>
	)
}
export default Header;