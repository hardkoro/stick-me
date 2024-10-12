"""Bot definition."""

import io
import logging
import os
import uuid

import httpx
from telegram import Bot, InputSticker, Sticker, Update, User
from telegram.error import TelegramError
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram.constants import StickerFormat

from stick_me.exceptions import UnsetEnvironmentError


LOGGER = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise UnsetEnvironmentError("BOT_TOKEN environment variable is not set!")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", CURRENT_DIR)

STICKER_SET_NAME = os.getenv("STICKER_SET_NAME", "favorites_by_st1ck_m3_bot")
STICKER_SET_TITLE = os.getenv("STICKER_SET_TITLE", "My favorites")
EMOJI = os.getenv("EMOJI", "❤️")


def main() -> None:
    """Main entry point."""
    LOGGER.info("Starting bot ...")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    sticker_handler = MessageHandler(filters.Sticker.STATIC, handle_sticker)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(sticker_handler)

    application.run_polling()

    LOGGER.info("Finished starting bot")


async def start(update: Update, context: CallbackContext) -> None:
    """Start the bot."""
    await notify_user(
        bot=context.bot,
        chat_id=update.effective_chat.id,
        message="Hi, I'm a sticker bot. Send me a sticker and I'll add it to your sticker set.",
    )


async def notify_user(
    bot: Bot,
    chat_id: int,
    message: str,
) -> None:
    """Notify user."""
    await bot.send_message(chat_id=chat_id, text=message)


async def handle_sticker(update: Update, context: CallbackContext) -> None:
    """Handle sticker message."""
    LOGGER.info("Handling sticker from %s ...", update.effective_user.name)

    bot = context.bot
    user = update.message.from_user
    sticker = update.message.sticker
    chat_id = update.effective_chat.id

    if not sticker:
        await notify_user(bot, chat_id, "Please send a sticker")
        LOGGER.warning("Received invalid sticker from %s", user.name)
        return

    await process_sticker(bot, user, chat_id, sticker)

    LOGGER.info("Finished handling sticker from %s", user.name)


async def process_sticker(
    bot: Bot,
    user: User,
    chat_id: int,
    sticker: Sticker,
) -> None:
    """Process sticker."""
    LOGGER.info("Processing sticker %s from %s ...", sticker.file_id, user.name)

    sticker_bytes = await download_file(bot, sticker.file_id)
    await upload_sticker(bot, user, chat_id, sticker_bytes)

    LOGGER.info("Finished processing sticker %s from %s", sticker.file_id, user.name)


async def download_file(bot: Bot, file_id: str) -> bytes:
    """Download sticker file."""
    LOGGER.info("Downloading sticker %s ...", file_id)

    file = await bot.get_file(file_id)
    file_url = file.file_path

    async with httpx.AsyncClient() as client:
        response = await client.get(file_url)
        response.raise_for_status()
        sticker_bytes = response.content

    LOGGER.info("Finished downloading sticker %s", file_id)

    return sticker_bytes


async def upload_sticker(
    bot: Bot,
    user: User,
    chat_id: int,
    sticker_bytes: bytes,
) -> None:
    """Upload sticker to user."""
    LOGGER.info("Uploading sticker to %s ...", user.name)

    sticker_file = io.BytesIO(sticker_bytes)
    sticker_file.name = f"{uuid.uuid4()}_sticker.png"

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
        await notify_user(
            bot=bot,
            chat_id=chat_id,
            message="Sticker added to your set!",
        )
    except TelegramError as exc:
        if "STICKERSET_INVALID" in str(exc):
            await create_sticker_set(
                bot=bot,
                user=user,
                chat_id=chat_id,
                sticker=sticker,
            )
        else:
            await notify_user(
                bot=bot,
                chat_id=chat_id,
                message="Failed to add sticker to your set!",
            )
            LOGGER.error("Failed to upload sticker to %s: %s", user.name, exc)

    LOGGER.info("Finished uploading sticker to %s", user.name)


async def create_sticker_set(
    bot: Bot,
    user: User,
    chat_id: int,
    sticker: InputSticker,
) -> None:
    """Create sticker set."""
    LOGGER.info("Creating sticker set for %s ...", user.name)

    await bot.create_new_sticker_set(
        user_id=user.id,
        name=STICKER_SET_NAME,
        title=STICKER_SET_TITLE,
        stickers=[sticker],
    )

    await notify_user(
        bot=bot,
        chat_id=chat_id,
        message="Sticker set created and the sticker added to your set!",
    )

    LOGGER.info("Finished creating sticker set for %s", user.name)
