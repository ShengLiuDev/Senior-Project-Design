import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './Login';
import LoginCallback from './LoginCallback';
import ScoreHomepage from './ScoreHomepage';
import Interview from './Interview';
import AllResults from './AllResults';
import ProtectedRoute from './ProtectedRoute';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/login/callback" element={<LoginCallback />} />
          
          {/* Protected Routes */}
          <Route path="/score-homepage" element={
            <ProtectedRoute>
              <ScoreHomepage />
            </ProtectedRoute>
          } />
          <Route path="/interview" element={
            <ProtectedRoute>
              <Interview />
            </ProtectedRoute>
          } />
          <Route path="/all-results" element={
            <ProtectedRoute>
              <AllResults />
            </ProtectedRoute>
          } />
          
          {/* Redirect root to appropriate page */}
          <Route path="/" element={
            localStorage.getItem('jwt_token') ? 
              <Navigate to="/score-homepage" replace /> : 
              <Navigate to="/login" replace />
          } />
        </Routes>
      </div>
    </Router>
  );
}

export default App; 