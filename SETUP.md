# Инструкция по запуску бота

## Шаг 1: Установка зависимостей

```bash
pip install -r requirements.txt
```

## Шаг 2: Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
cp .env.example .env
```

Отредактируйте `.env` и укажите:
- `TELEGRAM_BOT_TOKEN` - токен вашего бота (получите у @BotFather в Telegram)
- Параметры базы данных (если используете Docker, оставьте значения по умолчанию)

## Шаг 3: Запуск базы данных

### Вариант 1: Использование Docker (рекомендуется)

```bash
# Запустите PostgreSQL
docker-compose up -d postgres

# Дождитесь запуска (несколько секунд)
docker-compose ps
```

### Вариант 2: Локальная установка PostgreSQL

Установите PostgreSQL локально и обновите `DATABASE_URL` в `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/cowatch
```

## Шаг 4: Инициализация базы данных

```bash
python -m bot.database.init_db
```

Вы должны увидеть сообщение: "Database tables created successfully!"

## Шаг 5: Запуск бота

```bash
python run_bot.py
```

Или:

```bash
python -m bot.main
```

Бот должен запуститься и вы должны увидеть в логах:
```
INFO - Starting bot...
INFO - Database initialized successfully
```

## Проверка работы

1. Найдите вашего бота в Telegram
2. Отправьте команду `/start`
3. Бот должен ответить приветствием и показать главное меню

## Команды для тестирования

1. `/start` - регистрация
2. `/add_movie` - добавьте тестовую ссылку (например, `https://www.kinopoisk.ru/film/123/`)
3. Создайте слот с датой в будущем
4. `/my_slots` - посмотрите созданные слоты
5. `/profile` - посмотрите свой профиль

## Устранение проблем

### Ошибка подключения к базе данных

Убедитесь, что:
- PostgreSQL запущен (`docker-compose ps`)
- Переменные окружения в `.env` правильные
- База данных инициализирована

### Ошибка "TELEGRAM_BOT_TOKEN is not set"

Проверьте, что файл `.env` существует и содержит `TELEGRAM_BOT_TOKEN`

### Модуль не найден

Убедитесь, что все зависимости установлены:
```bash
pip install -r requirements.txt
```

