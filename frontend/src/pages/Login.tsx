import React, { useState } from 'react';
import { BuildingOffice2Icon, LockClosedIcon } from '@heroicons/react/24/outline';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const REGISTRATION_ENABLED = process.env.REACT_APP_ENABLE_REGISTRATION === 'true';

const Login: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const routeState = location.state as any;
  const returnTo = routeState?.from?.pathname || '/dashboard';
  const authReason = routeState?.reason;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (isLogin) {
        await login(email, password);
        navigate(returnTo, { replace: true });
      } else {
        if (!REGISTRATION_ENABLED) {
          setError('Регистрация временно отключена');
          return;
        }
        await register(fullName, password, email, companyName);
        setIsLogin(true);
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Не удалось выполнить вход');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-10">
      <div className="mx-auto flex min-h-[80vh] max-w-md items-center">
        <div className="w-full">
          <div className="mb-7 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600 text-white shadow-sm">
              <BuildingOffice2Icon className="h-8 w-8" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900">ЖКХ CRM</h1>
            <p className="mt-2 text-sm text-slate-500">Система управления заявками управляющей компании</p>
          </div>

          <form onSubmit={handleSubmit} className="card space-y-5 p-6 sm:p-8">
            {authReason && (
              <div className="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">
                {authReason === 'expired'
                  ? 'Сессия администратора истекла. Войдите снова — после входа вы вернётесь на нужную страницу.'
                  : 'Войдите как администратор, чтобы открыть настройки CRM.'}
              </div>
            )}
            <div>
              <h2 className="text-xl font-semibold text-slate-900">{isLogin ? 'Вход в систему' : 'Регистрация'}</h2>
              <p className="mt-1 text-sm text-slate-500">Введите данные учетной записи сотрудника</p>
            </div>

            {!isLogin && (
              <>
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">ФИО</label>
                  <input className="input-field" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">Организация</label>
                  <input className="input-field" value={companyName} onChange={(e) => setCompanyName(e.target.value)} required />
                </div>
              </>
            )}

            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">Email</label>
              <input
                className="input-field"
                type="email"
                autoComplete="email"
                placeholder="name@company.ru"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">Пароль</label>
              <div className="relative">
                <LockClosedIcon className="pointer-events-none absolute left-3 top-3 h-5 w-5 text-slate-400" />
                <input
                  className="input-field pl-10"
                  type="password"
                  autoComplete="current-password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            {error && <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

            <button type="submit" disabled={isLoading} className="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-60">
              {isLoading ? 'Выполняем вход…' : isLogin ? 'Войти' : 'Зарегистрироваться'}
            </button>

            {REGISTRATION_ENABLED && (
              <button
                type="button"
                onClick={() => setIsLogin((value) => !value)}
                className="w-full text-center text-sm font-medium text-blue-600 hover:text-blue-700"
              >
                {isLogin ? 'Нет аккаунта? Зарегистрироваться' : 'Уже есть аккаунт? Войти'}
              </button>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
