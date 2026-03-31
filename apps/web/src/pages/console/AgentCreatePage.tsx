/**
 * Agent 创建页面入口
 * 4步分步向导表单
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AgentCreateWizard } from '@/components/agent/AgentCreateWizard';
import type { AgentConfig } from '@/types';
import { createAgent, saveDraft } from '@/api/agents';
import { ArrowLeft, Save } from 'lucide-react';

export function AgentCreatePage() {
  const navigate = useNavigate();
  const [isSaving, setIsSaving] = useState(false);

  // 保存草稿
  const handleSaveDraft = async (config: AgentConfig) => {
    setIsSaving(true);
    try {
      await saveDraft(config);
      alert('草稿保存成功！');
    } catch (error) {
      console.error('Failed to save draft:', error);
      alert('保存草稿失败');
    } finally {
      setIsSaving(false);
    }
  };

  // 发布 Agent
  const handlePublish = async (config: AgentConfig) => {
    setIsSaving(true);
    try {
      const result = await createAgent(config);
      alert(`Agent "${result.name}" 创建成功！`);
      navigate(`/console/agents/${result.agent_id}`);
    } catch (error) {
      console.error('Failed to create agent:', error);
      alert('创建 Agent 失败');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* 头部 */}
      <header className="flex items-center justify-between border-b px-6 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/console/agents')}
            className="rounded-md p-2 hover:bg-accent"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold">创建 Agent</h1>
            <p className="text-sm text-muted-foreground">配置您的智能助手</p>
          </div>
        </div>
        <button
          onClick={() => {
            // 触发保存草稿
            const wizardEl = document.querySelector('[data-wizard]');
            if (wizardEl) {
              wizardEl.dispatchEvent(new CustomEvent('save-draft'));
            }
          }}
          disabled={isSaving}
          className="flex items-center gap-2 rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent disabled:opacity-50"
        >
          <Save className="h-4 w-4" />
          {isSaving ? '保存中...' : '暂存草稿'}
        </button>
      </header>

      {/* 向导内容 */}
      <div className="flex-1 overflow-auto p-6">
        <AgentCreateWizard
          onSaveDraft={handleSaveDraft}
          onPublish={handlePublish}
          isSaving={isSaving}
        />
      </div>
    </div>
  );
}
