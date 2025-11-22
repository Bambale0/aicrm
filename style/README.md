# 🎨 СТИЛЬ AI CRM - КОМПЛЕКТ ДЛЯ НОВЫХ ПРОЕКТОВ

## 📦 Что содержится в папке style/

Этот комплект содержит полный набор стилей, компонентов и конфигураций React/TypeScript приложения AI CRM системы для быстрого создания новых сайтов с тем же дизайном.

## 🗂️ Структура

```
style/
├── components/          # Реактивные компоненты
│   ├── ErrorBoundary.tsx       # Обработка ошибок
│   └── ui/                     # Базовые UI компоненты
├── contexts/            # React Context поставщики
│   └── AuthContext.tsx         # Контекст аутентификации
├── hooks/               # Кастомные React хуки
│   └── usePullToRefresh.ts     # Pull-to-refresh функционал
├── services/            # API и другие сервисы
│   └── api.ts                  # Полный API клиент с интерсепторами
├── types/               # TypeScript объявления
│   └── heroicons.d.ts          # Типы для Heroicons
├── index.css             # Основные CSS стили (Tailwind)
├── package.json          # Зависимости проекта
├── tailwind.config.js    # Конфигурация Tailwind CSS
├── tsconfig.json         # Конфигурация TypeScript
└── postcss.config.js     # Конфигурация PostCSS
```

## 🚀 Быстрый старт нового проекта

### 1. Создать новый проект
```bash
npx create-react-app my-new-project --template typescript
cd my-new-project
```

### 2. Установить зависимости
```bash
npm install @heroicons/react lucide-react axios @tailwindcss/postcss postcss react-router-dom
```

### 3. Скопировать файлы стиля
```bash
# Копировать все файлы из style/
cp -r /path/to/style/* ./src/

# Переместить package.json в корень если нужно
cp src/package.json ./
npm install
```

### 4. Настроить Tailwind CSS
```bash
# Установить Tailwind
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Скопировать конфигурацию
cp src/tailwind.config.js ./
cp src/postcss.config.js ./
```

### 5. Импортировать стили
```javascript
// src/index.tsx
import './index.css';  // Важно импортировать первым
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <BrowserRouter>
    <App />
  </BrowserRouter>
);
```

## 🎨 Дизайн-система

### Цветовая палитра
```css
/* Основные цвета */
--primary: #2563eb (blue-600)
--secondary: #f3f4f6 (gray-100)
--accent: #4f46e5 (indigo-600)
--danger: #dc2626 (red-600)
--success: #16a34a (green-600)
--warning: #f59e0b (amber-500)

/* Серые оттенки */
--gray-50: #f9fafb
--gray-100: #f3f4f6
--gray-200: #e5e7eb
--gray-300: #d1d5db
--gray-400: #9ca3af
--gray-500: #6b7280
--gray-600: #4b5563
--gray-700: #374151
--gray-800: #1f2937
--gray-900: #111827
```

### Типографика
```css
/* Заголовки */
h1: text-3xl font-bold text-gray-900
h2: text-2xl font-bold text-gray-900
h3: text-lg font-medium text-gray-900

/* Основной текст */
body: text-base text-gray-700 leading-relaxed
small: text-sm text-gray-500

/* Кнопки */
.btn-primary: bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg
.btn-secondary: bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg
.btn-danger: bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg
```

### Компоненты интерфейса

#### Кнопки (Button.tsx)
```jsx
<Button variant="primary" size="md" disabled={loading}>
  Создать
</Button>

<Button variant="outline" size="sm" onClick={handleCancel}>
  Отмена
</Button>
```

#### Модальные окна
```jsx
const [showModal, setShowModal] = useState(false);

{showModal && (
  <Modal onClose={() => setShowModal(false)}>
    <h3>Подтверждение действия</h3>
    <p>Вы уверены?</p>
    <div className="flex mt-4">
      <Button onClick={handleConfirm}>Да</Button>
      <Button variant="secondary" onClick={() => setShowModal(false)}>
        Отмена
      </Button>
    </div>
  </Modal>
)}
```

#### Настраничная навигация
```jsx
const [currentPage, setCurrentPage] = useState(1);
const totalPages = Math.ceil(totalItems / itemsPerPage);

<Pagination
  currentPage={currentPage}
  totalPages={totalPages}
  onPageChange={setCurrentPage}
/>
```

#### Лоадеры
```jsx
// Спиннер загрузки
<div className="flex justify-center items-center h-64">
  <Spinner size="lg" />
</div>

// Скелетоны
<div className="space-y-4">
  <Skeleton className="h-4 w-full" />
  <Skeleton className="h-4 w-3/4" />
  <Skeleton className="h-4 w-1/2" />
</div>
```

### Иконки

Все иконки доступны через Heroicons:

```jsx
import {
  HomeIcon,
  UserIcon,
  CogIcon,
  PlusIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

<HomeIcon className="w-6 h-6" />
```

## 🔧 API Интеграция

### Настройка API клиента
```javascript
// services/api.ts уже содержит полную настройку
import { apiService } from '../services/api';

// Пример использования
const loadUsers = async () => {
  try {
    const users = await apiService.getUsers();
    setUsers(users);
  } catch (error) {
    alert('Ошибка загрузки пользователей');
  }
};
```

### Аутентификация
```jsx
import { AuthContext } from '../contexts/AuthContext';

const { user, login, logout } = useContext(AuthContext);

// Логин
await login({ email, password });

// Проверка аутентификации
if (!user) {
  return <Navigate to="/login" />;
}
```

## 📱 Адаптивный дизайн

Все компоненты адаптивны из коробки благодаря Tailwind CSS:

```jsx
// Для мобильных устройств
<div className="block md:hidden">
  Мобильная версия
</div>

<div className="hidden md:block lg:hidden">
  Медиум версия
</div>

<div className="hidden lg:block">
  Широкоэкранная версия
</div>

// Грид с автоматической адаптацией
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Колонки автоматически адаптируются */}
</div>
```

## 🎯 Паттерны использования

### 1. Формы с валидацией
```jsx
const [formData, setFormData] = useState({
  name: '',
  email: '',
  password: ''
});

const [errors, setErrors] = useState({});

const handleSubmit = async (e) => {
  e.preventDefault();

  // Валидация
  if (!formData.name) {
    setErrors({ name: 'Имя обязательно' });
    return;
  }

  try {
    await apiService.createUser(formData);
    alert('Пользователь создан!');
  } catch (error) {
    setErrors({ general: 'Ошибка создания пользователя' });
  }
};

return (
  <form onSubmit={handleSubmit} className="space-y-4">
    <InputField
      label="Имя"
      value={formData.name}
      onChange={(value) => setFormData({...formData, name: value})}
      error={errors.name}
    />
    <Button type="submit">Создать</Button>
  </form>
);
```

### 2. Работа со списками
```jsx
const [items, setItems] = useState([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
  loadItems();
}, []);

const loadItems = async () => {
  setLoading(true);
  try {
    const data = await apiService.getItems();
    setItems(data);
  } finally {
    setLoading(false);
  }
};

if (loading) {
  return <Spinner />;
}

return (
  <div className="space-y-4">
    {items.map(item => (
      <ItemCard
        key={item.id}
        item={item}
        onUpdate={loadItems}
      />
    ))}
  </div>
);
```

### 3. Обработка ошибок
```jsx
const [error, setError] = useState(null);

try {
  await someAsyncOperation();
} catch (err) {
  setError('Произошла ошибка. Попробуйте еще раз.');
}

// В компоненте
{error && (
  <Alert variant="error" onClose={() => setError(null)}>
    {error}
  </Alert>
)}
```

## 🛠️ Разработка и деплой

### Локальная разработка
```bash
npm start
```

### Проверка типов
```bash
npm run type-check
```

### Сборка для продакшена
```bash
npm run build
```

### Запуск линтера
```bash
npm run lint
```

## 📋 Чеклист нового проекта

- [ ] Создан новый проект с TypeScript
- [ ] Установлены все зависимости из style/package.json
- [ ] Скопированы все файлы из style/ в src/
- [ ] Настроен Tailwind CSS
- [ ] Импортированы стили в index.tsx
- [ ] Настроен роутинг с React Router
- [ ] Проведены все точки входа (routes)
- [ ] Проверена адаптивность
- [ ] Запущены тесты (если есть)
- [ ] Произведена сборка для продакшена

## 🎊 Готово!

Теперь у вас есть полный набор инструментов для создания сайтов в едином стиле с AI CRM системой. Все компоненты протестированы и готовы к использованию!

Примечание: Этот комплект оптимизирован для быстрого старта новых проектов и поддерживает современные практик разработки React приложений.
