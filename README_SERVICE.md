# AI CRM System - SystemD Service Deployment

## Описание
Этот файл содержит инструкции по установке и управлению AI CRM системы как systemd сервиса.

## Установка сервиса

### 1. Скопировать сервис файл
```bash
sudo cp aicrm.service /etc/systemd/system/
```

### 2. Перезагрузить systemd
```bash
sudo systemctl daemon-reload
```

### 3. Запустить сервис
```bash
sudo systemctl start aicrm
```

### 4. Включить автозапуск при загрузке системы
```bash
sudo systemctl enable aicrm
```

### 5. Проверить статус
```bash
sudo systemctl status aicrm
```

## Управление сервисом

### Просмотр логов
```bash
# Просмотр последних логов
sudo journalctl -u aicrm -f

# Просмотр логов за последний час
sudo journalctl -u aicrm --since "1 hour ago"
```

### Остановка сервиса
```bash
sudo systemctl stop aicrm
```

### Перезапуск сервиса
```bash
sudo systemctl restart aicrm
```

## Мониторинг

### Проверка работоспособности
```bash
curl http://localhost:8001/ping
curl http://localhost:8001/health
```

## Безопасность

### Рекомендации
1. Измените пользователя с `root` на dedicated пользователя
2. Настройте firewall для ограничения доступа к порту 8001
3. Используйте HTTPS в продакшене
