/**
 * 注册页面
 */

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { ApiError } from '@/api/client';
import { Bot, Mail, Lock, Eye, EyeOff, Loader2, User, CheckCircle } from 'lucide-react';
import { cn } from '@workspace/ui/lib/utils';

const PASSWORD_RULES = [
  { test: (p: string) => p.length >= 8, label: '至少8个字符' },
  { test: (p: string) => /[A-Z]/.test(p), label: '包含大写字母' },
  { test: (p: string) => /[a-z]/.test(p), label: '包含小写字母' },
  { test: (p: string) => /[0-9]/.test(p), label: '包含数字' },
  { test: (p: string) => /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(p), label: '包含特殊字符' },
];

export function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { register } = useAuth();
  const navigate = useNavigate();

  const passwordValid = PASSWORD_RULES.every((rule) => rule.test(password));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('两次输入的密码不一致');
      return;
    }

    if (!passwordValid) {
      setError('密码不符合要求');
      return;
    }

    setIsLoading(true);

    try {
      await register({ email, password, name: name || undefined });
      navigate('/console/chat', { replace: true });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else {
        setError('注册失败，请重试');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-background to-muted p-4">
      <div className="w-full max-w-md space-y-8">
        {/* Logo */}
        <div className="text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-primary">
            <Bot className="h-8 w-8 text-primary-foreground" />
          </div>
          <h1 className="mt-4 text-3xl font-bold">AgentNex</h1>
          <p className="mt-2 text-muted-foreground">创建您的账号</p>
        </div>

        {/* 注册表单 */}
        <form onSubmit={handleSubmit} className="space-y-6 rounded-xl border bg-card p-8 shadow-lg">
          <h2 className="text-xl font-semibold">注册</h2>

          {error && (
            <div className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {error}
            </div>
          )}

          {/* 用户名 */}
          <div className="space-y-2">
            <label htmlFor="name" className="text-sm font-medium">
              用户名 <span className="text-muted-foreground">(可选)</span>
            </label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="您的名字"
                className="w-full rounded-md border bg-background py-2 pl-10 pr-4 text-sm outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          {/* 邮箱 */}
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">
              邮箱
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                className="w-full rounded-md border bg-background py-2 pl-10 pr-4 text-sm outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          {/* 密码 */}
          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium">
              密码
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full rounded-md border bg-background py-2 pl-10 pr-10 text-sm outline-none focus:ring-2 focus:ring-primary"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>
            {/* 密码强度提示 */}
            <div className="grid grid-cols-2 gap-1 text-xs">
              {PASSWORD_RULES.map((rule, idx) => (
                <div
                  key={idx}
                  className={cn(
                    'flex items-center gap-1',
                    rule.test(password) ? 'text-green-600' : 'text-muted-foreground'
                  )}
                >
                  <CheckCircle className="h-3 w-3" />
                  {rule.label}
                </div>
              ))}
            </div>
          </div>

          {/* 确认密码 */}
          <div className="space-y-2">
            <label htmlFor="confirmPassword" className="text-sm font-medium">
              确认密码
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
              <input
                id="confirmPassword"
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full rounded-md border bg-background py-2 pl-10 pr-4 text-sm outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          {/* 提交按钮 */}
          <button
            type="submit"
            disabled={isLoading || !passwordValid}
            className={cn(
              'flex w-full items-center justify-center gap-2 rounded-md bg-primary py-2.5 text-sm font-medium text-primary-foreground transition-colors',
              isLoading || !passwordValid ? 'cursor-not-allowed opacity-70' : 'hover:bg-primary/90'
            )}
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                注册中...
              </>
            ) : (
              '注册'
            )}
          </button>

          {/* 登录链接 */}
          <p className="text-center text-sm text-muted-foreground">
            已有账号？{' '}
            <Link to="/login" className="text-primary hover:underline">
              立即登录
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
