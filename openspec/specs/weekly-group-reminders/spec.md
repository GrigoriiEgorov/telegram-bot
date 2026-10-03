# weekly-group-reminders Specification

## Purpose

Предоставляет Telegram-группам независимые еженедельные напоминания о фотографиях недели с управлением расписанием и текстом со стороны администраторов.

## Requirements

### Requirement: Group-specific reminder configuration

The system SHALL maintain an independent reminder configuration for each Telegram group, including weekday, local time, IANA timezone, message text, and enabled state.

#### Scenario: New group receives defaults
- **WHEN** the bot receives a supported command in a group with no existing configuration
- **THEN** the system creates that group's configuration with Sunday at 20:00 in `Europe/Moscow`, a default weekly-photo message, and reminders enabled

#### Scenario: Groups do not share settings
- **WHEN** an administrator changes the schedule or message in one group
- **THEN** the configuration of every other group remains unchanged

### Requirement: Administrator configuration commands

The system SHALL allow only current Telegram group administrators to change reminder settings through bot commands.

#### Scenario: Administrator updates schedule
- **WHEN** a group administrator submits a valid schedule command containing a weekday and local time
- **THEN** the system stores the schedule for that group and confirms the resulting configuration

#### Scenario: Non-administrator attempts a change
- **WHEN** a non-administrator submits a configuration command
- **THEN** the system does not change the configuration and informs the user that administrator permissions are required

#### Scenario: Invalid configuration is rejected
- **WHEN** an administrator submits an invalid weekday, time, timezone, or empty/oversized message
- **THEN** the system leaves the previous configuration unchanged and returns a usage or validation error

### Requirement: Reminder lifecycle commands

The system SHALL provide administrator commands to view the current configuration, enable or disable reminders, send a test message, and replace the reminder text.

#### Scenario: Administrator disables reminders
- **WHEN** an administrator disables reminders for a group
- **THEN** the system persists the disabled state and does not send scheduled reminders for that group

#### Scenario: Administrator enables reminders
- **WHEN** an administrator enables reminders for a group
- **THEN** the system persists the enabled state and includes the group in future scheduled reminder evaluation

#### Scenario: Administrator requests status
- **WHEN** an administrator requests the group status
- **THEN** the system reports the configured weekday, local time, timezone, enabled state, and reminder text

#### Scenario: Administrator sends a test
- **WHEN** an administrator requests a test reminder
- **THEN** the system sends the currently configured reminder text immediately without changing the schedule or enabled state

### Requirement: Scheduled delivery

The system SHALL send one reminder message to each enabled group when its configured weekly schedule occurs, interpreting the configured time in the configured IANA timezone.

#### Scenario: Weekly reminder is due
- **WHEN** the current time reaches an enabled group's configured weekday and local time
- **THEN** the bot sends that group's configured message to the group

#### Scenario: Process restarts near a scheduled time
- **WHEN** the bot restarts and a scheduled occurrence is already being or has just been processed
- **THEN** the system does not send duplicate reminders for the same group and weekly occurrence

#### Scenario: Telegram delivery fails temporarily
- **WHEN** Telegram rejects or does not accept a scheduled send
- **THEN** the failure is logged and the process remains able to evaluate later scheduled occurrences

### Requirement: Persistent and safe configuration storage

The system SHALL persist group configurations and delivery idempotency state in PostgreSQL and SHALL NOT require the Telegram token to be stored in the database.

#### Scenario: Service restarts
- **WHEN** the Railway service restarts
- **THEN** previously saved group configurations and processed-occurrence state remain available

#### Scenario: Secret is configured
- **WHEN** the service starts with its Telegram token supplied through an environment variable
- **THEN** the token is used for Telegram API access and is not emitted in logs or user-facing messages
