CREATE TABLE IF NOT EXISTS group_reminder_configs (
    chat_id BIGINT PRIMARY KEY,
    weekday SMALLINT NOT NULL CHECK (weekday BETWEEN 0 AND 6),
    local_time TIME NOT NULL,
    timezone TEXT NOT NULL,
    message TEXT NOT NULL CHECK (char_length(message) BETWEEN 1 AND 4096),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reminder_occurrences (
    chat_id BIGINT NOT NULL REFERENCES group_reminder_configs(chat_id) ON DELETE CASCADE,
    occurrence_key DATE NOT NULL,
    claimed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (chat_id, occurrence_key)
);
