/**
 * 知识库管理页面（占位）
 */

import { Database, Plus } from 'lucide-react';

export function KnowledgePage() {
  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between border-b px-6 py-4">
        <div>
          <h1 className="text-2xl font-bold">知识库管理</h1>
          <p className="text-sm text-muted-foreground">上传文档，构建向量知识库</p>
        </div>
        <button className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
          <Plus className="h-4 w-4" />
          新建知识库
        </button>
      </header>

      <div className="flex flex-1 items-center justify-center">
        <div className="text-center text-muted-foreground">
          <Database className="mx-auto h-16 w-16 mb-4" />
          <p className="text-lg font-medium">知识库功能开发中</p>
          <p className="text-sm">即将支持文档上传、向量索引、语义检索</p>
        </div>
      </div>
    </div>
  );
}
