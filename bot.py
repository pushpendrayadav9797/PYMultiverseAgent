import os
import re
import threading
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

FORCE_JOIN_CHANNEL = os.getenv(
    "FORCE_JOIN_CHANNEL"
)

STORAGE_CHANNEL_ID = int(
    os.getenv(
        "STORAGE_CHANNEL_ID",
        "-1003968203837"
    )
)


# =========================================================
# FORCE JOIN CHECK
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

        print(
            "JOIN CHECK ERROR:",
            repr(e)
        )

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

    # -----------------------------------------------------
    # NORMAL /START
    # -----------------------------------------------------

    if not args:

        await update.message.reply_text(
            "👋 Welcome to PY Multiverse Agent!\n\n"
            "📁 Send or forward me a file.\n"
            "🔗 You can also send any URL.\n\n"
            "I will generate a link for you."
        )

        return

    # Link payload
    payload = args[0]

    # -----------------------------------------------------
    # FORCE JOIN
    # -----------------------------------------------------

    if not await is_joined(
        context.bot,
        user.id
    ):

        channel_username = (
            FORCE_JOIN_CHANNEL.lstrip("@")
        )

        keyboard = [

            [
                InlineKeyboardButton(
                    "📢 Join Channel",
                    url=(
                        f"https://t.me/"
                        f"{channel_username}"
                    )
                )
            ],

            [
                InlineKeyboardButton(
                    "✅ I've Joined",
                    callback_data=(
                        f"check_{payload}"
                    )
                )
            ]

        ]

        await update.message.reply_text(
            "🔒 Please join our channel first.\n\n"
            "Join the channel and then press "
            "\"I've Joined\".",
            reply_markup=(
                InlineKeyboardMarkup(
                    keyboard
                )
            )
        )

        return

    # -----------------------------------------------------
    # DELIVER STORED MESSAGE
    # -----------------------------------------------------

    try:

        message_id = int(payload)

        await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=STORAGE_CHANNEL_ID,
            message_id=message_id
        )

    except Exception as e:

        print(
            "START DELIVERY ERROR:",
            repr(e)
        )

        await update.message.reply_text(
            "❌ This link is invalid or expired."
        )


# =========================================================
# JOIN VERIFICATION BUTTON
# =========================================================

async def check_join(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    payload = query.data.replace(
        "check_",
        "",
        1
    )

    user = query.from_user

    # -----------------------------------------------------
    # CHECK JOIN
    # -----------------------------------------------------

    if not await is_joined(
        context.bot,
        user.id
    ):

        await query.answer(
            "❌ You haven't joined the channel yet.",
            show_alert=True
        )

        return

    await query.answer(
        "✅ Verified!"
    )

    # -----------------------------------------------------
    # SEND STORED FILE / URL
    # -----------------------------------------------------

    try:

        message_id = int(payload)

        await context.bot.copy_message(
            chat_id=user.id,
            from_chat_id=STORAGE_CHANNEL_ID,
            message_id=message_id
        )

        # Delete join message
        try:

            await query.message.delete()

        except Exception:
            pass

    except Exception as e:

        print(
            "CHECK JOIN DELIVERY ERROR:",
            repr(e)
        )

        try:

            await query.message.reply_text(
                "❌ File/link is invalid or expired."
            )

        except Exception:
            pass


# =========================================================
# URL DETECTOR
# =========================================================

def extract_url(text):

    if not text:
        return None

    pattern = r"https?://[^\s]+"

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
#
# Supports:
# Direct files
# Forwarded files
# Photos
# Videos
# Audio
# Documents
# APK
# ZIP
# GIF
# Voice
# Video Note
# Stickers
# Google Drive URL
# Any HTTPS URL
# =========================================================

async def make_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    # Only private chat
    if update.effective_chat.type != "private":
        return

    message = update.message

    if message is None:
        return

    try:

        stored_message = None

        # =================================================
        # 1. DOCUMENT
        #
        # PDF / DOC / ZIP / APK / RAR / etc.
        #
        # DIRECT + FORWARDED BOTH
        # =================================================

        if message.document:

            print(
                "DOCUMENT RECEIVED"
            )

            stored_message = (
                await context.bot.send_document(
                    chat_id=STORAGE_CHANNEL_ID,
                    document=(
                        message.document.file_id
                    ),
                    caption=message.caption
                )
            )

        # =================================================
        # 2. VIDEO
        #
        # DIRECT + FORWARDED BOTH
        # =================================================

        elif message.video:

            print(
                "VIDEO RECEIVED"
            )

            stored_message = (
                await context.bot.send_video(
                    chat_id=STORAGE_CHANNEL_ID,
                    video=message.video.file_id,
                    caption=message.caption
                )
            )

        # =================================================
        # 3. AUDIO
        #
        # DIRECT + FORWARDED BOTH
        # =================================================

        elif message.audio:

            print(
                "AUDIO RECEIVED"
            )

            stored_message = (
                await context.bot.send_audio(
                    chat_id=STORAGE_CHANNEL_ID,
                    audio=message.audio.file_id,
                    caption=message.caption
                )
            )

        # =================================================
        # 4. PHOTO
        #
        # DIRECT + FORWARDED BOTH
        # =================================================

        elif message.photo:

            print(
                "PHOTO RECEIVED"
            )

            stored_message = (
                await context.bot.send_photo(
                    chat_id=STORAGE_CHANNEL_ID,
                    photo=(
                        message.photo[-1].file_id
                    ),
                    caption=message.caption
                )
            )

        # =================================================
        # 5. ANIMATION / GIF
        #
        # DIRECT + FORWARDED BOTH
        # =================================================

        elif message.animation:

            print(
                "ANIMATION RECEIVED"
            )

            stored_message = (
                await context.bot.send_animation(
                    chat_id=STORAGE_CHANNEL_ID,
                    animation=(
                        message.animation.file_id
                    ),
                    caption=message.caption
                )
            )

        # =================================================
        # 6. VOICE
        #
        # DIRECT + FORWARDED BOTH
        # =================================================

        elif message.voice:

            print(
                "VOICE RECEIVED"
            )

            stored_message = (
                await context.bot.send_voice(
                    chat_id=STORAGE_CHANNEL_ID,
                    voice=message.voice.file_id
                )
            )

        # =================================================
        # 7. VIDEO NOTE
        #
        # DIRECT + FORWARDED BOTH
        # =================================================

        elif message.video_note:

            print(
                "VIDEO NOTE RECEIVED"
            )

            stored_message = (
                await context.bot.send_video_note(
                    chat_id=STORAGE_CHANNEL_ID,
                    video_note=(
                        message.video_note.file_id
                    )
                )
            )

        # =================================================
        # 8. STICKER
        #
        # DIRECT + FORWARDED BOTH
        # =================================================

        elif message.sticker:

            print(
                "STICKER RECEIVED"
            )

            stored_message = (
                await context.bot.send_sticker(
                    chat_id=STORAGE_CHANNEL_ID,
                    sticker=(
                        message.sticker.file_id
                    )
                )
            )

        # =================================================
        # 9. TEXT URL
        #
        # GOOGLE DRIVE
        # MEGA
        # WEBSITE
        # TELEGRAM URL
        # ANY HTTPS URL
        # =================================================

        elif message.text:

            url = extract_url(
                message.text
            )

            if not url:

                await message.reply_text(
                    "❌ Is message me valid URL nahi mila.\n\n"
                    "🔗 https:// se start hone wala "
                    "link bhejo."
                )

                return

            print(
                "URL RECEIVED:",
                url
            )

            # Store original URL
            stored_message = (
                await context.bot.send_message(
                    chat_id=STORAGE_CHANNEL_ID,
                    text=message.text
                )
            )

        # =================================================
        # 10. UNSUPPORTED
        # =================================================

        else:

            await message.reply_text(
                "❌ Ye message/file type "
                "supported nahi hai."
            )

            return

        # =================================================
        # GENERATE BOT LINK
        # =================================================

        bot_info = (
            await context.bot.get_me()
        )

        bot_username = bot_info.username

        generated_link = (
            f"https://t.me/"
            f"{bot_username}"
            f"?start="
            f"{stored_message.message_id}"
        )

        await message.reply_text(
            "✅ Link Generated!\n\n"
            f"🔗 {generated_link}"
        )

        print(
            "LINK GENERATED:",
            generated_link
        )

    except Exception as e:

        print(
            "MAKE LINK ERROR:",
            repr(e)
        )

        await message.reply_text(
            "❌ Link generate nahi ho paya.\n\n"
            "Check karo ki bot Storage Channel "
            "ka admin hai."
        )


# =========================================================
# /ID COMMAND
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

        self.send_response(
            200
        )

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
        (
            "0.0.0.0",
            port
        ),
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

    # -----------------------------------------------------
    # CHECK SETTINGS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # HEALTH SERVER
    # -----------------------------------------------------

    start_health_server()

    # -----------------------------------------------------
    # CREATE APPLICATION
    # -----------------------------------------------------

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # -----------------------------------------------------
    # /START
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # -----------------------------------------------------
    # /ID
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler(
            "id",
            get_id
        )
    )

    # -----------------------------------------------------
    # JOIN BUTTON
    # -----------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            check_join,
            pattern=r"^check_"
        )
    )

    # -----------------------------------------------------
    # FILES + FORWARDED FILES + URLS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # START POLLING
    # -----------------------------------------------------

    app.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# =========================================================
# RUN BOT
# =========================================================

if __name__ == "__main__":

    main()
