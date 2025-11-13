# Инструкция по деплою на сервер

## Что было исправлено для работы на сервере

1. ✅ **Убран хардкод пути** в `migrations/env.py` - теперь путь определяется динамически
2. ✅ **Улучшена обработка путей SQLite** в `config.py` - используется абсолютный путь
3. ✅ **Автоматическое применение миграций** при старте бота

## Настройка переменных окружения на сервере

### Для PostgreSQL (рекомендуется для продакшена)

В `.env` или переменных окружения укажите:

```bash
DATABASE_URL=postgresql://user:password@host:5432/cowatch
TELEGRAM_BOT_TOKEN=your_bot_token
MIN_PARTICIPANTS_DEFAULT=2
```

### Для SQLite (только для тестирования)

```bash
DATABASE_URL_SQLITE=sqlite:////absolute/path/to/cowatch.db
# или используйте переменную DATABASE_PATH для пути к файлу
DATABASE_PATH=/absolute/path/to/cowatch.db
TELEGRAM_BOT_TOKEN=your_bot_token
```

## Как работает инициализация БД

При старте бота (`python run_bot.py`):

1. Вызывается `init_database()` из `bot/database/init_db.py`
2. Проверяется наличие таблицы `alembic_version`
3. Если БД существует без версионирования - автоматически помечается нужной версией
4. Применяются все новые миграции до `head`

## Docker деплой

Если используете `docker-compose.yaml`:

1. **init-db** сервис запускает миграции один раз при первом деплое
2. **bot-service** также применяет миграции при старте (на случай обновлений)

Убедитесь, что в `.env` указан правильный `DATABASE_URL`:

```bash
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
```

## Проверка после деплоя

1. Проверьте логи бота - должно быть:
   ```
   INFO - Running database migrations to head (database: ...)
   INFO - Database migrations applied successfully!
   ```

2. Проверьте версию миграций:
   ```bash
   alembic -c alembic.ini current
   ```
   Должно показать: `20251111_000002 (head)`

3. Проверьте таблицы в БД:
   ```bash
   # Для PostgreSQL
   psql -U user -d cowatch -c "\dt"
   
   # Для SQLite
   sqlite3 cowatch.db ".tables"
   ```

## Возможные проблемы

### Проблема: "Alembic config not found"
**Решение**: Убедитесь, что `alembic.ini` находится в `botService/` директории

### Проблема: "table already exists"
**Решение**: БД уже существует. Миграции автоматически обработают это, но если ошибка повторяется - проверьте логи

### Проблема: "ModuleNotFoundError: No module named 'bot'"
**Решение**: Убедитесь, что рабочая директория - `botService/` или добавьте путь в PYTHONPATH

## Структура БД после миграций

После успешного применения миграций будут созданы таблицы:

- `users` - пользователи
- `movies` - фильмы и сериалы
- `slots` - слоты для просмотра
- `slot_participants` - участники слотов
- `rooms` - комнаты для обсуждения
- `ratings` - рейтинги пользователей
- `episodes` - эпизоды сериалов
- `comments` - комментарии в комнатах
- `likes` - лайки на комментарии
- `watch_history` - история просмотров
- `alembic_version` - версия миграций (служебная)

## Откат миграций (если нужно)

```bash
# Откатить последнюю миграцию
alembic -c alembic.ini downgrade -1

# Откатить до конкретной версии
alembic -c alembic.ini downgrade 20251111_000001
```

**⚠️ Внимание**: Откат миграций может привести к потере данных!

