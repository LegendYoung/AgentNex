/**
 * 设置页面（占位）
 */

import { Settings, User, Key, Bell } from 'lucide-react';

export function SettingsPage() {
  return (
    <div className="flex h-full flex-col">
      <header className="border-b px-6 py-4">
        <h1 className="text-2xl font-bold">设置</h1>
        <p className="text-sm text-muted-foreground">管理您的账户和偏好设置</p>
      </header>

      <div className="flex-1 overflow-auto p-6">
        <div className="mx-auto max-w-2xl space-y-6">
          {/* 个人信息 */}
          <section className="rounded-lg border bg-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <User className="h-5 w-5 text-muted-foreground" />
              <h2 className="font-semibold">个人信息</h2>
            </div>
            <p className="text-sm text-muted-foreground">修改您的个人资料和头像</p>
          </section>

          {/* 安全设置 */}
          <section className="rounded-lg border bg-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <Key className="h-5 w-5 text-muted-foreground" />
              <h2 className="font-semibold">安全设置</h2>
            </div>
            <p className="text-sm text-muted-foreground">修改密码、管理 API 密钥</p>
          </section>

          {/* 通知设置 */}
          <section className="rounded-lg border bg-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <Bell className="h-5 w-5 text-muted-foreground" />
              <h2 className="font-semibold">通知设置</h2>
            </div>
            <p className="text-sm text-muted-foreground">管理邮件和系统通知偏好</p>
          </section>
        </div>
      </div>
    </div>
  );
}
