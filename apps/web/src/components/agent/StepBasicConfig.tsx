/**
 * 步骤1：基础配置
 * 名称、描述、系统提示词、模型选择、参数配置
 */

import { useState } from 'react';
import type { AgentConfig } from '@/types';
import { cn } from '@workspace/ui/lib/utils';
import { ChevronRight, Eye } from 'lucide-react';

interface StepBasicConfigProps {
  config: AgentConfig;
  updateConfig: (updates: Partial<AgentConfig>) => void;
  onNext: () => void;
}

// 支持的模型列表
const MODELS = [
  { id: 'qwen-plus', name: '通义千问-Plus', provider: '阿里云' },
  { id: 'qwen-max', name: '通义千问-Max', provider: '阿里云' },
  { id: 'qwen-turbo', name: '通义千问-Turbo', provider: '阿里云' },
  { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'OpenAI' },
  { id: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI' },
  { id: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet', provider: 'Anthropic' },
];

export function StepBasicConfig({ config, updateConfig, onNext }: StepBasicConfigProps) {
  const [showPreview, setShowPreview] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 校验
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!config.name || config.name.length < 2) {
      newErrors.name = '名称至少需要2个字符';
    } else if (config.name.length > 32) {
      newErrors.name = '名称不能超过32个字符';
    }

    if (!config.system_prompt || config.system_prompt.length < 10) {
      newErrors.system_prompt = '系统提示词至少需要10个字符';
    } else if (config.system_prompt.length > 5000) {
      newErrors.system_prompt = '系统提示词不能超过5000个字符';
    }

    if (config.description && config.description.length > 200) {
      newErrors.description = '描述不能超过200个字符';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 下一步
  const handleNext = () => {
    if (validate()) {
      onNext();
    }
  };

  // 预览系统提示词拼接效果
  const previewPrompt = `## 角色定义
${config.system_prompt || '暂无系统提示词'}

## 配置参数
- 模型：${config.model_id}
- 温度：${config.temperature}
- Top-P：${config.top_p}`;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">基础配置</h2>
        <p className="text-sm text-muted-foreground">
          配置 Agent 的基本信息和模型参数
        </p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* 左侧：表单 */}
        <div className="space-y-4">
          {/* Agent 名称 */}
          <div>
            <label className="mb-2 block text-sm font-medium">
              Agent 名称 <span className="text-destructive">*</span>
            </label>
            <input
              type="text"
              value={config.name}
              onChange={(e) => updateConfig({ name: e.target.value })}
              placeholder="例如：智能客服助手"
              className={cn(
                'w-full rounded-md border bg-background px-3 py-2 text-sm outline-none',
                'focus:ring-2 focus:ring-primary',
                errors.name && 'border-destructive'
              )}
            />
            <div className="mt-1 flex justify-between text-xs">
              {errors.name ? (
                <span className="text-destructive">{errors.name}</span>
              ) : (
                <span className="text-muted-foreground">2-32个字符</span>
              )}
              <span className="text-muted-foreground">{config.name.length}/32</span>
            </div>
          </div>

          {/* Agent 描述 */}
          <div>
            <label className="mb-2 block text-sm font-medium">描述</label>
            <input
              type="text"
              value={config.description || ''}
              onChange={(e) => updateConfig({ description: e.target.value })}
              placeholder="简要描述 Agent 的功能和用途"
              className={cn(
                'w-full rounded-md border bg-background px-3 py-2 text-sm outline-none',
                'focus:ring-2 focus:ring-primary',
                errors.description && 'border-destructive'
              )}
            />
            <div className="mt-1 flex justify-between text-xs text-muted-foreground">
              <span>可选，最多200个字符</span>
              <span>{config.description?.length || 0}/200</span>
            </div>
          </div>

          {/* 系统提示词 */}
          <div>
            <div className="mb-2 flex items-center justify-between">
              <label className="text-sm font-medium">
                系统提示词 <span className="text-destructive">*</span>
              </label>
              <button
                type="button"
                onClick={() => setShowPreview(!showPreview)}
                className="flex items-center gap-1 text-xs text-primary hover:underline"
              >
                <Eye className="h-3 w-3" />
                预览效果
              </button>
            </div>
            <textarea
              value={config.system_prompt}
              onChange={(e) => updateConfig({ system_prompt: e.target.value })}
              placeholder="详细描述 Agent 的角色、职责和行为准则..."
              rows={6}
              className={cn(
                'w-full rounded-md border bg-background px-3 py-2 text-sm outline-none',
                'focus:ring-2 focus:ring-primary',
                'resize-none',
                errors.system_prompt && 'border-destructive'
              )}
            />
            <div className="mt-1 flex justify-between text-xs">
              {errors.system_prompt ? (
                <span className="text-destructive">{errors.system_prompt}</span>
              ) : (
                <span className="text-muted-foreground">支持 Markdown，10-5000个字符</span>
              )}
              <span className="text-muted-foreground">{config.system_prompt.length}/5000</span>
            </div>
          </div>

          {/* 模型选择 */}
          <div>
            <label className="mb-2 block text-sm font-medium">LLM 模型</label>
            <select
              value={config.model_id}
              onChange={(e) => updateConfig({ model_id: e.target.value })}
              className={cn(
                'w-full rounded-md border bg-background px-3 py-2 text-sm outline-none',
                'focus:ring-2 focus:ring-primary'
              )}
            >
              {MODELS.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name} ({model.provider})
                </option>
              ))}
            </select>
          </div>

          {/* 参数配置 */}
          <div className="grid grid-cols-2 gap-4">
            {/* Temperature */}
            <div>
              <label className="mb-2 block text-sm font-medium">
                Temperature: {config.temperature.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={config.temperature}
                onChange={(e) => updateConfig({ temperature: parseFloat(e.target.value) })}
                className="w-full"
              />
              <div className="mt-1 flex justify-between text-xs text-muted-foreground">
                <span>稳定</span>
                <span>创造性</span>
              </div>
            </div>

            {/* Top-P */}
            <div>
              <label className="mb-2 block text-sm font-medium">
                Top-P: {config.top_p.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={config.top_p}
                onChange={(e) => updateConfig({ top_p: parseFloat(e.target.value) })}
                className="w-full"
              />
              <div className="mt-1 flex justify-between text-xs text-muted-foreground">
                <span>精确</span>
                <span>多样</span>
              </div>
            </div>
          </div>
        </div>

        {/* 右侧：预览 */}
        {showPreview && (
          <div className="rounded-lg border bg-muted/50 p-4">
            <h3 className="mb-3 text-sm font-semibold">提示词预览</h3>
            <pre className="whitespace-pre-wrap rounded bg-background p-3 text-xs">
              {previewPrompt}
            </pre>
          </div>
        )}
      </div>

      {/* 底部按钮 */}
      <div className="flex justify-end border-t pt-4">
        <button
          onClick={handleNext}
          className="flex items-center gap-2 rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          下一步
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
