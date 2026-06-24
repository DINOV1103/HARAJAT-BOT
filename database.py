import sqlite3
from datetime import datetime, date

DB_NAME = "harajat.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Harajat/Daromad
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('expense', 'income')),
            amount REAL NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # Qarzlar
    cur.execute("""
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            debt_type TEXT NOT NULL CHECK(debt_type IN ('given', 'taken')),
            person TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            due_date TEXT NOT NULL,
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'returned')),
            created_at TEXT NOT NULL
        )
    """)
    
    # Foydalanuvchilar (broadcast uchun)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_transaction(user_id: int, type_: str, amount: float, description: str, date: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO transactions (user_id, type, amount, description, date, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, type_, amount, description, date, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def add_debt(user_id: int, debt_type: str, person: str, amount: float, description: str, due_date: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO debts (user_id, debt_type, person, amount, description, due_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, debt_type, person, amount, description, due_date, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_transactions_by_date(user_id: int, date_str: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT amount, description, type FROM transactions WHERE user_id=? AND date=? ORDER BY id", (user_id, date_str))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_transactions_by_range(user_id: int, start_date: str, end_date: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT amount, description, date, type FROM transactions WHERE user_id=? AND date BETWEEN ? AND ? ORDER BY date",
        (user_id, start_date, end_date)
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_active_debts(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, debt_type, person, amount, description, due_date FROM debts WHERE user_id=? AND status='active' ORDER BY due_date",
        (user_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def mark_debt_returned(debt_id: int, user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE debts SET status='returned' WHERE id=? AND user_id=?", (debt_id, user_id))
    conn.commit()
    conn.close()


def get_today_reminders(user_id: int):
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT person, amount, description, debt_type FROM debts WHERE user_id=? AND due_date=? AND status='active'",
        (user_id, today)
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def save_user(user_id: int, username: str = None, first_name: str = None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO users (user_id, username, first_name, joined_at) VALUES (?, ?, ?, ?)",
        (user_id, username, first_name, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows]

