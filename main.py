import os, zipfile, textwrap, py_compile

base = "/mnt/data/ali_date_bot_source"
os.makedirs(base, exist_ok=True)

main_py = r'''import os
import re
import sqlite3
import secrets
from datetime import datetime, timezone

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = 8250229395
DB_PATH = os.environ.get("DB_PATH", "registrations.db")

FIELDS = [
    ("name", "نام", "لطفاً نام خود را وارد کنید."),
    ("birth_date", "تاریخ تولد", "لطفاً تاریخ تولد خود را به عدد ارسال کنید. مثال: 1388/05/12"),
    ("eye_color", "رنگ چشم", "لطفاً رنگ چشم خود را ارسال کنید."),
    ("height", "قد", "لطفاً قد خود را ارسال کنید. مثال: 175 سانتی‌متر"),
    ("weight", "وزن", "لطفاً وزن خود را ارسال کنید. مثال: 65 کیلوگرام"),
    ("hair_color", "رنگ مو", "لطفاً رنگ موی خود را ارسال کنید."),
    ("hair_length", "اندازه مو", "لطفاً اندازه موی خود را ارسال کنید."),
    ("favorite_color", "رنگ مورد علاقه", "لطفاً رنگ مورد علاقه خود را ارسال کنید."),
    ("favorite_song", "آهنگ مورد علاقه", "لطفاً نام آهنگ مورد علاقه خود را ارسال کنید."),
    ("favorite_number", "عدد مورد علاقه", "لطفاً عدد مورد علاقه خود را ارسال کنید."),
    ("favorite_animal", "حیوان مورد علاقه", "لطفاً حیوان مورد علاقه خود را ارسال کنید."),
    ("username", "نام کاربری / آیدی", "خیلی هم عالی، اطلاعات اولیه ثبت شد!\nلطفاً نام کاربری (آیدی) تلگرام خود را ارسال کنید. مثال: @username"),
]
FIELD_BY_KEY = {f[0]: f for f in FIELDS}
EDITABLE_FIELDS = FIELDS[:]  # all fields, including username

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                user_id INTEGER PRIMARY KEY,
                tracking_id TEXT NOT NULL,
                data TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'in_progress',
                updated_at TEXT NOT NULL
            )
        """)

def get_registration(user_id):
    import json
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM registrations WHERE user_id = ?", (user_id,)
        ).fetchone()
    if not row:
        return None
    result = dict(row)
    result["data"] = json.loads(result["data"] or "{}")
    return result

def save_registration(user_id, tracking_id, data, status="in_progress"):
    import json
    with db() as conn:
        conn.execute("""
            INSERT INTO registrations (user_id, tracking_id, data, status, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                tracking_id=excluded.tracking_id,
                data=excluded.data,
                status=excluded.status,
                updated_at=excluded.updated_at
        """, (
            user_id, tracking_id,
            json.dumps(data, ensure_ascii=False),
            status,
            datetime.now(timezone.utc).isoformat()
        ))

def new_tracking_id():
    return "ALI-" + secrets.token_hex(4).upper()

def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("بله ✅", callback_data="start_yes"),
            InlineKeyboardButton("نخیر", callback_data="start_no"),
        ]
    ])

def summary_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("تأیید ✅", callback_data="confirm_yes"),
            InlineKeyboardButton("تأیید نیست", callback_data="confirm_no"),
        ],
        [InlineKeyboardButton("ویرایش ✏️", callback_data="edit_open")],
    ])

def edit_keyboard():
    rows = []
    row = []
    for key, label, _prompt in EDITABLE_FIELDS:
        row.append(InlineKeyboardButton(label, callback_data=f"edit:{key}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("بازگشت به خلاصه", callback_data="edit_back")])
    return InlineKeyboardMarkup(rows)

def format_summary(data, tracking_id):
    lines = [
        "📋 خلاصه اطلاعات ثبت‌شده",
        f"🔖 شماره پیگیری: {tracking_id}",
        "",
    ]
    for key, label, _prompt in FIELDS:
        value = data.get(key, "—")
        lines.append(f"• {label}: {value}")
    lines += ["", "اگر اطلاعات درست است، روی «تأیید» بزنید."]
    return "\n".join(lines)

async def show_summary(update, context, user_id=None):
    user_id = user_id or update.effective_user.id
    reg = get_registration(user_id)
    if not reg:
        return
    text = format_summary(reg["data"], reg["tracking_id"])
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=summary_keyboard())
    else:
        await update.effective_message.reply_text(text, reply_markup=summary_keyboard())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "سلام!\nآیا برای ثبت دیت با علی آمده‌اید؟",
        reply_markup=main_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action = query.data

    if action == "start_no":
        await query.message.reply_text("این دکمه کار نمی‌کند؛ لطفاً برای ادامه روی دکمه «بله» بزنید.")
        return

    if action == "start_yes":
        reg = get_registration(user_id)
        tracking_id = reg["tracking_id"] if reg else new_tracking_id()
        data = reg["data"] if reg else {}
        save_registration(user_id, tracking_id, data, "in_progress")
        context.user_data["mode"] = "collect"
        context.user_data["field_index"] = 0
        context.user_data["tracking_id"] = tracking_id
        context.user_data["data"] = data
        await query.message.reply_text(FIELDS[0][2])
        return

    if action == "confirm_no":
        await query.message.reply_text("این دکمه برای تأیید استفاده نمی‌شود؛ لطفاً اگر اطلاعات درست است روی «تأیید» بزنید یا از «ویرایش» استفاده کنید.")
        return

    if action == "confirm_yes":
        reg = get_registration(user_id)
        if not reg or any(not reg["data"].get(k) for k, _, _ in FIELDS):
            await query.message.reply_text("اطلاعات کامل نیست. لطفاً /start را بزنید و ثبت‌نام را تکمیل کنید.")
            return
        save_registration(user_id, reg["tracking_id"], reg["data"], "confirmed")
        admin_text = (
            "🆕 ثبت جدید تأیید شد\n"
            f"🔖 شماره پیگیری: {reg['tracking_id']}\n"
            f"👤 نام تلگرام: {query.from_user.full_name}\n"
            f"🆔 آیدی عددی کاربر: {user_id}\n\n"
            + "\n".join(f"• {label}: {reg['data'].get(key, '—')}" for key, label, _ in FIELDS)
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text)
        except Exception:
            await query.message.reply_text(
                "ثبت شما تأیید شد، اما پیام به مدیر ارسال نشد. لطفاً به مدیر اطلاع دهید که ربات را باز کند و /start بزند."
            )
            await query.message.reply_text("تشکر از همکاری تان.", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ویرایش ✏️", callback_data="edit_open")]
            ]))
            return
        await query.message.reply_text(
            "تشکر از همکاری تان.\nاطلاعات شما با موفقیت تأیید شد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ویرایش ✏️", callback_data="edit_open")]
            ])
        )
        return

    if action == "edit_open":
        await query.message.reply_text("کدام بخش را می‌خواهید ویرایش کنید؟", reply_markup=edit_keyboard())
        return

    if action == "edit_back":
        await show_summary(update, context, user_id)
        return

    if action.startswith("edit:"):
        key = action.split(":", 1)[1]
        if key not in FIELD_BY_KEY:
            await query.message.reply_text("این بخش پیدا نشد. لطفاً دوباره انتخاب کنید.")
            return
        context.user_data["mode"] = "edit"
        context.user_data["edit_key"] = key
        await query.message.reply_text(f"لطفاً مقدار جدید برای «{FIELD_BY_KEY[key][1]}» را ارسال کنید.")
        return

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    value = update.message.text.strip()
    if not value:
        await update.message.reply_text("لطفاً یک مقدار معتبر ارسال کنید.")
        return

    mode = context.user_data.get("mode")
    reg = get_registration(user_id)
    if not reg:
        await update.message.reply_text("برای شروع ثبت‌نام /start را بزنید.")
        return

    data = reg["data"]
    tracking_id = reg["tracking_id"]

    if mode == "edit":
        key = context.user_data.get("edit_key")
        if key not in FIELD_BY_KEY:
            await update.message.reply_text("لطفاً از دکمه ویرایش، بخش موردنظر را انتخاب کنید.")
            return
        if key == "birth_date" and not re.fullmatch(r"[0-9۰-۹٠-٩/.\-\s]+", value):
            await update.message.reply_text("تاریخ تولد را فقط با عدد ارسال کنید. مثال: 1388/05/12")
            return
        data[key] = value
        save_registration(user_id, tracking_id, data, "in_progress")
        context.user_data["mode"] = None
        await update.message.reply_text("اطلاعات ویرایش شد.")
        await update.message.reply_text(format_summary(data, tracking_id), reply_markup=summary_keyboard())
        return

    if mode != "collect":
        await update.message.reply_text("برای ادامه، از دکمه‌های ربات استفاده کنید یا /start را بزنید.")
        return

    index = context.user_data.get("field_index", 0)
    if index >= len(FIELDS):
        await update.message.reply_text(format_summary(data, tracking_id), reply_markup=summary_keyboard())
        return

    key, label, prompt = FIELDS[index]
    if key == "birth_date" and not re.fullmatch(r"[0-9۰-۹٠-٩/.\-\s]+", value):
        await update.message.reply_text("تاریخ تولد را به عدد ارسال کنید. مثال: 1388/05/12")
        return

    data[key] = value
    save_registration(user_id, tracking_id, data, "in_progress")
    index += 1
    context.user_data["field_index"] = index

    if index < len(FIELDS):
        await update.message.reply_text(FIELDS[index][2])
    else:
        context.user_data["mode"] = None
        await update.message.reply_text("خیلی هم عالی، اطلاعات ثبت شد!")
        await update.message.reply_text(format_summary(data, tracking_id), reply_markup=summary_keyboard())

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("روند فعلی متوقف شد. برای شروع دوباره /start را بزنید.")

def main():
    if not BOT_TOKEN:
        raise RuntimeError("متغیر محیطی BOT_TOKEN تنظیم نشده است.")
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    print("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
'''

requirements = "python-telegram-bot==22.5\n"

readme = r'''# ربات ثبت دیت با علی

## فایل‌ها
- `main.py`: سورس اصلی ربات
- `requirements.txt`: کتابخانه موردنیاز

## تنظیم در Render
- Build Command:
  `pip install -r requirements.txt`
- Start Command:
  `python main.py`
- Environment Variable:
  - Key: `BOT_TOKEN`
  - Value: توکن ربات از BotFather

## مدیر
اعلان ثبت جدید به آیدی عددی `8250229395` فرستاده می‌شود. مدیر باید یک‌بار ربات را باز کند و `/start` بزند تا امکان پیام‌دادن به او فراهم شود.

## نکته ذخیره‌سازی
این نسخه از SQLite استفاده می‌کند. روی سرویس‌های میزبانی رایگان، فایل محلی ممکن است در بعضی شرایط از بین برود یا پس از استقرار تازه حفظ نشود. برای نگهداری مطمئن اطلاعات، دیسک پایدار Render یا دیتابیس مدیریت‌شده تنظیم کنید.

## اجرا در کامپیوتر
```bash
pip install -r requirements.txt
```
متغیر محیطی `BOT_TOKEN` را تنظیم کنید، سپس:
```bash
python main.py
```

توکن ربات را در کد ننویسید و با کسی شریک نکنید.
'''

with open(os.path.join(base, "main.py"), "w", encoding="utf-8") as f:
    f.write(main_py)
with open(os.path.join(base, "requirements.txt"), "w", encoding="utf-8") as f:
    f.write(requirements)
with open(os.path.join(base, "README.txt"), "w", encoding="utf-8") as f:
    f.write(readme)

# Syntax-check the Python source without executing it.
py_compile.compile(os.path.join(base, "main.py"), doraise=True)

zip_path = "/mnt/data/ali_date_bot_source.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for filename in ["main.py", "requirements.txt", "README.txt"]:
        z.write(os.path.join(base, filename), arcname=filename)

print("Created and syntax-checked:", zip_path)
print("Files:", ", ".join(["main.py", "requirements.txt", "README.txt"]))
