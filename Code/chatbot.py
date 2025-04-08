
import configparser
import logging
from telegram import Update
from telegram.ext import (Updater, MessageHandler,
                          Filters, CommandHandler, CallbackContext)
import psycopg2
from psycopg2 import sql
from hkbu_chatgpt import HKBU_ChatGPT


user_games = {}
users = set()

# DB_CONFIG = {
#     'dbname': 'chatbot',
#     'user': 'ychwu',
#     'password': '19957112johnWU',
#     'host': 'localhost'
#     # 'port': '5432'
# }


def get_database_connection():
    """连接到PostgreSQL databse"""
    config = configparser.ConfigParser()
    config.read('config.ini')
    db_config = {
        # 'dbname': config['DATABASE']['DBNAME'],
        'user': config['DATABASE']['USER'],
        'password': config['DATABASE']['PASSWORD'],
        'host': config['DATABASE']['HOST']
    }
    return psycopg2.connect(**db_config)
    # return psycopg2.connect(**DB_CONFIG)


def show_tips(update: Update, context: CallbackContext) -> None:
    """/help显示所有Command"""
    update.message.reply_text(
        "Commands: \n"
        "/start: To Start the chat\n"
        "/find: To Find matches\n"
        "/show: To Show the games you input\n"
    )


def start_chat(update: Update, context: CallbackContext) -> None:
    """开始对话并记录当前user_id"""
    user_id = update.effective_user.id
    update.message.reply_text(
        "Welcome to the Gamers' Chat! \n"
        "Please input the games in parethesis you like separated by commas, "
        "for example(League of Legend, Dota2, Valorant ...)\n"
        "Or Ask ChatGPT question\n"
        "Can type /help to see Commands"
    )

    users.add(user_id)


def handle_input(update: Update, context: CallbackContext) -> None:
    """处理用户输入"""
    user_id = update.effective_user.id
    input_text = update.message.text
    # 用户未点击/start开始的情况
    if user_id not in users:
        update.message.reply_text(
            "Please type /start before you start the chat."
        )
        return

    # 用户通过()输入游戏的情况
    if input_text.count('(') == 1 and input_text.count(')') == 1:
        input_text = input_text.lstrip('(')
        input_text = input_text.rstrip(')')
        input_games = []
        # 解析以及存储用户输入游戏名
        for game in input_text.split(','):
            if game.strip():
                game = game.strip()
                print(f"game: {game}")
                input_games.append(game)
        # 输入为空的情况下，请求重新输入
        if len(input_games) == 0:
            update.message.reply_text(
                "Failed to receive any game, Please re-input the games you like in parenthesis separated by commas, "
                "for example(League of Legend, Dota2, Valorant ...)\n"
            )
            return

        try:
            connection = get_database_connection()
            cursor = connection.cursor()
            query = sql.SQL("""
                INSERT INTO user_games (user_id, games)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE
                SET games = EXCLUDED.games
            """)
            test_input_games = ["WOW", "League of Legend"]
            test_user_id = 123456
            print(f"test_input_games: {test_input_games}")
            print(f"input_games: {input_games}")
            print(f"query: {query.string}")
            cursor.execute(query, (test_user_id, test_input_games))
            cursor.execute(query, (user_id, input_games))
            connection.commit()
            update.message.reply_text(f"Save your games: {', '.join(input_games)}"
                                      )
        except Exception as e:
            update.message.reply_text(f"Fail to save games!"
                                      )
            print(str(e))
        finally:
            if connection:
                cursor.close()
                connection.close()

    # ChatGPT API处理输入的情况
    else:
        global chatgpt
        reply_message = chatgpt.submit(input_text)
        logging.info("Update: " + str(update))
        logging.info("context: " + str(context))
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=reply_message)


def show_games(update: Update, context: CallbackContext) -> None:
    """展示当前用户的游戏"""
    user_id = update.effective_user.id
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT games FROM user_games WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if not result:
            update.message.reply_text(
                "Cannot find games you are interested in! \n"
                "Please input the games you like inside parentheses separated by commas,"
                "for example(League of Legend, Dota2, Valorant ...)"
            )
            return

        else:
            print(f"database result: {str(result)}")
            update.message.reply_text(
                "The games you input are: \n"
                f"{result[0]}"
            )

    except Exception as e:
        update.message.reply_text(f"Database error: {e}")

    finally:
        if connection:
            cursor.close()
            connection.close()


def find_matches(update: Update, context: CallbackContext) -> None:
    """通过游戏寻找相似用户"""
    user_id = update.effective_user.id

    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT games FROM user_games WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if not result:
            update.message.reply_text(
                "Cannot find games you are interested in! \n"
                "Please input the games you like inside parentheses separated by commas,"
                "for example(League of Legend, Dota2, Valorant ...)"
            )
            return

        print(f"database result 1: {str(result)}")
        current_user_games = set(result[0])

        print(f"current_user_game: {current_user_games}")

        best_match = None
        best_score = 0

        cursor.execute(
            "SELECT user_id, games FROM user_games WHERE user_id != %s", (user_id,))

        for item in cursor.fetchall():
            uid, games = item[0], set(item[1])
            # 通过IOU计算用户游戏间的相似度
            intersection = current_user_games.intersection(games)
            union = current_user_games.union(games)

            similarity = len(intersection)/len(union) if union else 0

            if similarity > best_score:
                best_score = similarity
                best_match = uid

        if not best_match:
            print(f"database result 2: {str(result)}")
            update.message.reply_text(
                "We failed to find people with same interest as you do, please try again later."
            )
        else:
            cursor.execute(
                "SELECT games FROM user_games WHERE user_id = %s", (best_match,))
            match_games = cursor.fetchone()[0]
            update.message.reply_text(
                f"We find some gamer similar to you who plays : {', '.join(match_games)}\n With user_id: {best_match}"
            )
            print(f'best_match: {best_match}')
            # 向best_match的user发送消息
            context.bot.send_message(
                chat_id=best_match,
                text=f"We find some gamer similar to you who plays: {', '.join(current_user_games)}\n With user_id: {user_id}")

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

    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        query = sql.SQL("""
            INSERT INTO user_games (user_id, games)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET games = EXCLUDED.games
        """)
        test_input_games = ["WOW", "League of Legend"]
        test_user_id = 123456
        print(f"test_input_games: {test_input_games}")
        print(f"query: {query.string}")
        cursor.execute(query, (test_user_id, test_input_games))
        connection.commit()
    except Exception as e:
        print(str(e))
    finally:
        if connection:
            cursor.close()
            connection.close()

    updater = Updater(
        token=(config['TELEGRAM']['ACCESS_TOKEN']), use_context=True)
    dispatcher = updater.dispatcher

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    dispatcher.add_handler(CommandHandler('start', start_chat))
    dispatcher.add_handler(CommandHandler('help', show_tips))
    dispatcher.add_handler(CommandHandler('find', find_matches))
    dispatcher.add_handler(CommandHandler('show', show_games))
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command, handle_input))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
