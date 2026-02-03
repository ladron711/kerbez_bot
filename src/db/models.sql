CREATE TABLE IF NOT EXISTS lots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_code TEXT UNIQUE NOT NULL,
    title TEXT,
    customer TEXT,
    price REAL,
    method TEXT,
    status TEXT,
    start_date TEXT,
    end_date TEXT,
    link TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

