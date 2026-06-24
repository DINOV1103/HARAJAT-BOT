# db.py
import aiosqlite
from datetime import datetime

DB_PATH = "harajat.db"

CREATE_SQL = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    first_name TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT,
    amount REAL,
    category TEXT,
    note TEXT,
    created_at TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS debts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    person TEXT,
    amount REAL,
    direction TEXT,
    due_date TEXT,
    note TEXT,
    created_at TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
"""

async def init_db(path: str = DB_PATH):
    async with aiosqlite.connect(path) as db:
        await db.executescript(CREATE_SQL)
        await db.commit()

async def add_user(user_id: int, first_name: str, path: str = DB_PATH):
    async with aiosqlite.connect(path) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users(user_id, first_name, created_at) VALUES (?,?,?)",
            (user_id, first_name, datetime.utcnow().isoformat())
        )
        await db.commit()

async def add_transaction(user_id: int, ttype: str, amount: float, category: str, note: str, path: str = DB_PATH):
    async with aiosqlite.connect(path) as db:
        await db.execute(
            "INSERT INTO transactions(user_id,type,amount,category,note,created_at) VALUES (?,?,?,?,?,?)",
            (user_id, ttype, amount, category, note, datetime.utcnow().isoformat())
        )
        await db.commit()

async def get_balance(user_id: int, path: str = DB_PATH) -> float:
    async with aiosqlite.connect(path) as db:
        cur = await db.execute(
            "SELECT COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE -amount END),0) FROM transactions WHERE user_id=?",
            (user_id,)
        )
        row = await cur.fetchone()
        return float(row[0] or 0.0)

async def get_daily(user_id: int, date_iso: str, path: str = DB_PATH):
    async with aiosqlite.connect(path) as db:
        cur = await db.execute(
            "SELECT id,type,amount,category,note,created_at FROM transactions WHERE user_id=? AND date(created_at)=date(?) ORDER BY created_at",
            (user_id, date_iso)
        )
        return await cur.fetchall()

async def get_monthly(user_id: int, year_month: str, path: str = DB_PATH):
    async with aiosqlite.connect(path) as db:
        cur = await db.execute(
            "SELECT id,type,amount,category,note,created_at FROM transactions WHERE user_id=? AND strftime('%Y-%m',created_at)=? ORDER BY created_at",
            (user_id, year_month)
        )
        return await cur.fetchall()

async def add_debt(user_id: int, person: str, amount: float, direction: str, due_date: str, note: str, path: str = DB_PATH):
    async with aiosqlite.connect(path) as db:
        await db.execute(
            "INSERT INTO debts(user_id,person,amount,direction,due_date,note,created_at) VALUES (?,?,?,?,?,?,?)",
            (user_id, person, amount, direction, due_date, note, datetime.utcnow().isoformat())
        )
        await db.commit()

async def list_debts(user_id: int, path: str = DB_PATH):
    async with aiosqlite.connect(path) as db:
        cur = await db.execute(
            "SELECT id,person,amount,direction,due_date,note FROM debts WHERE user_id=? ORDER BY due_date",
            (user_id,)
        )
        return await cur.fetchall()

async def get_all_users(path: str = DB_PATH):
    async with aiosqlite.connect(path) as db:
        cur = await db.execute("SELECT user_id FROM users")
        return [r[0] for r in await cur.fetchall()]

async def count_users_and_transactions(path: str = DB_PATH):
    async with aiosqlite.connect(path) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        users = (await cur.fetchone())[0]
        cur = await db.execute("SELECT COUNT(*) FROM transactions")
        trans = (await cur.fetchone())[0]
        return users, trans