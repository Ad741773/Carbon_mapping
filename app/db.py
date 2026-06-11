"""
db.py — lightweight SQLite3 wrapper.
Replaces SQLAlchemy so the project has zero external DB dependencies.
"""
import sqlite3, os
from contextlib import contextmanager

DB_PATH = os.getenv("DATABASE_URL", "ecotrace.db").replace("sqlite:////", "/").replace("sqlite:///", "")

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def tx():
    """Context-manager for a committed transaction."""
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetchone(sql: str, params=()):
    conn = get_conn()
    row = conn.execute(sql, params).fetchone()
    conn.close()
    return dict(row) if row else None


def fetchall(sql: str, params=()):
    conn = get_conn()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def execute(sql: str, params=()):
    with tx() as conn:
        cur = conn.execute(sql, params)
        return cur.lastrowid


def init_db():
    with tx() as conn:
        conn.executescript(SCHEMA)
    _seed_demo_data()


# ── Schema ─────────────────────────────────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    city          TEXT,
    country       TEXT,
    avatar_url    TEXT,
    is_active     INTEGER DEFAULT 1,
    created_at    TEXT    DEFAULT (datetime('now')),
    updated_at    TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS carbon_records (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id                INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date                   TEXT    NOT NULL,
    transport_emissions    REAL    DEFAULT 0,
    electricity_emissions  REAL    DEFAULT 0,
    food_emissions         REAL    DEFAULT 0,
    fuel_emissions         REAL    DEFAULT 0,
    total_emissions        REAL    DEFAULT 0,
    transport_details      TEXT    DEFAULT '[]',
    electricity_kwh        REAL    DEFAULT 0,
    fuel_details           TEXT    DEFAULT '{}',
    food_type              TEXT    DEFAULT 'vegetarian',
    created_at             TEXT    DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_cr_user_date ON carbon_records(user_id, date);

CREATE TABLE IF NOT EXISTS goals (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title          TEXT    NOT NULL,
    description    TEXT,
    category       TEXT    DEFAULT 'overall',
    target_value   REAL    NOT NULL,
    current_value  REAL    DEFAULT 0,
    start_date     TEXT,
    end_date       TEXT,
    is_completed   INTEGER DEFAULT 0,
    created_at     TEXT    DEFAULT (datetime('now')),
    updated_at     TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS recommendations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tips       TEXT    DEFAULT '[]',
    source     TEXT    DEFAULT 'rule_engine',
    created_at TEXT    DEFAULT (datetime('now'))
);
"""


def _seed_demo_data():
    if fetchone("SELECT id FROM users LIMIT 1"):
        return   # already seeded

    from werkzeug.security import generate_password_hash
    from datetime import date, timedelta
    import random, json

    demos = [
        ("Priya Sharma",  "priya@demo.com"),
        ("Lena Fischer",  "lena@demo.com"),
        ("Carlos Mendez", "carlos@demo.com"),
        ("Yuki Tanaka",   "yuki@demo.com"),
        ("Amara Diallo",  "amara@demo.com"),
    ]

    with tx() as conn:
        for name, email in demos:
            pw = generate_password_hash("Demo@1234")
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?,?,?)",
                (name, email, pw)
            )
            uid = cur.lastrowid
            for i in range(60):
                d    = (date.today() - timedelta(days=i)).isoformat()
                t_em = round(random.uniform(0.5, 3.0), 3)
                e_em = round(random.uniform(0.3, 1.5), 3)
                f_em = round(random.uniform(0.8, 2.5), 3)
                u_em = round(random.uniform(0.1, 0.8), 3)
                tot  = round(t_em + e_em + f_em + u_em, 3)
                conn.execute(
                    """INSERT INTO carbon_records
                       (user_id,date,transport_emissions,electricity_emissions,
                        food_emissions,fuel_emissions,total_emissions,food_type)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (uid, d, t_em, e_em, f_em, u_em, tot, "vegetarian")
                )
