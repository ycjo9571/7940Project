
from telegram import Update
from telegram.ext import (Updater, MessageHandler, Filters, CommandHandler,
                          CallbackContext)
from hkbu_chatgpt import HKBU_ChatGPT


import configparser
import logging
import os


def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    updater = Updater(
        token=(config['TELEGRAM']['ACCESS_TOKEN']), use_context=True)
    dispatcher = updater.dispatcher
    # global redis1
    # redis1 = redis.Redis(host=(os.environ['HOST']),
    #                      password=(os.environ['PASSWORD']),
    #                      port=(os.environ['REDISPORT']),
    #                      decode_responses=(os.environ['DECODE_RESPONSE']),
    #                      username=(os.environ['USER_NAME'])
    #                      )

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    # echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)

    # dispatcher.add_handler(CommandHandler('add', add))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(CommandHandler('hello', greeting_command))

    global chatgpt
    chatgpt = HKBU_ChatGPT()
    chatgpt_handler = MessageHandler(Filters.text & (~Filters.command),
                                     equiped_chatgpt)

    dispatcher.add_handler(chatgpt_handler)

    updater.start_polling()
    updater.idle()


# def echo(update, context):
#     reply_message = update.message.text.upper()
#     logging.info('Update: ' + str(update))
#     logging.info('context: ' + str(context))
#     context.bot.send_message(
#         chat_id=update.effective_chat.id, text=reply_message)


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Helping you right now')


# def add(update: Update, context: CallbackContext) -> None:

#     try:
#         global redis1
#         logging.info(context.args[0])
#         msg = context.args[0]
#         redis1.incr(msg)

#         update.message.reply_text('You have said ' + msg + ' for ' +
#                                   redis1.get(msg) + ' times.')

#     except (IndexError, ValueError):
#         update.message.reply_text('Usage: /add <keyword>')


def greeting_command(update: Update, context: CallbackContext) -> None:
    '''Say 'Good day, <name>' to user if they type '/hello <name>' '''
    name = context.args[0]
    update.message.reply_text('Good day, ' + name + "!")


def equiped_chatgpt(update, context):
    global chatgpt
    reply_message = chatgpt.submit(update.message.text)
    logging.info('Update: ' + str(update))
    logging.info('context: ' + str(context))
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=reply_message)


if __name__ == '__main__':
    main()
