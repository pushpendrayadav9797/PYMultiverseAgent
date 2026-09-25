import os
import threading
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)


# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
FORCE_JOIN_CHANNEL = os.getenv("FORCE_JOIN_CHANNEL")

STORAGE_CHANNEL_ID = int(
    os.getenv("STORAGE_CHANNEL_ID", "-1003968203837")
)


# =========================================================
# CHECK USER JOIN
# =========================================================

async def is_joined(bot, user_id):

    try:

        member = await bot.get_chat_member(
            FORCE_JOIN_CHANNEL,
            user_id
        )

        return member.status in (
            "member",
            "administrator",
            "creator"
        )

    except Exception as e:

        print("JOIN CHECK ERROR:", e)

        return False


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.message is None:
        return

    user = update.effective_user
    args = context.args

    # Normal /start
    if not args:

        await update.message.reply_text(
            "👋 Welcome to PY Multiverse Agent!\n\n"
            "📁 Send or forward a file.\n"
            "🔗 You can also send a Google Drive or other URL.\n\n"
            "I will generate a link for you."
        )

        return

    payload = args[0]

    # =====================================================
    # FORCE JOIN
    # =====================================================

    if not await is_joined(
        context.bot,
        user.id
    ):

        channel_username = FORCE_JOIN_CHANNEL.lstrip("@")

        keyboard = [
            [
                InlineKeyboardButton(
                    "📢 Join Channel",
                    url=f"https://t.me/{channel_username}"
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ I've Joined",
                    callback_data=f"check_{payload}"
                )
            ]
        ]

        await update.message.reply_text(
            "🔒 Please join our channel first.\n\n"
            "Join the channel and then press "
            "\"I've Joined\".",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

        return

    # =====================================================
    # DELIVER STORED MESSAGE
    # =====================================================

    try:

        message_id = int(payload)

        await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=STORAGE_CHANNEL_ID,
            message_id=message_id
        )

    except Exception as e:

        print("START DELIVERY ERROR:", e)

        await update.message.reply_text(
            "❌ This link is invalid or expired."
        )


# =========================================================
# JOIN CHECK BUTTON
# =========================================================

async def check_join(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    payload = query.data.replace(
        "check_",
        "",
        1
    )

    user = query.from_user

    # =====================================================
    # CHECK JOIN AGAIN
    # =====================================================

    if not await is_joined(
        context.bot,
        user.id
    ):

        await query.answer(
            "❌ You haven't joined the channel yet.",
            show_alert=True
        )

        return

    # =====================================================
    # SEND FILE / URL
    # =====================================================

    try:

        message_id = int(payload)

        await context.bot.copy_message(
            chat_id=user.id,
            from_chat_id=STORAGE_CHANNEL_ID,
            message_id=message_id
        )

        try:

            await query.message.delete()

        except Exception:
            pass

    except Exception as e:

        print("CHECK JOIN DELIVERY ERROR:", e)

        try:

            await query.message.reply_text(
                "❌ File/link is invalid or expired."
            )

        except Exception:
            pass


# =========================================================
# URL DETECTION
# =========================================================

def extract_url(text):

    if not text:
        return None

    # Find normal web URLs
    pattern = r'https?://[^\s]+'

    match = re.search(
        pattern,
        text
    )

    if match:

        return match.group(0).rstrip(
            ".,!?)]}"
        )

    return None


# =========================================================
# CREATE LINK
# =========================================================

async def make_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_chat.type != "private":
        return

    message = update.message

    if message is None:
        return

    try:

        stored_message = None

        # =================================================
        # DOCUMENT
        # PDF / ZIP / APK / DOC / ETC.
        # =================================================

        if message.document:

            stored_message = await context.bot.send_document(
                chat_id=STORAGE_CHANNEL_ID,
                document=message.document.file_id,
                caption=message.caption
            )

        # =================================================
        # VIDEO
        # =================================================

        elif message.video:

            stored_message = await context.bot.send_video(
                chat_id=STORAGE_CHANNEL_ID,
                video=message.video.file_id,
                caption=message.caption
            )

        # =================================================
        # AUDIO
        # =================================================

        elif message.audio:

            stored_message = await context.bot.send_audio(
                chat_id=STORAGE_CHANNEL_ID,
                audio=message.audio.file_id,
                caption=message.caption
            )

        # =================================================
        # VOICE
        # =================================================

        elif message.voice:

            stored_message = await context.bot.send_voice(
                chat_id=STORAGE_CHANNEL_ID,
                voice=message.voice.file_id
            )

        # =================================================
        # PHOTO
        # =================================================

        elif message.photo:

            stored_message = await context.bot.send_photo(
                chat_id=STORAGE_CHANNEL_ID,
                photo=message.photo[-1].file_id,
                caption=message.caption
            )

        # =================================================
        # ANIMATION / GIF
        # =================================================

        elif message.animation:

            stored_message = await context.bot.send_animation(
                chat_id=STORAGE_CHANNEL_ID,
                animation=message.animation.file_id,
                caption=message.caption
            )

        # =================================================
        # VIDEO NOTE
        # =================================================

        elif message.video_note:

            stored_message = await context.bot.send_video_note(
                chat_id=STORAGE_CHANNEL_ID,
                video_note=message.video_note.file_id
            )

        # =================================================
        # STICKER
        # =================================================

        elif message.sticker:

            stored_message = await context.bot.send_sticker(
                chat_id=STORAGE_CHANNEL_ID,
                sticker=message.sticker.file_id
            )

        # =================================================
        # URL
        # GOOGLE DRIVE / WEBSITE / TELEGRAM / ETC.
        # =================================================

        elif message.text:

            url = extract_url(
                message.text
            )

            if not url:

                await message.reply_text(
                    "❌ Is message me koi valid URL nahi mila.\n\n"
                    "📁 File bhejo ya\n"
                    "🔗 https:// se start hone wala link bhejo."
                )

                return

            # Store the URL as a message
            stored_message = await context.bot.send_message(
                chat_id=STORAGE_CHANNEL_ID,
                text=message.text
            )

        # =================================================
        # UNSUPPORTED
        # =================================================

        else:

            await message.reply_text(
                "❌ Ye message/file type supported nahi hai."
            )

            return

        # =================================================
        # GENERATE TELEGRAM LINK
        # =================================================

        bot_info = await context.bot.get_me()

        bot_username = bot_info.username

        file_link = (
            f"https://t.me/{bot_username}"
            f"?start={stored_message.message_id}"
        )

        await message.reply_text(
            "✅ Link successfully generated!\n\n"
            f"🔗 {file_link}"
        )

    except Exception as e:

        print(
            "MAKE LINK ERROR:",
            repr(e)
        )

        await message.reply_text(
            "❌ Link create nahi ho paya.\n\n"
            "Check karo ki bot Storage Channel ka admin hai."
        )


# =========================================================
# /ID
# =========================================================

async def get_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.message is None:
        return

    chat = update.effective_chat

    await update.message.reply_text(
        f"🆔 Chat ID:\n`{chat.id}`",
        parse_mode="Markdown"
    )


# =========================================================
# RENDER HEALTH SERVER
# =========================================================

class HealthHandler(
    BaseHTTPRequestHandler
):

    def do_GET(self):

        self.send_response(200)

        self.send_header(
            "Content-type",
            "text/plain"
        )

        self.end_headers()

        self.wfile.write(
            b"PY Multiverse Agent is running!"
        )

    def log_message(
        self,
        format,
        *args
    ):
        return


def start_health_server():

    port = int(
        os.environ.get(
            "PORT",
            "10000"
        )
    )

    server = ThreadingHTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True
    )

    thread.start()

    print(
        f"Health server running on port {port}"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    if not BOT_TOKEN:

        print(
            "ERROR: BOT_TOKEN is missing."
        )

        return

    if not FORCE_JOIN_CHANNEL:

        print(
            "ERROR: FORCE_JOIN_CHANNEL is missing."
        )

        return

    if not STORAGE_CHANNEL_ID:

        print(
            "ERROR: STORAGE_CHANNEL_ID is missing."
        )

        return

    # Start Render health server
    start_health_server()

    # Create application
    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # /start
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # /id
    app.add_handler(
        CommandHandler(
            "id",
            get_id
        )
    )

    # Join verification
    app.add_handler(
        CallbackQueryHandler(
            check_join,
            pattern=r"^check_"
        )
    )

    # Files + URLs + forwards
    app.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE
            & ~filters.COMMAND,
            make_link
        )
    )

    print(
        "PY Multiverse Agent started..."
    )

    app.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
