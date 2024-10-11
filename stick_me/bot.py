"""Bot definition."""

import logging
import os

import httpx
from telegram import Update, Bot, InputSticker
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
from telegram.constants import StickerFormat



LOGGER = logging.getLogger(__name__)

STICKER_SET_NAME = "favorites_by_st1ck_m3_bot"
STICKER_SET_TITLE = "My favorites"
EMOJI = "❤️"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


BOT_TOKEN = os.environ.get("BOT_TOKEN")


def main() -> None:
    """Main entry point."""
    LOGGER.info("Starting bot ...")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    sticker_handler = MessageHandler(filters.Sticker.STATIC, handle_sticker)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(sticker_handler)

    application.run_polling()

    LOGGER.info("Bot started")


async def start(update: Update, context: CallbackContext) -> None:
    """Start the bot."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please send me a sticker."
    )


async def handle_sticker(update: Update, context: CallbackContext) -> None:
    """Handle sticker message."""
    LOGGER.info("Received sticker from %s", update.effective_user.name)

    bot = context.bot
    user = update.message.from_user
    sticker = update.message.sticker

    if not sticker:
        await bot.send_message(
            chat_id=update.effective_chat.id, text="Please send a sticker"
        )
        LOGGER.warning("Received invalid sticker from %s", user.name)
        return

    file_id = sticker.file_id
    sticker_path = await download_file(bot, file_id)
    await upload_sticker(bot, update, user, sticker_path)

    os.remove(sticker_path)
    LOGGER.info("Handled sticker from %s", user.name)


async def download_file(bot: Bot, file_id: str) -> str:
    """Download sticker file."""
    LOGGER.info("Downloading sticker %s ...", file_id)

    file = await bot.get_file(file_id)

    file_path = file.file_path
    download_path = CURRENT_DIR + "/" + file_path.split("/")[-1]
    with httpx.stream("GET", file_path) as response:
        response.raise_for_status()
        with open(download_path, "wb") as sticker_file:
            for chunk in response.iter_bytes():
                sticker_file.write(chunk)

    LOGGER.info("Downloaded sticker %s", file_id)

    return download_path


async def upload_sticker(
    bot: Bot,
    update: Update,
    user: Update.effective_user,
    sticker_path: str,
) -> None:
    """Upload sticker to user."""
    LOGGER.info("Uploading sticker to %s ...", user.name)

    with open(sticker_path, "rb") as sticker_file:
        response = await bot.upload_sticker_file(
            user.id,
            sticker_file,
            sticker_format=StickerFormat.STATIC,
        )
        uploaded_file_id = response.file_id

        sticker = InputSticker(
            sticker=uploaded_file_id,
            emoji_list=[EMOJI],
            format=StickerFormat.STATIC,
        )

        try:
            await bot.add_sticker_to_set(
                user_id=user.id,
                name=STICKER_SET_NAME,
                sticker=sticker,
            )
            await bot.send_message(
                chat_id=update.effective_chat.id,
                text="Sticker added to your set!",
            )
        except Exception as _:
            # If the sticker set doesn't exist, create it
            await bot.create_new_sticker_set(
                user_id=user.id,
                name=STICKER_SET_NAME,
                title=STICKER_SET_TITLE,
                stickers=[sticker],
            )

            await bot.send_message(
                chat_id=update.effective_chat.id,
                text="Created a new sticker set and added the sticker!",
            )

    LOGGER.info("Uploaded sticker to %s", user.name)
