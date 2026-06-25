# HARAJAT Bot — Moliyaviy menejer

Telegram orqali shaxsiy harajat, daromad va qarzlarni boshqarish boti. Endi
**qarz daftari**, **avtomatik bildirishnoma**, **admin panel** va **umumiy
balans** bilan to'liq moliyaviy menejer holatiga keltirilgan.

## Fayllar tuzilishi (PAPKASIZ — mobil uchun qulay)

```
harajat_bot/
├── bot.py                   # Ishga tushirish nuqtasi
├── config.py                # Token, ADMIN_ID, bildirishnoma vaqti
├── database.py              # SQLite: users, transactions, debts
├── keyboards.py             # Barcha tugmalar
├── states.py                # FSM holatlari
├── utils.py                 # Formatlash/parsing yordamchilari
├── scheduler.py             # Kunlik qarz eslatmasi (APScheduler)
├── handlers_common.py       # /start, asosiy menyu
├── handlers_finance.py      # Harajat/daromad, hisobotlar, balans
├── handlers_debts.py        # Qarz daftari
├── handlers_admin.py        # Admin panel
├── requirements.txt
├── .env.example
└── README.md
```

> **Nega papka yo'q?** GitHub'ga mobil orqali "Upload files" qilinganda,
> fayl tanlagich papka tuzilishini saqlay olmaydi — barcha fayllar tepaga
> tushib qoladi. Shu sababli loyiha ataylab **bitta darajali** (flat)
> qilib qurilgan — endi qanday yuklasangiz ham muammo bo'lmaydi.

## O'rnatish (avvalgidan o'zgarmagan)

```bash
cd harajat_bot
pip install -r requirements.txt
```

`.env.example`ni `.env` deb nomlang va tokenni yozing:
```
BOT_TOKEN=...
```

Ishga tushirish:
```bash
python bot.py
```

## ⚠️ Hozirgi GitHub repozitoriyangizni TUZATISH (muhim!)

Hozir repozitoriyangizda `handlers` papkasiz, fayllar tepada noto'g'ri
nomlar bilan yotgan bo'lishi mumkin. Tuzatish uchun GitHub'da (mobil
brauzerda):

**1) Quyidagi ESKI fayllarni o'chiring** (har birining yonidagi ❌ tugmasini bosing):
- `__init__.py`
- `admin.py`
- `common.py`
- `debts.py`
- `finance.py`
- `_.env-2.example.txt` (bu ham kerak emas — token Railway Variables orqali kiritilgan)

**2) `bot.py` ni shu yangisi bilan ALMASHTIRING** (eski faylga bosib, "..." → "Delete" qiling, keyin yangisini yuklang — yoki to'g'ridan-to'g'ri ustiga "Upload files" qilsangiz, GitHub o'zi "almashtirilsinmi?" deb so'raydi)

**3) Quyidagi YANGI fayllarni qo'shing** (papkasiz, to'g'ridan-to'g'ri tepaga):
- `handlers_common.py`
- `handlers_finance.py`
- `handlers_debts.py`
- `handlers_admin.py`

**4) Commit qiling** — Railway avtomatik qayta build qiladi (Deployments bo'limida "Building" ko'rinadi, keyin "Active"/yashil bo'ladi)

Tokenni qayta kiritish kerak emas — u allaqachon Railway'ning Variables bo'limida saqlangan.

## Yangi imkoniyatlar

### 📒 Qarz daftari
| Tugma | Vazifasi |
|---|---|
| 🤝 Qarz berish | Ism → summa → kalendardan qaytarish sanasini tanlash |
| 📥 Qarz olish | Xuddi shunday, lekin "kimdan oldingiz" so'raladi |
| 📋 Qarzlar | Faol qarzlar ro'yxati (⏰ — muddati o'tgan). Har bir qatorni bosib, "qaytarildi" deb belgilash mumkin |

### ⏰ Avtomatik bildirishnoma
Har kuni soat **09:00** (Toshkent vaqti) bot tekshiradi: qaysi qarzlarning
qaytarish sanasi **aynan bugun** — shu foydalanuvchiga avtomatik xabar
yuboriladi. Bitta qarz uchun bildirishnoma faqat **bir marta** yuboriladi
(bot qayta ishga tushsa ham takrorlanmaydi).

> Vaqtni o'zgartirish uchun `config.py` faylida `REMINDER_HOUR` / `REMINDER_MINUTE`ni tahrirlang.

### 📈 Umumiy balans
Asosiy menyudagi yangi tugma — jami daromad, jami harajat, sof holat
(ortiqcha/kamomad) va qarzlar bo'yicha umumiy ko'rinishni bir joyda ko'rsatadi.

### 🛠 Admin panel
Faqat Telegram ID **`1691140865`** uchun ko'rinadi (asosiy menyuning oxirida
qo'shimcha tugma chiqadi):

| Bo'lim | Vazifasi |
|---|---|
| 📊 Statistika | Foydalanuvchilar soni, jami harajat/daromad, faol va yopilgan qarzlar |
| 📢 Xabar yuborish | Botdan foydalangan **barcha** foydalanuvchilarga bir vaqtda xabar yuborish |
| 👥 Foydalanuvchilar | Ism, username va ID bo'yicha ro'yxat (so'nggi 30 ta) |

Admin ID'ni o'zgartirish kerak bo'lsa — `config.py` faylidagi `ADMIN_ID` qiymatini tahrirlang.

## Texnik eslatmalar

- **Bildirishnoma ishlashi uchun** bot 24/7 ishlab turishi kerak (Railway'da bo'lsa avtomatik tayyor)
- **Ma'lumotlar bazasi** (`harajat.db`) Railway qayta deploy qilinganda tozalanib qolishi mumkin — bu xavfni yo'qotish uchun Railway'da **Volume** (doimiy xotira) qo'shish tavsiya etiladi
- Barcha summalar **butun so'm** ko'rinishida ishlaydi (tiyin/kasr son qo'llab-quvvatlanmaydi)

## Kengaytirish g'oyalari

- Harajat kategoriyalari bo'yicha statistika
- Excel/CSV eksport
- Oylik byudjet limiti va ogohlantirish
- Muddati o'tgan qarzlar uchun har kuni qaytariladigan eslatma (hozir faqat aynan muddat kunida yuboriladi)
