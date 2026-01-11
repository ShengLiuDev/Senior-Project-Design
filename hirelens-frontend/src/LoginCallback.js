import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader, AlertCircle } from 'lucide-react';

function LoginCallback() {
  const navigate = useNavigate();
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        console.log('LoginCallback: Processing callback...');
        console.log('Full URL:', window.location.href);
        
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');
        const errorParam = urlParams.get('error');

        console.log('Token received:', token ? `${token.substring(0, 20)}...` : 'None');
        console.log('Error param:', errorParam);

        if (errorParam) {
          throw new Error(`Authentication error: ${errorParam}`);
        }

        if (!token) {
          throw new Error('No token received from server');
        }

        // Validate token structure
        const parts = token.split('.');
        if (parts.length !== 3) {
          throw new Error('Invalid token format');
        }

        // Try to decode the payload to verify it's valid
        try {
          const payload = JSON.parse(atob(parts[1]));
          console.log('Token payload:', payload);
        } catch (decodeError) {
          throw new Error('Failed to decode token payload');
        }

        localStorage.setItem('jwt_token', token);
        console.log('Token stored successfully');
        navigate('/score-homepage');
      } catch (err) {
        console.error('LoginCallback error:', err);
        setError(err.message);
        // Wait 3 seconds then redirect to login
        setTimeout(() => navigate('/login?error=auth_failed'), 3000);
      }
    };

    handleCallback();
  }, [navigate]);

  return (
    <div className="login-page">
      <div className="login-background">
        <div className="gradient-orb orb-1" />
        <div className="gradient-orb orb-2" />
      </div>
      <div className="loading-state">
        {error ? (
          <>
            <AlertCircle size={48} style={{ color: 'var(--color-error)' }} />
            <span style={{ color: 'var(--color-error)' }}>{error}</span>
            <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
              Redirecting to login...
            </span>
          </>
        ) : (
          <>
            <Loader className="spin" size={48} />
            <span>Completing sign in...</span>
          </>
        )}
      </div>
    </div>
  );
}

export default LoginCallback;
