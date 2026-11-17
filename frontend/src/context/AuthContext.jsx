import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const saved = typeof window !== 'undefined' && window.localStorage ? window.localStorage.getItem('stackdoctor_user') : null;
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState(() => {
    try {
      return typeof window !== 'undefined' && window.localStorage ? window.localStorage.getItem('stackdoctor_token') : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function verifyUser() {
      if (token) {
        try {
          const res = await authAPI.me();
          setUser(res.data.user);
          localStorage.setItem('stackdoctor_user', JSON.stringify(res.data.user));
        } catch {
          logout();
        }
      }
      setLoading(false);
    }
    verifyUser();
  }, [token]);

  const login = async (identifier, password) => {
    const res = await authAPI.login({ identifier, password });
    const { access_token, user: loggedUser } = res.data;
    localStorage.setItem('stackdoctor_token', access_token);
    localStorage.setItem('stackdoctor_user', JSON.stringify(loggedUser));
    setToken(access_token);
    setUser(loggedUser);
    return loggedUser;
  };

  const register = async (username, email, password) => {
    const res = await authAPI.register({ username, email, password });
    const { access_token, user: newUser } = res.data;
    localStorage.setItem('stackdoctor_token', access_token);
    localStorage.setItem('stackdoctor_user', JSON.stringify(newUser));
    setToken(access_token);
    setUser(newUser);
    return newUser;
  };

  const logout = async () => {
    try {
      if (token) {
        await authAPI.logout();
      }
    } catch {
      // Ignore logout errors
    } finally {
      localStorage.removeItem('stackdoctor_token');
      localStorage.removeItem('stackdoctor_user');
      setToken(null);
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
