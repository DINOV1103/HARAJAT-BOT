"""
Formatlash va matnni tahlil qilish uchun yordamchi funksiyalar.
"""

import re


def format_amount(amount: float) -> str:
    return f"{int(amount):,}".replace(",", " ") + " so'm"


def format_date_human(date_str: str) -> str:
    y, m, d = date_str.split("-")
    return f"{d}.{m}.{y}"


def parse_amount_and_description(text: str):
    """
    '50000 taksi' -> (50000.0, 'taksi')
    Summa har doim xabar boshida bo'lishi kerak.
    """
    text = (text or "").strip()
    match = re.match(r"^([\d\s.,]+)\s*(.*)$", text)
    if not match:
        return None, None
    raw_number = match.group(1)
    description = match.group(2).strip() or "Izohsiz"
    clean_number = re.sub(r"[\s.,]", "", raw_number)
    if not clean_number.isdigit() or clean_number == "":
        return None, None
    amount = float(clean_number)
    if amount <= 0:
        return None, None
    return amount, description


def parse_plain_amount(text: str):
    """Faqat summa kutilganda ishlatiladi (masalan, qarz summasi)."""
    text = (text or "").strip()
    clean_number = re.sub(r"[\s.,]", "", text)
    if not clean_number.isdigit() or clean_number == "":
        return None
    amount = float(clean_number)
    if amount <= 0:
        return None
    return amount
