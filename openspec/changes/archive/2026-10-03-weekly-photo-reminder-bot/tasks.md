# Tasks

## 1. Project and runtime foundation

- [x] 1.1 Create the Python project structure, dependency lock/requirements, configuration loader, and safe startup validation; verify the application starts with development placeholders and fails without required secrets or database configuration.
- [x] 1.2 Add Dockerfile and local development instructions for Python and PostgreSQL; verify the image builds and the documented local start command is valid.
- [x] 1.3 Define environment variable names for the Telegram token, PostgreSQL connection, and optional scheduler settings; verify logs never contain secret values.

## 2. Persistence model

- [x] 2.1 Implement PostgreSQL migrations for per-group reminder configuration and processed weekly occurrences with the required uniqueness constraints; verify migrations apply to a clean database.
- [x] 2.2 Implement repository operations for defaults, independent group settings, enabled state, message text, and occurrence claims; verify repository tests cover persistence across reconnects and isolation between groups.
- [x] 2.3 Document the chosen stale-occurrence/catch-up policy after downtime and verify it with repository or scheduler tests.

## 3. Telegram commands and authorization

- [x] 3.1 Implement group configuration initialization with defaults for Sunday 20:00 `Europe/Moscow` and the default weekly-photo message; verify a first supported group command creates exactly one configuration.
- [x] 3.2 Implement administrator status checks for all mutating commands and safe rejection for non-administrators; verify authorization tests cover both administrator and ordinary member requests.
- [x] 3.3 Implement schedule, timezone, message, enable, disable, status, and test-reminder commands with validation and unchanged state on invalid input; verify command tests cover valid, invalid, and unauthorized cases.
- [x] 3.4 Add user-facing command help and error messages in Russian; verify every supported command has documented syntax and a test for its response path.

## 4. Scheduling and delivery

- [x] 4.1 Implement timezone-aware weekly due-occurrence calculation for independent group schedules; verify tests cover Sunday 20:00 Moscow time, another timezone, boundary minutes, and disabled groups.
- [x] 4.2 Implement idempotent occurrence claiming and Telegram delivery handling so a restart or repeated scheduler tick cannot send the same occurrence twice; verify tests cover duplicate ticks and restart-like retries.
- [x] 4.3 Implement bounded Telegram error handling and scheduler-loop isolation; verify one failed group delivery is logged and does not prevent another due group from being evaluated.
- [x] 4.4 Connect asynchronous Telegram polling, command handlers, persistence, and scheduler lifecycle; verify an integration test or local smoke test can initialize the bot and execute a test reminder.

## 5. Railway deployment and operational documentation

- [x] 5.1 Add Railway deployment configuration for one persistent service and PostgreSQL connection wiring; verify the service build/start command matches the Docker image.
- [x] 5.2 Add deployment documentation covering Telegram bot creation, adding the bot to a group, administrator commands, Railway variables, migrations, logs, and rollback; verify the instructions contain no real credentials and are executable by a new maintainer.
- [x] 5.3 Run formatting, static checks, unit tests, migration tests, and the documented Docker/local smoke test; verify all required OpenSpec scenarios have corresponding automated or explicitly documented validation.
