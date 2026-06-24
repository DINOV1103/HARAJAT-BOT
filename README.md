# HARAJAT Bot

Telegram orqali shaxsiy harajat va daromadlarni kuzatish boti.

## Fayllar tuzilishi

```
harajat_bot/
├── bot.py             # Asosiy fayl - shu faylni ishga tushirasiz
├── database.py        # SQLite bilan ishlash (avtomatik harajat.db fayl yaratiladi)
├── keyboards.py        # Tugmalar (klaviaturalar)
├── requirements.txt    # Kerakli kutubxonalar ro'yxati
├── .env.example         # Token qayerga yozilishini ko'rsatuvchi namuna
└── README.md
```

## 1-qadam: Bot tokenini olish

1. Telegram'da **@BotFather** ga yoziing
2. `/newbot` buyrug'ini yuboring
3. Bot uchun nom va username so'raydi (username "bot" bilan tugashi kerak, masalan: `mening_harajat_bot`)
4. BotFather sizga token beradi, masalan: `7123456789:AAExampleTokenHere`

## 2-qadam: Kompyuterga o'rnatish

Python 3.10+ kerak. Terminalda:

```bash
cd harajat_bot
pip install -r requirements.txt
```

## 3-qadam: Tokenni sozlash

`.env.example` faylini `.env` deb nomlang va ichidagi tokenni almashtiring:

```
BOT_TOKEN=7123456789:AAExampleTokenHere
```

## 4-qadam: Botni ishga tushirish

```bash
python bot.py
```

Konsolda xatolik chiqmasa, bot ishlay boshlaydi. Telegram'da botingizga `/start` yuboring.

## Botdan qanday foydalanish

| Tugma | Vazifasi |
|---|---|
| 💸 Harajat qo'shish | Bosgandan keyin summa va sababini yozasiz (masalan: `50000 taksi`) — bugungi kunga qo'shiladi |
| 💰 Daromad qo'shish | Bosgandan keyin summa va manbasini yozasiz (masalan: `500000 oylik`) — bugungi kunga qo'shiladi |
| 📊 Bugungi harajat | Bugun qilingan barcha harajatlar ro'yxati va jami summa |
| 📆 Haftalik harajat | Joriy hafta (dushanbadan bugungi kungacha) harajatlari, kun bo'yicha guruhlangan |
| 🗓 Oylik harajat | Joriy oy harajatlari, kun bo'yicha guruhlangan |
| 📅 Kalendar | Istalgan oy/kunni tanlab, o'sha kundagi harajat **va** daromadni ko'rish |

**Muhim:** Summa yozayotganda raqamni har doim **boshida** yozing. To'g'ri: `50000 taksi`. Noto'g'ri: `taksiga 50000`.

## Doimiy ishlashi uchun (24/7) — bepul variantlar

Kompyuteringiz o'chirilganda bot ham to'xtaydi. Doimiy ishlashi uchun bepul hosting variantlari:

- **Railway.app** — oyiga bepul limit beradi, GitHub orqali avtomatik deploy qiladi
- **Render.com** — "Background Worker" turida bepul tarif mavjud
- **PythonAnywhere** — kichik botlar uchun bepul tarif bor

Har birida: loyihani GitHub'ga yuklaysiz, keyin platforma orqali ulaysiz, `BOT_TOKEN`ni "Environment Variables" bo'limiga kiritasiz, `python bot.py` ni start buyrug'i sifatida belgilaysiz.

## Kengaytirish g'oyalari (xohlasangiz so'rang, qo'shib beraman)

- Harajat kategoriyalari (oziq-ovqat, transport, kiyim va h.k.) bo'yicha statistika
- Excel/CSV formatda hisobot eksport qilish
- Oylik byudjet belgilash va limitdan oshganda ogohlantirish
- Bir nechta valyutada hisob yuritish
- Daromad bo'yicha haftalik/oylik statistika tugmalari
