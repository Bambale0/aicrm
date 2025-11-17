import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import BackgroundStars from '../components/BackgroundVideo';

const Login: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (isLogin) {
        await login(email, password);
        navigate('/dashboard');
      } else {
        await register(username, password, email);
        navigate('/dashboard');
      }
    } catch (error: any) {
      let errorMessage = 'Произошла ошибка';

      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (Array.isArray(detail)) {
          // Обработка массива ошибок валидации
          errorMessage = detail.map((err: any) => err.msg || err.message).join(', ');
        } else if (detail.msg) {
          errorMessage = detail.msg;
        }
      }

      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      <BackgroundStars />

      <div className="min-h-screen flex items-center justify-center p-4 relative z-10">
        <div className="w-full max-w-md space-y-8">
          <div className="text-center">
            <img
              src="/лого.png"
              alt="AI CRM Logo"
              className="w-20 h-auto max-h-20 object-contain drop-shadow-2xl mx-auto mb-8"
            />
            <h2 className="text-3xl sm:text-4xl font-bold text-gradient mb-2">
              {isLogin ? 'Вход в систему' : 'Регистрация'}
            </h2>
            <p className="text-van-gogh-wheat-field text-lg font-medium">
              AI CRM система управления
            </p>
          </div>

          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="card p-8">
              {!isLogin && (
                <div className="mb-6">
                  <label htmlFor="username" className="block text-sm font-semibold text-van-gogh-wheat-field mb-3">
                    Имя пользователя
                  </label>
                  <input
                    id="username"
                    name="username"
                    type="text"
                    required={!isLogin}
                    className="input-field text-lg"
                    placeholder="Имя пользователя"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                  />
                </div>
              )}

              <div className="mb-6">
                <label htmlFor="email-address" className="block text-sm font-semibold text-van-gogh-wheat-field mb-3">
                  Email
                </label>
                <input
                  id="email-address"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  className="input-field text-lg"
                  placeholder="your@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>

              <div className="mb-6">
                <label htmlFor="password" className="block text-sm font-semibold text-van-gogh-wheat-field mb-3">
                  Пароль
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  className="input-field text-lg"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            {error && (
              <div className="bg-van-gogh-vermilion/20 backdrop-blur-sm border-2 border-van-gogh-vermilion/50 text-van-gogh-vermilion px-6 py-4 rounded-xl text-sm text-center font-medium shadow-lg flex items-center justify-center">
                <svg className="w-5 h-5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full flex justify-center items-center disabled:opacity-50 disabled:cursor-not-allowed text-lg py-4 px-8 rounded-xl font-semibold shadow-2xl transform hover:scale-105 transition-all duration-300"
            >
              {isLoading && <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-3" />}
              {isLoading ? 'Загрузка...' : (isLogin ? '🚀 Войти' : '✨ Зарегистрироваться')}
            </button>

            <div className="text-center">
              <button
                type="button"
                onClick={() => setIsLogin(!isLogin)}
                className="text-van-gogh-cadmium-yellow hover:text-van-gogh-vermilion text-base font-medium transition-all duration-300 hover:scale-105 transform"
              >
                {isLogin ? '🎨 Нет аккаунта? Зарегистрироваться' : '🎭 Уже есть аккаунт? Войти'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
