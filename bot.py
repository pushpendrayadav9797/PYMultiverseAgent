import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
FORCE_JOIN_CHANNEL = os.getenv("FORCE_JOIN_CHANNEL")   # example: @PYMultiverseBooks
STORAGE_CHANNEL_ID = int(os.getenv("STORAGE_CHANNEL_ID"))


async def is_joined(bot, user_id):
    try:
        member = await bot.get_chat_member(FORCE_JOIN_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    # Normal /start
    if not args:
        await update.message.reply_text(
            "👋 Welcome to PY Multiverse!\n\n"
            "📄 File Link Bot is ready.\n"
            "Send me a file to generate its link."
        )
        return

    # Force Join check
    if not await is_joined(context.bot, user.id):
        keyboard = [
            [
                InlineKeyboardButton(
                    "📢 Join Channel",
                    url=f"https://t.me/{FORCE_JOIN_CHANNEL.lstrip('@')}"
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ I've Joined",
                    callback_data=f"check_{args[0]}"
                )
            ],
        ]

        await update.message.reply_text(
            "🔒 Please join our channel first.\n\n"
            "After joining, press **I've Joined**.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    # File link
    try:
        message_id = int(args[0])

        await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=STORAGE_CHANNEL_ID,
            message_id=message_id,
        )

    except Exception:
        await update.message.reply_text(
            "❌ This file link is invalid or the file is no longer available."
        )


async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    payload = query.data.replace("check_", "", 1)

    if not await is_joined(context.bot, user.id):
        await query.answer(
            "❌ You haven't joined the channel yet.",
            show_alert=True,
        )
        return

    try:
        await context.bot.copy_message(
            chat_id=user.id,
            from_chat_id=STORAGE_CHANNEL_ID,
            message_id=int(payload),
        )

        await query.message.delete()

    except Exception:
        await query.message.reply_text(
            "❌ File link is invalid or expired."
        )


async def make_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    try:
        copied = await context.bot.copy_message(
            chat_id=STORAGE_CHANNEL_ID,
            from_chat_id=message.chat_id,
            message_id=message.message_id,
        )

        bot_username = (await context.bot.get_me()).username

        link = f"https://t.me/{bot_username}?start={copied.message_id}"

        await message.reply_text(
            "✅ File Link Generated!\n\n"
            f"🔗 {link}\n\n"
            "Anyone opening this link will need to join the channel first."
        )

    except Exception as e:
        await message.reply_text(
            "❌ Error while creating link."
        )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, make_link))

    app.add_handler(
        __import__("telegram.ext", fromlist=["CallbackQueryHandler"])
        .CallbackQueryHandler(check_join, pattern=r"^check_")
    )

    print("PY Multiverse File Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
