/**
 * 控制台主布局
 * 侧边栏 + 内容区
 */

import { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
  Bot,
  Database,
  Users,
  Settings,
  LogOut,
  Menu,
  X,
  MessageSquare,
  ChevronDown,
  User,
  Network,
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@workspace/ui/lib/utils';

const navItems = [
  { to: '/console/chat', icon: MessageSquare, label: '对话', end: true },
  { to: '/console/agents', icon: Bot, label: 'Agent' },
  { to: '/console/agent-teams', icon: Network, label: 'Agent团队' },
  { to: '/console/knowledge', icon: Database, label: '知识库' },
  { to: '/console/teams', icon: Users, label: '团队' },
  { to: '/console/settings', icon: Settings, label: '设置' },
];

export function ConsoleLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-background">
      {/* 侧边栏 */}
      <aside
        className={cn(
          'flex h-full flex-col border-r bg-card transition-all duration-300',
          sidebarOpen ? 'w-64' : 'w-16'
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center justify-between border-b px-4">
          {sidebarOpen && (
            <span className="text-xl font-bold text-primary">AgentNex</span>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="rounded-md p-2 hover:bg-accent"
          >
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {/* 导航菜单 */}
        <nav className="flex-1 space-y-1 p-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }: { isActive: boolean }) =>
                cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )
              }
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {sidebarOpen && <span>{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* 用户信息 */}
        <div className="border-t p-2">
          <div className="relative">
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className={cn(
                'flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm hover:bg-accent',
                !sidebarOpen && 'justify-center'
              )}
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground">
                <User className="h-4 w-4" />
              </div>
              {sidebarOpen && (
                <>
                  <div className="flex-1 truncate text-left">
                    <div className="truncate font-medium">{user?.name || user?.email}</div>
                    <div className="text-xs text-muted-foreground">{user?.role}</div>
                  </div>
                  <ChevronDown className="h-4 w-4 shrink-0" />
                </>
              )}
            </button>

            {/* 下拉菜单 */}
            {userMenuOpen && sidebarOpen && (
              <div className="absolute bottom-full left-0 right-0 mb-1 rounded-md border bg-popover p-1 shadow-lg">
                <button
                  onClick={() => {
                    setUserMenuOpen(false);
                    navigate('/console/settings');
                  }}
                  className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent"
                >
                  <Settings className="h-4 w-4" />
                  设置
                </button>
                <button
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-destructive hover:bg-accent"
                >
                  <LogOut className="h-4 w-4" />
                  登出
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* 主内容区 */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
