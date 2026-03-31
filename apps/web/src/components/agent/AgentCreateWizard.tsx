/**
 * Agent 创建向导组件
 * 4步分步表单
 */

import { useState, useEffect } from 'react';
import { cn } from '@workspace/ui/lib/utils';
import type { AgentConfig } from '@/types';
import { StepBasicConfig } from './StepBasicConfig';
import { StepCapabilities } from './StepCapabilities';
import { StepTest } from './StepTest';
import { StepPublish } from './StepPublish';
import { Check } from 'lucide-react';

const STEPS = [
  { id: 1, name: '基础配置', description: '名称、描述、模型设置' },
  { id: 2, name: '能力开关', description: '记忆、知识库、工具' },
  { id: 3, name: '实时测试', description: '测试 Agent 效果' },
  { id: 4, name: '发布确认', description: '权限配置、发布' },
];

// 默认配置
const DEFAULT_CONFIG: AgentConfig = {
  name: '',
  description: '',
  avatar_url: '',
  system_prompt: '',
  model_id: 'qwen-plus',
  temperature: 0.7,
  top_p: 0.9,
  enable_memory: false,
  memory_type: 'short_term',
  memory_window: 10,
  enable_knowledge: false,
  knowledge_base_ids: [],
  enable_tools: false,
  tool_config: {
    web_search: false,
    file_read: false,
    python_exec: false,
    permission: 'all',
  },
  is_public: false,
  team_permissions: [],
};

interface AgentCreateWizardProps {
  onSaveDraft: (config: AgentConfig) => void;
  onPublish: (config: AgentConfig) => void;
  isSaving: boolean;
  initialConfig?: AgentConfig;
}

export function AgentCreateWizard({
  onSaveDraft,
  onPublish,
  isSaving,
  initialConfig,
}: AgentCreateWizardProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [config, setConfig] = useState<AgentConfig>(initialConfig || DEFAULT_CONFIG);
  const [testSessionId, setTestSessionId] = useState<string>();

  // 监听保存草稿事件
  useEffect(() => {
    const wizardEl = document.querySelector('[data-wizard]');
    if (!wizardEl) return;

    const handleSaveDraft = () => {
      onSaveDraft(config);
    };

    wizardEl.addEventListener('save-draft', handleSaveDraft);
    return () => {
      wizardEl.removeEventListener('save-draft', handleSaveDraft);
    };
  }, [config, onSaveDraft]);

  // 更新配置
  const updateConfig = (updates: Partial<AgentConfig>) => {
    setConfig((prev) => ({ ...prev, ...updates }));
  };

  // 下一步
  const nextStep = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
    }
  };

  // 上一步
  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  // 发布
  const handlePublish = () => {
    onPublish(config);
  };

  return (
    <div data-wizard className="mx-auto max-w-5xl">
      {/* 步骤指示器 */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {STEPS.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    'flex h-10 w-10 items-center justify-center rounded-full border-2 transition-colors',
                    currentStep === step.id
                      ? 'border-primary bg-primary text-primary-foreground'
                      : currentStep > step.id
                        ? 'border-primary bg-primary text-primary-foreground'
                        : 'border-muted-foreground/30 text-muted-foreground'
                  )}
                >
                  {currentStep > step.id ? (
                    <Check className="h-5 w-5" />
                  ) : (
                    <span className="text-sm font-semibold">{step.id}</span>
                  )}
                </div>
                <div className="mt-2 text-center">
                  <div
                    className={cn(
                      'text-sm font-medium',
                      currentStep === step.id ? 'text-foreground' : 'text-muted-foreground'
                    )}
                  >
                    {step.name}
                  </div>
                  <div className="text-xs text-muted-foreground">{step.description}</div>
                </div>
              </div>
              {index < STEPS.length - 1 && (
                <div
                  className={cn(
                    'mx-4 h-0.5 w-16',
                    currentStep > step.id ? 'bg-primary' : 'bg-muted-foreground/30'
                  )}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 步骤内容 */}
      <div className="rounded-lg border bg-card p-6">
        {currentStep === 1 && (
          <StepBasicConfig
            config={config}
            updateConfig={updateConfig}
            onNext={nextStep}
          />
        )}
        {currentStep === 2 && (
          <StepCapabilities
            config={config}
            updateConfig={updateConfig}
            onNext={nextStep}
            onPrev={prevStep}
          />
        )}
        {currentStep === 3 && (
          <StepTest
            config={config}
            sessionId={testSessionId}
            setSessionId={setTestSessionId}
            onNext={nextStep}
            onPrev={prevStep}
          />
        )}
        {currentStep === 4 && (
          <StepPublish
            config={config}
            updateConfig={updateConfig}
            onPublish={handlePublish}
            onPrev={prevStep}
            isSaving={isSaving}
          />
        )}
      </div>
    </div>
  );
}
