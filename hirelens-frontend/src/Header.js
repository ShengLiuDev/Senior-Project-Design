import React from 'react';
import './Header.css';
function Header() {
	return (
		<header className="header">{
			//links to go here eventually
			<div className="header-content">
                <span>(Logo here)</span>
                <span>Practice</span>
                <span>Review</span>
                <span>(Username here)</span>
            </div>
		}</header>
	)
}
export default Header;