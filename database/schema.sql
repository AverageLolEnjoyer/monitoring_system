-- Схема базы данных системы мониторинга

-- Таблица метрик
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT NOT NULL,
    timestamp REAL NOT NULL,
    status TEXT NOT NULL,
    response_time_ms REAL,
    error_message TEXT,
    is_healthy BOOLEAN
);

-- Таблица событий восстановления
CREATE TABLE IF NOT EXISTS recovery_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT NOT NULL,
    timestamp REAL NOT NULL,
    success BOOLEAN NOT NULL,
    recovery_method TEXT,
    details TEXT
);

-- Таблица алертов
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT NOT NULL,
    timestamp REAL NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    acknowledged BOOLEAN DEFAULT 0
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_metrics_service ON metrics(service_name);
CREATE INDEX IF NOT EXISTS idx_metrics_time ON metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_time ON alerts(timestamp);