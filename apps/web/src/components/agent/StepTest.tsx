/**
 * 步骤3：实时测试
 * 测试 Agent 运行效果
 */

import { useState, useRef, useEffect } from 'react';
import type { AgentConfig, AgentTestResult } from '@/types';
import { testAgent } from '@/api/agents';
import { cn } from '@workspace/ui/lib/utils';
import {
  ChevronLeft,
  ChevronRight,
  Send,
  Trash2,
  ChevronDown,
  ChevronUp,
  Loader2,
} from 'lucide-react';

interface StepTestProps {
  config: AgentConfig;
  sessionId?: string;
  setSessionId: (id?: string) => void;
  onNext: () => void;
  onPrev: () => void;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  result?: AgentTestResult;
}

export function StepTest({
  config,
  sessionId,
  setSessionId,
  onNext,
  onPrev,
}: StepTestProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [expandedLogs, setExpandedLogs] = useState<Set<number>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 发送消息
  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const result = await testAgent({
        agent_config: config,
        message: input,
        session_id: sessionId,
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: result.response,
        result,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Test failed:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: '测试失败，请检查配置后重试。',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // 清空对话
  const handleClear = () => {
    setMessages([]);
    setSessionId(undefined);
  };

  // 切换日志展开
  const toggleLog = (index: number) => {
    setExpandedLogs((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  return (
    <div className="flex h-[600px] flex-col">
      <div className="mb-4">
        <h2 className="text-xl font-semibold">实时测试</h2>
        <p className="text-sm text-muted-foreground">
          测试 Agent 的运行效果，查看工具调用、知识库检索等中间日志
        </p>
      </div>

      {/* 对话区域 */}
      <div className="flex-1 overflow-auto rounded-lg border bg-muted/30 p-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-muted-foreground">
            <p className="mb-2 text-lg font-medium">开始测试</p>
            <p className="text-sm">输入问题，测试 Agent 的回复效果</p>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={cn(
                  'rounded-lg p-3',
                  msg.role === 'user' ? 'bg-primary text-primary-foreground ml-auto max-w-[80%]' : 'bg-background max-w-[100%]'
                )}
              >
                <div className="whitespace-pre-wrap text-sm">{msg.content}</div>

                {/* 日志展示 */}
                {msg.result && (
                  <div className="mt-3 space-y-2 border-t pt-3">
                    {/* 工具调用 */}
                    {msg.result.tool_calls && msg.result.tool_calls.length > 0 && (
                      <div>
                        <button
                          onClick={() => toggleLog(index)}
                          className="flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                        >
                          {expandedLogs.has(index) ? (
                            <ChevronUp className="h-3 w-3" />
                          ) : (
                            <ChevronDown className="h-3 w-3" />
                          )}
                          工具调用 ({msg.result.tool_calls.length})
                        </button>
                        {expandedLogs.has(index) && (
                          <div className="mt-2 space-y-2">
                            {msg.result.tool_calls.map((tool, i) => (
                              <div key={i} className="rounded bg-muted p-2 text-xs">
                                <div className="font-medium">{tool.tool}</div>
                                <div className="mt-1 text-muted-foreground">
                                  输入: {tool.input}
                                </div>
                                <div className="mt-1 text-muted-foreground">
                                  输出: {tool.output}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* 知识库检索 */}
                    {msg.result.knowledge_retrieved &&
                      msg.result.knowledge_retrieved.length > 0 && (
                        <div>
                          <button
                            onClick={() => toggleLog(index + 1000)}
                            className="flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                          >
                            {expandedLogs.has(index + 1000) ? (
                              <ChevronUp className="h-3 w-3" />
                            ) : (
                              <ChevronDown className="h-3 w-3" />
                            )}
                            知识库检索 ({msg.result.knowledge_retrieved.length})
                          </button>
                          {expandedLogs.has(index + 1000) && (
                            <div className="mt-2 space-y-2">
                              {msg.result.knowledge_retrieved.map((item, i) => (
                                <div key={i} className="rounded bg-muted p-2 text-xs">
                                  <div className="flex justify-between">
                                    <span className="text-muted-foreground">
                                      {item.document}
                                    </span>
                                    <span className="text-primary">
                                      相似度: {(item.similarity * 100).toFixed(1)}%
                                    </span>
                                  </div>
                                  <div className="mt-1">{item.content}</div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                    {/* 记忆调用 */}
                    {msg.result.memory_used && msg.result.memory_used.length > 0 && (
                      <div>
                        <button
                          onClick={() => toggleLog(index + 2000)}
                          className="flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                        >
                          {expandedLogs.has(index + 2000) ? (
                            <ChevronUp className="h-3 w-3" />
                          ) : (
                            <ChevronDown className="h-3 w-3" />
                          )}
                          记忆调用 ({msg.result.memory_used.length})
                        </button>
                        {expandedLogs.has(index + 2000) && (
                          <div className="mt-2 space-y-2">
                            {msg.result.memory_used.map((mem, i) => (
                              <div key={i} className="rounded bg-muted p-2 text-xs">
                                <div>{mem.content}</div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* 输入区域 */}
      <div className="mt-4 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="输入测试问题..."
          disabled={isLoading}
          className="flex-1 rounded-md border bg-background px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
        />
        <button
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
          className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
          发送
        </button>
        <button
          onClick={handleClear}
          disabled={messages.length === 0}
          className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent disabled:opacity-50"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>

      {/* 底部按钮 */}
      <div className="mt-4 flex justify-between border-t pt-4">
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
