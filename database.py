"""
Ma'lumotlar bazasi bilan ishlash uchun funksiyalar.
SQLite ishlatiladi - foydalanuvchilar va analitika jadvali qo'shilgan versiyasi.
"""

import sqlite3
from datetime import datetime

DB_NAME = "harajat.db"


def init_db():
    """Bot birinchi marta ishga tushganda jadvallarni yaratadi."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Tranzaksiyalar jadvali
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
    
    # Foydalanuvchilar jadvali (Xabar tarqatish va admin paneli uchun)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            joined_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def add_user(user_id: int, username: str, full_name: str):
    """Yangi foydalanuvchini ro'yxatga oladi (agar mavjud bo'lmasa)."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO users (user_id, username, full_name, joined_at)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, username, full_name, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_all_users():
    """Barchaga xabar yuborish uchun barcha foydalanuvchilar ID ro'yxatini oladi."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


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
    """Bitta kun uchun yozuvlarni qaytaradi."""
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
    """Davr (hafta/oy) uchun yozuvlarni qaytaradi."""
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


def get_admin_stats():
    """Admin panel uchun global statistikani yig'adi."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0] or 0
    
    cur.execute("SELECT SUM(amount) FROM transactions WHERE type='expense'")
    total_expense = cur.fetchone()[0] or 0
    
    cur.execute("SELECT SUM(amount) FROM transactions WHERE type='income'")
    total_income = cur.fetchone()[0] or 0
    
    conn.close()
    return total_users, total_expense, total_income


