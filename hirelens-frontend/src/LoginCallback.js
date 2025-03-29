import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from './Header';
import './FrontPage.css';

function LoginCallback() {
    const navigate = useNavigate();

    useEffect(() => {
        const handleCallback = async () => {
            try {
                // Get the token from URL
                const urlParams = new URLSearchParams(window.location.search);
                const token = urlParams.get('token');

                if (!token) {
                    throw new Error('No token received');
                }

                // Store the token
                localStorage.setItem('jwt_token', token);
                
                // Redirect to interview page
                navigate('/score-homepage');

            } catch (error) {
                console.error('Callback error:', error);
                navigate('/login?error=auth_failed');
            }
        };

        handleCallback();
    }, [navigate]);

    return (
        <div>
            <Header />
            <div className="callback-container">
                <div className="callback-box">
                    <h2>Completing login...</h2>
                    <div className="spinner"></div>
                </div>
            </div>
        </div>
    );
}

export default LoginCallback; 