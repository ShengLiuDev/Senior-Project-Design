import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import LoginCallback from './LoginCallback';
import Dashboard from './pages/Dashboard';
import Interview from './pages/Interview';
import Results from './pages/Results';
import ProtectedRoute from './ProtectedRoute';

function App() {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/login/callback" element={<LoginCallback />} />

        {/* Protected Routes */}
        <Route path="/score-homepage" element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } />
        <Route path="/interview" element={
          <ProtectedRoute>
            <Interview />
          </ProtectedRoute>
        } />
        <Route path="/all-results" element={
          <ProtectedRoute>
            <Results />
          </ProtectedRoute>
        } />

        {/* Redirect root to appropriate page */}
        <Route path="/" element={
          localStorage.getItem('jwt_token') ?
            <Navigate to="/score-homepage" replace /> :
            <Navigate to="/login" replace />
        } />
      </Routes>
    </Router>
  );
}

export default App;
