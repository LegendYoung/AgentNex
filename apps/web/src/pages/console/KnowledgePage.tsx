/**
 * 知识库管理页面
 * 知识库列表、创建、文档上传、检索测试
 */

import { useState, useEffect } from 'react';
import type { PaginatedResponse } from '@/types';
import { cn } from '@workspace/ui/lib/utils';
import {
  Database,
  Plus,
  Search,
  Upload,
  Trash2,
  FileText,
  MoreVertical,
  X,
  Check,
  Loader2,
} from 'lucide-react';

// 知识库类型定义
interface KnowledgeBase {
  kb_id: string;
  name: string;
  description?: string;
  doc_count: number;
  chunk_size: number;
  chunk_overlap: number;
  is_public: boolean;
  creator: {
    user_id: string;
    name: string;
    email: string;
  };
  created_at: string;
  updated_at: string;
}

// 文档类型定义
interface Document {
  doc_id: string;
  filename: string;
  file_size: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  chunk_count?: number;
  created_at: string;
}

export function KnowledgePage() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKb, setSelectedKb] = useState<KnowledgeBase | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [visibility, setVisibility] = useState<'all' | 'my' | 'shared'>('all');

  // 加载知识库列表
  useEffect(() => {
    loadKnowledgeBases();
  }, [visibility]);

  const loadKnowledgeBases = async () => {
    setIsLoading(true);
    try {
      // TODO: 调用实际 API
      // const result = await listKnowledgeBases({ visibility });
      // setKnowledgeBases(result.items);

      // 模拟数据
      setKnowledgeBases([
        {
          kb_id: 'kb-1',
          name: '产品文档库',
          description: '产品相关的技术文档和手册',
          doc_count: 45,
          chunk_size: 512,
          chunk_overlap: 128,
          is_public: false,
          creator: { user_id: '1', name: 'Admin', email: 'admin@agentnex.io' },
          created_at: '2026-03-30T10:00:00',
          updated_at: '2026-03-31T14:30:00',
        },
        {
          kb_id: 'kb-2',
          name: 'FAQ知识库',
          description: '常见问题解答',
          doc_count: 128,
          chunk_size: 512,
          chunk_overlap: 128,
          is_public: true,
          creator: { user_id: '1', name: 'Admin', email: 'admin@agentnex.io' },
          created_at: '2026-03-29T08:00:00',
          updated_at: '2026-03-31T10:00:00',
        },
      ]);
    } catch (error) {
      console.error('Failed to load knowledge bases:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* 头部 */}
      <header className="flex items-center justify-between border-b px-6 py-4">
        <div>
          <h1 className="text-2xl font-bold">知识库管理</h1>
          <p className="text-sm text-muted-foreground">
            上传文档，构建向量知识库，支持语义检索
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          新建知识库
        </button>
      </header>

      {/* 工具栏 */}
      <div className="flex items-center gap-4 border-b px-6 py-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索知识库..."
            className="w-full rounded-md border bg-background py-2 pl-9 pr-4 text-sm outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <div className="flex items-center gap-2">
          {(['all', 'my', 'shared'] as const).map((v) => (
            <button
              key={v}
              onClick={() => setVisibility(v)}
              className={cn(
                'rounded-md px-3 py-1.5 text-sm transition-colors',
                visibility === v ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
              )}
            >
              {v === 'all' ? '全部' : v === 'my' ? '我的' : '共享'}
            </button>
          ))}
        </div>
      </div>

      {/* 内容区域 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 左侧：知识库列表 */}
        <div className="w-80 border-r overflow-auto">
          {isLoading ? (
            <div className="flex h-64 items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : knowledgeBases.length === 0 ? (
            <div className="flex h-64 flex-col items-center justify-center text-muted-foreground">
              <Database className="h-12 w-12 mb-4" />
              <p className="text-sm">暂无知识库</p>
            </div>
          ) : (
            <div className="divide-y">
              {knowledgeBases.map((kb) => (
                <button
                  key={kb.kb_id}
                  onClick={() => setSelectedKb(kb)}
                  className={cn(
                    'w-full p-4 text-left transition-colors hover:bg-accent',
                    selectedKb?.kb_id === kb.kb_id && 'bg-accent'
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{kb.name}</div>
                      <div className="mt-1 text-xs text-muted-foreground truncate">
                        {kb.description || '暂无描述'}
                      </div>
                      <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                        <FileText className="h-3 w-3" />
                        <span>{kb.doc_count} 个文档</span>
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 右侧：知识库详情 */}
        <div className="flex-1 overflow-auto">
          {selectedKb ? (
            <KnowledgeBaseDetail kb={selectedKb} onUpdate={loadKnowledgeBases} />
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              <div className="text-center">
                <Database className="mx-auto h-16 w-16 mb-4" />
                <p className="text-lg font-medium">选择知识库</p>
                <p className="text-sm">从左侧列表选择知识库查看详情</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 创建知识库弹窗 */}
      {showCreateModal && (
        <CreateKnowledgeBaseModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            loadKnowledgeBases();
          }}
        />
      )}
    </div>
  );
}

// 知识库详情组件
function KnowledgeBaseDetail({
  kb,
  onUpdate,
}: {
  kb: KnowledgeBase;
  onUpdate: () => void;
}) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [showUpload, setShowUpload] = useState(false);
  const [showSearch, setShowSearch] = useState(false);

  useEffect(() => {
    loadDocuments();
  }, [kb.kb_id]);

  const loadDocuments = async () => {
    try {
      // TODO: 调用实际 API
      setDocuments([
        {
          doc_id: 'doc-1',
          filename: '产品手册.pdf',
          file_size: 2048576,
          status: 'completed',
          chunk_count: 45,
          created_at: '2026-03-30T10:00:00',
        },
        {
          doc_id: 'doc-2',
          filename: '用户指南.docx',
          file_size: 1536000,
          status: 'completed',
          chunk_count: 32,
          created_at: '2026-03-30T11:00:00',
        },
      ]);
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const handleDelete = async (docId: string) => {
    if (!confirm('确定要删除此文档吗？')) return;
    try {
      // TODO: 调用删除 API
      setDocuments(documents.filter((d) => d.doc_id !== docId));
    } catch (error) {
      console.error('Failed to delete document:', error);
    }
  };

  return (
    <div className="p-6">
      {/* 知识库信息 */}
      <div className="mb-6 rounded-lg border p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h2 className="text-xl font-semibold">{kb.name}</h2>
            <p className="text-sm text-muted-foreground">
              {kb.description || '暂无描述'}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowSearch(true)}
              className="rounded-md border px-3 py-1.5 text-sm hover:bg-accent"
            >
              检索测试
            </button>
            <button
              onClick={() => setShowUpload(true)}
              className="flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              <Upload className="h-4 w-4" />
              上传文档
            </button>
          </div>
        </div>
        <div className="grid grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">分块大小：</span>
            <span className="font-medium">{kb.chunk_size} 字符</span>
          </div>
          <div>
            <span className="text-muted-foreground">重叠长度：</span>
            <span className="font-medium">{kb.chunk_overlap} 字符</span>
          </div>
          <div>
            <span className="text-muted-foreground">文档数量：</span>
            <span className="font-medium">{kb.doc_count} 个</span>
          </div>
          <div>
            <span className="text-muted-foreground">可见性：</span>
            <span className="font-medium">{kb.is_public ? '公开' : '私有'}</span>
          </div>
        </div>
      </div>

      {/* 文档列表 */}
      <div>
        <h3 className="mb-3 font-semibold">文档列表</h3>
        {documents.length === 0 ? (
          <div className="rounded-lg border p-8 text-center text-muted-foreground">
            <FileText className="mx-auto h-12 w-12 mb-4" />
            <p className="text-sm">暂无文档，点击"上传文档"添加</p>
          </div>
        ) : (
          <div className="rounded-lg border divide-y">
            {documents.map((doc) => (
              <div key={doc.doc_id} className="flex items-center justify-between p-4">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <div className="font-medium">{doc.filename}</div>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{(doc.file_size / 1024 / 1024).toFixed(2)} MB</span>
                      <span>{doc.chunk_count} 个分块</span>
                      <span
                        className={cn(
                          doc.status === 'completed' && 'text-green-600',
                          doc.status === 'processing' && 'text-blue-600',
                          doc.status === 'failed' && 'text-red-600'
                        )}
                      >
                        {doc.status === 'completed'
                          ? '已完成'
                          : doc.status === 'processing'
                            ? '处理中'
                            : '失败'}
                      </span>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(doc.doc_id)}
                  className="rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 上传文档弹窗 */}
      {showUpload && (
        <UploadDocumentModal
          kbId={kb.kb_id}
          onClose={() => setShowUpload(false)}
          onSuccess={() => {
            setShowUpload(false);
            loadDocuments();
          }}
        />
      )}

      {/* 检索测试弹窗 */}
      {showSearch && (
        <SearchTestModal
          kbId={kb.kb_id}
          onClose={() => setShowSearch(false)}
        />
      )}
    </div>
  );
}

// 创建知识库弹窗
function CreateKnowledgeBaseModal({
  onClose,
  onSuccess,
}: {
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [chunkSize, setChunkSize] = useState(512);
  const [chunkOverlap, setChunkOverlap] = useState(128);
  const [isPublic, setIsPublic] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  const handleCreate = async () => {
    if (!name.trim()) {
      alert('请输入知识库名称');
      return;
    }

    setIsCreating(true);
    try {
      // TODO: 调用实际 API
      await new Promise((resolve) => setTimeout(resolve, 1000));
      alert('知识库创建成功');
      onSuccess();
    } catch (error) {
      console.error('Failed to create knowledge base:', error);
      alert('创建失败');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg border bg-background p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">新建知识库</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-accent">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="mb-2 block text-sm font-medium">
              名称 <span className="text-destructive">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="知识库名称"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium">描述</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="知识库描述"
              rows={2}
              className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-2 block text-sm font-medium">
                分块大小: {chunkSize}
              </label>
              <input
                type="range"
                min="100"
                max="2000"
                step="100"
                value={chunkSize}
                onChange={(e) => setChunkSize(parseInt(e.target.value))}
                className="w-full"
              />
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium">
                重叠长度: {chunkOverlap}
              </label>
              <input
                type="range"
                min="0"
                max="500"
                step="50"
                value={chunkOverlap}
                onChange={(e) => setChunkOverlap(parseInt(e.target.value))}
                className="w-full"
              />
            </div>
          </div>

          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                className="h-4 w-4"
              />
              <span className="text-sm">公开知识库</span>
            </label>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent"
          >
            取消
          </button>
          <button
            onClick={handleCreate}
            disabled={isCreating}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {isCreating ? '创建中...' : '创建'}
          </button>
        </div>
      </div>
    </div>
  );
}

// 上传文档弹窗
function UploadDocumentModal({
  kbId,
  onClose,
  onSuccess,
}: {
  kbId: string;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    if (files.length + selectedFiles.length > 10) {
      alert('最多上传10个文件');
      return;
    }
    setFiles([...files, ...selectedFiles]);
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    setUploading(true);
    try {
      // TODO: 调用实际 API
      for (const file of files) {
        setUploadProgress((prev) => ({ ...prev, [file.name]: 0 }));
        // 模拟上传进度
        for (let i = 0; i <= 100; i += 20) {
          await new Promise((resolve) => setTimeout(resolve, 200));
          setUploadProgress((prev) => ({ ...prev, [file.name]: i }));
        }
      }
      alert('上传成功');
      onSuccess();
    } catch (error) {
      console.error('Failed to upload:', error);
      alert('上传失败');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg border bg-background p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">上传文档</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-accent">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4">
          {/* 文件选择 */}
          <div className="rounded-lg border-2 border-dashed p-6 text-center">
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.txt,.md"
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
              <p className="mt-2 text-sm text-muted-foreground">
                点击选择或拖拽文件到此处
              </p>
              <p className="text-xs text-muted-foreground">
                支持 PDF、DOCX、TXT、Markdown，单文件最大 50MB
              </p>
            </label>
          </div>

          {/* 已选文件列表 */}
          {files.length > 0 && (
            <div className="space-y-2">
              {files.map((file, index) => (
                <div key={index} className="flex items-center justify-between rounded-md border p-2">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <div className="text-sm font-medium">{file.name}</div>
                      <div className="text-xs text-muted-foreground">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </div>
                    </div>
                  </div>
                  {uploadProgress[file.name] !== undefined ? (
                    <div className="text-xs text-primary">
                      {uploadProgress[file.name]}%
                    </div>
                  ) : (
                    <button
                      onClick={() => removeFile(index)}
                      className="rounded p-1 hover:bg-accent"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <button
            onClick={onClose}
            disabled={uploading}
            className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent disabled:opacity-50"
          >
            取消
          </button>
          <button
            onClick={handleUpload}
            disabled={uploading || files.length === 0}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {uploading ? '上传中...' : '上传'}
          </button>
        </div>
      </div>
    </div>
  );
}

// 检索测试弹窗
function SearchTestModal({
  kbId,
  onClose,
}: {
  kbId: string;
  onClose: () => void;
}) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<
    Array<{ content: string; similarity: number; document: string }>
  >([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    try {
      // TODO: 调用实际 API
      await new Promise((resolve) => setTimeout(resolve, 500));
      setResults([
        {
          content: '这是一段匹配的文本内容示例，展示了知识库检索结果...',
          similarity: 0.92,
          document: '产品手册.pdf',
        },
        {
          content: '另一段相关内容，包含了用户查询的关键信息...',
          similarity: 0.85,
          document: '用户指南.docx',
        },
      ]);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-2xl rounded-lg border bg-background p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">检索测试</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-accent">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4">
          {/* 搜索框 */}
          <div className="flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="输入查询内容..."
              className="flex-1 rounded-md border bg-background px-3 py-2 text-sm"
            />
            <button
              onClick={handleSearch}
              disabled={isSearching}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {isSearching ? '搜索中...' : '搜索'}
            </button>
          </div>

          {/* 搜索结果 */}
          {results.length > 0 && (
            <div className="space-y-3">
              {results.map((result, index) => (
                <div key={index} className="rounded-lg border p-3">
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{result.document}</span>
                    <span className="font-medium text-primary">
                      相似度: {(result.similarity * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="text-sm">{result.content}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
