import React, { createContext, ReactNode, useContext, useEffect, useState } from 'react';
import api, {
  AUTH_SESSION_EXPIRED_EVENT,
  AUTH_TOKEN_STORAGE_KEY,
} from '../services/api';

interface User {
  id: number;
  email: string;
  full_name?: string;
  company_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  role: string;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  register: (fullName: string, password: string, email: string, companyName?: string) => Promise<void>;
  logout: () => Promise<void>;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  sessionExpired: boolean;
}

const AUTH_REQUIRED = process.env.REACT_APP_AUTH_REQUIRED !== 'false';
const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sessionExpired, setSessionExpired] = useState(false);

  useEffect(() => {
    const handleSessionExpired = () => {
      setUser(null);
      setSessionExpired(true);
      setIsLoading(false);
    };

    window.addEventListener(AUTH_SESSION_EXPIRED_EVENT, handleSessionExpired);
    return () => {
      window.removeEventListener(AUTH_SESSION_EXPIRED_EVENT, handleSessionExpired);
    };
  }, []);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const response = await api.get('/auth/me');
        setUser(response.data);
        setSessionExpired(false);
      } catch {
        localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
        setUser(null);
        setSessionExpired(true);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await api.post('/auth/login/json', { email, password });
    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, response.data.access_token);
    const userResponse = await api.get('/auth/me');
    setUser(userResponse.data);
    setSessionExpired(false);
  };

  const register = async (fullName: string, password: string, email: string, companyName?: string) => {
    await api.post('/auth/register', {
      full_name: fullName,
      password,
      email,
      company_name: companyName,
    });
  };

  const logout = async () => {
    const token = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
    if (token) {
      try {
        await api.post('/auth/logout');
      } catch {
        // Local logout must still succeed when the server session is already gone.
      }
    }
    localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
    setUser(null);
    setSessionExpired(false);
  };

  const isAdmin =
    Boolean(user?.is_superuser) ||
    ['admin', 'superuser'].includes(String(user?.role || '').toLowerCase());

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        register,
        logout,
        isLoading,
        isAuthenticated: !AUTH_REQUIRED || Boolean(user),
        isAdmin,
        sessionExpired,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
