import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

function ProtectedRoute({ children }) {
    const location = useLocation();
    const token = localStorage.getItem('jwt_token');

    if (!token) {
        // Redirect to login but save the attempted location
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    return children;
}

export default ProtectedRoute; 