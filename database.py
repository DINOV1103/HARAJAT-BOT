"""
Ma'lumotlar bazasi bilan ishlash uchun funksiyalar.
SQLite - Qarzlar va Admin statistikasi modullari bilan kengaytirilgan shakli.
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
    
    # Qarzlar jadvali
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('oldim', 'berdim')),
            amount REAL NOT NULL,
            person TEXT NOT NULL,
            due_date TEXT NOT NULL,
            is_paid INTEGER DEFAULT 0,
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


# ================= QARZLAR MODULI =================

def add_debt(user_id: int, type_: str, amount: float, person: str, due_date: str):
    """Yangi faol qarz yozuvini qo'shadi."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO debts (user_id, type, amount, person, due_date, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, type_, amount, person, due_date, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_active_debts(user_id: int):
    """Foydalanuvchining to'lanmagan faol qarzlarini qaytaradi."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, type, amount, person, due_date FROM debts
        WHERE user_id=? AND is_paid=0 ORDER BY due_date ASC
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def settle_debt(debt_id: int, user_id: int):
    """Qarzni to'langan deb belgilaydi (statusini o'zgartiradi)."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "UPDATE debts SET is_paid=1 WHERE id=? AND user_id=?",
        (debt_id, user_id),
    )
    conn.commit()
    conn.close()


# ================= ADMIN PANEL MODULI =================

def get_admin_stats():
    """Admin uchun global va chuqurlashtirilgan tahliliy statistikani qaytaradi."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Umumiy unikal foydalanuvchilar soni
    cur.execute(
        """
        SELECT COUNT(DISTINCT user_id) FROM (
            SELECT user_id FROM transactions
            UNION
            SELECT user_id FROM debts
        )
        """
    )
    total_users = cur.fetchone()[0] or 0
    
    # Jami harajatlar summasi va soni
    cur.execute("SELECT COUNT(*), SUM(amount) FROM transactions WHERE type='expense'")
    exp_count, exp_sum = cur.fetchone()
    exp_sum = exp_sum or 0
    
    # Jami daromadlar summasi va soni
    cur.execute("SELECT COUNT(*), SUM(amount) FROM transactions WHERE type='income'")
    inc_count, inc_sum = cur.fetchone()
    inc_sum = inc_sum or 0
    
    # Tizimdagi yopilmagan qarzlar soni
    cur.execute("SELECT COUNT(*) FROM debts WHERE is_paid=0")
    active_debts_count = cur.fetchone()[0] or 0
    
    conn.close()
    return total_users, exp_count, exp_sum, inc_count, inc_sum, active_debts_count

