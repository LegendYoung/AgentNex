import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { Button } from '@workspace/ui/components/button';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
        return (
            <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
                <div className="max-w-md rounded-lg border bg-card p-6 text-center shadow-lg">
                    <h2 className="mb-4 text-2xl font-bold text-destructive">应用加载失败</h2>
                    <p className="mb-4 text-muted-foreground">
                        很抱歉，应用遇到了一个错误。请尝试刷新页面。
                    </p>
                    <p className="mb-6 text-sm text-muted-foreground">
                        错误信息: {this.state.error?.message || "未知错误"}
                    </p>
                    <Button onClick={this.handleReset} variant="default">
                        刷新页面
                    </Button>
                </div>
            </div>
        );
    }

    return this.props.children;
  }
}