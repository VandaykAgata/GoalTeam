CREATE TABLE IF NOT EXISTS leads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    phone       TEXT    NOT NULL,
    email       TEXT    NOT NULL,
    message     TEXT    NOT NULL,
    source      TEXT    NOT NULL,
    summary     TEXT    NOT NULL,
    category    TEXT    NOT NULL,
    urgency     TEXT    NOT NULL,
    score       INTEGER NOT NULL,
    reasoning   TEXT    NOT NULL,
    received_at TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_leads_category    ON leads(category);
CREATE INDEX IF NOT EXISTS idx_leads_received_at ON leads(received_at);
