
import os
import logging

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

TOKEN = os.environ.get("BOT_TOKEN")

(
    START, NAME, BIRTHDAY, EYE_COLOR, HEIGHT, WEIGHT,
    HAIR_COLOR, HAIR_LENGTH, FAVORITE_COLOR, FAVORITE_SONG,
    FAVORITE_NUMBER, FAVORITE_ANIMAL, USERNAME, CONFIRM
) = range(14)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def digits_to_english(text):
    table = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789",
    )
    return text.translate(table)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("بله ✅", callback_data="yes"),
            InlineKeyboardButton("نخیر ❌", callback_data="no"),
        ]
    ]

    await update.message.reply_text(
        "آیا برای ثبت دیت با علی آمده‌اید؟",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return START


async def start_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.data == "no":
        await query.answer(
            "باید دکمه بله را بزنید.",
            show_alert=True,
        )
        return START

    await query.answer()
    await query.edit_message_text("عالی! لطفاً نام خود را بنویسید:")
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("تاریخ تولد خود را به شکل عددی بنویسید؛ مثلاً 1388/05/12")
    return BIRTHDAY


async def get_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["birthday"] = digits_to_english(update.message.text.strip())
    await update.message.reply_text("رنگ چشم شما چیست؟")
    return EYE_COLOR


async def get_eye_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["eye_color"] = update.message.text.strip()
    await update.message.reply_text("قد شما چند سانتی‌متر است؟")
    return HEIGHT


async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["height"] = update.message.text.strip()
    await update.message.reply_text("وزن شما چند کیلوگرم است؟")
    return WEIGHT


async def get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["weight"] = update.message.text.strip()
    await update.message.reply_text("رنگ موی شما چیست؟")
    return HAIR_COLOR


async def get_hair_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["hair_color"] = update.message.text.strip()
    await update.message.reply_text("اندازه موی شما چقدر است؟")
    return HAIR_LENGTH


async def get_hair_length(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["hair_length"] = update.message.text.strip()
    await update.message.reply_text("رنگ موردعلاقه شما چیست؟")
    return FAVORITE_COLOR


async def get_favorite_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["favorite_color"] = update.message.text.strip()
    await update.message.reply_text("آهنگ موردعلاقه شما چیست؟")
    return FAVORITE_SONG


async def get_favorite_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["favorite_song"] = update.message.text.strip()
    await update.message.reply_text("عدد موردعلاقه شما چیست؟")
    return FAVORITE_NUMBER


async def get_favorite_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["favorite_number"] = digits_to_english(
        update.message.text.strip()
    )
    await update.message.reply_text("حیوان موردعلاقه شما چیست؟")
    return FAVORITE_ANIMAL


async def get_favorite_animal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["favorite_animal"] = update.message.text.strip()

    await update.message.reply_text(
        "خیلی هم عالی! دیت ثبت شد 😊\n\n"
        "حالا نام کاربری تلگرام یا آیدی خود را بنویسید:"
    )
    return USERNAME


async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["username"] = update.message.text.strip()

    d = context.user_data

    summary = (
        "📋 اطلاعات ثبت‌شده شما:\n\n"
        f"👤 نام: {d['name']}\n"
        f"🎂 تاریخ تولد: {d['birthday']}\n"
        f"👁 رنگ چشم: {d['eye_color']}\n"
        f"📏 قد: {d['height']}\n"
        f"⚖️ وزن: {d['weight']}\n"
        f"💇 رنگ مو: {d['hair_color']}\n"
        f"💇 اندازه مو: {d['hair_length']}\n"
        f"🎨 رنگ موردعلاقه: {d['favorite_color']}\n"
        f"🎵 آهنگ موردعلاقه: {d['favorite_song']}\n"
        f"🔢 عدد موردعلاقه: {d['favorite_number']}\n"
        f"🐾 حیوان موردعلاقه: {d['favorite_animal']}\n"
        f"📱 نام کاربری یا آیدی: {d['username']}\n\n"
        "آیا اطلاعات بالا درست است؟"
    )

    keyboard = [
        [
            InlineKeyboardButton("تأیید است ✅", callback_data="confirm_yes"),
            InlineKeyboardButton("تأیید نیست ❌", callback_data="confirm_no"),
        ]
    ]

    await update.message.reply_text(
        summary,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CONFIRM


async def confirm_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.data == "confirm_no":
        await query.answer(
            "این دکمه فعلاً کار نمی‌کند؛ لطفاً تأیید است را بزنید.",
            show_alert=True,
        )
        return CONFIRM

    await query.answer()
    await query.edit_message_text(
        "ممنون از شما! ❤️\nاطلاعات شما تأیید شد و دیت با موفقیت ثبت گردید."
    )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("فرایند ثبت متوقف شد. برای شروع دوباره /start را بزنید.")
    context.user_data.clear()
    return ConversationHandler.END


def main():
    if not TOKEN:
        raise RuntimeError(
            "توکن تنظیم نشده است؛ متغیر BOT_TOKEN را در Render بررسی کنید."
        )

    app = Application.builder().token(TOKEN).build()

    conversation = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START: [CallbackQueryHandler(start_choice, pattern="^(yes|no)$")],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            BIRTHDAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_birthday)],
            EYE_COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_eye_color)],
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_height)],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_weight)],
            HAIR_COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_hair_color)],
            HAIR_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_hair_length)],
            FAVORITE_COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_favorite_color)],
            FAVORITE_SONG: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_favorite_song)],
            FAVORITE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_favorite_number)],
            FAVORITE_ANIMAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_favorite_animal)],
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)],
            CONFIRM: [CallbackQueryHandler(
                confirm_choice,
                pattern="^(confirm_yes|confirm_no)$"
            )],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conversation)
    logger.info("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
