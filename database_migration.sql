-- Миграция базы данных: Добавление полей для верификации email и названия компании
-- Выполнить эти команды в PostgreSQL как пользователь с правами администратора

-- Добавить поле для названия компании
ALTER TABLE users ADD COLUMN IF NOT EXISTS company_name VARCHAR(255);

-- Добавить поля для верификации email
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_expires TIMESTAMP;

-- Комментарии к полям (опционально)
COMMENT ON COLUMN users.company_name IS 'Название компании пользователя';
COMMENT ON COLUMN users.email_verified IS 'Флаг подтверждения email адреса';
COMMENT ON COLUMN users.email_verification_token IS 'Токен для верификации email';
COMMENT ON COLUMN users.email_verification_expires IS 'Срок действия токена верификации';

-- Проверка: Просмотр структуры таблицы после миграции
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'users'
-- ORDER BY ordinal_position;
