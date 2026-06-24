"""
Moliya Menejeri - Ma'lumotlar bazasi boshqaruvi.
"""

import sqlite3
from datetime import datetime

DB_NAME = "harajat.db"


def init_db():
    """Barcha kerakli jadvallarni yaratish va ma'lumotlar bazasini initsializatsiya qilish."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # 1. Tranzaksiyalar jadvali (Daromad va Harajatlar)
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
    
    # 2. Qarz daftari jadvali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            person_name TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('lent', 'borrowed')),
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'paid')),
            created_at TEXT NOT NULL
        )
    """)
    
    # 3. Eslatmalar jadvali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # 4. Foydalanuvchilar jadvali (Admin statistika uchun)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            joined_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()


def add_user(user_id: int, username: str, full_name: str):
    """Yangi foydalanuvchini ro'yxatga olish."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO users (user_id, username, full_name, joined_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, username, full_name, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_users_count() -> int:
    """Jami bot foydalanuvchilari sonini olish (Admin uchun)."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    conn.close()
    return count


def get_all_user_ids():
    """Barcha foydalanuvchilar ID ro'yxatini olish (Xabar yuborish uchun)."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    ids = [r[0] for r in cur.fetchall()]
    conn.close()
    return ids


def add_transaction(user_id: int, type_: str, amount: float, description: str, date: str):
    """Tranzaksiya qo'shish."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transactions (user_id, type, amount, description, date, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, type_, amount, description, date, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_transactions_by_date(user_id: int, date: str, type_: str = None):
    """Kunlik tranzaksiyalarni olish."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if type_:
        cur.execute("""
            SELECT amount, description, type FROM transactions 
            WHERE user_id=? AND date=? AND type=? ORDER BY id
        """, (user_id, date, type_))
    else:
        cur.execute("""
            SELECT amount, description, type FROM transactions 
            WHERE user_id=? AND date=? ORDER BY id
        """, (user_id, date))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_transactions_by_range(user_id: int, start_date: str, end_date: str, type_: str = None):
    """Ma'lum bir davr oralig'idagi tranzaksiyalarni olish."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if type_:
        cur.execute("""
            SELECT amount, description, date, type FROM transactions 
            WHERE user_id=? AND date BETWEEN ? AND ? AND type=? ORDER BY date
        """, (user_id, start_date, end_date, type_))
    else:
        cur.execute("""
            SELECT amount, description, date, type FROM transactions 
            WHERE user_id=? AND date BETWEEN ? AND ? ORDER BY date
        """, (user_id, start_date, end_date))
    rows = cur.fetchall()
    conn.close()
    return rows


def add_debt(user_id: int, person_name: str, amount: float, type_: str):
    """Qarz yozuvini qo'shish (lent - berildi, borrowed - olindi)."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO debts (user_id, person_name, amount, type, status, created_at)
        VALUES (?, ?, ?, ?, 'active', ?)
    """, (user_id, person_name, amount, type_, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_active_debts(user_id: int):
    """Yopilmagan (faol) qarzlarni olish."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, person_name, amount, type FROM debts 
        WHERE user_id=? AND status='active' ORDER BY id DESC
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def mark_debt_as_paid(debt_id: int, user_id: int):
    """Qarzni to'landi deb o'zgartirish."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE debts SET status='paid' WHERE id=? AND user_id=?", (debt_id, user_id))
    conn.commit()
    conn.close()


def add_note(user_id: int, content: str):
    """Yangi eslatma yozish."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO notes (user_id, content, created_at) VALUES (?, ?, ?)",
                (user_id, content, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_notes(user_id: int):
    """Foydalanuvchining barcha eslatmalarini olish."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, content FROM notes WHERE user_id=? ORDER BY id DESC", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def delete_note(note_id: int, user_id: int):
    """Eslatmani o'chirish."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM notes WHERE id=? AND user_id=?", (note_id, user_id))
    conn.commit()
    conn.close()
    
