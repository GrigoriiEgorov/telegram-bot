# Design

## Context

Репозиторий на момент планирования не содержит application code, тестов или существующих capabilities; change является greenfield. Бот должен обслуживать несколько Telegram-групп, хранить независимые настройки и работать как один постоянно запущенный процесс в Railway. See `proposal.md` for motivation and `specs/weekly-group-reminders/spec.md` for the observable contract.

## Goals / Non-Goals

**Goals:**

- Реализовать Python-бота с long polling и административными командами.
- Хранить конфигурацию групп и состояние отправленных недельных occurrences в PostgreSQL.
- Обеспечить корректную работу с IANA timezones и защиту от дублей после перезапуска.
- Подготовить Docker/Railway deployment с секретами через environment variables.
- Покрыть parsing, authorization, scheduling, persistence и delivery idempotency тестами.

**Non-Goals:**

- Сбор, хранение или анализ фотографий.
- Отслеживание, кто из участников уже отправил фотографию.
- Web-интерфейс, webhook, отдельный HTTP API или multi-instance deployment.
- Авторизация вне Telegram administrator status.

## Decisions

### Python Telegram application

Использовать зрелую Python-библиотеку для Telegram Bot API с asynchronous handlers и встроенным long polling. Long polling не требует публичного HTTPS endpoint и соответствует одному постоянно работающему Railway service. Webhook оставляется возможным последующим изменением, если появится требование к HTTP-инфраструктуре.

### PostgreSQL as source of truth

PostgreSQL выбран вместо SQLite, потому что конфигурации должны жить в управляемом облачном хранилище и не зависеть от локальной файловой системы контейнера. Минимальная модель включает таблицу настроек группы и уникальную запись для уже обработанной пары `(group_id, occurrence_key)`.

### Per-group configuration

Настройки идентифицируются Telegram `chat_id`. В таблице хранятся weekday, local time, timezone, message text, enabled flag и timestamps. Новая группа получает defaults лениво при первой поддерживаемой команде; это не требует отдельного onboarding workflow.

### Scheduling and idempotency

Планировщик периодически вычисляет текущую дату/время в timezone каждой enabled-группы. Для наступившего occurrence используется транзакционная уникальность в PostgreSQL: запись occurrence создаётся до или вместе с отправкой по выбранной retry-политике, чтобы перезапуск не создавал дубликаты. Ошибки Telegram должны быть видны в логах и не останавливать цикл обработки остальных групп; конкретная retry-политика должна быть реализована с ограниченным повтором и сохранением возможности повторной доставки.

### Administrator authorization

Каждая изменяющая команда проверяет текущий Telegram administrator status отправителя и отклоняет запрос обычного участника. Бот не ослабляет права из-за локально сохранённой роли: источником истины для authorization является Telegram.

### Railway deployment

Приложение запускается как один persistent service из Dockerfile. PostgreSQL подключается через Railway-provided connection variable. Telegram token передаётся отдельной secret environment variable. Health/observability на первом этапе ограничиваются startup validation, structured logs без секретов и логированием ошибок доставки; масштабирование в несколько экземпляров не входит в текущий scope.

## Risks / Trade-offs

- [Risk] Один экземпляр ограничивает отказоустойчивость и масштабирование. → Явно зафиксировать single-instance scope и сделать delivery idempotent для безопасного будущего расширения.
- [Risk] Процесс может быть недоступен в момент расписания. → Выполнять проверку due occurrences после старта и хранить occurrence state; точное окно catch-up должно быть покрыто тестами.
- [Risk] Неправильный timezone или формат команды приведёт к неожиданному времени. → Использовать только валидные IANA timezone names и возвращать понятные validation errors.
- [Risk] Telegram может ограничивать частоту или отклонить отправку. → Обрабатывать API errors без остановки scheduler loop и логировать chat id, occurrence и тип ошибки без токена.
- [Risk] PostgreSQL connection/configuration недоступны. → Fail fast на старте с безопасным диагностическим сообщением и описать обязательные Railway variables.

## Migration Plan

1. Создать PostgreSQL service в Railway и передать connection string приложению.
2. Выполнить безопасное создание таблиц при старте или отдельной migration command.
3. Задать Telegram token в secret environment variable и запустить один service instance.
4. Добавить бота в тестовую группу, проверить administrator commands, `/test` и фактическое расписание.
5. При rollback остановить новый deployment и вернуть предыдущий image; данные PostgreSQL не удалять.

## Open Questions

Нет. Реализация использует `TELEGRAM_BOT_TOKEN`, `DATABASE_URL` и необязательный `SCHEDULER_INTERVAL_SECONDS`; после простоя устаревшее напоминание не отправляется.
