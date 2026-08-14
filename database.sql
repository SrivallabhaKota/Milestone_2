-- ═══════════════════════════════════════════════════════════════════════════
-- FinGoal Database Schema
-- Smart Goal Planning & Savings + Investment Management
-- SQLite3
-- ═══════════════════════════════════════════════════════════════════════════

PRAGMA foreign_keys = ON;

-- ─── Profile (single local user profile) ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS profile (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    name                      TEXT    NOT NULL DEFAULT 'My Profile',
    email                     TEXT,
    phone                     TEXT,
    currency                  TEXT    NOT NULL DEFAULT '₹',
    monthly_saving_capacity   REAL    DEFAULT 0.0,
    monthly_investment_capacity REAL  DEFAULT 0.0,
    notes                     TEXT,
    created_at                TEXT    DEFAULT (datetime('now')),
    updated_at                TEXT    DEFAULT (datetime('now'))
);

-- ─── Goals ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS goals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_name       TEXT    NOT NULL,
    goal_type       TEXT,
    description     TEXT,
    target_amount   REAL    NOT NULL DEFAULT 0.0,
    current_amount  REAL    NOT NULL DEFAULT 0.0,
    start_date      TEXT,
    target_date     TEXT,
    category        TEXT    DEFAULT 'Personal',
    priority        TEXT    DEFAULT 'Medium',
    status          TEXT    NOT NULL DEFAULT 'Active',
    notes           TEXT,
    created_at      TEXT    DEFAULT (datetime('now')),
    updated_at      TEXT    DEFAULT (datetime('now'))
);

-- ─── Goal Parts / Milestones ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS goal_parts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id         INTEGER NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    part_name       TEXT    NOT NULL,
    target_amount   REAL    NOT NULL DEFAULT 0.0,
    saved_amount    REAL    NOT NULL DEFAULT 0.0,
    due_date        TEXT,
    status          TEXT    NOT NULL DEFAULT 'Pending',
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- ─── Savings Records ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS savings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id         INTEGER NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    amount          REAL    NOT NULL,
    saving_date     TEXT    NOT NULL DEFAULT (date('now')),
    note            TEXT,
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- ─── Investments ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS investments (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    investment_name         TEXT    NOT NULL,
    investment_type         TEXT    NOT NULL DEFAULT 'Other',
    invested_amount         REAL    NOT NULL DEFAULT 0.0,
    current_value           REAL    NOT NULL DEFAULT 0.0,
    investment_date         TEXT,
    maturity_date           TEXT,
    expected_return_rate    REAL    DEFAULT 0.0,
    status                  TEXT    NOT NULL DEFAULT 'Active',
    notes                   TEXT,
    created_at              TEXT    DEFAULT (datetime('now')),
    updated_at              TEXT    DEFAULT (datetime('now'))
);

-- ─── Indexes ──────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_goals_status    ON goals(status);
CREATE INDEX IF NOT EXISTS idx_goals_category  ON goals(category);
CREATE INDEX IF NOT EXISTS idx_goal_parts_goal ON goal_parts(goal_id);
CREATE INDEX IF NOT EXISTS idx_savings_goal    ON savings(goal_id);
CREATE INDEX IF NOT EXISTS idx_inv_type        ON investments(investment_type);
CREATE INDEX IF NOT EXISTS idx_inv_status      ON investments(status);

-- ─── Default Profile Record ───────────────────────────────────────────────────
INSERT OR IGNORE INTO profile (id, name, currency, monthly_saving_capacity, monthly_investment_capacity)
VALUES (1, 'My Profile', '₹', 10000, 5000);

-- ─── Sample Goals (optional demo data — remove if not needed) ─────────────────
INSERT OR IGNORE INTO goals (id, goal_name, goal_type, description, target_amount, current_amount,
    start_date, target_date, category, priority, status, notes)
VALUES
(1, 'Buy Laptop', 'Purchase', 'Save for a new laptop for work and projects',
 80000, 35000, '2026-01-01', '2026-12-31', 'Electronics', 'High', 'Active',
 'Looking at MacBook Air or Dell XPS'),
(2, 'Emergency Fund', 'Savings', '3-month emergency fund',
 150000, 75000, '2025-06-01', '2026-06-30', 'Emergency', 'High', 'Active',
 'Keep in liquid FD or savings account'),
(3, 'Travel to Goa', 'Travel', 'Family trip to Goa',
 40000, 40000, '2026-01-01', '2026-08-01', 'Travel', 'Medium', 'Completed',
 'Completed ahead of schedule!');

-- ─── Sample Goal Parts ────────────────────────────────────────────────────────
INSERT OR IGNORE INTO goal_parts (id, goal_id, part_name, target_amount, saved_amount, due_date, status)
VALUES
(1, 1, 'Part 1 — First ₹20,000', 20000, 20000, '2026-03-31', 'Completed'),
(2, 1, 'Part 2 — Second ₹20,000', 20000, 15000, '2026-06-30', 'In Progress'),
(3, 1, 'Part 3 — Third ₹20,000', 20000, 0, '2026-09-30', 'Pending'),
(4, 1, 'Part 4 — Final ₹20,000', 20000, 0, '2026-12-31', 'Pending');

-- ─── Sample Savings ───────────────────────────────────────────────────────────
INSERT OR IGNORE INTO savings (id, goal_id, amount, saving_date, note)
VALUES
(1, 1, 10000, '2026-01-15', 'January salary saving'),
(2, 1, 10000, '2026-02-10', 'February saving'),
(3, 1, 15000, '2026-03-05', 'Bonus saving'),
(4, 2, 25000, '2026-01-01', 'Initial deposit'),
(5, 2, 25000, '2026-03-01', 'Q1 saving'),
(6, 2, 25000, '2026-06-01', 'Q2 saving');

-- ─── Sample Investments ───────────────────────────────────────────────────────
INSERT OR IGNORE INTO investments (id, investment_name, investment_type, invested_amount,
    current_value, investment_date, maturity_date, expected_return_rate, status, notes)
VALUES
(1, 'SBI Blue Chip Fund', 'Mutual Funds', 50000, 57500,
 '2025-04-01', '2028-04-01', 12.0, 'Active', 'Long-term SIP'),
(2, 'HDFC FD', 'Fixed Deposit', 100000, 107500,
 '2026-01-01', '2027-01-01', 7.5, 'Active', '1-year fixed deposit'),
(3, 'Reliance Industries', 'Stocks', 25000, 28000,
 '2025-10-01', NULL, 15.0, 'Active', 'Long-term holding'),
(4, 'Sovereign Gold Bond', 'Gold', 30000, 33000,
 '2025-07-01', '2033-07-01', 8.0, 'Active', 'SGB Series 2025');
