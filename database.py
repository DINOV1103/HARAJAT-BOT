"""
Ma'lumotlar bazasi bilan ishlash uchun funksiyalar (SQLite).
"""

import sqlite3
from datetime import datetime

from config import DB_NAME


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            first_seen TEXT
        )
        """
    )

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

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('given', 'taken')),
            person_name TEXT NOT NULL,
            amount REAL NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'paid')),
            created_at TEXT NOT NULL,
            paid_at TEXT,
            last_reminded_date TEXT
        )
        """
    )

    conn.commit()
    conn.close()


# ---------- Foydalanuvchilar ----------

def register_user(user_id: int, username: str, full_name: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users (user_id, username, full_name, first_seen)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, full_name=excluded.full_name
        """,
        (user_id, username, full_name, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_all_user_ids():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


def get_user_count() -> int:
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    conn.close()
    return count


def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, full_name, first_seen FROM users ORDER BY first_seen DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------- Harajat / Daromad ----------

def add_transaction(user_id: int, type_: str, amount: float, description: str, date: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO transactions (user_id, type, amount, description, date, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, type_, amount, description, date, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_transactions_by_date(user_id: int, date: str, type_: str = None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if type_:
        cur.execute(
            "SELECT amount, description, type FROM transactions WHERE user_id=? AND date=? AND type=? ORDER BY id",
            (user_id, date, type_),
        )
    else:
        cur.execute(
            "SELECT amount, description, type FROM transactions WHERE user_id=? AND date=? ORDER BY id",
            (user_id, date),
        )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_transactions_by_range(user_id: int, start_date: str, end_date: str, type_: str = None):
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


def get_user_balance(user_id: int) -> dict:
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND type='expense'", (user_id,))
    total_expense = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND type='income'", (user_id,))
    total_income = cur.fetchone()[0]

    cur.execute(
        "SELECT COALESCE(SUM(amount),0) FROM debts WHERE user_id=? AND type='given' AND status='active'",
        (user_id,),
    )
    debt_given = cur.fetchone()[0]

    cur.execute(
        "SELECT COALESCE(SUM(amount),0) FROM debts WHERE user_id=? AND type='taken' AND status='active'",
        (user_id,),
    )
    debt_taken = cur.fetchone()[0]

    conn.close()
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net": total_income - total_expense,
        "debt_given": debt_given,
        "debt_taken": debt_taken,
    }


# ---------- Qarz daftari ----------

def add_debt(user_id: int, type_: str, person_name: str, amount: float, due_date: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO debts (user_id, type, person_name, amount, due_date, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, 'active', ?)",
        (user_id, type_, person_name, amount, due_date, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_debts(user_id: int, type_: str = None, status: str = "active"):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if type_:
        cur.execute(
            "SELECT id, person_name, amount, due_date FROM debts "
            "WHERE user_id=? AND type=? AND status=? ORDER BY due_date",
            (user_id, type_, status),
        )
    else:
        cur.execute(
            "SELECT id, person_name, amount, due_date FROM debts WHERE user_id=? AND status=? ORDER BY due_date",
            (user_id, status),
        )
    rows = cur.fetchall()
    conn.close()
    return rows


def mark_debt_paid(debt_id: int, user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "UPDATE debts SET status='paid', paid_at=? WHERE id=? AND user_id=?",
        (datetime.now().isoformat(), debt_id, user_id),
    )
    conn.commit()
    conn.close()


def get_debts_due_on(due_date: str):
    """
    Berilgan kunga qaytarish muddati to'g'ri kelgan, hali bildirishnoma
    yuborilmagan faol qarzlarni qaytaradi (barcha foydalanuvchilar bo'yicha).
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, type, person_name, amount FROM debts "
        "WHERE due_date=? AND status='active' AND (last_reminded_date IS NULL OR last_reminded_date != ?)",
        (due_date, due_date),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def mark_debt_reminded(debt_id: int, reminded_date: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE debts SET last_reminded_date=? WHERE id=?", (reminded_date, debt_id))
    conn.commit()
    conn.close()


# ---------- Admin statistikasi ----------

def get_admin_stats() -> dict:
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM transactions WHERE type='expense'")
    expense_count, expense_sum = cur.fetchone()

    cur.execute("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM transactions WHERE type='income'")
    income_count, income_sum = cur.fetchone()

    cur.execute("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM debts WHERE type='given' AND status='active'")
    given_count, given_sum = cur.fetchone()

    cur.execute("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM debts WHERE type='taken' AND status='active'")
    taken_count, taken_sum = cur.fetchone()

    cur.execute("SELECT COUNT(*) FROM debts WHERE status='paid'")
    paid_count = cur.fetchone()[0]

    conn.close()
    return {
        "total_users": total_users,
        "expense_count": expense_count, "expense_sum": expense_sum,
        "income_count": income_count, "income_sum": income_sum,
        "given_count": given_count, "given_sum": given_sum,
        "taken_count": taken_count, "taken_sum": taken_sum,
        "paid_count": paid_count,
    }
