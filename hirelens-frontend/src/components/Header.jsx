import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { 
  Eye, 
  Home, 
  Video, 
  History, 
  LogOut, 
  ChevronDown,
  User
} from 'lucide-react';

function Header() {
  const [username, setUsername] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const token = localStorage.getItem('jwt_token');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setUsername(payload.name || payload.email?.split('@')[0] || 'User');
      } catch (error) {
        console.error('Error decoding token:', error);
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('jwt_token');
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <header className="header">
      <div className="header-container">
        <Link to="/score-homepage" className="logo">
          <Eye className="logo-icon" />
          <span>HireLens</span>
        </Link>

        <nav className="nav-menu">
          <Link 
            to="/score-homepage" 
            className={`nav-link ${isActive('/score-homepage') ? 'active' : ''}`}
          >
            <Home size={18} />
            <span>Dashboard</span>
          </Link>
          <Link 
            to="/interview" 
            className={`nav-link ${isActive('/interview') ? 'active' : ''}`}
          >
            <Video size={18} />
            <span>Practice</span>
          </Link>
          <Link 
            to="/all-results" 
            className={`nav-link ${isActive('/all-results') ? 'active' : ''}`}
          >
            <History size={18} />
            <span>History</span>
          </Link>
        </nav>

        {username && (
          <div className="user-dropdown">
            <button 
              className="user-button"
              onClick={() => setShowDropdown(!showDropdown)}
            >
              <div className="avatar">
                <User size={18} />
              </div>
              <span className="user-name">{username}</span>
              <ChevronDown size={16} className={`chevron ${showDropdown ? 'rotated' : ''}`} />
            </button>
            
            {showDropdown && (
              <>
                <div className="dropdown-overlay" onClick={() => setShowDropdown(false)} />
                <div className="dropdown-menu">
                  <button onClick={handleLogout} className="dropdown-item">
                    <LogOut size={16} />
                    <span>Sign Out</span>
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </header>
  );
}

export default Header;
