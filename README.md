# Руководство по развертыванию SIZ Manager

## Требования к системе
- Docker 20.10.17+
- Docker Compose 2.3.0+
- 1 ГБ оперативной памяти
- 5 ГБ свободного места на диске

## Конфигурация окружения
1. Создайте файл `.env` в корне проекта:
```bash
SECRET_KEY=сгенерируйте_ключ_openssl_rand_-hex_32
DJANGO_DEBUG=False
ALLOWED_HOSTS=localhost,web
CSRF_TRUSTED_ORIGINS=http://localhost,http://web,
```

## Развертывание для Linux
```bash
# Создайте необходимые директории
mkdir -p data staticfiles media backups

# Запустите сервисы
docker compose up -d --build

# Создайте миграции
docker compose exec web python manager/manage.py makemigrations

# Примените миграции
docker compose exec web python manager/manage.py migrate

# Создайте суперпользователя
docker compose exec web python manager/manage.py createsuperuser
```

## Развертывание для Windows (PowerShell)
```powershell
# Создайте директории
New-Item -ItemType Directory -Force -Path data,staticfiles,media,backups

# Запустите сервисы
docker compose up -d --build

# Создайте миграции
docker compose exec web python manager/manage.py makemigrations

# Выполните миграции
docker compose exec web python manager/manage.py migrate

# Создайте администратора
docker compose exec web python manager/manage.py createsuperuser
```

## Особенности SQLite
1. Файл БД хранится в `./data/db.sqlite3`
2. Резервное копирование выполняется ежедневно в 02:00 UTC
3. Для ручного бэкапа:
```bash
docker compose exec web /app/backups/backup_db.sh
```

## Ключевые команды
```bash
# Просмотр логов приложения
docker compose logs -f web

# Пересборка контейнеров
docker compose down && docker compose up -d --build

# Очистка устаревших данных
docker compose exec web python manage.py clearsessions
```

## Безопасность
1. Всегда устанавливайте `DJANGO_DEBUG=False` в продакшене
2. Регулярно обновляйте SECRET_KEY
3. Ограничьте доступ к портам 8000 и 80

## Структура проекта
```
siz_manager/
├── data/           # Директория SQLite баз данных
├── backups/        # Резервные копии БД
├── media/          # Загружаемые файлы
├── staticfiles/    # Собранные статические файлы
└── manager/        # Исходный код приложения
```

## Мониторинг
```bash
# Проверка здоровья приложения
curl http://localhost:8000/health/

# Статус cron задач
docker compose exec web tail -f /var/log/cron.log
```

## Обновление версии
```bash
docker compose down
git pull origin main
docker compose up -d --build
docker compose exec web python manage.py migrate
```

## Устранение неполадок
```bash
# Восстановление из бэкапа
docker compose exec web cp /app/backups/latest.sqlite3 /app/data/db.sqlite3

# Пересоздание индексов
docker compose exec web python manage.py reindex
