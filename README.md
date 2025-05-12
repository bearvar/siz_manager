# Руководство по развертыванию SIZ Manager

## Конфигурация окружения
1. Создайте файл `.env.prod` в корне проекта:
```bash
DEBUG=0
ALLOWED_HOSTS='*'
SQLITE_DB_PATH=/app/manager/data/db.sqlite3
DJANGO_SETTINGS_MODULE="manager.settings"
CSRF_TRUSTED_ORIGINS=http://123.123.123.123
CSRF_COOKIE_SECURE=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SAMESITE=Lax
SESSION_COOKIE_SAMESITE=Lax
```
В CSRF_TRUSTED_ORIGINS должен быть указан IP сервера на котором будет развернут проект.
Также нужно добавить SECRET_KEY в этот файл. Его можно сгенерировать через командную строку.
Для linux:
```bash
echo "SECRET_KEY=$(openssl rand -base64 64 | tr -d '\n')" >> .env.prod
```
Для windows:
  Используя OpenSSL (если установлен):
```powershell
echo "SECRET_KEY=$(openssl rand -base64 64)" >> .env.prod
```
  Или чистый PowerShell:
```powershell
$bytes = New-Object Byte[] 64
[Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($bytes)
$secret = [Convert]::ToBase64String($bytes)
echo "SECRET_KEY=$secret" >> .env.prod
```

## Развертывание
```bash
# Создайте необходимые директории и задайте им права доступа
# Команды для Linux:
mkdir -p data static media backups
chown -R 1000:1000 data static media backups
# Команды для Windows:
mkdir data static media backups
icacls data static media backups /grant "%username%":(F) /T

# Разместить в папке проекта файлы `docker-compose.prod.yml` и `nginx-prod.conf`.

# Скачать образ приложения
docker compose -f docker-compose.prod.yml pull

# Запустите сервисы
docker compose -f docker-compose.prod.yml up -d

# Создайте миграции
docker compose -f docker-compose.prod.yml exec web python manager/manage.py makemigrations core users

# Примените миграции
docker compose -f docker-compose.prod.yml exec web python manager/manage.py migrate

# Создайте суперпользователя (после выполнения команды следуйте подсказам контекстного меню)
docker compose -f docker-compose.prod.yml exec web python manager/manage.py createsuperuser
```


## Ключевые команды
```bash
# Просмотр логов приложения
docker compose -f docker-compose.prod.yml logs web --tail=100 -f

# Просмотр логов прокси
docker compose -f docker-compose.prod.yml logs nginx --tail=100 -f

# Остановка контейнеров
docker compose -f docker-compose.prod.yml stop

# Запуск контейнеров
docker compose -f docker-compose.prod.yml up -d
```