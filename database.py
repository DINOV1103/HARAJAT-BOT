"""
Moliya Menejeri - Ma'lumotlar bazasi boshqaruvi.
"""

import sqlite3
from datetime import datetime

DB_NAME = "harajat.db"


def init_db():
    """Barcha kerakli jadvallarni yaratish va migratsiyalarni tekshirish."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Tranzaksiyalar jadvali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('expense', 'income')),
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # Qarz daftari jadvali (due_date qo'shilgan holda)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            person_name TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('lent', 'borrowed')),
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'paid')),
            due_date TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    # Eslatmalar jadvali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # Foydalanuvchilar jadvali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            joined_at TEXT NOT NULL
        )
    """)
    
    # Eski foydalanuvchilar bazasiga yangi ustunlarni xavfsiz qo'shish (Migration)
    try:
        cur.execute("ALTER TABLE transactions ADD COLUMN category TEXT DEFAULT 'Boshqa'")
    except sqlite3.OperationalError:
        pass
        
    try:
        cur.execute("ALTER TABLE debts ADD COLUMN due_date TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


def add_user(user_id: int, username: str, full_name: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO users (user_id, username, full_name, joined_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, username, full_name, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_users_count() -> int:
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    conn.close()
    return count


def get_all_user_ids():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    ids = [r[0] for r in cur.fetchall()]
    conn.close()
    return ids


def add_transaction(user_id: int, type_: str, amount: float, category: str, description: str, date: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transactions (user_id, type, amount, category, description, date, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, type_, amount, category, description, date, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_transactions_by_date(user_id: int, date: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT amount, category, description, type FROM transactions 
        WHERE user_id=? AND date=? ORDER BY id
    """, (user_id, date))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_transactions_by_range(user_id: int, start_date: str, end_date: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT amount, category, description, date, type FROM transactions 
        WHERE user_id=? AND date BETWEEN ? AND ? ORDER BY date ASC, id ASC
    """, (user_id, start_date, end_date))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_all_transactions_for_excel(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT date, type, category, amount, description FROM transactions 
        WHERE user_id=? ORDER BY date DESC
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def add_debt(user_id: int, person_name: str, amount: float, type_: str, due_date: str):
    """Yangi qarz yozuvini qaytarish muddati (due_date) bilan qo'shish."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO debts (user_id, person_name, amount, type, status, due_date, created_at)
        VALUES (?, ?, ?, ?, 'active', ?, ?)
    """, (user_id, person_name, amount, type_, due_date, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_active_debts(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, person_name, amount, type, due_date FROM debts 
        WHERE user_id=? AND status='active' ORDER BY id DESC
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_todays_due_debts(current_date: str):
    """Bugun qaytarilishi kerak bo'lgan barcha faol qarzlarni topish (Eslatma uchun)."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, user_id, person_name, amount, type FROM debts 
        WHERE due_date=? AND status='active'
    """, (current_date,))
    rows = cur.fetchall()
    conn.close()
    return rows


def mark_debt_as_paid(debt_id: int, user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE debts SET status='paid' WHERE id=? AND user_id=?", (debt_id, user_id))
    conn.commit()
    conn.close()


def add_note(user_id: int, content: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO notes (user_id, content, created_at) VALUES (?, ?, ?)",
                (user_id, content, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_notes(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, content FROM notes WHERE user_id=? ORDER BY id DESC", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def delete_note(note_id: int, user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM notes WHERE id=? AND user_id=?", (note_id, user_id))
    conn.commit()
    conn.close()
    
    
