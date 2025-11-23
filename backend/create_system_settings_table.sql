-- Миграция для создания таблицы system_settings
-- Выполнить после развертывания новых моделей

CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    site_name VARCHAR(255) NOT NULL DEFAULT 'AICRM',
    site_description TEXT,
    admin_email VARCHAR(255),
    support_email VARCHAR(255),

    -- Настройки безопасности
    session_timeout_minutes INTEGER NOT NULL DEFAULT 60,
    max_login_attempts INTEGER NOT NULL DEFAULT 5,
    lockout_duration_minutes INTEGER NOT NULL DEFAULT 15,
    password_min_length INTEGER NOT NULL DEFAULT 8,
    require_2fa BOOLEAN DEFAULT FALSE,

    -- Настройки мониторинга
    enable_monitoring BOOLEAN DEFAULT TRUE,
    monitoring_interval_seconds INTEGER DEFAULT 60,
    alert_email_enabled BOOLEAN DEFAULT TRUE,
    performance_thresholds JSONB,

    -- Настройки логирования
    log_level VARCHAR(50) DEFAULT 'INFO',
    log_retention_days INTEGER DEFAULT 30,
    enable_audit_log BOOLEAN DEFAULT TRUE,

    -- Настройки кэширования
    redis_enabled BOOLEAN DEFAULT TRUE,
    redis_host VARCHAR(255) DEFAULT 'localhost',
    redis_port INTEGER DEFAULT 6379,
    cache_ttl_seconds INTEGER DEFAULT 3600,

    -- Email SMTP настройки
    smtp_enabled BOOLEAN DEFAULT FALSE,
    smtp_host VARCHAR(255),
    smtp_port INTEGER DEFAULT 587,
    smtp_user VARCHAR(255),
    smtp_password TEXT,  -- Зашифрованный
    smtp_use_tls BOOLEAN DEFAULT TRUE,
    smtp_use_ssl BOOLEAN DEFAULT FALSE,
    smtp_from_email VARCHAR(255),
    smtp_from_name VARCHAR(255),

    -- Telegram настройки
    telegram_enabled BOOLEAN DEFAULT FALSE,
    telegram_bot_token TEXT,  -- Зашифрованный
    telegram_chat_id VARCHAR(255),
    telegram_webhook_url VARCHAR(500),
    telegram_notification_enabled BOOLEAN DEFAULT TRUE,

    -- Настройки уведомлений
    notifications_enabled BOOLEAN DEFAULT TRUE,
    email_notifications_enabled BOOLEAN DEFAULT TRUE,
    websocket_notifications_enabled BOOLEAN DEFAULT TRUE,
    push_notifications_enabled BOOLEAN DEFAULT FALSE,

    -- Настройки бэкапа
    auto_backup_enabled BOOLEAN DEFAULT TRUE,
    backup_frequency_hours INTEGER DEFAULT 24,
    backup_retention_days INTEGER DEFAULT 7,
    backup_path VARCHAR(500),

    -- Настройки обновлений
    auto_update_enabled BOOLEAN DEFAULT FALSE,
    update_check_frequency_hours INTEGER DEFAULT 24,
    update_channel VARCHAR(50) DEFAULT 'stable',

    -- Метки времени
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_system_settings_site_name ON system_settings(site_name);
CREATE INDEX IF NOT EXISTS idx_system_settings_created_at ON system_settings(created_at);

-- Триггер для обновления updated_at
CREATE OR REPLACE FUNCTION update_system_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER system_settings_updated_at_trigger
    BEFORE UPDATE ON system_settings
    FOR EACH ROW EXECUTE FUNCTION update_system_settings_updated_at();

-- Вставляем настройки по умолчанию
INSERT INTO system_settings (
    site_name, site_description,
    session_timeout_minutes, max_login_attempts, lockout_duration_minutes, password_min_length,
    enable_monitoring, monitoring_interval_seconds, alert_email_enabled,
    log_level, log_retention_days, enable_audit_log,
    redis_enabled, redis_host, redis_port, cache_ttl_seconds,
    notifications_enabled, email_notifications_enabled, websocket_notifications_enabled, push_notifications_enabled,
    auto_backup_enabled, backup_frequency_hours, backup_retention_days,
    auto_update_enabled, update_check_frequency_hours, update_channel
) VALUES (
    'AICRM',
    'AI-powered Communication Relationship Manager',
    60, 5, 15, 8,
    TRUE, 60, TRUE,
    'INFO', 30, TRUE,
    TRUE, 'localhost', 6379, 3600,
    TRUE, TRUE, TRUE, FALSE,
    TRUE, 24, 7,
    FALSE, 24, 'stable'
) ON CONFLICT DO NOTHING;

-- Комментарий к таблице
COMMENT ON TABLE system_settings IS 'Глобальные системные настройки приложения';
COMMENT ON COLUMN system_settings.performance_thresholds IS 'Пороги производительности в формате JSON: {"cpu_percent": 80, "memory_percent": 85}';
