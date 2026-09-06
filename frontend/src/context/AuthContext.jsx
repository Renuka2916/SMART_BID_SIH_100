import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('gem_user');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('gem_auth_token'));
  const [loading, setLoading] = useState(true);

  // Sync session on mount
  useEffect(() => {
    const initAuth = async () => {
      const savedToken = localStorage.getItem('gem_auth_token');
      if (savedToken) {
        try {
          const res = await api.get('/auth/me');
          setUser(res.data);
          localStorage.setItem('gem_user', JSON.stringify(res.data));
        } catch (err) {
          console.warn('Session verification failed or expired:', err);
          logout();
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email, password) => {
    try {
      const res = await api.post('/auth/login', { email: email.trim(), password });
      const { access_token, user: userData } = res.data;

      localStorage.setItem('gem_auth_token', access_token);
      localStorage.setItem('gem_user', JSON.stringify(userData));

      setToken(access_token);
      setUser(userData);
      return { success: true, user: userData };
    } catch (err) {
      if (!err.response) {
        return { 
          success: false, 
          error: 'Cannot connect to backend server. Please make sure the backend is running on http://127.0.0.1:8000 (or double-click run_backend.bat).' 
        };
      }
      const detail = err.response?.data?.detail || 'Authentication failed. Please check your credentials.';
      return { success: false, error: detail };
    }
  };

  const logout = () => {
    localStorage.removeItem('gem_auth_token');
    localStorage.removeItem('gem_user');
    setToken(null);
    setUser(null);
  };

  const isProcurementOfficer = user?.role?.name === 'Procurement Officer' || user?.role?.name === 'Admin';

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    isProcurementOfficer,
    isAuthenticated: !!token && !!user
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
