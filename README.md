# Stick Me

A Telegram bot which helps to create a sticker set with your beloved stickers.

## Run the script

Create a copy of `.env.example` file and populate it with the correct database URI:

```shell
cp .env.example .env

echo BOT_TOKEN=<bot_token> > .env
```

Optionally, you can specify a directory to temporary store downloaded files like so:

```shell
echo DOWNLOAD_DIR=<download_dir> > .env
```

Additionally, you can configure the name, the title and the emoji set for the added
stickers like so:

```shell
echo STICKER_SET_NAME=<sticker_set_name> > .env
echo STICKER_SET_TITLE=<sticker_set_title> > .env
echo EMOJI=<emoji> > .env
```

Then, run the bot

```shell
poetry run python -m stick_me
```

Find the bot in Telegram and send stickers to it, then add the corresponding sticker set
to your pins. Voilá!

## Development

To lint the project run the following command to execute the linting script:

```shell
poetry run ./lint.sh
```
