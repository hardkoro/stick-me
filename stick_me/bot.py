"""Bot definition."""

import io
import logging
import uuid

import httpx
from telegram import Bot, InputSticker, Update
from telegram.error import TelegramError
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram.constants import StickerFormat

from stick_me.constants import (
    DOWNLOAD_DIR,
    EMOJI,
    INVALID_STICKER_SET_PATTERN,
    STICKER_SET_NAME,
    STICKER_SET_TITLE,
)
from stick_me.models import Conversation, Sticker, User


LOGGER = logging.getLogger(__name__)


class StickMeBot:
    """Telegram bot for managing stickers."""

    ADD_STICKERS_URL = "https://t.me/addstickers"

    def __init__(
        self,
        token: str,
        async_client: httpx.AsyncClient,
        download_dir: str = DOWNLOAD_DIR,
        sticker_set_name: str = STICKER_SET_NAME,
        sticker_set_title: str = STICKER_SET_TITLE,
        emoji: str = EMOJI,
    ) -> None:
        """Initialize bot."""
        self._token = token
        self._client = async_client

        self._download_dir = download_dir
        self._sticker_set_name = sticker_set_name
        self._sticker_set_title = sticker_set_title
        self._emoji = emoji

    def run(self) -> None:
        """Main entry point."""
        LOGGER.info("Starting bot ...")

        try:
            application = ApplicationBuilder().token(self._token).build()

            sticker_handler = MessageHandler(filters.Sticker.STATIC, self.handle_sticker)

            application.add_handler(CommandHandler("start", self.start))
            application.add_handler(sticker_handler)

            LOGGER.info("Finished starting bot")
            application.run_polling()
        finally:
            LOGGER.info("Stopping bot ...")
            LOGGER.info("Finished stopping bot")

    async def start(self, update: Update, context: CallbackContext) -> None:
        """Start the bot."""
        assert update.effective_user
        assert update.effective_chat

        bot = context.bot
        user = User(
            id=update.effective_user.id,
            name=update.effective_user.name,
        )
        conversation = Conversation(
            user=user,
            chat_id=update.effective_chat.id,
        )

        LOGGER.info("Starting conversation with %s ...", conversation.username)

        await self._notify_user(
            bot=bot,
            conversation=conversation,
            message=(
                "Hi, I'm a sticker bot!\n"
                + "Send me a sticker and I'll add it to your sticker set."
            ),
        )

        LOGGER.info("Finished starting conversation with %s", conversation.username)

    async def handle_sticker(self, update: Update, context: CallbackContext) -> None:
        """Handle sticker message."""
        assert update.effective_user
        assert update.effective_chat
        assert update.message

        bot = context.bot
        user = User(
            id=update.effective_user.id,
            name=update.effective_user.name,
        )
        conversation = Conversation(
            user=user,
            chat_id=update.effective_chat.id,
        )

        LOGGER.info("Handling sticker from %s ...", conversation.username)

        if not update.message.sticker:
            await self._notify_user(
                bot=bot, conversation=conversation, message="Please send a sticker"
            )
            LOGGER.warning("Received invalid sticker from %s", conversation.username)
            return

        sticker = Sticker(
            file_id=update.message.sticker.file_id,
            emoji=update.message.sticker.emoji or self._emoji,
        )

        await self._process_sticker(bot, conversation, sticker)

        await self._notify_user(
            bot=bot,
            conversation=conversation,
            message=f"The link to the sticker set: {self._get_sticker_set_link()}",
        )

        LOGGER.info("Finished handling sticker from %s", conversation.username)

    @staticmethod
    async def _notify_user(
        bot: Bot,
        conversation: Conversation,
        message: str,
    ) -> None:
        """Notify user."""
        await bot.send_message(chat_id=conversation.chat_id, text=message)

    def _get_sticker_set_link(self) -> str:
        """Get sticker set link."""
        return f"{self.ADD_STICKERS_URL}/{self._sticker_set_name}"

    async def _process_sticker(
        self,
        bot: Bot,
        conversation: Conversation,
        sticker: Sticker,
    ) -> None:
        """Process sticker."""
        LOGGER.info("Processing sticker %s from %s ...", sticker.file_id, conversation.username)

        sticker.content = await self._download_file(bot, sticker)
        await self._upload_sticker(bot, conversation, sticker)

        LOGGER.info(
            "Finished processing sticker %s from %s", sticker.file_id, conversation.username
        )

    async def _download_file(self, bot: Bot, sticker: Sticker) -> bytes:
        """Download sticker file."""
        LOGGER.info("Downloading sticker %s ...", sticker.file_id)

        file = await bot.get_file(sticker.file_id)
        file_url = file.file_path or ""

        async with self._client as client:
            response = await client.get(file_url)
            response.raise_for_status()
            sticker_bytes = response.content

        LOGGER.info("Finished downloading sticker %s", sticker.file_id)

        return sticker_bytes

    async def _upload_sticker(
        self,
        bot: Bot,
        conversation: Conversation,
        sticker: Sticker,
    ) -> None:
        """Upload sticker to user."""
        LOGGER.info("Uploading sticker to %s ...", conversation.username)

        assert sticker.content
        sticker_file = io.BytesIO(sticker.content)
        sticker_file.name = f"{uuid.uuid4()}_sticker.png"

        response = await bot.upload_sticker_file(
            conversation.user_id,
            sticker_file,
            sticker_format=StickerFormat.STATIC,
        )
        uploaded_file_id = response.file_id

        input_sticker = InputSticker(
            sticker=uploaded_file_id,
            emoji_list=[sticker.emoji],
            format=StickerFormat.STATIC,
        )

        try:
            if await bot.add_sticker_to_set(
                user_id=conversation.user_id,
                name=STICKER_SET_NAME,
                sticker=input_sticker,
            ):
                await self._notify_user(
                    bot=bot,
                    conversation=conversation,
                    message=(
                        "Sticker added to your set!\n"
                        + "It might take up to a couple of minutes to appear."
                    ),
                )
                LOGGER.info("Added sticker to %s", conversation.username)
            else:
                await self._notify_user(
                    bot=bot,
                    conversation=conversation,
                    message="Failed to add sticker to your set!",
                )
                LOGGER.error("Failed to add sticker to %s", conversation.username)
        except TelegramError as exc:
            if INVALID_STICKER_SET_PATTERN in str(exc):
                await self._create_sticker_set(
                    bot=bot,
                    conversation=conversation,
                    sticker=input_sticker,
                )
            else:
                await self._notify_user(
                    bot=bot,
                    conversation=conversation,
                    message="Failed to add sticker to your set!",
                )
                LOGGER.error("Failed to upload sticker to %s: %s", conversation.username, exc)

        LOGGER.info("Finished uploading sticker to %s", conversation.username)

    async def _create_sticker_set(
        self,
        bot: Bot,
        conversation: Conversation,
        sticker: InputSticker,
    ) -> None:
        """Create sticker set."""
        LOGGER.info("Creating sticker set for %s ...", conversation.username)

        await bot.create_new_sticker_set(
            user_id=conversation.user_id,
            name=STICKER_SET_NAME,
            title=STICKER_SET_TITLE,
            stickers=[sticker],
        )

        await self._notify_user(
            bot=bot,
            conversation=conversation,
            message=(
                "Sticker set created and the sticker added to your set!\n"
                + "It might take up to a couple of minutes to appear."
            ),
        )

        LOGGER.info("Finished creating sticker set for %s", conversation.username)
