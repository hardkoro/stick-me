"""Main entry point."""

import logging
import os

import httpx

from stick_me.bot import StickMeBot
from stick_me.exceptions import UnsetEnvironmentError


def main() -> None:
    """Main entry point."""
    token = os.getenv("BOT_TOKEN")

    if not token:
        raise UnsetEnvironmentError("BOT_TOKEN is not set")

    async_client = httpx.AsyncClient()
    bot = StickMeBot(token=token, async_client=async_client)
    bot.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
