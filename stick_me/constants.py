"""Constants."""

import os


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", CURRENT_DIR)

STICKER_SET_NAME = os.getenv("STICKER_SET_NAME", "favorites_by_st1ck_m3_bot")
STICKER_SET_TITLE = os.getenv("STICKER_SET_TITLE", "My favorites")
EMOJI = os.getenv("EMOJI", "❤️")

INVALID_STICKER_SET_PATTERN = "Stickerset_invalid"
