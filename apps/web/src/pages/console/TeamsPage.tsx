/**
 * 团队管理页面（占位）
 */

import { Users, Plus } from 'lucide-react';

export function TeamsPage() {
  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between border-b px-6 py-4">
        <div>
          <h1 className="text-2xl font-bold">团队管理</h1>
          <p className="text-sm text-muted-foreground">创建团队，邀请成员协作</p>
        </div>
        <button className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
          <Plus className="h-4 w-4" />
          创建团队
        </button>
      </header>

      <div className="flex flex-1 items-center justify-center">
        <div className="text-center text-muted-foreground">
          <Users className="mx-auto h-16 w-16 mb-4" />
          <p className="text-lg font-medium">团队功能开发中</p>
          <p className="text-sm">即将支持团队创建、成员邀请、资源共享</p>
        </div>
      </div>
    </div>
  );
}
