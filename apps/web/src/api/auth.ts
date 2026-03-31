/**
 * 认证相关 API
 */

import { api, tokenStorage, ApiError } from './client';
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  User,
  ChangePasswordRequest,
} from '@/types/auth';

export interface RegisterResponse {
  success: boolean;
  data: {
    user_id: string;
    email: string;
    name: string;
    role: string;
    created_at: string;
  };
}

export interface MeResponse {
  success: boolean;
  data: User;
}

export interface MessageResponse {
  success: boolean;
  message: string;
}

/**
 * 用户登录
 */
export async function login(request: LoginRequest): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>('/api/v1/auth/login', request, {
    skipAuth: true,
  });

  // 存储 Token
  tokenStorage.setTokens(response.access_token, response.refresh_token);

  return response;
}

/**
 * 用户注册
 */
export async function register(request: RegisterRequest): Promise<RegisterResponse> {
  return api.post<RegisterResponse>('/api/v1/auth/register', request, {
    skipAuth: true,
  });
}

/**
 * 用户登出
 */
export function logout(): void {
  tokenStorage.clearTokens();
  window.location.href = '/login';
}

/**
 * 获取当前用户信息
 */
export async function getCurrentUser(): Promise<User> {
  const response = await api.get<MeResponse>('/api/v1/auth/me');
  return response.data;
}

/**
 * 修改密码
 */
export async function changePassword(request: ChangePasswordRequest): Promise<MessageResponse> {
  return api.post<MessageResponse>('/api/v1/auth/change-password', request);
}

/**
 * 检查是否已登录
 */
export function isAuthenticated(): boolean {
  return !!tokenStorage.getAccessToken();
}

export { ApiError };
