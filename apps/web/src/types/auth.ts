// 认证相关类型定义

export type PlatformRole = 'super_admin' | 'admin' | 'user';
export type UserStatus = 'active' | 'disabled';

export interface User {
  user_id: string;
  email: string;
  name: string | null;
  role: PlatformRole;
  status?: UserStatus;
  require_password_change?: boolean;
  created_at?: string;
  last_login_at?: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name?: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
}
