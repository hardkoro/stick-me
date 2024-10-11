#!/bin/bash

# Run ruff
poetry run ruff format .
poetry run ruff check .

# Run pylint
poetry run pylint stick_me

# Run mypy
poetry run mypy stick_me
