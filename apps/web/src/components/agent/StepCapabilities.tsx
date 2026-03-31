/**
 * 步骤2：能力开关
 * 记忆功能、知识库、工具调用配置
 */

import { useState, useEffect } from 'react';
import type { AgentConfig, ToolConfig } from '@/types';
import { cn } from '@workspace/ui/lib/utils';
import { ChevronLeft, ChevronRight, Database, Brain, Wrench } from 'lucide-react';

interface StepCapabilitiesProps {
  config: AgentConfig;
  updateConfig: (updates: Partial<AgentConfig>) => void;
  onNext: () => void;
  onPrev: () => void;
}

// 知识库列表（示例数据，实际应从 API 获取）
const MOCK_KNOWLEDGE_BASES = [
  { id: 'kb-1', name: '产品文档库', doc_count: 45 },
  { id: 'kb-2', name: '技术手册', doc_count: 32 },
  { id: 'kb-3', name: 'FAQ知识库', doc_count: 128 },
];

export function StepCapabilities({
  config,
  updateConfig,
  onNext,
  onPrev,
}: StepCapabilitiesProps) {
  const [knowledgeBases, setKnowledgeBases] = useState(MOCK_KNOWLEDGE_BASES);
  const [showMemoryConfig, setShowMemoryConfig] = useState(config.enable_memory);
  const [showKnowledgeConfig, setShowKnowledgeConfig] = useState(config.enable_knowledge);
  const [showToolsConfig, setShowToolsConfig] = useState(config.enable_tools);

  // 同步开关状态
  useEffect(() => {
    setShowMemoryConfig(config.enable_memory);
    setShowKnowledgeConfig(config.enable_knowledge);
    setShowToolsConfig(config.enable_tools);
  }, [config.enable_memory, config.enable_knowledge, config.enable_tools]);

  // 切换开关
  const toggleCapability = (
    capability: 'enable_memory' | 'enable_knowledge' | 'enable_tools'
  ) => {
    const newValue = !config[capability];
    updateConfig({ [capability]: newValue });

    // 关闭时清空相关配置
    if (!newValue) {
      if (capability === 'enable_memory') {
        updateConfig({
          memory_type: 'short_term',
          memory_window: 10,
        });
      } else if (capability === 'enable_knowledge') {
        updateConfig({
          knowledge_base_ids: [],
        });
      } else if (capability === 'enable_tools') {
        updateConfig({
          tool_config: {
            web_search: false,
            file_read: false,
            python_exec: false,
            permission: 'all',
          },
        });
      }
    }
  };

  // 更新工具配置
  const updateToolConfig = (updates: Partial<ToolConfig>) => {
    updateConfig({
      tool_config: {
        ...config.tool_config,
        ...updates,
      },
    });
  };

  // 切换知识库选择
  const toggleKnowledgeBase = (kbId: string) => {
    const currentIds = config.knowledge_base_ids;
    if (currentIds.includes(kbId)) {
      updateConfig({
        knowledge_base_ids: currentIds.filter((id) => id !== kbId),
      });
    } else {
      updateConfig({
        knowledge_base_ids: [...currentIds, kbId],
      });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">能力开关</h2>
        <p className="text-sm text-muted-foreground">
          为 Agent 启用记忆、知识库和工具调用能力
        </p>
      </div>

      <div className="space-y-4">
        {/* 记忆功能 */}
        <div className="rounded-lg border">
          <div
            className={cn(
              'flex items-center justify-between p-4 cursor-pointer',
              config.enable_memory && 'border-b bg-muted/30'
            )}
            onClick={() => toggleCapability('enable_memory')}
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/10">
                <Brain className="h-5 w-5 text-purple-500" />
              </div>
              <div>
                <div className="font-medium">记忆功能</div>
                <div className="text-sm text-muted-foreground">
                  让 Agent 记住对话内容，实现上下文连续
                </div>
              </div>
            </div>
            <div
              className={cn(
                'relative h-6 w-11 rounded-full transition-colors',
                config.enable_memory ? 'bg-primary' : 'bg-muted-foreground/30'
              )}
            >
              <div
                className={cn(
                  'absolute top-1 h-4 w-4 rounded-full bg-white transition-transform',
                  config.enable_memory ? 'translate-x-6' : 'translate-x-1'
                )}
              />
            </div>
          </div>

          {/* 记忆配置 */}
          {config.enable_memory && (
            <div className="space-y-4 p-4">
              {/* 记忆类型 */}
              <div>
                <label className="mb-2 block text-sm font-medium">记忆类型</label>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="memory_type"
                      value="short_term"
                      checked={config.memory_type === 'short_term'}
                      onChange={() => updateConfig({ memory_type: 'short_term' })}
                      className="h-4 w-4"
                    />
                    <span className="text-sm">短期记忆（仅当前会话）</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="memory_type"
                      value="long_term"
                      checked={config.memory_type === 'long_term'}
                      onChange={() => updateConfig({ memory_type: 'long_term' })}
                      className="h-4 w-4"
                    />
                    <span className="text-sm">长期记忆（跨会话）</span>
                  </label>
                </div>
              </div>

              {/* 记忆窗口 */}
              <div>
                <label className="mb-2 block text-sm font-medium">
                  记忆窗口：{config.memory_window} 轮对话
                </label>
                <input
                  type="range"
                  min="1"
                  max="50"
                  value={config.memory_window}
                  onChange={(e) => updateConfig({ memory_window: parseInt(e.target.value) })}
                  className="w-full max-w-md"
                />
                <div className="mt-1 flex max-w-md justify-between text-xs text-muted-foreground">
                  <span>1轮</span>
                  <span>50轮</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 知识库 */}
        <div className="rounded-lg border">
          <div
            className={cn(
              'flex items-center justify-between p-4 cursor-pointer',
              config.enable_knowledge && 'border-b bg-muted/30'
            )}
            onClick={() => toggleCapability('enable_knowledge')}
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10">
                <Database className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <div className="font-medium">知识库</div>
                <div className="text-sm text-muted-foreground">
                  让 Agent 基于知识库内容回答问题
                </div>
              </div>
            </div>
            <div
              className={cn(
                'relative h-6 w-11 rounded-full transition-colors',
                config.enable_knowledge ? 'bg-primary' : 'bg-muted-foreground/30'
              )}
            >
              <div
                className={cn(
                  'absolute top-1 h-4 w-4 rounded-full bg-white transition-transform',
                  config.enable_knowledge ? 'translate-x-6' : 'translate-x-1'
                )}
              />
            </div>
          </div>

          {/* 知识库配置 */}
          {config.enable_knowledge && (
            <div className="p-4">
              <label className="mb-2 block text-sm font-medium">选择知识库</label>
              <div className="space-y-2">
                {knowledgeBases.map((kb) => (
                  <label
                    key={kb.id}
                    className={cn(
                      'flex items-center justify-between rounded-md border p-3 cursor-pointer',
                      config.knowledge_base_ids.includes(kb.id) && 'border-primary bg-primary/5'
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={config.knowledge_base_ids.includes(kb.id)}
                        onChange={() => toggleKnowledgeBase(kb.id)}
                        className="h-4 w-4"
                      />
                      <div>
                        <div className="font-medium">{kb.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {kb.doc_count} 个文档
                        </div>
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 工具调用 */}
        <div className="rounded-lg border">
          <div
            className={cn(
              'flex items-center justify-between p-4 cursor-pointer',
              config.enable_tools && 'border-b bg-muted/30'
            )}
            onClick={() => toggleCapability('enable_tools')}
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
                <Wrench className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <div className="font-medium">工具调用</div>
                <div className="text-sm text-muted-foreground">
                  让 Agent 调用外部工具，扩展能力
                </div>
              </div>
            </div>
            <div
              className={cn(
                'relative h-6 w-11 rounded-full transition-colors',
                config.enable_tools ? 'bg-primary' : 'bg-muted-foreground/30'
              )}
            >
              <div
                className={cn(
                  'absolute top-1 h-4 w-4 rounded-full bg-white transition-transform',
                  config.enable_tools ? 'translate-x-6' : 'translate-x-1'
                )}
              />
            </div>
          </div>

          {/* 工具配置 */}
          {config.enable_tools && (
            <div className="space-y-4 p-4">
              <div>
                <label className="mb-2 block text-sm font-medium">内置工具</label>
                <div className="space-y-2">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={config.tool_config?.web_search || false}
                      onChange={(e) =>
                        updateToolConfig({ web_search: e.target.checked })
                      }
                      className="h-4 w-4"
                    />
                    <span className="text-sm">网页搜索</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={config.tool_config?.file_read || false}
                      onChange={(e) =>
                        updateToolConfig({ file_read: e.target.checked })
                      }
                      className="h-4 w-4"
                    />
                    <span className="text-sm">文件读取</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={config.tool_config?.python_exec || false}
                      onChange={(e) =>
                        updateToolConfig({ python_exec: e.target.checked })
                      }
                      className="h-4 w-4"
                    />
                    <span className="text-sm">Python 执行</span>
                  </label>
                </div>
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium">权限控制</label>
                <select
                  value={config.tool_config?.permission || 'all'}
                  onChange={(e) =>
                    updateToolConfig({
                      permission: e.target.value as ToolConfig['permission'],
                    })
                  }
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                >
                  <option value="all">全部允许</option>
                  <option value="allow_only">仅允许选中的工具</option>
                  <option value="deny_only">仅禁止选中的工具</option>
                </select>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 底部按钮 */}
      <div className="flex justify-between border-t pt-4">
        <button
          onClick={onPrev}
          className="flex items-center gap-2 rounded-md border px-6 py-2 text-sm font-medium hover:bg-accent"
        >
          <ChevronLeft className="h-4 w-4" />
          上一步
        </button>
        <button
          onClick={onNext}
          className="flex items-center gap-2 rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          下一步
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
