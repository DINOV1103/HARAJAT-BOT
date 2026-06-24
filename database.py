"""
Ma'lumotlar bazasi bilan ishlash uchun funksiyalar.
SQLite ishlatiladi - alohida server kerak emas, fayl ko'rinishida saqlanadi.
"""

import sqlite3
from datetime import datetime

DB_NAME = "harajat.db"


def init_db():
    """Bot birinchi marta ishga tushganda jadval yaratadi (agar mavjud bo'lmasa)."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
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
    conn.commit()
    conn.close()


def add_transaction(user_id: int, type_: str, amount: float, description: str, date: str):
    """Yangi harajat yoki daromad yozuvini qo'shadi."""
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


def get_transactions_by_date(user_id: int, date: str, type_: str = None):
    """Bitta kun uchun yozuvlarni qaytaradi: (amount, description, type)."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if type_:
        cur.execute(
            "SELECT amount, description, type FROM transactions "
            "WHERE user_id=? AND date=? AND type=? ORDER BY id",
            (user_id, date, type_),
        )
    else:
        cur.execute(
            "SELECT amount, description, type FROM transactions "
            "WHERE user_id=? AND date=? ORDER BY id",
            (user_id, date),
        )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_transactions_by_range(user_id: int, start_date: str, end_date: str, type_: str = None):
    """Davr (hafta/oy) uchun yozuvlarni qaytaradi: (amount, description, date, type)."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if type_:
        cur.execute(
            "SELECT amount, description, date, type FROM transactions "
            "WHERE user_id=? AND date BETWEEN ? AND ? AND type=? ORDER BY date",
            (user_id, start_date, end_date, type_),
        )
    else:
        cur.execute(
            "SELECT amount, description, date, type FROM transactions "
            "WHERE user_id=? AND date BETWEEN ? AND ? ORDER BY date",
            (user_id, start_date, end_date),
        )
    rows = cur.fetchall()
    conn.close()
    return rows
