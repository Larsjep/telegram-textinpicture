#!/usr/bin/env python

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from argparse import ArgumentParser
import json
import time
from io import BytesIO
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
log = logging.getLogger('text_in_picture')


class TextInPictureBot(object):

    def __init__(self, api_token, config_file):
        log.info("Starting server")
        self.api_token = api_token
        log.info("Token: {}".format(api_token))
        self._config = json.load(open(config_file))
        self._updater = Updater(token=api_token)
        self._dispatcher = self._updater.dispatcher
        self._dispatcher.add_handler(CommandHandler('hi', self._hi))
        self._dispatcher.add_handler(CommandHandler('start', self._start))
        self._dispatcher.add_handler(CommandHandler('kaspersay', self._handle_say, allow_edited=True))
        self._dispatcher.add_handler(MessageHandler(Filters.text, callback=self._handle_message))
        self._origin_message_send_picture = {}

    def _hi(self, bot, update):
        user = update.message.from_user.username
        bot.send_message(chat_id=update.message.chat_id, text="Hello @{0}, how are you doing today?".format(user))

    def _start(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="Hello @{0}, send some text and Kasper will show a sign")

    def _handle_say(self, bot, update):
        if update.message:
            self._say(bot, update.message, text_skip=11)
        elif update.edited_message:
            # We have to delete the old picture, because the API doesn't provide a function to edit a photo
            old_picture_id = self._origin_message_send_picture.get(update.edited_message.message_id, None)
            if old_picture_id:
                bot.delete_message(update.edited_message.chat_id, old_picture_id)
            self._say(bot, update.edited_message, text_skip=11)

    def _handle_message(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="You said: {}".format(update.message.text))
        self._say(bot, update.message)

    def _say(self, bot, message, text_skip=0):
        img = Image.open(self._config["picture"])
        draw = ImageDraw.Draw(img)
        text = message.text[text_skip:]

        x1, y1, x2, y2 = self._config["textbox_coordinates"]
        log.info("Got message: {}".format(text))
        font_file = self._config["font"]

        for font_size in range(25, 60):
            font = ImageFont.truetype(font_file, font_size)
            xsize, ysize = draw.textsize(text, font=font)
            if xsize > x2 - x1 or ysize > y2 - y1:
                font = ImageFont.truetype(font_file, font_size - 1)
                break

        draw.text((x1, y1), text, (0, 0, 0), font=font)

        memory_img = BytesIO()  # this is a file object
        img.save(memory_img, format="jpeg")
        memory_img.seek(0)

        send_message = bot.send_photo(chat_id=message.chat_id, photo=memory_img)
        self._origin_message_send_picture[message.message_id] = send_message.message_id

    def start(self):
        self._updater.start_polling()
        while True:
            time.sleep(5)


parser = ArgumentParser(description='Text in Picture telegram bot')
parser.add_argument('api_token', help='Telegram API token')

args = parser.parse_args()

bot = TextInPictureBot(args.api_token, 'config.json')

bot.start()
