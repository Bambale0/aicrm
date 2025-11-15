import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiService } from '../services/api.ts';

interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  register: (username: string, password: string, email: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        try {
          const userData = await apiService.getCurrentUser();
          setUser(userData);
        } catch (error) {
          localStorage.removeItem('auth_token');
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      await apiService.login({ email, password });
      const userData = await apiService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      throw error;
    }
  };

  const register = async (username: string, password: string, email: string) => {
    try {
      await apiService.register({ username, password, email });
      await login(email, password);
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    apiService.logout();
    setUser(null);
  };

  const value: AuthContextType = {
    user,
    login,
    register,
    logout,
    isLoading,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
