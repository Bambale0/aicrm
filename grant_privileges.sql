-- Предоставление прав пользователю aicrm_user на таблицу users
-- Выполнить как superuser (postgres или другой администратор)

-- Сделать пользователя владельцем таблицы users
ALTER TABLE users OWNER TO aicrm_user;

-- Или предоставить права на изменение структуры таблицы:
-- GRANT ALL PRIVILEGES ON TABLE users TO aicrm_user;
-- GRANT USAGE ON SCHEMA public TO aicrm_user;

-- Проверка владельца таблицы
-- SELECT schemaname, tablename, tableowner
-- FROM pg_tables
-- WHERE tablename = 'users';
