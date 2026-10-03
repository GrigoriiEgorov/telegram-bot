# Weekly Photo Reminder Bot

Telegram-бот, который отправляет в группах еженедельное напоминание делиться фотографиями своей недели.

## Local development

1. Установить Python 3.12+.
2. Скопировать `.env.example` в `.env` и указать токен бота.
3. Запустить PostgreSQL: `docker compose up -d postgres`.
4. Установить проект: `pip install -e '.[dev]'`.
5. Запустить бота: `weekly-photo-reminder`.

Миграции применяются автоматически при старте. Токен не записывается в базу и не выводится в логи.

## Commands

Команды настройки выполняются администраторами группы:

- `/schedule sunday 20:00` — установить день и время;
- `/timezone Europe/Moscow` — установить IANA timezone;
- `/message Время делиться фотографиями недели 📸` — изменить текст;
- `/on`, `/off` — включить или выключить напоминания;
- `/status` — показать текущие настройки;
- `/test` — отправить тестовое сообщение;
- `/help` — показать справку.

Новая группа по умолчанию получает воскресенье 20:00 `Europe/Moscow`, включённые напоминания и стандартный текст.

## Railway deployment

Создать PostgreSQL service и persistent service для приложения. В service приложения задать:

- `TELEGRAM_BOT_TOKEN` — secret token, полученный у BotFather;
- `DATABASE_URL` — connection string PostgreSQL от Railway;
- `SCHEDULER_INTERVAL_SECONDS` — необязательно, по умолчанию `30`.

Start command: `weekly-photo-reminder`. Сервис рассчитан на один экземпляр и использует Telegram long polling. После деплоя добавить бота в тестовую группу, назначить его администратором и выполнить `/status` или `/test`.

При rollback не удалять PostgreSQL service: настройки групп хранятся в базе.

Если сервис был недоступен в момент напоминания, бот не отправляет устаревшее сообщение при следующем запуске в другой день. Он отправит ближайшее наступившее расписание.

## Checks

```bash
ruff check .
pytest
docker build -t weekly-photo-reminder-bot .
```
