/**
 * 认证 Hook
 * 管理用户登录状态、Token、用户信息
 */

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import {
  login as apiLogin,
  register as apiRegister,
  logout as apiLogout,
  getCurrentUser,
  isAuthenticated,
} from '@/api/auth';
import { tokenStorage } from '@/api/client';
import type { User, LoginRequest, RegisterRequest } from '@/types/auth';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (request: LoginRequest) => Promise<void>;
  register: (request: RegisterRequest) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 初始化：检查是否已登录
  useEffect(() => {
    const initAuth = async () => {
      if (isAuthenticated()) {
        try {
          const userData = await getCurrentUser();
          setUser(userData);
        } catch {
          tokenStorage.clearTokens();
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  // 登录
  const login = useCallback(async (request: LoginRequest) => {
    const response = await apiLogin(request);
    setUser(response.user);
  }, []);

  // 注册
  const register = useCallback(async (request: RegisterRequest) => {
    await apiRegister(request);
    // 注册成功后自动登录
    await login({ email: request.email, password: request.password });
  }, [login]);

  // 登出
  const logout = useCallback(() => {
    setUser(null);
    apiLogout();
  }, []);

  // 刷新用户信息
  const refreshUser = useCallback(async () => {
    if (isAuthenticated()) {
      const userData = await getCurrentUser();
      setUser(userData);
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
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
