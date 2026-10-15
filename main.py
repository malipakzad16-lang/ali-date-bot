
import os
import re
import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# توکن را در تنظیمات محیطی سرور وارد کن
TOKEN = os.environ.get("8978895008:AAEXtLajM1ey4kf5YysCS8qEenb-Bfwa9oU")

START, NAME, BIRTHDAY, EYE_COLOR, USERNAME, CONFIRM = range(6)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def digits_to_english(text: str) -> str:
    """تبدیل ارقام فارسی و عربی به ارقام انگلیسی."""
    table = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789",
    )
    return text.translate(table)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.clear()

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("بله ✅", callback_data="start_yes"),
            InlineKeyboardButton("نخیر ❌", callback_data="start_no"),
        ]
    ])

    await update.effective_message.reply_text(
        "سلام! 👋\n\n"
        "آیا برای ثبت دیت با علی آمده‌اید؟",
        reply_markup=keyboard,
    )
    return START


async def start_choice(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if query.data == "start_no":
        await query.answer(
            "این دکمه کار نمی‌کند! لطفاً دکمه بله را بزنید.",
            show_alert=True,
        )
        return START

    await query.answer()
    await query.edit_message_text(
        "خیلی هم عالی! 😊\n\n"
        "لطفاً نام خود را وارد کنید:"
    )
    return NAME


async def get_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    name = update.effective_message.text.strip()

    if not name:
        await update.effective_message.reply_text(
            "لطفاً نام خود را وارد کنید."
        )
        return NAME

    context.user_data["name"] = name

    await update.effective_message.reply_text(
        "لطفاً تاریخ تولد خود را به عدد ارسال کنید.\n"
        "مثال: 1388/05/12"
    )
    return BIRTHDAY


async def get_birthday(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    birthday = digits_to_english(
        update.effective_message.text.strip()
    )

    try:
        datetime.strptime(birthday, "%Y/%m/%d")
    except ValueError:
        await update.effective_message.reply_text(
            "تاریخ تولد معتبر نیست.\n"
            "لطفاً به شکل سال/ماه/روز ارسال کنید.\n"
            "مثال: 1388/05/12"
        )
        return BIRTHDAY

    context.user_data["birthday"] = birthday

    await update.effective_message.reply_text(
        "لطفاً رنگ چشم خود را ارسال کنید:"
    )
    return EYE_COLOR


async def get_eye_color(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    eye_color = update.effective_message.text.strip()

    if not eye_color:
        await update.effective_message.reply_text(
            "لطفاً رنگ چشم خود را ارسال کنید."
        )
        return EYE_COLOR

    context.user_data["eye_color"] = eye_color

    await update.effective_message.reply_text(
        "خیلی هم عالی! ✅ دیت ثبت شد.\n\n"
        "لطفاً نام کاربری (آیدی) تلگرام خود را ارسال کنید.\n"
        "مثال: @username"
    )
    return USERNAME


async def get_username(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    username = update.effective_message.text.strip()

    # اعتبارسنجی قالب آیدی تلگرام
    if not re.fullmatch(r"@[A-Za-z][A-Za-z0-9_]{4,31}", username):
        await update.effective_message.reply_text(
            "آیدی معتبر نیست.\n"
            "لطفاً آیدی را با @ ارسال کنید.\n"
            "مثال: @username"
        )
        return USERNAME

    context.user_data["username"] = username

    data = context.user_data

    report = (
        "📋 مشخصات ثبت‌شده شما:\n\n"
        f"👤 نام: {data['name']}\n"
        f"🎂 تاریخ تولد: {data['birthday']}\n"
        f"👁 رنگ چشم: {data['eye_color']}\n"
        f"🔗 آیدی تلگرام: {data['username']}\n\n"
        "آیا اطلاعات بالا درست است؟"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "تأیید است ✅",
                callback_data="confirm_yes",
            ),
            InlineKeyboardButton(
                "تأیید نیست ❌",
                callback_data="confirm_no",
            ),
        ]
    ])

    await update.effective_message.reply_text(
        report,
        reply_markup=keyboard,
    )
    return CONFIRM


async def confirm_choice(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if query.data == "confirm_no":
        await query.answer(
            "این دکمه کار نمی‌کند! لطفاً دکمه تأیید را بزنید.",
            show_alert=True,
        )
        return CONFIRM

    await query.answer()

    await query.edit_message_text(
        "✅ اطلاعات شما تأیید شد.\n\n"
        "🙏 تشکر از همکاری تان!\n"
        "ثبت دیت شما با موفقیت تکمیل شد."
    )

    logger.info(
        "Registration confirmed for Telegram user ID: %s",
        update.effective_user.id,
    )

    context.user_data.clear()
    return ConversationHandler.END


def main():
    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN تنظیم نشده است. "
            "توکن را در Environment Variables سرور وارد کنید."
        )

    app = Application.builder().token(TOKEN).build()

    conversation = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START: [
                CallbackQueryHandler(
                    start_choice,
                    pattern=r"^start_(yes|no)$",
                )
            ],
            NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_name,
                )
            ],
            BIRTHDAY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_birthday,
                )
            ],
            EYE_COLOR: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_eye_color,
                )
            ],
            USERNAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_username,
                )
            ],
            CONFIRM: [
                CallbackQueryHandler(
                    confirm_choice,
                    pattern=r"^confirm_(yes|no)$",
                )
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )

    app.add_handler(conversation)

    logger.info("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
