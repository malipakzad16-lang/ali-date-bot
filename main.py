
import os
import re
import json
import sqlite3
import secrets
from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
    ("birth_date", "تاریخ تولد", "لطفاً تاریخ تولد خود را به عدد ارسال کنید."),
    ("eye_color", "رنگ چشم", "لطفاً رنگ چشم خود را ارسال کنید."),
    ("height", "قد", "لطفاً قد خود را ارسال کنید."),
    ("weight", "وزن", "لطفاً وزن خود را ارسال کنید."),
    ("hair_color", "رنگ مو", "لطفاً رنگ موی خود را ارسال کنید."),
    ("hair_length", "اندازه مو", "لطفاً اندازه موی خود را ارسال کنید."),
    ("favorite_color", "رنگ مورد علاقه", "لطفاً رنگ مورد علاقه خود را ارسال کنید."),
    ("favorite_song", "آهنگ مورد علاقه", "لطفاً آهنگ مورد علاقه خود را ارسال کنید."),
    ("favorite_number", "عدد مورد علاقه", "لطفاً عدد مورد علاقه خود را ارسال کنید."),
    ("favorite_animal", "حیوان مورد علاقه", "لطفاً حیوان مورد علاقه خود را ارسال کنید."),
    ("username", "نام کاربری / آیدی", "خیلی هم عالی، اطلاعات ثبت شد!\nلطفاً نام کاربری (آیدی) خود را ارسال کنید."),
]

FIELD_MAP = {item[0]: item for item in FIELDS}


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                user_id INTEGER PRIMARY KEY,
                tracking_id TEXT NOT NULL,
                data TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'in_progress',
                updated_at TEXT NOT NULL
            )
        """)


def get_registration(user_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM registrations WHERE user_id = ?",
            (user_id,),
        ).fetchone()

    if not row:
        return None

    result = dict(row)
    result["data"] = json.loads(result["data"])
    return result


def save_registration(user_id, tracking_id, data, status="in_progress"):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO registrations
                (user_id, tracking_id, data, status, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                tracking_id = excluded.tracking_id,
                data = excluded.data,
                status = excluded.status,
                updated_at = excluded.updated_at
        """, (
            user_id,
            tracking_id,
            json.dumps(data, ensure_ascii=False),
            status,
            datetime.now(timezone.utc).isoformat(),
        ))


def make_tracking_id():
    return "ALI-" + secrets.token_hex(4).upper()


# ---------------- KEYBOARDS ----------------

def start_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("بله ✅", callback_data="start_yes"),
        InlineKeyboardButton("نخیر", callback_data="start_no"),
    ]])


def summary_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("تأیید ✅", callback_data="confirm_yes"),
            InlineKeyboardButton("تأیید نیست", callback_data="confirm_no"),
        ],
        [
            InlineKeyboardButton("ویرایش ✏️", callback_data="edit_open"),
        ],
    ])


def edit_keyboard():
    rows = []
    row = []

    for key, label, _ in FIELDS:
        row.append(
            InlineKeyboardButton(label, callback_data=f"edit:{key}")
        )
        if len(row) == 2:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    rows.append([
        InlineKeyboardButton("بازگشت به خلاصه", callback_data="edit_back")
    ])

    return InlineKeyboardMarkup(rows)


# ---------------- TEXTS ----------------

def make_summary(data, tracking_id):
    lines = [
        "📋 خلاصه اطلاعات ثبت‌شده",
        f"🔖 شماره پیگیری: {tracking_id}",
        "",
    ]

    for key, label, _ in FIELDS:
        lines.append(f"• {label}: {data.get(key, '—')}")

    lines.extend([
        "",
        "لطفاً اطلاعات خود را بررسی کنید.",
    ])

    return "\n".join(lines)


async def show_summary(message, user_id):
    registration = get_registration(user_id)

    if registration:
        await message.reply_text(
            make_summary(
                registration["data"],
                registration["tracking_id"],
            ),
            reply_markup=summary_keyboard(),
        )


# ---------------- COMMANDS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.effective_message.reply_text(
        "سلام!\nآیا برای ثبت دیت با علی آمده‌اید؟",
        reply_markup=start_keyboard(),
    )


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_summary(update.effective_message, update.effective_user.id)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.effective_message.reply_text(
        "روند فعلی متوقف شد. برای شروع دوباره /start را بزنید."
    )


# ---------------- BUTTON HANDLER ----------------

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    action = query.data

    # دکمه نخیر: پیام جدید نفرست؛ همان پنل را به پنل بله تبدیل کن
    if action == "start_no":
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("بله ✅", callback_data="start_yes")
            ]])
        )
        return

    # شروع ثبت‌نام
    if action == "start_yes":
        registration = get_registration(user_id)

        if registration and registration["status"] == "confirmed":
            await query.message.reply_text(
                "ثبت قبلی شما تأیید شده است. برای دیدن اطلاعات /summary را بزنید."
            )
            return

        tracking_id = (
            registration["tracking_id"]
            if registration
            else make_tracking_id()
        )
        data = registration["data"] if registration else {}

        first_missing = next(
            (
                i for i, (key, _, _) in enumerate(FIELDS)
                if not data.get(key)
            ),
            len(FIELDS),
        )

        save_registration(user_id, tracking_id, data, "in_progress")

        context.user_data["mode"] = "collect"
        context.user_data["field_index"] = first_missing
        context.user_data["tracking_id"] = tracking_id

        if first_missing >= len(FIELDS):
            context.user_data["mode"] = None
            await show_summary(query.message, user_id)
        else:
            await query.message.reply_text(FIELDS[first_missing][2])
        return

    # دکمه تأیید نیست
    if action == "confirm_no":
        await query.answer(
            "لطفاً دکمه تأیید را بزنید یا اطلاعات را ویرایش کنید.",
            show_alert=True,
        )
        return

    # تأیید نهایی
    if action == "confirm_yes":
        registration = get_registration(user_id)

        if not registration or any(
            not registration["data"].get(key)
            for key, _, _ in FIELDS
        ):
            await query.message.reply_text(
                "اطلاعات کامل نیست. لطفاً /start را بزنید."
            )
            return

        if registration["status"] == "confirmed":
            await query.message.reply_text(
                "اطلاعات شما قبلاً تأیید شده است. تشکر از همکاری تان."
            )
            return

        save_registration(
            user_id,
            registration["tracking_id"],
            registration["data"],
            "confirmed",
        )

        admin_lines = [
            "🆕 ثبت جدید تأیید شد",
            f"🔖 شماره پیگیری: {registration['tracking_id']}",
            f"👤 نام حساب تلگرام: {query.from_user.full_name}",
            f"🆔 آیدی عددی کاربر: {user_id}",
            "",
        ]

        for key, label, _ in FIELDS:
            admin_lines.append(
                f"• {label}: {registration['data'].get(key, '—')}"
            )

        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text="\n".join(admin_lines),
            )
        except Exception as error:
            print(f"Admin notification error: {error}")
            await query.message.reply_text(
                "ثبت شما تأیید شد، اما اعلان به مدیر ارسال نشد. "
                "مدیر باید ربات را باز کند و /start بزند."
            )

        await query.message.reply_text(
            "تشکر از همکاری تان.",
        )
        return

    # نمایش پنل ویرایش فقط از خلاصه اطلاعات
    if action == "edit_open":
        registration = get_registration(user_id)

        if not registration:
            await query.message.reply_text(
                "ابتدا /start را بزنید و اطلاعات خود را ثبت کنید."
            )
            return

        await query.message.reply_text(
            "کدام بخش را می‌خواهید ویرایش کنید؟",
            reply_markup=edit_keyboard(),
        )
        return

    if action == "edit_back":
        await show_summary(query.message, user_id)
        return

    # انتخاب بخش برای ویرایش
    if action.startswith("edit:"):
        key = action.split(":", 1)[1]

        if key not in FIELD_MAP:
            await query.message.reply_text("بخش انتخاب‌شده معتبر نیست.")
            return

        context.user_data["mode"] = "edit"
        context.user_data["edit_key"] = key

        await query.message.reply_text(
            f"لطفاً مقدار جدید برای «{FIELD_MAP[key][1]}» را ارسال کنید."
        )
        return


# ---------------- MESSAGE HANDLER ----------------

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    value = update.effective_message.text.strip()

    if not value:
        await update.effective_message.reply_text(
            "لطفاً یک مقدار معتبر ارسال کنید."
        )
        return

    registration = get_registration(user_id)

    if not registration:
        await update.effective_message.reply_text(
            "برای شروع /start را بزنید."
        )
        return

    data = registration["data"]
    tracking_id = registration["tracking_id"]
    mode = context.user_data.get("mode")

    # ویرایش یک فیلد
    if mode == "edit":
        key = context.user_data.get("edit_key")

        if key not in FIELD_MAP:
            await update.effective_message.reply_text(
                "لطفاً بخش موردنظر را از پنل ویرایش انتخاب کنید."
            )
            return

        if key == "birth_date" and not re.fullmatch(
            r"[0-9۰-۹٠-٩/.\-\s]+", value
        ):
            await update.effective_message.reply_text(
                "لطفاً تاریخ تولد را فقط به عدد ارسال کنید."
            )
            return

        data[key] = value

        # بعد از تغییر، تأیید قبلی باطل می‌شود
        save_registration(user_id, tracking_id, data, "in_progress")

        context.user_data["mode"] = None
        context.user_data.pop("edit_key", None)

        await update.effective_message.reply_text(
            "اطلاعات ویرایش شد."
        )
        await update.effective_message.reply_text(
            make_summary(data, tracking_id),
            reply_markup=summary_keyboard(),
        )
        return

    # ثبت اطلاعات به ترتیب
    if mode != "collect":
        await update.effective_message.reply_text(
            "برای ادامه از دکمه‌های ربات استفاده کنید یا /start را بزنید."
        )
        return

    index = context.user_data.get("field_index", 0)

    if index >= len(FIELDS):
        context.user_data["mode"] = None
        await show_summary(update.effective_message, user_id)
        return

    key, _label, _prompt = FIELDS[index]

    if key == "birth_date" and not re.fullmatch(
        r"[0-9۰-۹٠-٩/.\-\s]+", value
    ):
        await update.effective_message.reply_text(
            "لطفاً تاریخ تولد را فقط به عدد ارسال کنید."
        )
        return

    data[key] = value
    save_registration(user_id, tracking_id, data, "in_progress")

    index += 1
    context.user_data["field_index"] = index

    if index < len(FIELDS):
        await update.effective_message.reply_text(FIELDS[index][2])
    else:
        context.user_data["mode"] = None
        await update.effective_message.reply_text(
            "خیلی هم عالی، اطلاعات ثبت شد!"
        )
        await update.effective_message.reply_text(
            make_summary(data, tracking_id),
            reply_markup=summary_keyboard(),
        )


# ---------------- MAIN ----------------

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "متغیر محیطی BOT_TOKEN در Render تنظیم نشده است."
        )

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)
    )

    print("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
