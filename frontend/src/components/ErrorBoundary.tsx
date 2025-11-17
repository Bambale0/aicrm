import React, { Component, ErrorInfo, ReactNode } from 'react';
import { ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import Button from './ui/Button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo
    });

    // Log error to monitoring service
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Here you could send error to monitoring service like Sentry
    // logErrorToService(error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen flex items-center justify-center p-4">
          <div className="max-w-md w-full">
            <div className="card text-center">
              <div className="flex justify-center mb-4">
                <ExclamationTriangleIcon className="w-16 h-16 text-red-500" />
              </div>

              <h2 className="text-xl font-bold text-white mb-2">
                Что-то пошло не так
              </h2>

              <p className="text-gray-400 mb-6">
                Произошла неожиданная ошибка. Попробуйте перезагрузить страницу или повторить действие.
              </p>

              <div className="space-y-3">
                <Button
                  onClick={this.handleRetry}
                  variant="primary"
                  fullWidth
                >
                  <ArrowPathIcon className="w-4 h-4 mr-2" />
                  Повторить
                </Button>

                <Button
                  onClick={this.handleReload}
                  variant="secondary"
                  fullWidth
                >
                  Перезагрузить страницу
                </Button>
              </div>

              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-6 text-left">
                  <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-400">
                    Детали ошибки (для разработчиков)
                  </summary>
                  <pre className="mt-2 text-xs bg-gray-800 p-3 rounded overflow-auto max-h-40">
                    {this.state.error.toString()}
                    {this.state.errorInfo?.componentStack}
                  </pre>
                </details>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
