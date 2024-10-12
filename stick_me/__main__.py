"""Main entry point."""

import logging

from stick_me.bot import main


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
