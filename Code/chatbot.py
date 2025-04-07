
import configparser
import logging
from telegram import Update
from telegram.ext import (Updater, MessageHandler,
                          Filters, CommandHandler, CallbackContext)
import psycopg2
from psycopg2 import sql
from hkbu_chatgpt import HKBU_ChatGPT


user_games = {}
# user_games[123] = {'Dota2', 'Valorant'}
# user_games[456] = {'WOW', 'League of Legend'}
users = set()

DB_CONFIG = {
    'dbname': 'chatbot',
    'user': 'ychwu',
    'password': '19957112johnWU',
    'host': 'localhost'
    # 'port': '5432'
}


def get_database_connection():
    """连接到PostgreSQL databse"""
    # config = configparser.ConfigParser()
    # config.read('config.ini')
    # db_config = config['POSTGRESQL']
    # return psycopg2.connect(**db_config)
    return psycopg2.connect(**DB_CONFIG)


def show_tips(update: Update, context: CallbackContext) -> None:
    """/help显示所有Command"""
    update.message.reply_text(
        "/start: To Start the chat\n"
        "/find: To Find matches\n"
        "/change: Change games you play\n"
    )


def start_chat(update: Update, context: CallbackContext) -> None:
    """开始对话并记录当前user_id"""
    user_id = update.effective_user.id
    update.message.reply_text(
        "Welcome to the Gamers' Chat! Please input the games you like separated by commas, "
        "for example(League of Legend, Dota2, Valorant ...)\n"
        "Can type /help to see Commands"
    )

    users.add(user_id)


def change_games(update: Update, context: CallbackContext) -> None:
    """删除用户现在的游戏记录"""
    user_id = update.effective_user.id
    if user_id not in users:
        update.message.reply_text(
            "Please type /start before you start the chat."
        )
        return
    elif user_id not in user_games.keys():
        update.message.reply_text(
            "Cannot find games you are interested in! \n"
            "Please input the games you like separated by commas,"
            "for example(League of Legend, Dota2, Valorant ...)"
        )
        return
    else:
        user_games.pop(user_id)
        update.message.reply_text(
            "Re-enter the games you like: "
        )


def handle_input(update: Update, context: CallbackContext) -> None:
    """处理用户输入"""
    user_id = update.effective_user.id
    # 用户未点击/start开始的情况
    if user_id not in users:
        update.message.reply_text(
            "Please type /start before you start the chat."
        )
        return

    input_games = []
    # 解析以及存储用户输入游戏名
    for game in update.message.text.split(','):
        if game.strip():
            input_games.append(game)
    # 输入为空的情况下，请求重新输入
    if len(input_games) == 0:
        update.message.reply_text(
            "Failed to receive any game, please re-enter: "
        )
        return

    # user_games[user_id] = set(input_games)
    # # users.remove(user_id)
    # update.message.reply_text(f"Save your games: {', '.join(input_games)}"
    #                           )

    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        query = sql.SQL("""
            INSERT INTO user_games (user_id, games)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET games = EXCLUDED.games
        """)
        cursor.execute(query, (user_id, input_games))
        connection.commit()
        update.message.reply_text(f"Save your games: {', '.join(input_games)}"
                                  )
    except Exception as e:
        update.message.reply_text(f"Fail to save games!"
                                  )
        print(str(e))
    finally:
        pass
        # if connection:
        #     cursor.close()
        #     connection.close()
        # users.remove(user_id)


def find_matches(update: Update, context: CallbackContext) -> None:
    """通过游戏寻找相似用户"""
    user_id = update.effective_user.id
    # if user_id not in users:
    #     update.message.reply_text(
    #         "Please press /start"
    #     )
    #     return
    # elif user_id not in user_games.keys():
    #     update.message.reply_text(
    #         "Cannot find games you are interested in! \n"
    #         "Please input the games you like separated by commas,"
    #         "for example(League of Legend, Dota2, Valorant ...)"
    #     )
    #     return

    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT games FROM user_games WHERE user_id = %s", (user_id,))

        result = cursor.fetchone()
        if not result:
            update.message.reply_text(
                "Cannot find games you are interested in! \n"
                "Please input the games you like separated by commas,"
                "for example(League of Legend, Dota2, Valorant ...)"
            )
            return

        # current_user_games = user_games[user_id]
        print(f"database result: {str(result)}")
        current_user_games = set(result[0])

        best_match = None
        best_score = 0

        cursor.execute(
            "SELECT user_id, games FROM user_games WHERE user_id != %s", (user_id,))

        # for userid, games in user_games.items():
        #     if userid == user_id:
        for item in cursor.fetchall():
            uid, games = item[0], set(item[1])
            # 通过IOU计算用户游戏间的相似度
            intersection = current_user_games.intersection(games)
            union = current_user_games.union(games)

            similarity = len(intersection)/len(union) if union else 0

            if similarity > best_score:
                best_score = similarity
                best_match = id

        if not best_match:
            print(f"database result: {str(result)}")
            update.message.reply_text(
                "We failed to find people with same interest as you do, please try again later."
            )
        else:
            cursor.execute(
                "SELECT games FROM user_games WHERE user_id = %s", (best_match,))
            match_games = cursor.fetchone()[0]
            update.message.reply_text(
                f"We find some gamer similar to you who plays : {', '.join(match_games)}"
            )
            # context.bot.send_message(
            #     chat_id=best_match,
            #     text=f"We find some gamer similar to you who plays: {', '.join(current_user_games)}"

    except Exception as e:
        update.message.reply_text(f"Database error: {e}")

    finally:
        if connection:
            cursor.close()
            connection.close()


def main():

    config = configparser.ConfigParser()
    config.read('config.ini')

    global chatgpt
    chatgpt = HKBU_ChatGPT(config)

    updater = Updater(
        token=(config['TELEGRAM']['ACCESS_TOKEN']), use_context=True)
    dispatcher = updater.dispatcher

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    # echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    # dispatcher.add_handler(echo_handler)

    chatgpt_handler = MessageHandler(
        Filters.text & (~Filters.command), equiped_chatgpt)

    dispatcher.add_handler(CommandHandler('start', start_chat))
    dispatcher.add_handler(CommandHandler('help', show_tips))
    dispatcher.add_handler(CommandHandler('find', find_matches))
    dispatcher.add_handler(chatgpt_handler)
    # dispatcher.add_handler(CommandHandler('change', change_games))
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command, handle_input))

    updater.start_polling()
    updater.idle()


def equiped_chatgpt(update, context):
    global chatgpt
    reply_message = chatgpt.submit(update.message.text)
    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=reply_message)
# def echo(update, context):
#     reply_message = update.message.text.upper()
#     logging.info('Update: ' + str(update))
#     logging.info('context: ' + str(context))
#     context.bot.send_message(
#         chat_id=update.effective_chat.id, text=reply_message)


if __name__ == '__main__':
    main()
