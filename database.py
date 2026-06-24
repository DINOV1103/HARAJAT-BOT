"""
Ma'lumotlar bazasi bilan ishlash uchun funksiyalar.
"""

import sqlite3
from datetime import datetime, date

DB_NAME = "harajat.db"


def init_db():
    """Jadvallarni yaratadi."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Harajat va daromadlar
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('expense', 'income')),
            amount REAL NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    
    # Qarzlar jadvali
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('given', 'taken')),
            person TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'returned')),
            created_at TEXT NOT NULL
        )
        """
    )
    
    conn.commit()
    conn.close()


def add_transaction(user_id: int, type_: str, amount: float, description: str, date: str):
    """Yangi harajat yoki daromad qo'shish."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO transactions (user_id, type, amount, description, date, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, type_, amount, description, date, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def add_debt(user_id: int, debt_type: str, person: str, amount: float, description: str, due_date: str):
    """Yangi qarz qo'shish."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO debts (user_id, type, person, amount, description, due_date, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, debt_type, person, amount, description, due_date, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_active_debts(user_id: int):
    """Faol qarzlarni qaytaradi."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, type, person, amount, description, due_date FROM debts "
        "WHERE user_id=? AND status='active' ORDER BY due_date",
        (user_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_today_reminders(user_id: int):
    """Bugun qaytarilishi kerak bo'lgan qarzlarni qaytaradi."""
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT person, amount, description, type FROM debts "
        "WHERE user_id=? AND due_date=? AND status='active'",
        (user_id, today)
    )
    rows = cur.fetchall()
    conn.close()
    return rows
