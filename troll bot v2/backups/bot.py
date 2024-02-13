# coding=utf-8

import random
import telebot
import time
import datetime
import sqlite3
import re
import math
import threading
from html import escape
from telebot import types


def read_file(file_name):
    with open(file_name, 'r') as file:
        return file.read()


bot = telebot.TeleBot(read_file('token.ini'))

# bot = telebot.TeleBot("5943023867:AAG1eIeU6Y6zg05SlKKDk00_yr63_DbN0h8")

items_dict = {
    1: {
        "name": "\U0001F9F0 Тролл-Кейс",
        "price": 5000,
        "command": "/tcase",
        "prob": 0
    },
    2: {
        "name": "\U0001F48E Деньго-Кейс",
        "price": 5000,
        "command": "/mcase",
        "image": "moneycase.png",
        "prob": 0.325
    },
    3: {
        "name": "\U0001F608 Тролья бомба",
        "price": 8000,
        "command": "/megatroll",
        "image": "trollbomb.png",
        "prob": 0.07
    },
    4: {
        "name": "\U0001F504 Обнуление",
        "price": 10000,
        "command": "/removecooldowns",
        "image": "restorecooldowns.png",
        "prob": 0.05,
    },
    5: {
        "name": "\U0001F3AF Точный удар",
        "price": 7000,
        "command": "/targettroll",
        "image": "targettroll.png",
        "prob": 0.2
    },
    6: {
        "name": "\U00002796 Удаление",
        "price": 6000,
        "command": "/removetroll",
        "image": "minustroll.png",
        "prob": 0.2
    },
    7: {
        "name": "\U0001F6E1 Защита",
        "price": 8000,
        "image": "protection.png",
        "prob": 0.1
    },
    8: {
        "name": "\U0001F202\U0000FE0F Налоговая проверка",
        "price": 12000,
        "command": "/audit",
        "image": "taxaudit.png",
        "prob": 0.05
    },
    9: {
        "name": "\U0001F4E6 Обнуление предметов",
        "price": 100000,
        "command": "/restoreitems",
        "image": "restoreitems.png",
        "prob": 0.005
    }
}


slot_wins = {
    1: 3,
    2: 1.5,
    3: 1.5,
    4: 1.5,
    6: 1.5,
    11: 1.5,
    16: 1.5,
    17: 1.5,
    21: 1.5,
    22: 3,
    23: 1.5,
    24: 1.5,
    27: 1.5,
    32: 1.5,
    33: 1.5,
    38: 1.5,
    41: 1.5,
    42: 1.5,
    43: 3,
    44: 1.5,
    48: 1.5,
    49: 1.5,
    54: 1.5,
    59: 1.5,
    61: 1.5,
    62: 1.5,
    63: 1.5,
    64: 15
}


restricted_users_ids = (
    650007411,
    382328456,
    716273061,
    1545299122
)


employees_statuses = {
    0: {
        'name': 'обсулживающий персонал',
        'emoji': '\U0001F468\U0000200D\U0001F527',
        'multiplyer': 0.2,
        'xp_multiplyer': 1
    },
    1: {
        'name': 'офисный работник',
        'emoji': '\U0001F468\U0000200D\U0001F4BC',
        'multiplyer': 0.32,
        'xp_multiplyer': 1.6
    },
    2: {
        'name': 'менеджер',
        'emoji': '\U0001F468\U0000200D\U0001F4BB',
        'multiplyer': 0.5,
        'xp_multiplyer': 2
    },
    3: {
        'name': 'заместитель',
        'emoji': '\U0001F935\U0000200D\U00002642\U0000FE0F',
        'multiplyer': 0.7,
        'xp_multiplyer': 3
    }
}


suffixes = {
    'к': {
        'multiplyer': 1e3
    },
    'тыс': {
        'multiplyer': 1e3
    },
    'кк': {
        'multiplyer': 1e6
    },
    'млн': {
        'multiplyer': 1e6
    },
    'м': {
        'multiplyer': 1e6
    },
    'ккк': {
        'multiplyer': 1e9
    },
    'млрд': {
        'multiplyer': 1e9
    },
    'мд': {
        'multiplyer': 1e9
    },
    'кккк': {
        'multiplyer': 1e12
    },
    'т': {
        'multiplyer': 1e12
    },
    'тн': {
        'multiplyer': 1e12
    }
}


user_buttons = {}


def is_authorized_user(user_id):
    return user_id == 633398015


def is_target_chat(chat_id):
    return True


def is_restricted_user(user_id):
    return user_id in restricted_users_ids


def is_on_cooldown(cursor, user_id, cd_time, cd_type, cd_table):
    cursor.execute(
        'SELECT ' + cd_type + ' FROM ' + cd_table + ' WHERE user_id = ?', (user_id, ))
    result = cursor.fetchone()
    if result is not None:
        cooldown_time = result[0]
        elapsed_time = time.time() - cooldown_time
        remaining_time = cd_time - elapsed_time
        if remaining_time >= 0:
            # отправляем сообщение о том, сколько времени осталось до окончания кулдауна
            hours, remainder = divmod(remaining_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            message_text = f"\U000023F1 Подождите еще {int(hours)} часов {int(minutes)} минут {int(seconds)} секунд."
            return (message_text, True)
        else:
            return ('', False)
    else:
        return ('', False)


def check_buttons(chat_id, message_id, user_id):
    if user_id in user_buttons and user_buttons[user_id]:
        return
    else:
        # пользователь не нажал ни на одну кнопку, выполняем действие для кнопки 2
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        lost_xp = random.randint(100, 2000)
        bot.edit_message_text(
            f"\U0001F61E Проверка обнаружила весомые нарушения.\n\n\U0000303D Ваш бизнес потерял {lost_xp} XP", chat_id, message_id)
        cursor.execute(
            "UPDATE businesses SET experience = experience - ? WHERE user_id = ?", (lost_xp, user_id, ))
        conn.commit()
        conn.close()
        del user_buttons[user_id]


def wait_for_buttons(chat_id, message_id, user_id):
    timer = threading.Timer(300, check_buttons, [chat_id, message_id, user_id])
    timer.start()


def format_money(amount):
    suffixes = ['', 'к', 'кк', 'мд', 'тн']
    suffix_index = 0

    while amount >= 1e3 and suffix_index < len(suffixes)-1:
        amount /= 1e3
        suffix_index += 1

    formatted_amount = f"{math.floor(amount * 10) / 10}{suffixes[suffix_index]}" if (
        amount - int(amount)) > 0 else f"{math.floor(amount)}{suffixes[suffix_index]}"

    return formatted_amount

# region Помощь


@bot.message_handler(regexp="^(?:\/?(тпомощь|thelp)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def show_help(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    conn.commit()
    conn.close()

    bot.send_message(chat_id, f"\U00002049 Все команды можно узнать тут:\n\n<a href='https://teletype.in/@trollbot/commands'>КОМАНДЫ</a>",
                     parse_mode="HTML")

# endregion

# region Развлекательные


@bot.message_handler(regexp="^(?:\/?(troll|троллить|тролл|trol|трол)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def troll(message):

    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    has_cooldown = is_on_cooldown(
        cursor, user_id, 3600, "troll_cooldown", "cooldowns")

    if (has_cooldown[1]):
        bot.send_message(chat_id, has_cooldown[0], parse_mode="HTML")
        conn.close()
        return

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    # получаем случайного пользователя
    cursor.execute('SELECT user_id FROM users ORDER BY RANDOM() LIMIT 1')
    result = cursor.fetchone()
    if result is not None:
        trolled_user_id = result[0]
    else:
        # если в таблице нет пользователей
        bot.send_message(chat_id, "Никого нет в базе")
        conn.close()
        return

    try:
        trolled_user = bot.get_chat_member(message.chat.id, trolled_user_id)
        if trolled_user.user.first_name is not None:
            trolled_user_username = trolled_user.user.first_name
            if trolled_user.user.last_name is not None:
                trolled_user_username += " " + trolled_user.user.last_name
        else:
            trolled_user_username = "безымянного"
        trolled_link = f'<a href="tg://user?id={trolled_user_id}">{escape(trolled_user_username)}</a>'
    except Exception as e:
        trolled_link = "Неизвестного"

    cursor.execute(
        "SELECT created FROM businesses WHERE user_id = ?", (user_id, ))
    troll_business = cursor.fetchone()
    cursor.execute(
        "SELECT created FROM businesses WHERE user_id = ?", (trolled_user_id, ))
    trolled_business = cursor.fetchone()
    cursor.execute(
        "SELECT business_employee, employee_status FROM businesses WHERE user_id = ?", (user_id, ))
    company = cursor.fetchone()

    bot_id = bot.get_me().id

    if trolled_user_id == bot_id:
        message_text = f'\U0001F626 <a href="tg://user?id={user_id}">{escape(username)}</a> удалось затроллить бота.\n\nЗа это он(а) получает \U0001FA99 1000 ₺'
        cursor.execute(
            "UPDATE users SET money = money + 1000 WHERE user_id = ?", (user_id,))
        cursor.execute(
            'UPDATE users SET troll_count = troll_count + 1 WHERE user_id = ?', (user_id,))
        cursor.execute(
            'UPDATE users SET trolled_count = trolled_count + 1 WHERE user_id = ?', (trolled_user_id,))
        if (company is not None and company[0]):
            cursor.execute(
                "UPDATE businesses SET experience = experience + ? WHERE id = ?", (int(30 * employees_statuses[company[1]]['xp_multiplyer']), company[0], ))
            cursor.execute(
                "UPDATE businesses SET employee_productivity = employee_productivity + 1 WHERE user_id = ?", (user_id, ))
            conn.commit()

        if (troll_business is not None and troll_business[0] == 1):
            cursor.execute(
                "UPDATE businesses SET experience = experience + 120 WHERE user_id = ?", (user_id, ))
            conn.commit()
    elif user_id == trolled_user_id:
        message_text = f'\U0001F64D <a href="tg://user?id={user_id}">{escape(username)}</a> затроллил(а) сам себя...'
        cursor.execute(
            'UPDATE users SET troll_count = troll_count - 1 WHERE user_id = ?', (user_id,))
        if (company is not None and company[0]):
            cursor.execute(
                "UPDATE businesses SET experience = experience - ? WHERE id = ?", (int(20 * employees_statuses[company[1]]['xp_multiplyer']), company[0], ))
            conn.commit()
        if (trolled_business is not None and trolled_business[0] == 1):
            cursor.execute(
                "UPDATE businesses SET experience = experience - 100 WHERE user_id = ?", (trolled_user_id, ))
            conn.commit()
    else:
        cursor.execute('SELECT quantity FROM user_inventory WHERE user_id = ? and item_type = ?',
                       (trolled_user_id, items_dict[7]['name']))
        shield_quantity = cursor.fetchone()
        if (not shield_quantity):
            message_text = f'\U0001F9CC <a href="tg://user?id={user_id}">{escape(username)}</a> затроллил(а) ' + trolled_link
            cursor.execute(
                'UPDATE users SET troll_count = troll_count + 1 WHERE user_id = ?', (user_id,))
            cursor.execute(
                'UPDATE users SET trolled_count = trolled_count + 1 WHERE user_id = ?', (trolled_user_id,))
            cursor.execute(
                "DELETE FROM user_inventory WHERE user_id = ? AND item_type = ?", (trolled_user_id, items_dict[7]['name'],))
            if (company is not None and company[0]):
                cursor.execute(
                    "UPDATE businesses SET experience = experience + ? WHERE id = ?", (int(20 * employees_statuses[company[1]]['xp_multiplyer']), company[0], ))
                cursor.execute(
                    "UPDATE businesses SET employee_productivity = employee_productivity + 1 WHERE user_id = ?", (user_id, ))
                conn.commit()
            if (troll_business is not None and troll_business[0] == 1):
                cursor.execute(
                    "UPDATE businesses SET experience = experience + 100 WHERE user_id = ?", (user_id, ))
                conn.commit()
            if (trolled_business is not None and trolled_business[0] == 1):
                cursor.execute(
                    "UPDATE businesses SET experience = experience - 20 WHERE user_id = ?", (trolled_user_id, ))
                conn.commit()
        else:
            if (shield_quantity[0] >= 1):
                cursor.execute(
                    'UPDATE user_inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_type = ?', (trolled_user_id, items_dict[7]["name"]))

                message_text = f'\U00002639 <a href="tg://user?id={user_id}">{escape(username)}</a> попытался(лась) затроллить ' + trolled_link + f', но у ' + trolled_link + f' была {items_dict[7]["name"]}, поэтому ничего не вышло'
                if (company is not None and company[0]):
                    cursor.execute(
                        "UPDATE businesses SET experience = experience - ? WHERE id = ?", (int(5 * employees_statuses[company[1]]['xp_multiplyer']), company[0], ))
                    conn.commit()
                if (troll_business is not None and troll_business[0] == 1):
                    cursor.execute(
                        "UPDATE businesses SET experience = experience - 20 WHERE user_id = ?", (user_id, ))
                    conn.commit()
            else:
                message_text = f'\U0001F9CC <a href="tg://user?id={user_id}">{escape(username)}</a> затроллил(а)' + trolled_link
                cursor.execute(
                    'UPDATE users SET troll_count = troll_count + 1 WHERE user_id = ?', (user_id,))
                cursor.execute(
                    'UPDATE users SET trolled_count = trolled_count + 1 WHERE user_id = ?', (trolled_user_id,))
                cursor.execute(
                    "DELETE FROM user_inventory WHERE user_id = ? AND item_type = ?", (trolled_user_id, items_dict[7]['name'],))
                cursor.execute("DELETE FROM user_inventory WHERE user_id = ? AND item_type = ?", (
                    trolled_user_id, items_dict[7]['name'],))
                if (company is not None and company[0]):
                    cursor.execute(
                        "UPDATE businesses SET experience = experience + ? WHERE id = ?", (int(20 * employees_statuses[company[1]]['xp_multiplyer']), company[0], ))
                    conn.commit()
                if (troll_business is not None and troll_business[0] == 1):
                    cursor.execute(
                        "UPDATE businesses SET experience = experience + 100 WHERE user_id = ?", (user_id, ))
                    conn.commit()
                if (trolled_business is not None and trolled_business[0] == 1):
                    cursor.execute(
                        "UPDATE businesses SET experience = experience - 20 WHERE user_id = ?", (trolled_user_id, ))
                    conn.commit()

    cursor.execute(
        'UPDATE cooldowns SET troll_cooldown = ? WHERE user_id = ?', (int(time.time()), user_id))
    conn.commit()
    conn.close()

    bot.send_message(chat_id, message_text, parse_mode="HTML")


@bot.message_handler(regexp="^/?(сей|тскажи|tsay)(?:@crqrbot)?\s(.+)?$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def say_func(message):

    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user_id = message.from_user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    match = re.match(
        r'^/?(сей|тскажи|tsay)(?:@crqrbot)?\s*?(.+)?$', message.text)
    if match:
        message_text = match.group(2)
    else:
        message_text = ""

    if message_text:
        formatted_text = f"_{message_text}_".capitalize()
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(chat_id=message.chat.id,
                         text=formatted_text, parse_mode="Markdown")
    else:
        return


# endregion

# region Статистика

@bot.message_handler(regexp="^(?:\/?(стат|stat|тстата|tstats|stats)(@crqrbot)?)$")
def show_stat(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    cursor.execute(
        'SELECT troll_count, trolled_count FROM users WHERE user_id = ?', (user_id, ))
    stats = cursor.fetchone()

    message_text = f"\U0001F4CA Статистика пользователя <a href='tg://user?id={user_id}'>{escape(username)}</a>:\n\n\U0001F9CC Пользователь затроллил {stats[0]} человек\n\U00002639 Пользователя затроллили {stats[1]} человек\n\n"

    cursor.execute(
        "SELECT business_employee, created FROM businesses WHERE user_id = ?", (user_id, ))
    user_work = cursor.fetchone()

    if (user_work is None):
        message_text += "\U0001F477 Безработный"
    elif (user_work[1] == 1):
        cursor.execute(
            "SELECT business_name FROM businesses WHERE user_id = ?", (user_id, ))
        company_name = cursor.fetchone()[0]
        message_text += f"\U0001F935 Владеет: \'{company_name}\'"
    else:
        cursor.execute(
            "SELECT business_name FROM businesses WHERE id = ?", (user_work[0], ))
        company_name = cursor.fetchone()[0]
        message_text += f"\U0001F477 Работает в: \'{company_name}\'"

    bot.send_message(
        chat_id, message_text, parse_mode="HTML")
    conn.commit()
    conn.close()


@bot.message_handler(regexp="^(?:\/?(baltop|балтоп|богачи|олигархи)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def bal_top(message):

    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute(
        'SELECT user_id, money FROM users WHERE user_id != ? ORDER BY money DESC LIMIT 15', (bot.get_me().id, ))
    results = cursor.fetchall()
    conn.close()

    if len(results) == 0:
        bot.send_message(chat_id, "Нет пользователей в базе")
        return

    message_text = "<b>\U0001F3A9 Топ-15 богачей в чатике:</b>\n\n"

    for i, result in enumerate(results):
        rich_id = result[0]
        money = result[1]

        try:
            user = bot.get_chat_member(chat_id, rich_id).user
            username = user.first_name + " " + \
                user.last_name if user.last_name is not None else user.first_name
            top_element = f"{i + 1}. <a href='tg://user?id={rich_id}'>{escape(username)}</a>"
        except Exception as e:
            top_element = f"{i + 1}. Неизвестный"

        message_text += f"{top_element} — \U0001FA99 {format_money(money)} ₺\n"

    bot.send_message(chat_id, message_text, parse_mode="HTML")


@bot.message_handler(regexp="^(?:\/?(trolltop|троли|тролли|trolls)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def troll_top(message):

    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute(
        'SELECT user_id, troll_count FROM users ORDER BY troll_count DESC LIMIT 15')
    results = cursor.fetchall()
    conn.close()

    if len(results) == 0:
        bot.send_message(chat_id, "Нет пользователей в базе")
        conn.close()
        return

    message_text = "<b>😝 Топ-15 троллеров в чатике:</b>\n\n"

    for i, result in enumerate(results):
        troll_id = result[0]
        troll_count = result[1]

        try:
            user = bot.get_chat_member(chat_id, troll_id).user
            username = user.first_name + " " + \
                user.last_name if user.last_name is not None else user.first_name
            top_element = f"{i + 1}. <a href='tg://user?id={troll_id}'>{escape(username)}</a>"
        except Exception as e:
            top_element = f"{i + 1}. Неизвестный"

        message_text += f"{top_element} - {troll_count}\n"

    bot.send_message(chat_id, message_text, parse_mode="HTML")


@bot.message_handler(regexp="^(?:\/?(trolledtop|попущи|затролленые|trolled)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def trolled_top(message):

    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute(
        'SELECT user_id, trolled_count FROM users ORDER BY trolled_count DESC LIMIT 15')
    results = cursor.fetchall()
    conn.close()

    if len(results) == 0:
        bot.send_message(chat_id, "Нет пользователей в базе")
        conn.close()
        return

    message_text = "<b>🤮 Топ-15 затролленых (попущей) чатика:</b>\n\n"

    for i, result in enumerate(results):
        trolled_id = result[0]
        trolled_count = result[1]

        try:
            user = bot.get_chat_member(chat_id, trolled_id).user
            username = user.first_name + " " + \
                user.last_name if user.last_name is not None else user.first_name
            top_element = f"{i + 1}. <a href='tg://user?id={trolled_id}'>{escape(username)}</a>"
        except Exception as e:
            top_element = f"{i + 1}. Неизвестный"

        message_text += f"{top_element} - {trolled_count}\n"

    bot.send_message(chat_id, message_text, parse_mode="HTML")


@bot.message_handler(regexp="^(?:\/?(бизнесы|businesses|businesstop|бизнестоп)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def business_top(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute(
        "SELECT id, user_id, business_name, level FROM businesses WHERE created = 1")
    businesses = cursor.fetchall()
    conn.close()

    if len(businesses) == 0:
        bot.send_message(
            chat_id, "\U0001F937 Пока что в чате никто не создал бизнес.")
        conn.close()
        return

    message_text = "\U0001F935 Список бизнесов в чате:\n\n"

    for business in businesses:
        business_id = business[0]
        businessman_id = business[1]
        business_name = business[2]
        level = business[3]

        try:
            user = bot.get_chat_member(chat_id, businessman_id).user
            username = user.first_name + " " + \
                user.last_name if user.last_name is not None else user.first_name
            message_text += f"{business_id}. {business_name} | Уровень {level} | <a href='tg://user?id={businessman_id}'>{escape(username)}</a>\n"
        except Exception as e:
            message_text += f"{business_id}. {business_name} | Уровень {level} | Неизвестный\n"

    bot.send_message(chat_id, message_text, parse_mode="HTML")


@bot.message_handler(regexp="^(?:/?tbanlist|/?тбанлист|/?нарушители|/?забаненные)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def banlist(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute("SELECT user_id FROM users WHERE is_banned = 1")
    banlist = cursor.fetchall()

    if not banlist:
        bot.send_message(chat_id, "\U0001F389 Бан-лист пуст!")
        conn.close()
        return

    message_text = "\U0001F44E Забаненные пользователи:\n"
    for banned_user_id in banlist:
        try:
            user = bot.get_chat_member(chat_id, banned_user_id).user
            user_id = user.id

            if user.first_name is not None:
                username = user.first_name
                if user.last_name is not None:
                    username += " " + user.last_name
            else:
                username = "безымянный"
        except Exception as e:
            conn.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            conn.commit()
            print(f"Пользователь {user_id} не найден в чате {chat_id}: {e}")

        message_text += f"<a href='tg://user?id={user_id}'>{escape(username)}</a>" + "\n"

    bot.send_message(chat_id, message_text, parse_mode="HTML")
    conn.close()


# endregion

# region Деньги


@bot.message_handler(regexp="^(?:\/?(кошелек|деньги|money|wallet|tbalance|тбаланс)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def balance(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    cursor.execute(
        'SELECT money FROM users WHERE user_id = ?', (user_id,))
    current_money = cursor.fetchone()[0]

    empty_wallet_things = ['только мертвые мухи и пара пуговиц',
                           'только огромная дырка и плесень',
                           'только гнилая нитка и кусочки заплесневелой еды',
                           'пусто',
                           'ничего нет',
                           'только засохшая картошина из мака',
                           'только крошки и пыль',
                           'только паутина и давно мертвый паук',
                           'ни одной копейки, только море оптимизма и веры в лучшее',
                           'только немного капель пота и слез',
                           'только скрепки и несколько мятых бумажек',
                           'только бесполезная клубничная жвачка и чей-то волос',
                           'только полусгнивший орех и небольшая горстка пыли',
                           'только презерватив и ржавый гвоздь',
                           'только нераспакованный пакетик соли',
                           'только сломанная зажигалка и флешка с музыкой',
                           'только карта фикспрайса, на которой нет баллов']

    if (current_money == 0):
        bot.send_message(
            chat_id, f"\U0001F45B Кошелек пользователя <a href='tg://user?id={user_id}'>{escape(username)}</a>:\n\n\U0001F614 Тут {random.choice(empty_wallet_things)}...\n\nНо это можно исправить написав /work", parse_mode="HTML")
        conn.close()
    else:
        formatted_money = format_money(current_money)
        bot.send_message(
            chat_id, f"\U0001F45B Кошелек пользователя <a href='tg://user?id={user_id}'>{escape(username)}</a>:\n\n\U0001FA99 {formatted_money} ₺", parse_mode="HTML")
        conn.close()


@bot.message_handler(regexp="^(?:\/?((ферм[кпвс])|work|ворк|((за)?работа(ть)?)|(зарплата|зп)))(@crqrbot)?$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def work(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute(
        'SELECT created, business_employee FROM businesses WHERE user_id = ?', (user_id, ))
    result = cursor.fetchone()
    if (result is None):
        bot.send_message(
            chat_id, "\U0001F9DF Чтобы зарабатывать, нужно для начала устроиться на работу...")
        conn.close()
        return

    has_business = result[0]
    is_employee = result[1]

    if (has_business == 1):
        bot.send_message(chat_id, "\U0001F477 Бизнесмены не работают")
        conn.close()
        return

    if (not is_employee):
        bot.send_message(
            chat_id, "\U0001F9DF Чтобы зарабатывать, нужно устроиться на работу")
        conn.close()
        return

    has_cooldown = is_on_cooldown(
        cursor, user_id, 10800, "work_cooldown", "cooldowns")

    if (has_cooldown[1]):
        bot.send_message(chat_id, has_cooldown[0], parse_mode="HTML")
        conn.close()
        return

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    outcomes = ['salary', 'award']
    weights = [0.95, 0.05]
    result = random.choices(outcomes, weights)[0]

    cursor.execute("SELECT level FROM businesses WHERE id = ?",
                   (is_employee, ))
    company_level = cursor.fetchone()

    income_per_hour = int(
        (100 * company_level[0] ** 3) - (100 * company_level[0] ** 3 * 0.5))

    cursor.execute(
        "SELECT employee_status FROM businesses WHERE user_id = ?", (user_id, ))
    status = cursor.fetchone()[0]

    multiplyer = employees_statuses[status]['multiplyer']

    earned_money = int(income_per_hour * multiplyer)
    if result == 'salary':
        bot.send_message(
            chat_id, f"\U0001FAE1 Сегодня <a href='tg://user?id={user_id}'>{escape(username)}</a> заработал(а) \U0001FA99 {format_money(earned_money)} ₺", parse_mode="HTML")
        cursor.execute(
            'UPDATE users SET money = money + ? WHERE user_id = ?', (earned_money, user_id,))
    else:
        award_money = int(income_per_hour * multiplyer * 2)
        bot.send_message(
            chat_id, f"\U0001FAE1 Сегодня <a href='tg://user?id={user_id}'>{escape(username)}</a> заработал(а) \U0001FA99 {format_money(earned_money)} ₺\n\n\U0001F389 Также за хорошую работу он получает премию в размере \U0001FA99 {format_money(award_money)} ₺", parse_mode="HTML")
        cursor.execute(
            'UPDATE users SET money = money + ? WHERE user_id = ?', (earned_money + award_money, user_id,))
    cursor.execute(
        'UPDATE cooldowns SET work_cooldown = ? WHERE user_id = ?', (int(time.time()), user_id))
    conn.commit()
    conn.close()


@bot.message_handler(regexp="^(?:\/?(charity|получить|дайденег|хочуденег|wantmoney|givememoney)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def get_charity(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute("SELECT money FROM users WHERE user_id = ?", (user_id, ))
    user_money = cursor.fetchone()

    if (user_money[0] > 500):
        bot.send_message(chat_id, "\U0001F645 Вы не выглядите как бедняк...")
        conn.close()
        return

    bot_id = bot.get_me().id

    cursor.execute('SELECT money FROM users WHERE user_id = ?', (bot_id, ))
    bank = cursor.fetchone()

    if (bank[0] < 500):
        bot.send_message(
            chat_id, "\U0001F61E В фонде недостаточно средств для выдачи...")
        conn.close()
        return

    has_cooldown = is_on_cooldown(
        cursor, user_id, 172800, "charity_cooldown", "cooldowns")

    if (has_cooldown[1]):
        bot.send_message(chat_id, has_cooldown[0], parse_mode="HTML")
        conn.close()
        return

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    cursor.execute(
        "UPDATE users SET money = money - 500 WHERE user_id = ?", (bot_id, ))
    cursor.execute(
        "UPDATE users SET money = money + 500 WHERE user_id = ?", (user_id, ))
    cursor.execute('UPDATE cooldowns SET charity_cooldown = ? WHERE user_id = ?', (int(
        time.time()), user_id))
    conn.commit()
    conn.close()

    bot.send_message(
        chat_id, f"\U0001F64F Пользователю <a href='tg://user?id={user_id}'>{escape(username)}</a> было выдано \U0001FA99 500 ₺ из благотворительного фонда \'\U0001F49D Тролье Сердце\'", parse_mode="HTML")


@bot.message_handler(regexp="^(?:\/?(showfund|fundmoney|фонд|скольковфонде)(@crqrbot)?(\s\S+)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def fund_money(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    bot_id = bot.get_me().id

    cursor.execute("SELECT money FROM users WHERE user_id = ?", (bot_id, ))
    fund_money = cursor.fetchone()[0]

    bot.send_message(
        chat_id, f"В фонде \'\U0001F49D Тролье Сердце\' в данный момент \U0001FA99 {format_money(fund_money)} ₺\n\nЧтобы получить материальную помощь напишите \"/charity\"\n\n\U00002754 Получить помощь можно только, если у вас меньше \U0001FA99 500 ₺ на балансе!")


@bot.message_handler(regexp="^(?:\/?(вулкан|казино|vulkan|volcano|casino)(@crqrbot)?(\s\S+)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def casino(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    bet = re.search(r'(?<=\s)\S+', message.text)
    bet = bet.group() if bet else ""

    if (bet == ""):
        bot.send_message(
            chat_id, "\U0001F0CF Эй бро! Есть варик поднять бабла. Играл когда-нибудь в казино? Если нет, то бегом играть!\n\nЧтобы попробовать напиши \'/casino <ставка>\'")
        conn.close()
        return

    amount_match = re.match(r'^(\d*\.?\d+)([а-я]{0,4})$', bet)
    if not amount_match:
        bot.send_message(
            chat_id, "\U0000274C Некорректный формат количества денег. Используйте формат: 'кинуть 50к'")
        conn.close()
        return

    int_bet = float(amount_match.group(1))
    suffix = amount_match.group(2)

    if suffix and suffix in suffixes:
        multiplier = suffixes[suffix]['multiplyer']
        int_bet *= multiplier

    if (int_bet < 0):
        bot.send_message(
            chat_id, "\U0001F928 Ты решил обокрасть казино? Не выйдет.")
        conn.close()
        return

    if (int_bet == 0):
        bot.send_message(chat_id, "\U0001F928 Ты либо ставь либо уходи.")
        conn.close()
        return

    cursor.execute(
        'SELECT money FROM users WHERE user_id = ?', (user_id,))
    current_money = cursor.fetchone()[0]

    if (int_bet > current_money):
        bot.send_message(
            chat_id, "\U0001F62C Недостаточно денег в кошельке...\n\nПроверить баланс - /tbalance")
        conn.close()
        return

    has_cooldown = is_on_cooldown(
        cursor, user_id, 3600, "casino_cooldown", "cooldowns")

    if (has_cooldown[1]):
        bot.send_message(chat_id, has_cooldown[0], parse_mode="HTML")
        conn.close()
        return

    cursor.execute(
        'UPDATE users SET money = money - ? WHERE user_id = ?', (int_bet, user_id,))

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    outcomes = ['x2', 'x5', 'x10', 'loss']
    weights = [0.44, 0.01, 0.05, 0.50]
    result = random.choices(outcomes, weights)[0]

    if result == 'x2':
        cursor.execute(
            'UPDATE users SET money = money + (? * 2) WHERE user_id = ?', (int_bet, user_id,))
        bot.send_message(
            chat_id, text=f'\U0001F4C8 <a href="tg://user?id={user_id}">{escape(username)}</a> удвоил(а) ставку и выиграл(а) \U0001FA99{format_money(int_bet * 2)} ₺', parse_mode="HTML")
    elif result == 'x5':
        cursor.execute(
            'UPDATE users SET money = money + (? * 5) WHERE user_id = ?', (int_bet, user_id,))
        bot.send_message(
            chat_id, text=f'\U0001F4C8 <a href="tg://user?id={user_id}">{escape(username)}</a> сделал(а) x5 и выиграл(а) \U0001FA99 {format_money(int_bet * 5)} ₺', parse_mode="HTML")
    elif result == 'x10':
        cursor.execute(
            'UPDATE users SET money = money + (? * 10) WHERE user_id = ?', (int_bet, user_id,))
        bot.send_message(
            chat_id, text=f'\U0001F4C8 <a href="tg://user?id={user_id}">{escape(username)}</a> сорвал(а) куш и выиграл(а) \U0001FA99 {format_money(int_bet * 10)} ₺', parse_mode="HTML")
    else:
        bot.send_message(
            chat_id, text=f'\U0001F4C9 <a href="tg://user?id={user_id}">{escape(username)}</a> поверил(а) в себя и проиграл(а) \U0001FA99 {format_money(int_bet)} ₺', parse_mode="HTML")

    cursor.execute(
        'UPDATE cooldowns SET casino_cooldown = ? WHERE user_id = ?', (int(time.time()), user_id))
    conn.commit()
    conn.close()


@bot.message_handler(regexp="^(?:\/?(слоты|slots|тритопора|азино|макака)(@crqrbot)?(\s\S+)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def slots(message):

    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    bet = re.search(r'(?<=\s)\S+', message.text)
    bet = bet.group() if bet else ""

    if (bet == ""):
        bot.send_message(
            chat_id, f"\U0001F3B0 Эй! Что ты знаешь про игровые игровые автоматы?\n\n\U00002754 Расклад такой: ты ставишь деньгу, а дальше госпожа фортуна решит, как ей распорядиться. \n\n\U000025AA Пара в ряд - x0.5 сверху ставки \n\U000025AA 3 одинаковые - ставка x3 \n\U000025AA <b><i>777</i></b> - ДЖЕКПОТ ставка x15 \n\n Чтобы попробовать напиши \'/slots {escape('<ставка>')}\'", parse_mode="HTML")
        conn.close()
        return

    amount_match = re.match(r'^(\d*\.?\d+)([а-я]{0,4})$', bet)
    if not amount_match:
        bot.send_message(
            chat_id, "\U0000274C Некорректный формат количества денег. Используйте формат: 'кинуть 50к'")
        conn.close()
        return

    int_bet = float(amount_match.group(1))
    suffix = amount_match.group(2)

    if suffix and suffix in suffixes:
        multiplier = suffixes[suffix]['multiplyer']
        int_bet *= multiplier

    if (int_bet < 0):
        bot.send_message(
            chat_id, "\U0001F928 Ты решил обокрасть казино? Не выйдет.")
        conn.close()
        return

    if (int_bet == 0):
        bot.send_message(chat_id, "\U0001F928 Ты либо ставь либо уходи.")
        conn.close()
        return

    cursor.execute(
        'SELECT money FROM users WHERE user_id = ?', (user_id,))
    current_money = cursor.fetchone()[0]

    if (int_bet > current_money):
        bot.send_message(
            chat_id, "\U0001F62C Недостаточно денег в кошельке...\n\nПроверить баланс - /tbalance")
        conn.close()
        return

    has_cooldown = is_on_cooldown(
        cursor, user_id, 3600, "casino_cooldown", "cooldowns")

    if (has_cooldown[1]):
        bot.send_message(chat_id, has_cooldown[0], parse_mode="HTML")
        conn.close()
        return

    dice = bot.send_dice(chat_id, "\U0001F3B0")
    value = dice.dice.value
    dice_id = dice.id

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    multiplyer = slot_wins[value] if value in slot_wins else 0

    cursor.execute(
        'UPDATE users SET money = money - ? WHERE user_id = ?', (int_bet, user_id,))

    message_text = ""

    if (value in slot_wins):
        prize = math.ceil(int_bet * multiplyer)
        cursor.execute(
            'UPDATE users SET money = money + ? WHERE user_id = ?', (prize, user_id, ))
        conn.commit()
        if (multiplyer != 15):
            message_text = f"\U0001F389 Поздравляем, <a href='tg://user?id={user_id}'>{escape(username)}</a>, удача сегодня на вашей стороне. Вы выиграли \U0001FA99 {format_money(prize)} ₺"
        else:
            message_text = f"\U0001F6A8 <b>ДИНЬ ДИНЬ ДИНЬ</b> Автомат звенит, все подбегают к <a href='tg://user?id={user_id}'>{escape(username)}</a>, ведь сегодня он(а) сорвал(а) <i>ДЖЕКПОТ</i>.\n\nОн(а) выиграл(а) \U0001FA99 {format_money(prize)} ₺"

    else:
        message_text = f"\U0001F616 <a href='tg://user?id={user_id}'>{escape(username)}</a> не повезло, он(а) проиграл(а) {format_money(int_bet)}"

    cursor.execute(
        'UPDATE cooldowns SET casino_cooldown = ? WHERE user_id = ?', (int(time.time()), user_id))
    conn.commit()
    conn.close()
    time.sleep(3.5)
    bot.delete_message(chat_id, dice_id)
    bot.send_message(chat_id, message_text, parse_mode="HTML")


@bot.message_handler(regexp="^(?:\/?(тперевести|тпередать|заплатить|tgive|tpay|кинуть)(@crqrbot)?(\s\S+)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def pay_money(message):
    chat_id = message.chat.id

    if not is_target_chat(chat_id):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if is_restricted_user(user_id):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if is_banned:
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    if not message.reply_to_message:
        bot.send_message(
            chat_id, "\U0000274C Необходимо переслать сообщение пользователя, чтобы перевести деньги️")
        conn.close()
        return

    user_to_pay = message.reply_to_message.from_user
    user_to_pay_id = message.reply_to_message.from_user.id

    if is_restricted_user(user_to_pay_id):
        bot.send_message(
            chat_id, "\U0001F645 Пользователь был исключен из базы.")
        conn.close()
        return

    if user_id == user_to_pay_id:
        bot.send_message(
            chat_id, "\U0001F610 Нельзя дать денег самому себе...")
        conn.commit()
        conn.close()
        return

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_to_pay_id, ))
    to_pay_is_banned = cursor.fetchone()[0]

    if to_pay_is_banned:
        bot.send_message(
            chat_id, "\U0001F34C Пользователь, которому вы хотите перевести деньги, был забанен в боте. Вряд ли ему нужны деньги.")
        conn.close()
        return

    money_to_pay = re.search(r'(?<=\s)\S+', message.text)
    money_to_pay = money_to_pay.group() if money_to_pay else ""

    if money_to_pay == "":
        bot.send_message(
            chat_id, "\U0001F4B3 Чтобы переводить деньги, нужно переслать сообщение и написать: \'/тперевести <кол-во>\'")
        conn.close()
        return

    amount_match = re.match(r'^(\d*\.?\d+)([а-я]{0,4})$', money_to_pay)
    if not amount_match:
        bot.send_message(
            chat_id, "\U0000274C Некорректный формат количества денег. Используйте формат: 'кинуть 50к'")
        conn.close()
        return

    amount = float(amount_match.group(1))
    suffix = amount_match.group(2)

    if suffix and suffix in suffixes:
        multiplier = suffixes[suffix]['multiplyer']
        amount *= multiplier

    if amount <= 0:
        bot.send_message(
            chat_id, "\U0001F928 Внимание! В чате обнаружен вор. Бей его!!! \U0001F44A")
        conn.close()
        return

    cursor.execute(
        'SELECT money FROM users WHERE user_id = ?', (user_id,))
    current_money = cursor.fetchone()[0]

    if amount > current_money:
        bot.send_message(
            chat_id, "\U0001F62C Недостаточно денег в кошельке...\n\nПроверить баланс - /tbalance")
        conn.close()
        return

    cursor.execute(
        'UPDATE users SET money = money + ? WHERE user_id = ?', (amount, user_to_pay_id))
    cursor.execute(
        'UPDATE users SET money = money - ? WHERE user_id = ?', (amount, user_id))
    conn.commit()

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    bot_id = bot.get_me().id

    if user_to_pay_id == bot_id:
        message_text = f"\U0001F64F <a href='tg://user?id={user_id}'>{escape(username)}</a> пожертвовал(а) в фонд \"\U0001F49D Тролье Сердце\" \U0001FA99 {format_money(amount)} ₺"
    else:
        if user_to_pay.first_name is not None:
            username_to_pay = user_to_pay.first_name
            if user_to_pay.last_name is not None:
                username_to_pay += " " + user_to_pay.last_name
        else:
            username_to_pay = "безымянному"
        message_text = f"\U0001F91D <a href='tg://user?id={user_id}'>{escape(username)}</a> передал(а) <a href='tg://user?id={user_to_pay_id}'>{escape(username_to_pay)}</a> \U0001FA99 {format_money(amount)} ₺"

    conn.commit()
    conn.close()

    bot.send_message(
        chat_id, message_text, parse_mode="HTML")

# endregion

# region Магазин


@bot.message_handler(regexp="^(?:\/?(магазин|tshop|магаз)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def shop(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    message_text = f"<b>\U0001F9D4 Вай брат! Товары отменные не пожалеешь! Все свежее, заходи, покупай!</b>\n\n"
    for item in items_dict:
        message_text += f"{item}. {items_dict[item]['name']} — \U0001FA99 {format_money(items_dict[item]['price'])} ₺\n"

    message_text += f"\nЧтобы что-то купить, напиши \"<b>ткупить {escape('<номер> <количество>')}</b>\""

    bot.send_message(chat_id, message_text, parse_mode="HTML")


@bot.message_handler(regexp="^(?:\/?(ткупить|tbuy)(@crqrbot)?(\s\S+)?(\s\S+)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def buy_item(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    match = re.match(
        r'^\/?(ткупить|tbuy)(@crqrbot)?(\s+\S+){1,2}$', message.text)

    if match:
        items = match.group().split()[1:]
        item_number = items[0]
        item_quantity = items[1] if len(items) == 2 else 1
    else:
        bot.send_message(
            chat_id, f"\U0001F4B3 Чтобы что-то купить необходимо написать:\n\'<b>/ткупить {escape('<номер> <кол-во>')}</b>\'", parse_mode="HTML")
        conn.close()
        return

    try:
        int_item_number = int(item_number)
    except ValueError:
        bot.send_message(
            chat_id, "\U0000274C Номер предмета должен быть числом")
        conn.close()
        return

    try:
        int_item_quantity = int(item_quantity)
    except ValueError:
        bot.send_message(
            chat_id, "\U0000274C Количество предмета должно быть числом")
        conn.close()
        return

    if (int_item_number < 0):
        bot.send_message(
            chat_id, "\U0001F928 Номер предмета должен быть положительным")
        conn.close()
        return

    if (int_item_number == 0):
        bot.send_message(
            chat_id, "\U0001F928 Номер предмета - число строго больше нуля")
        conn.close()
        return

    if (int_item_number > len(items_dict)):
        bot.send_message(chat_id, f"\U0000274C Нет такого предмета")
        conn.close()
        return

    if (int_item_quantity < 0):
        bot.send_message(
            chat_id, "\U0001F928 Количество предмета должно быть положительным")
        conn.close()
        return

    if (int_item_quantity == 0):
        bot.send_message(
            chat_id, "\U0001F928 Количество предмета - число строго больше нуля")
        conn.close()
        return

    total_price = items_dict[int_item_number]["price"] * int_item_quantity

    cursor.execute(
        'SELECT money FROM users WHERE user_id = ?', (user_id,))
    current_money = cursor.fetchone()[0]

    if (total_price > current_money):
        bot.send_message(
            chat_id, "\U0001F62C Недостаточно денег в кошельке...\n\nПроверить баланс - /tbalance")
        conn.close()
        return

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    cursor.execute("SELECT quantity FROM user_inventory WHERE user_id = ? and item_type = ?",
                   (user_id, items_dict[int_item_number]["name"]))
    quantity = cursor.fetchone()

    if (quantity):
        cursor.execute("UPDATE user_inventory SET quantity = quantity + ? WHERE user_id = ? AND item_type = ?",
                       (int_item_quantity, user_id, items_dict[int_item_number]["name"]))
    else:
        cursor.execute("INSERT INTO user_inventory (user_id, item_type, quantity) VALUES (?, ?, ?)",
                       (user_id, items_dict[int_item_number]["name"], int_item_quantity))

    cursor.execute("UPDATE users SET money = money - ? WHERE user_id = ?",
                   (total_price, user_id))
    conn.commit()
    conn.close()

    message_text = f"\U0001F9FE <a href='tg://user?id={user_id}'>{escape(username)}</a> купил(а) {items_dict[int_item_number]['name']} в количестве {int_item_quantity} за \U0001FA99 {format_money(total_price)} ₺" + f"\n\n\U00002754 Чтобы использовать напишите - \"{items_dict[int_item_number]['command']}\"" if 'command' in items_dict[
        int_item_number] else f"\U0001F9FE <a href='tg://user?id={user_id}'>{escape(username)}</a> купил(а) {items_dict[int_item_number]['name']} в количестве {int_item_quantity} за \U0001FA99 {format_money(total_price)} ₺"

    bot.send_message(
        chat_id, message_text, parse_mode="HTML")

# endregion

# region Инвентарь


@bot.message_handler(regexp="^(?:\/?(инвентарь|inventory|вещи|хранилище|рюкзак|backpack|авоська)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def show_inventory(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute(
        "SELECT item_type, quantity FROM user_inventory WHERE user_id = ?  ORDER BY quantity DESC", (user_id,))
    inventory = cursor.fetchall()

    inventory_str = ''
    for i, item in enumerate(inventory):
        if (item[1] <= 0):
            cursor.execute(
                "DELETE FROM user_inventory WHERE user_id = ? AND item_type = ?", (user_id, item[0],))
            conn.commit()
            continue
        inventory_str += f"{i+1}. {item[0]}: {item[1]}\n"

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    # Если инвентарь пуст, отправляем сообщение об этом пользователю
    if not inventory_str:
        empty_inventory_things = ['только мертвые мухи и пара пуговиц',
                                  'только огромная дырка и плесень',
                                  'только гнилая нитка и кусочки заплесневелой еды',
                                  'пусто',
                                  'ничего нет',
                                  'только засохшая картошина из мака',
                                  'только крошки и пыль',
                                  'только паутина и давно мертвый паук',
                                  'ни одной вещи, только море оптимизма и веры в лучшее',
                                  'только немного капель пота и слез',
                                  'только скрепки и несколько мятых бумажек',
                                  'только бесполезная клубничная жвачка и чей-то волос',
                                  'только полусгнивший орех и небольшая горстка пыли',
                                  'только презерватив и ржавый гвоздь',
                                  'только нераспакованный пакетик соли',
                                  'только сломанная зажигалка и флешка с музыкой',
                                  'только карта фикспрайса, на которой нет баллов']
        bot.send_message(
            chat_id, f"\U0001F392 Рюкзак пользователя <a href='tg://user?id={user_id}'>{escape(username)}</a>:\n\n\U0001F614 Тут {random.choice(empty_inventory_things)}...", parse_mode="HTML")
        conn.close()
        return
    else:
        bot.send_message(
            message.chat.id, f"\U0001F392 Рюкзак пользователя <a href='tg://user?id={user_id}'>{escape(username)}</a>:\n\n{inventory_str}", parse_mode="HTML")

    conn.close()


# endregion

# region Предметы


@bot.message_handler(regexp="^(?:\/?(ткейс|tcase|itemcase|trollcase|троллкейс)(@crqrbot)?(\s\S+)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def open_item_case(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute("SELECT quantity FROM user_inventory WHERE user_id = ? and item_type = ?",
                   (user_id, items_dict[1]["name"]))
    quantity = cursor.fetchone()

    if (not quantity):
        bot.send_message(
            chat_id, f"\U0001F937 Нет предмета {items_dict[1]['name']} в инвентаре\n\nПосмотреть инвентарь - /inventory")
        conn.close()
        return

    if (quantity[0] <= 0):
        bot.send_message(
            chat_id, f"\U0001F937 Нет предмета {items_dict[1]['name']} в инвентаре\n\nПосмотреть инвентарь - /inventory")
        cursor.execute(
            "DELETE FROM user_inventory WHERE user_id = ? AND item_type = ?", (user_id, items_dict[1]["name"],))
        conn.commit()
        conn.close()
        return

    cases_to_open = re.search(r'(?<=\s)\S+', message.text)
    cases_to_open = cases_to_open.group() if cases_to_open else ""

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name + " "
    else:
        username = "безымянный"

    int_cases_to_open = 1

    all_items = list(items_dict.keys())

    weights = [item["prob"] for item in items_dict.values()]

    items_list = {}

    image = open('manyitems.png', 'rb')

    if (cases_to_open):

        try:
            int_cases_to_open = int(cases_to_open)
        except ValueError:
            bot.send_message(
                chat_id, "\U0000274C Чтобы открыть несколько кейсов, необходимо ввести целое число...")
            conn.close()
            return

        if (int_cases_to_open < 0):
            bot.send_message(
                chat_id, "\U0001F928 Количество кейсов не может быть отрицательным")
            conn.close()
            return

        if (int_cases_to_open == 0):
            bot.send_message(
                chat_id, "\U0001F928 Для чего тебе открывать \"ничего\"?")
            conn.close()
            return

        if (int_cases_to_open > quantity[0]):
            bot.send_message(
                chat_id, "\U0001F62C Нет столько кейсов в инвентаре...\n\nПосмотреть инвентарь - /inventory")
            conn.close()
            return

        for _ in range(int_cases_to_open):

            item_number = random.choices(all_items, weights=weights)[0]

            item = items_dict[item_number]["name"]

            if (item in items_list):
                items_list[item] += 1
            else:
                items_list[item] = 1

            cursor.execute("SELECT quantity FROM user_inventory WHERE user_id = ? AND item_type = ?",
                           (user_id, item, ))
            dropped_quantity = cursor.fetchone()

            if (dropped_quantity):
                if (dropped_quantity[0] <= 0):
                    cursor.execute("UPDATE user_inventory SET quantity = 1 WHERE user_id = ? and item_type = ?",
                                   (user_id, item, ))
                else:
                    cursor.execute("UPDATE user_inventory SET quantity = quantity + 1 WHERE user_id = ? and item_type = ?",
                                   (user_id, item, ))
            else:
                cursor.execute("INSERT INTO user_inventory (user_id, item_type, quantity) VALUES (?, ?, ?)",
                               (user_id, item, 1))

        conn.commit()

        items_list = sorted(items_list.items(),
                            key=lambda item: item[1], reverse=True)

        result = "\n".join([f"{item[0]} — {item[1]}" for item in items_list])

    else:
        item_number = random.choices(all_items, weights=weights)[0]

        item = items_dict[item_number]["name"]

        result = f"{item}"

        cursor.execute("SELECT quantity FROM user_inventory WHERE user_id = ? AND item_type = ?",
                       (user_id, items_dict[item_number]["name"], ))
        dropped_quantity = cursor.fetchone()

        image = open(items_dict[item_number]["image"], 'rb')

        if (dropped_quantity):
            if (dropped_quantity[0] <= 0):
                cursor.execute("UPDATE user_inventory SET quantity = 1 WHERE user_id = ? and item_type = ?",
                               (user_id, item, ))
            else:
                cursor.execute("UPDATE user_inventory SET quantity = quantity + 1 WHERE user_id = ? and item_type = ?",
                               (user_id, item, ))
        else:
            cursor.execute("INSERT INTO user_inventory (user_id, item_type, quantity) VALUES (?, ?, ?)",
                           (user_id, item, 1))

    cursor.execute('UPDATE user_inventory SET quantity = quantity - ? WHERE user_id = ? AND item_type = ?',
                   (int_cases_to_open, user_id, items_dict[1]["name"]))

    bot.send_photo(chat_id, image,
                   caption=f'\U0001F9F0 <a href="tg://user?id={user_id}">{escape(username)}</a> открыл(а) {int_cases_to_open} {items_dict[1]["name"]} и вытащил(а) оттуда:\n\n{result}', parse_mode="HTML")

    conn.commit()
    conn.close()


@bot.message_handler(regexp="^(?:\/?(дкейс|mcase|moneycase|деньгокейс)(@crqrbot)?(\s\S+)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def open_money_case(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute("SELECT quantity FROM user_inventory WHERE user_id = ? and item_type = ?",
                   (user_id, items_dict[2]["name"]))
    quantity = cursor.fetchone()

    if (not quantity):
        bot.send_message(
            chat_id, f"\U0001F937 Нет предмета {items_dict[2]['name']} в инвентаре\n\nПосмотреть инвентарь - /inventory")
        conn.close()
        return

    if (quantity[0] <= 0):
        bot.send_message(
            chat_id, f"\U0001F937 Нет предмета {items_dict[2]['name']} в инвентаре\n\nПосмотреть инвентарь - /inventory")
        cursor.execute(
            "DELETE FROM user_inventory WHERE user_id = ? AND item_type = ?", (user_id, items_dict[2]["name"],))
        conn.commit()
        conn.close()
        return

    cases_to_open = re.search(r'(?<=\s)\S+', message.text)
    cases_to_open = cases_to_open.group() if cases_to_open else ""

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    int_cases_to_open = 1

    if (cases_to_open):

        try:
            int_cases_to_open = int(cases_to_open)
        except ValueError:
            bot.send_message(
                chat_id, "\U0000274C Чтобы открыть несколько кейсов, необходимо ввести целое число...")
            conn.close()
            return

        if (int_cases_to_open < 0):
            bot.send_message(
                chat_id, "\U0001F928 Количество кейсов не может быть отрицательным")
            conn.close()
            return

        if (int_cases_to_open == 0):
            bot.send_message(
                chat_id, "\U0001F928 Для чего тебе открывать \"ничего\"?")
            conn.close()
            return

        if (int_cases_to_open > quantity[0]):
            bot.send_message(
                chat_id, "\U0001F62C Нет столько кейсов в инвентаре...\n\nПосмотреть инвентарь - /inventory")
            conn.close()
            return

        money_ammount = 0

        for _ in range(int_cases_to_open):
            outcomes = ['less', 'more', 'jackpot']
            weights = [0.55, 0.44, 0.01]

            result = random.choices(outcomes, weights)[0]

            if result == 'less':
                money_ammount += random.randrange(0, 5000, 100)
            elif result == 'jackpot':
                money_ammount += random.randrange(10000, 100000, 1000)
            else:
                money_ammount += random.randrange(6000, 10000, 100)
    else:
        outcomes = ['less', 'more', 'jackpot']
        weights = [0.55, 0.44, 0.01]

        result = random.choices(outcomes, weights)[0]

        if result == 'less':
            money_ammount = random.randrange(0, 5000, 100)
        elif result == 'jackpot':
            money_ammount = random.randrange(10000, 100000, 1000)
        else:
            money_ammount = random.randrange(6000, 10000, 100)

    cursor.execute(
        "UPDATE users SET money = money + ? WHERE user_id = ?", (money_ammount, user_id, ))

    cursor.execute('UPDATE user_inventory SET quantity = quantity - ? WHERE user_id = ? AND item_type = ?',
                   (int_cases_to_open, user_id, items_dict[2]["name"]))

    bot.send_message(
        chat_id, f'\U0001F9F0 <a href="tg://user?id={user_id}">{escape(username)}</a> открыл(а) {int_cases_to_open} {items_dict[2]["name"]} и вытащил(а) оттуда \U0001FA99 {format_money(money_ammount)} ₺', parse_mode="HTML")

    conn.commit()
    conn.close()


@bot.message_handler(regexp="^(?:\/?(мегатролл|мегатрол|megatroll|megatrol|trollbomb|trolbomb|тролбомб|троллбомб|трольябомба)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def megatroll(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute("SELECT quantity FROM user_inventory WHERE user_id = ? and item_type = ?",
                   (user_id, items_dict[3]["name"]))
    quantity = cursor.fetchone()

    if (not quantity):
        bot.send_message(
            chat_id, f"\U0001F937 Нет предмета {items_dict[3]['name']} в инвентаре\n\nПосмотреть инвентарь - /inventory")
        conn.close()
        return

    if (quantity[0] <= 0):
        bot.send_message(
            chat_id, f"\U0001F937 Нет предмета {items_dict[3]['name']} в инвентаре\n\nПосмотреть инвентарь - /inventory")
        cursor.execute(
            "DELETE FROM user_inventory WHERE user_id = ? AND item_type = ?", (user_id, items_dict[3]["name"],))
        conn.commit()
        conn.close()
        return

    now = datetime.datetime.fromtimestamp(int(time.time()))

    cursor.execute(
        "SELECT mt_cooldown FROM cooldowns WHERE user_id = ?", (user_id, ))
    last_used = datetime.datetime.fromtimestamp(
        cursor.fetchone()[0])

    timediff = int((now - last_used).total_seconds())

    if (timediff >= 86400):
        cursor.execute(
            "UPDATE users SET mt_used = 0 WHERE user_id = ?", (user_id, ))
        conn.commit()

    cursor.execute("SELECT mt_used FROM users WHERE user_id = ?", (user_id, ))
    megatroll_used = cursor.fetchone()[0]

    if (megatroll_used >= 3):
        bot.send_message(
            chat_id, f"\U0000270B Вы использовали слишком много предмета {items_dict[3]['name']}\n\n", parse_mode="HTML")
        conn.commit()
        conn.close()
        return

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    message_text = f"\U0001F4A5 <a href='tg://user?id={user_id}'>{escape(username)}</a> взорвал(а) \U0001F608 Тролью бомбу. Осколки задели следующих:\n"

    number_to_troll = random.randint(3, 6)

    cursor.execute(
        "SELECT created FROM businesses WHERE user_id = ?", (user_id, ))
    troll_business = cursor.fetchone()

    cursor.execute(
        "SELECT business_employee, employee_status FROM businesses WHERE user_id = ?", (user_id, ))
    company = cursor.fetchone()

    message_id = bot.send_message(
        chat_id, f"\U0001F4A5 <a href='tg://user?id={user_id}'>{escape(username)}</a> взорвал(а) \U0001F608 Тролью бомбу. Осколки летят...", parse_mode="HTML").id

    cursor.execute(
        'SELECT user_id FROM users ORDER BY RANDOM() LIMIT ?', (number_to_troll, ))
    result = cursor.fetchall()
    if result is not None:
        for trolled_user_id in result:
            try:
                trolled_user = bot.get_chat_member(message.chat.id, trolled_user_id[0])
                if trolled_user.user.first_name is not None:
                    trolled_user_username = trolled_user.user.first_name
                    if trolled_user.user.last_name is not None:
                        trolled_user_username += " " + trolled_user.user.last_name
                else:
                    trolled_user_username = "безымянного"
                trolled_link = f'<a href="tg://user?id={trolled_user_id[0]}">{escape(trolled_user_username)}</a>'
            except Exception as e:
                trolled_link = "Неизвестного"

            cursor.execute(
                "SELECT created FROM businesses WHERE user_id = ?", (trolled_user_id[0], ))
            trolled_business = cursor.fetchone()

            cursor.execute('SELECT quantity FROM user_inventory WHERE user_id = ? and item_type = ?',
                           (trolled_user_id[0], items_dict[7]['name']))
            shield_quantity = cursor.fetchone()
            if (trolled_user_id[0] == user_id):
                message_text += trolled_link + "\n"
                cursor.execute(
                    'UPDATE users SET troll_count = troll_count - 1 WHERE user_id = ?', (trolled_user_id[0],))
                if (troll_business is not None and troll_business[0] == 1):
                    cursor.execute(
                        "UPDATE businesses SET experience = experience - 100 WHERE user_id = ?", (user_id, ))
                    conn.commit()
                if (company is not None and company[0]):
                    cursor.execute(
                        "UPDATE businesses SET experience = experience - ? WHERE id = ?", (int(20 * employees_statuses[company[1]]['xp_multiplyer']), company[0], ))
                    conn.commit()
            else:
                if (not shield_quantity):
                    message_text += trolled_link + "\n"
                    cursor.execute(
                        'UPDATE users SET troll_count = troll_count + 1 WHERE user_id = ?', (user_id,))
                    cursor.execute(
                        'UPDATE users SET trolled_count = trolled_count + 1 WHERE user_id = ?', (trolled_user_id[0],))
                    cursor.execute(
                        "DELETE FROM user_inventory WHERE user_id = ? AND item_type = ?", (trolled_user_id[0], items_dict[7]['name'],))
                    if (troll_business is not None and troll_business[0] == 1):
                        cursor.execute(
                            "UPDATE businesses SET experience = experience + 100 WHERE user_id = ?", (user_id, ))
                        conn.commit()
                    if (trolled_business is not None and trolled_business[0] == 1):
                        cursor.execute(
                            "UPDATE businesses SET experience = experience - 20 WHERE user_id = ?", (trolled_user_id[0], ))
                        conn.commit()
                    if (company is not None and company[0]):
                        cursor.execute(
                            "UPDATE businesses SET experience = experience + ? WHERE id = ?", (int(20 * employees_statuses[company[1]]['xp_multiplyer']), company[0], ))
                        cursor.execute(
                            "UPDATE businesses SET employee_productivity = employee_productivity + 1 WHERE user_id = ?", (user_id, ))
                    conn.commit()
                    conn.commit()
                else:
                    if (shield_quantity[0] >= 1):
                        message_text += trolled_link + " у пользователя была {items_dict[7]['name']}, троллинг не прошел\n"
                        cursor.execute(
                            'UPDATE user_inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_type = ?', (trolled_user_id[0], items_dict[7]["name"]))
                        if (troll_business is not None and troll_business[0] == 1):
                            cursor.execute(
                                "UPDATE businesses SET experience = experience - 20 WHERE user_id = ?", (user_id, ))
                            conn.commit()
                        if (company is not None and company[0]):
                            cursor.execute(
                                "UPDATE businesses SET experience = experience - ? WHERE id = ?", (int(5 * employees_statuses[company[1]]['xp_multiplyer']), company[0], ))
                        conn.commit()
                    else:
                        message_text += trolled_link + "\n"
                        cursor.execute(
                            'UPDATE users SET troll_count = troll_count + 1 WHERE user_id = ?', (user_id,))
                        cursor.execute(
                            'UPDATE users SET trolled_count = trolled_count + 1 WHERE user_id = ?', (trolled_user_id[0],))
                        cursor.execute("DELETE FROM user_inventory WHERE user_id = ? AND item_type = ?", (
                            trolled_user_id[0], items_dict[7]['name'],))
                        if (troll_business is not None and troll_business[0] == 1):
                            cursor.execute(
                                "UPDATE businesses SET experience = experience + 100 WHERE user_id = ?", (user_id, ))
                            conn.commit()
                        if (trolled_business is not None and trolled_business[0] == 1):
                            cursor.execute(
                                "UPDATE businesses SET experience = experience - 20 WHERE user_id = ?", (trolled_user_id[0], ))
                            conn.commit()
                        if (company is not None and company[0]):
                            cursor.execute(
                                "UPDATE businesses SET experience = experience + ? WHERE id = ?", (int(20 * employees_statuses[company[1]]['xp_multiplyer']), company[0], ))
                            cursor.execute(
                                "UPDATE businesses SET employee_productivity = employee_productivity + 1 WHERE user_id = ?", (user_id, ))
                            conn.commit()

            conn.commit()
    else:
        # если в таблице нет пользователей
        bot.send_message(chat_id, "никого в базе")
        conn.close()
        return

    cursor.execute('UPDATE user_inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_type = ?',
                   (user_id, items_dict[3]["name"]))
    cursor.execute(
        "UPDATE users SET mt_used = mt_used + 1 WHERE user_id = ?", (user_id, ))
    cursor.execute("UPDATE cooldowns SET mt_cooldown = ? WHERE user_id = ?", (int(
        time.time()), user_id, ))
    conn.commit()
    conn.close()

    bot.edit_message_text(message_text, chat_id, message_id, parse_mode="HTML")


@bot.message_handler(regexp="^(?:\/?(removecooldowns|обнулить|путин|убратькулдауны|обнуление)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def remove_cooldowns(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute("SELECT quantity FROM user_inventory WHERE user_id = ? and item_type = ?",
                   (user_id, items_dict[4]["name"]))
    quantity = cursor.fetchone()

    if (not quantity):
        bot.send_message(
            chat_id, f"\U0001F937 Нет предмета {items_dict[4]['name']} в инвентаре\n\nПосмотреть инвентарь - /inventory")
        conn.close()
        return

    if (quantity[0] <= 0):
        bot.send_message(
            chat_id, f"\U0001F937 Нет предмета {items_dict[4]['name']} в инвентаре\n\nПосмотреть инвентарь - /inventory")
        cursor.execute(
            "DELETE FROM user_inventory WHERE user_id = ? AND item_type = ?", (user_id, items_dict[4]["name"],))
        conn.commit()
        conn.close()
        return

    now = datetime.datetime.fromtimestamp(int(time.time()))

    cursor.execute(
        "SELECT rc_cooldown FROM cooldowns WHERE user_id = ?", (user_id, ))
    last_used = datetime.datetime.fromtimestamp(
        cursor.fetchone()[0])

    timediff = int((now - last_used).total_seconds())

    if (timediff >= 86400):
        cursor.execute(
            "UPDATE users SET rc_used = 0 WHERE user_id = ?", (user_id, ))
        conn.commit()

    cursor.execute("SELECT rc_used FROM users WHERE user_id = ?", (user_id, ))
    removecooldowns_used = cursor.fetchone()[0]

    if (removecooldowns_used >= 2):
        bot.send_message(
            chat_id, f"\U0000270B Вы использовали слишком много предмета {items_dict[4]['name']}\n\n", parse_mode="HTML")
        conn.commit()
        conn.close()
        return

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    cursor.execute('UPDATE user_inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_type = ?',
                   (user_id, items_dict[4]["name"]))
    cursor.execute(
        "UPDATE users SET rc_used = rc_used + 1 WHERE user_id = ?", (user_id, ))
    cursor.execute(
        "UPDATE cooldowns SET troll_cooldown = 0, casino_cooldown = 0, work_cooldown = 0, get_job_cooldown = 0 WHERE user_id = ?", (user_id,))
    cursor.execute("UPDATE cooldowns SET rc_cooldown = ? WHERE user_id = ?", (int(
        time.time()), user_id, ))

    conn.commit()
    conn.close()

    bot.send_message(
        chat_id, f"\U0001F504 <a href='tg://user?id={user_id}'>{escape(username)}</a> обнулил(а) свои кулдауны", parse_mode="HTML")


@bot.message_handler(regexp="^(?:\/?(restoreitems|обнулить предметы|обнуление предметов|)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def restore_items(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute("SELECT quantity FROM user_inventory WHERE user_id = ? and item_type = ?",
                   (user_id, items_dict[9]["name"]))
    quantity = cursor.fetchone()

    if (not quantity):
        bot.send_message(
            chat_id, f"\U0001F937 Нет предмета {items_dict[9]['name']} в инвентаре\n\nПосмотреть инвентарь - /inventory")
        conn.close()
        return

    if (quantity[0] <= 0):
        bot.send_message(
            chat_id, f"\U0001F937 Нет предмета {items_dict[9]['name']} в инвентаре\n\nПосмотреть инвентарь - /inventory")
        cursor.execute(
            "DELETE FROM user_inventory WHERE user_id = ? AND item_type = ?", (user_id, items_dict[4]["name"],))
        conn.commit()
        conn.close()
        return

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    cursor.execute('UPDATE user_inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_type = ?',
                   (user_id, items_dict[9]["name"]))
    cursor.execute(
        "UPDATE users SET mt_used = 0, tt_used = 0, rc_used = 0, rt_used = 0, ta_used = 0 WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()

    bot.send_message(
        chat_id, f"\U0001F4E6 <a href='tg://user?id={user_id}'>{escape(username)}</a> обнулил(а) использования предметов", parse_mode="HTML")


@bot.message_handler(regexp="^(?:\/?(targettroll|таргертролл|ттролл|ttroll|target|точныйудар)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def target_troll(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute("SELECT quantity FROM user_inventory WHERE user_id = ? and item_type = ?",
                   (user_id, items_dict[5]["name"]))
    quantity = cursor.fetchone()

    if (not quantity):
        bot.send_message(
            chat_id, f"\U0001F937 Нет предмета {items_dict[5]['name']} в инвентаре\n\nПосмотреть инвентарь - /inventory")
        conn.close()
        return

    if (quantity[0] <= 0):
        bot.send_message(
            chat_id, f"\U0001F937 Нет предмета {items_dict[5]['name']} в инвентаре\n\nПосмотреть инвентарь - /inventory")
        cursor.execute(
            "DELETE FROM user_inventory WHERE user_id = ? AND item_type = ?", (user_id, items_dict[5]["name"],))
        conn.commit()
        conn.close()
        return

    now = datetime.datetime.fromtimestamp(int(time.time()))

    cursor.execute(
        "SELECT tt_cooldown FROM cooldowns WHERE user_id = ?", (user_id, ))
    last_used = datetime.datetime.fromtimestamp(
        cursor.fetchone()[0])

    timediff = int((now - last_used).total_seconds())

    if (timediff > 86400):
        cursor.execute(
            "UPDATE users SET tt_used = 0 WHERE user_id = ?", (user_id, ))
        conn.commit()

    cursor.execute("SELECT tt_used FROM users WHERE user_id = ?", (user_id, ))
    traget_used = cursor.fetchone()[0]

    if (traget_used >= 5):
        bot.send_message(
            chat_id, f"\U0000270B Вы использовали слишком много предмета {items_dict[5]['name']}\n\n", parse_mode="HTML")
        conn.commit()
        conn.close()
        return

    if (not message.reply_to_message):
        bot.send_message(
            chat_id, f"\U0001F645 Чтобы использовать {items_dict[5]['name']}, необходимо переслать сообщение пользователя.")
        conn.close()
        return

    user_to_troll = message.reply_to_message.from_user
    user_to_troll_id = message.reply_to_message.from_user.id

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    if user_to_troll.first_name is not None:
        trolled_username = user_to_troll.first_name
        if user_to_troll.last_name is not None:
            trolled_username += " " + user_to_troll.last_name
    else:
        username = "безымянный"

    cursor.execute(
        "SELECT created FROM businesses WHERE user_id = ?", (user_id, ))
    troll_business = cursor.fetchone()
    cursor.execute(
        "SELECT created FROM businesses WHERE user_id = ?", (user_to_troll_id, ))
    trolled_business = cursor.fetchone()
    cursor.execute(
        "SELECT business_employee, employee_status FROM businesses WHERE user_id = ?", (user_id, ))
    company = cursor.fetchone()

    cursor.execute('SELECT quantity FROM user_inventory WHERE user_id = ? and item_type = ?',
                   (user_to_troll_id, items_dict[7]['name']))

    shield_quantity = cursor.fetchone()
    if (not shield_quantity):
        message_text = f"\U0001F9CC <a href='tg://user?id={user_id}'>{escape(username)}</a> использовал(а) {items_dict[5]['name']} на <a href='tg://user?id={user_to_troll_id}'>{escape(trolled_username)}</a>"
        cursor.execute(
            'UPDATE users SET troll_count = troll_count + 1 WHERE user_id = ?', (user_id,))
        cursor.execute(
            'UPDATE users SET trolled_count = trolled_count + 1 WHERE user_id = ?', (user_to_troll_id,))
        cursor.execute(
            "DELETE FROM user_inventory WHERE user_id = ? AND item_type = ?", (user_to_troll_id, items_dict[7]['name'],))
        if (troll_business is not None and troll_business[0] == 1):
            cursor.execute(
                "UPDATE businesses SET experience = experience + 100 WHERE user_id = ?", (user_id, ))
        if (trolled_business is not None and trolled_business[0] == 1):
            cursor.execute(
                "UPDATE businesses SET experience = experience - 20 WHERE user_id = ?", (user_to_troll_id, ))
        if (company is not None and company[0]):
            cursor.execute(
                "UPDATE businesses SET experience = experience + ? WHERE id = ?", (int(20 * employees_statuses[company[1]]['xp_multiplyer']), company[0], ))
            cursor.execute(
                "UPDATE businesses SET employee_productivity = employee_productivity + 1 WHERE user_id = ?", (user_id, ))
        conn.commit()
    else:
        if (shield_quantity[0] >= 1):
            message_text = f"\U00002639 <a href='tg://user?id={user_id}'>{escape(username)}</a> использовал(а) {items_dict[5]['name']} на <a href='tg://user?id={user_to_troll_id}'>{escape(trolled_username)}</a>, но у <a href='tg://user?id={user_to_troll_id}'>{escape(trolled_username)}</a> была {items_dict[7]['name']}, поэтому троллинг не прошел"
            cursor.execute('UPDATE user_inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_type = ?',
                           (user_to_troll_id, items_dict[7]["name"]))
            if (troll_business is not None and troll_business[0] == 1):
                cursor.execute(
                    "UPDATE businesses SET experience = experience - 20 WHERE user_id = ?", (user_id, ))
            if (company is not None and company[0]):
                cursor.execute(
                    "UPDATE businesses SET experience = experience - ? WHERE id = ?", (int(5 * employees_statuses[company[1]]['xp_multiplyer']), company[0], ))
            conn.commit()
        else:
            message_text = f"\U0001F9CC <a href='tg://user?id={user_id}'>{escape(username)}</a> использовал(а) {items_dict[5]['name']} на <a href='tg://user?id={user_to_troll_id}'>{escape(trolled_username)}</a>"
            cursor.execute(
                'UPDATE users SET troll_count = troll_count + 1 WHERE user_id = ?', (user_id,))
            cursor.execute(
                'UPDATE users SET trolled_count = trolled_count + 1 WHERE user_id = ?', (user_to_troll_id,))
            cursor.execute("DELETE FROM user_inventory WHERE user_id = ? AND item_type = ?",
                           (user_to_troll_id, items_dict[7]['name'],))
            if (troll_business is not None and troll_business[0] == 1):
                cursor.execute(
                    "UPDATE businesses SET experience = experience + 100 WHERE user_id = ?", (user_id, ))
            if (trolled_business is not None and trolled_business[0] == 1):
                cursor.execute(
                    "UPDATE businesses SET experience = experience - 20 WHERE user_id = ?", (user_to_troll_id, ))
            if (company is not None and company[0]):
                cursor.execute(
                    "UPDATE businesses SET experience = experience + ? WHERE id = ?", (int(20 * employees_statuses[company[1]]['xp_multiplyer']), company[0], ))
                cursor.execute(
                    "UPDATE businesses SET employee_productivity = employee_productivity + 1 WHERE user_id = ?", (user_id, ))
            conn.commit()

    cursor.execute('UPDATE user_inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_type = ?',
                   (user_id, items_dict[5]["name"]))
    cursor.execute(
        "UPDATE users SET tt_used = tt_used + 1 WHERE user_id = ?", (user_id, ))
    cursor.execute("UPDATE cooldowns SET tt_cooldown = ? WHERE user_id = ?", (int(
        time.time()), user_id, ))

    conn.commit()
    conn.close()

    bot.send_message(
        chat_id, message_text, parse_mode="HTML")


@bot.message_handler(regexp="^(?:\/?(removetroll|удалить|убрать|удалитьтролл|удалитьтрол|removetrol|remove)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def remove_troll(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute("SELECT quantity FROM user_inventory WHERE user_id = ? and item_type = ?",
                   (user_id, items_dict[6]["name"], ))
    quantity = cursor.fetchone()

    if (not quantity):
        bot.send_message(
            chat_id, f"\U0001F937 Нет предмета {items_dict[6]['name']} в инвентаре\n\nПосмотреть инвентарь - /inventory")
        conn.close()
        return

    if (quantity[0] <= 0):
        bot.send_message(
            chat_id, f"\U0001F937 Нет предмета {items_dict[6]['name']} в инвентаре\n\nПосмотреть инвентарь - /inventory")
        cursor.execute(
            "DELETE FROM user_inventory WHERE user_id = ? AND item_type = ?", (user_id, items_dict[6]["name"],))
        conn.commit()
        conn.close()
        return

    now = datetime.datetime.fromtimestamp(int(time.time()))

    cursor.execute(
        "SELECT rt_cooldown FROM cooldowns WHERE user_id = ?", (user_id, ))
    last_used = datetime.datetime.fromtimestamp(
        cursor.fetchone()[0])

    timediff = int((now - last_used).total_seconds())

    if (timediff > 86400):
        cursor.execute(
            "UPDATE users SET rt_used = 0 WHERE user_id = ?", (user_id, ))
        conn.commit()

    cursor.execute("SELECT rt_used FROM users WHERE user_id = ?", (user_id, ))
    remove_used = cursor.fetchone()[0]

    if (remove_used >= 5):
        bot.send_message(
            chat_id, f"\U0000270B Вы использовали слишком много предмета {items_dict[6]['name']}\n\n", parse_mode="HTML")
        conn.commit()
        conn.close()
        return

    cursor.execute(
        'SELECT trolled_count FROM users WHERE user_id = ?', (user_id, ))
    trolled_count = cursor.fetchone()[0]

    if (trolled_count <= 0):
        bot.send_message(
            chat_id, "\U0001F17E Вас пока еще никто не затроллил, нечего убирать!")
        conn.close()
        return

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    cursor.execute('UPDATE user_inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_type = ?',
                   (user_id, items_dict[6]["name"]))

    cursor.execute(
        'UPDATE users SET trolled_count = trolled_count - 1 WHERE user_id = ?', (user_id, ))

    cursor.execute(
        "SELECT created FROM businesses WHERE user_id = ?", (user_id, ))
    troll_business = cursor.fetchone()

    cursor.execute(
        "SELECT business_employee, employee_status FROM businesses WHERE user_id = ?", (user_id, ))
    company = cursor.fetchone()

    if (company is not None and company[0]):
        cursor.execute("UPDATE businesses SET experience = experience + ? WHERE id = ?",
                       (int(5 * employees_statuses[company[1]]['xp_multiplyer']), company[0], ))

    if (troll_business is not None and troll_business[0] == 1):
        cursor.execute(
            "UPDATE businesses SET experience = experience + 20 WHERE user_id = ?", (user_id, ))

    cursor.execute(
        "UPDATE users SET rt_used = rt_used + 1 WHERE user_id = ?", (user_id, ))

    cursor.execute("UPDATE cooldowns SET rt_cooldown = ? WHERE user_id = ?", (int(
        time.time()), user_id, ))

    bot.send_message(
        chat_id, f"\U00002796 <a href='tg://user?id={user_id}'>{escape(username)}</a> убрал у себя 1 тролл, теперь он затроллен {trolled_count - 1} раз", parse_mode="HTML")

    conn.commit()
    conn.close()


@bot.message_handler(regexp="^(?:\/?(audit|аудит|налоговая проверка)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def tax_audit(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute("SELECT quantity FROM user_inventory WHERE user_id = ? and item_type = ?",
                   (user_id, items_dict[8]["name"]))
    quantity = cursor.fetchone()

    if (not quantity):
        bot.send_message(
            chat_id, f"\U0001F937 Нет предмета {items_dict[8]['name']} в инвентаре\n\nПосмотреть инвентарь - /inventory")
        conn.close()
        return

    if (quantity[0] <= 0):
        bot.send_message(
            chat_id, f"\U0001F937 Нет предмета {items_dict[8]['name']} в инвентаре\n\nПосмотреть инвентарь - /inventory")
        cursor.execute(
            "DELETE FROM user_inventory WHERE user_id = ? AND item_type = ?", (user_id, items_dict[8]["name"],))
        conn.commit()
        conn.close()
        return

    now = datetime.datetime.fromtimestamp(int(time.time()))

    cursor.execute(
        "SELECT ta_cooldown FROM cooldowns WHERE user_id = ?", (user_id, ))
    last_used = datetime.datetime.fromtimestamp(
        cursor.fetchone()[0])

    timediff = int((now - last_used).total_seconds())

    if (timediff > 86400):
        cursor.execute(
            "UPDATE users SET ta_used = 0 WHERE user_id = ?", (user_id, ))
        conn.commit()

    cursor.execute("SELECT ta_used FROM users WHERE user_id = ?", (user_id, ))
    audit_used = cursor.fetchone()[0]

    if (audit_used >= 2):
        bot.send_message(
            chat_id, f"\U0000270B Вы использовали слишком много предмета {items_dict[8]['name']}\n\n", parse_mode="HTML")
        conn.commit()
        conn.close()
        return

    if (not message.reply_to_message):
        bot.send_message(
            chat_id, f"\U0001F645 Чтобы использовать {items_dict[8]['name']}, необходимо переслать сообщение пользователя.")
        conn.close()
        return

    user_to_audit = message.reply_to_message.from_user
    user_to_audit_id = message.reply_to_message.from_user.id

    cursor.execute(
        "SELECT created, level, experience FROM businesses WHERE user_id = ?", (user_to_audit_id, ))
    user_to_audit_business = cursor.fetchone()

    if (user_to_audit_business is not None):
        if (user_to_audit_business[0] == 0):
            bot.send_message(
                chat_id, "\U0001F937 У пользователя, которого вы хотите проверить, нет бизнеса")
            conn.close()
            return
    else:
        bot.send_message(
            chat_id, "\U0001F937 У пользователя, которого вы хотите проверить, нет бизнеса")
        conn.close()
        return

    if (user_to_audit_business[2] <= 100):
        bot.send_message(
            chat_id, "\U0001F937 У пользователя, которого вы хотите проверить, менее 100 опыта")
        conn.close()
        return

    cursor.execute("SELECT money FROM users WHERE user_id = ?",
                   (user_to_audit_id, ))
    user_money = cursor.fetchone()[0]

    bribe_money = int(
        2 * (100 * user_to_audit_business[1] ** 3) - (100 * user_to_audit_business[1] ** 3 * 0.5) + (user_money * 0.3))

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    if user_to_audit.first_name is not None:
        audit_username = user_to_audit.first_name
        if user_to_audit.last_name is not None:
            audit_username += " " + user_to_audit.last_name
    else:
        username = "безымянный"

    bribe_button = types.InlineKeyboardButton(
        "\U0001F381 Взятка", callback_data=f"{user_to_audit_id}:bribe:{bribe_money}")
    luck_button = types.InlineKeyboardButton(
        "\U0001F340 Удача", callback_data=f"{user_to_audit_id}:luck")

    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.row(bribe_button, luck_button)

    message_id = bot.send_message(
        chat_id, f"\U0001F4E2 Внимание, <a href ='tg://user?id={user_to_audit_id}'>{escape(audit_username)}</a>!\n\n\U0001F62E <a href='tg://user?id={user_id}'>{escape(username)}</a> настучал(а) на вас в налоговую...\n\n\U0001F914 У вас есть 2 варианта:\n1. Дать взятку — \U0001FA99 {bribe_money} ₺\n2. Понадеяться на удачу", parse_mode="HTML", reply_markup=markup).id

    cursor.execute("UPDATE user_inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_type = ?",
                   (user_id, items_dict[8]['name'], ))
    cursor.execute(
        "UPDATE users SET ta_used = ta_used + 1 WHERE user_id = ?", (user_id, ))

    cursor.execute("UPDATE cooldowns SET ta_cooldown = ? WHERE user_id = ?", (int(
        time.time()), user_id, ))

    conn.commit()
    conn.close()

    threading.Thread(target=wait_for_buttons, args=(
        chat_id, message_id, user_to_audit_id)).start()

    user_buttons[user_to_audit_id] = False


# endregion

# region Бизнесы


@bot.message_handler(regexp="^(?:\/?(бизнес создать|создать бизнес|createbusiness)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def create_business(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute(
        'SELECT created FROM businesses WHERE user_id = ?', (user_id, ))
    has_business = cursor.fetchone()

    if (has_business is not None and has_business[0] == 1):
        bot.send_message(
            chat_id, "\U0001F937 У вас уже есть бизнес.\n\n\U00002754 Посмотреть информацию можно, написав: \'<b>мой бизнес</b>\'", parse_mode="HTML")
        conn.close()
        return

    cursor.execute('SELECT money FROM users WHERE user_id = ?', (user_id, ))
    current_money = cursor.fetchone()[0]

    if (current_money < 75000):
        bot.send_message(
            chat_id, "\U0001F62C Недостаточно денег в кошельке...\n\nПроверить баланс - /tbalance")
        conn.close()
        return

    cursor.execute(
        'UPDATE users SET money = money - 75000 WHERE user_id = ?', (user_id, ))
    if (has_business is None):
        cursor.execute("INSERT INTO businesses (user_id, withdraw_time, created ) VALUES (?, ?, ?)",
                       (user_id, int(time.time()), 1))
    else:
        cursor.execute('UPDATE businesses SET created = ?, withdraw_time = ?, business_employee = "", employee_status = 0, employee_productivity = 0 WHERE user_id = ?', (1, int(
            time.time()), user_id, ))

    conn.commit()
    conn.close()
    bot.send_message(
        chat_id, "\U0001F44C Бизнес успешно создан!\n\n\U00002754 Посмотреть о нём информацию можно, написав: \'<b>мой бизнес</b>\'", parse_mode="HTML")


@bot.message_handler(regexp="^(?:\/?(мой бизнес|my business)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def my_business(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute('SELECT * FROM businesses WHERE user_id = ?', (user_id, ))
    business = cursor.fetchone()

    if (business is None):
        bot.send_message(chat_id, "\U0001F937 У вас пока что нет бизнеса.\n\n\U00002754 Но вы в любой момент можете его создать, написав: \'<b>бизнес создать</b>\' (стоимость - \U0001FA99 75к ₺)", parse_mode="HTML")
        conn.close()
        return
    elif (business[2] == 0):
        bot.send_message(chat_id, "\U0001F937 У вас пока что нет бизнеса.\n\n\U00002754 Но вы в любой момент можете его создать, написав: \'<b>бизнес создать</b>\' (стоимость - \U0001FA99 75к ₺)", parse_mode="HTML")
        conn.close()
        return

    current_xp = business[5]
    level_xp = (100 + 50 * business[4] ** 3)
    required_xp = level_xp - current_xp
    income_per_hour = int(
        (100 * business[4] ** 3) - (100 * business[4] ** 3 * 0.5))

    last_withdraw_time = business[8]
    ellapsed_time = time.time() - last_withdraw_time
    hours = int(ellapsed_time // 3600)

    current_income = income_per_hour * hours
    if (current_income != 0):
        cursor.execute("UPDATE businesses SET current_income = current_income + ?, withdraw_time = ? WHERE user_id = ?",
                       (current_income, int(time.time()), user_id))
        conn.commit()

    cursor.execute(
        "SELECT current_income FROM businesses WHERE user_id = ?", (user_id, ))
    current_income = cursor.fetchone()[0]

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    message_text = f"\U0001F3E2 Бизнес пользователя <a href='tg://user?id={user_id}'>{escape(username)}</a>\n\n\U0001F3F7 Название: \"{business[3]}\"\n\U0000303D Уровень: {business[4]}\n"

    if (required_xp <= 0):
        message_text += f"\U00002705 Доступен новый уровень \'/levelup\'\n\U0001F31F Опыт: {current_xp}\n\U0001F4B9 Доход в час: \U0001FA99 {format_money(income_per_hour)} ₺/час\n\n\U0001F3E6 Текущая прибыль: \U0001FA99 {format_money(current_income)} ₺"
    else:
        message_text += f"\U0001F4CA До следующего уровня: {required_xp}XP\n\U0001F31F Опыт: {current_xp}\n\U0001F4B9 Доход в час: \U0001FA99 {format_money(income_per_hour)} ₺/час\n\n\U0001F3E6 Текущая прибыль: \U0001FA99 {format_money(current_income)} ₺"

    if (business[4] == 0):
        message_text += "\n\n\U00002754 <b><i>У вас нулевой уровень, чтобы получать доход, необходимо иметь хотя бы первый.</i></b>"

    employees_button = types.InlineKeyboardButton(
        "\U0001F9D1\U0000200D\U0001F4BC Сотрудники", callback_data=f"{business[0]}:employees")
    join_button = types.InlineKeyboardButton(
        "\U0001F4D4 Вступить", callback_data=f"{business[0]}:join")

    markup = types.InlineKeyboardMarkup()

    markup.row(employees_button, join_button)

    conn.commit()
    conn.close()
    bot.send_message(chat_id, message_text,
                     reply_markup=markup, parse_mode="HTML")


@bot.message_handler(regexp="^(?:\/?(show business|бизинф|показать бизнес)(@crqrbot)?(\s\S+)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def show_business(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    business_id = re.search(r'(?<=\s)\S+', message.text)
    business_id = business_id.group() if business_id else ""

    if (business_id == ""):
        bot.send_message(
            chat_id, "\U0001F4B3 Чтобы посмотреть информацию о бизнесе, необходимо ввести его номер...")
        conn.close()
        return

    try:
        int_business_id = int(business_id)
    except ValueError:
        bot.send_message(
            chat_id, "\U0001F477 Чтобы посмотреть информацию о бизнесе, необходимо ввести его номер...")
        conn.close()
        return

    if (int_business_id < 0):
        bot.send_message(
            chat_id, "\U0001F477 Номера бизнесов — целые неотрицательные числа.")
        conn.close()
        return

    cursor.execute(
        "SELECT user_id, business_name, created, level, experience FROM businesses WHERE id = ?", (int_business_id, ))
    business = cursor.fetchone()

    if (business is None):
        bot.send_message(
            chat_id, f"\U0001F937 Не существует бизнеса с номером {int_business_id}")
        conn.close()
        return

    if (business[2] == 0):
        bot.send_message(
            chat_id, f"\U0001F937 Не существует бизнеса с номером {int_business_id}")
        conn.close()
        return

    businessman_id = business[0]
    business_name = business[1]
    level = business[3]
    current_xp = business[4]
    income_per_hour = int(
        (100 * level ** 3) - (100 * level ** 3 * 0.5))

    businessman = bot.get_chat_member(chat_id, businessman_id).user

    if businessman.first_name is not None:
        username = businessman.first_name
        if businessman.last_name is not None:
            username += " " + businessman.last_name
    else:
        username = "безымянный"

    cursor.execute(
        "SELECT user_id FROM businesses WHERE business_employee = ?", (business_id, ))
    employees = cursor.fetchall()

    employees_button = types.InlineKeyboardButton(
        "\U0001F9D1\U0000200D\U0001F4BC Сотрудники", callback_data=f"{int_business_id}:employees")
    join_button = types.InlineKeyboardButton(
        "\U0001F4D4 Вступить", callback_data=f"{int_business_id}:join")

    markup = types.InlineKeyboardMarkup()

    markup.row(employees_button, join_button)

    message_text = f"\U0001F3E2 Это бизнес пользователя <a href='tg://user?id={user_id}'>{escape(username)}</a>\n\n\U0001F3F7 Название: {business_name}\n\U0000303D Уровень: {level}\n\U0001F31F Опыт: {current_xp}\n\U0001F4B9 Доход в час: \U0001FA99 {format_money(income_per_hour)} ₺/час"

    conn.commit()
    conn.close()

    bot.send_message(chat_id, message_text,
                     reply_markup=markup, parse_mode="HTML")


@bot.message_handler(regexp="^(?:\/?(вывести деньги|получить доход|доход|income)(@crqrbot)?(\s\S+)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def get_income(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute('SELECT * FROM businesses WHERE user_id = ?', (user_id, ))
    business = cursor.fetchone()

    if (business is None):
        bot.send_message(chat_id, "\U0001F937 У вас пока что нет бизнеса.\n\n\U00002754 Но вы в любой момент можете его создать, написав: \'<b>бизнес создать</b>\' (стоимость - \U0001FA99 75к ₺)", parse_mode="HTML")
        conn.close()
        return
    elif (business[2] == 0):
        bot.send_message(chat_id, "\U0001F937 У вас пока что нет бизнеса.\n\n\U00002754 Но вы в любой момент можете его создать, написав: \'<b>бизнес создать</b>\' (стоимость - \U0001FA99 75к ₺)", parse_mode="HTML")
        conn.close()
        return

    money_to_withdraw = re.search(r'(?<=\s)\S+', message.text)
    money_to_withdraw = money_to_withdraw.group() if money_to_withdraw else ""

    int_money_to_withdraw = 1

    try:
        int_money_to_withdraw = int(money_to_withdraw)
    except ValueError:
        money_to_withdraw = ""

    if (int_money_to_withdraw < 0):
        bot.send_message(
            chat_id, "\U0001F4B0 Бизнес не может работать в убыль")
        conn.close()
        return

    if (int_money_to_withdraw == 0):
        bot.send_message(
            chat_id, "\U0001F928 Для чего тебе выводить \"ничего\"?")
        conn.close()
        return

    income_per_hour = int(
        (100 * business[4] ** 3) - (100 * business[4] ** 3 * 0.5))
    last_withdraw_time = business[8]
    ellapsed_time = time.time() - last_withdraw_time
    hours = int(ellapsed_time // 3600)

    cursor.execute(
        "SELECT current_income FROM businesses WHERE user_id = ?", (user_id, ))
    current_income = cursor.fetchone()[0] + income_per_hour * hours

    if (not money_to_withdraw):
        if (current_income == 0):
            bot.send_message(
                chat_id, "\U0001F61E Ваш бизнес пока что ничего не принес, попробуйте позже.")
            conn.close()
            return

        bot.send_message(
            chat_id, f"\U0001F4B0 Ваш бизнес принес вам \U0001FA99 {current_income} ₺")

        cursor.execute('UPDATE users SET money = money + ? WHERE user_id = ?',
                       (current_income, user_id, ))
        cursor.execute("UPDATE businesses SET withdraw_time = ?, current_income = 0 WHERE user_id = ?", (int(
            time.time()), user_id, ))

    else:
        if (int_money_to_withdraw > current_income):
            bot.send_message(
                chat_id, "\U0001F4B0 Ваш бизнес еще столько не принес")
            conn.commit()
            conn.close()
            return

        bot.send_message(
            chat_id, f"\U0001F4B0 Вы успешно вывели \U0001FA99 {format_money(int_money_to_withdraw)} ₺ со своего бизнеса")

        cursor.execute('UPDATE users SET money = money + ? WHERE user_id = ?',
                       (int_money_to_withdraw, user_id, ))
        cursor.execute("UPDATE businesses SET withdraw_time = ?, current_income = current_income - ? WHERE user_id = ?", (int(
            time.time()), int_money_to_withdraw, user_id, ))

    conn.commit()
    conn.close()


@bot.message_handler(regexp="^/?(бизнес переименовать|переименовать бизнес|renamebusiness)(?:@crqrbot)?\s*(.+)?$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def rename_business(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute('SELECT * FROM businesses WHERE user_id = ?', (user_id, ))
    business = cursor.fetchone()

    if (business is None):
        bot.send_message(chat_id, "\U0001F937 У вас пока что нет бизнеса.\n\n\U00002754 Но вы в любой момент можете его создать, написав: \'<b>бизнес создать</b>\' (стоимость - \U0001FA99 75к ₺)", parse_mode="HTML")
        conn.close()
        return
    elif (business[2] == 0):
        bot.send_message(chat_id, "\U0001F937 У вас пока что нет бизнеса.\n\n\U00002754 Но вы в любой момент можете его создать, написав: \'<b>бизнес создать</b>\' (стоимость - \U0001FA99 75к ₺)", parse_mode="HTML")
        conn.close()
        return

    match = re.match(
        r'^/?(бизнес переименовать|переименовать бизнес|renamebusiness)(?:@crqrbot)?\s*(.+)?$', message.text)
    if match:
        name = match.group(2)
    else:
        name = ""

    if (not name):
        bot.send_message(
            chat_id, "\U0000274C Укажите название, чтобы переименовать бизнес")
        conn.close()
        return

    if (len(name) > 15):
        bot.send_message(chat_id, "\U0001F4CF Название слишком длинное")
        conn.close()
        return

    cursor.execute(
        "UPDATE businesses SET business_name = ? WHERE user_id = ?", (name, user_id, ))
    conn.commit()
    conn.close()

    bot.send_message(
        chat_id, f"\U0001F3F7 Название бизнеса успешно изменено на \"{name}\"")


@bot.message_handler(regexp="^(?:\/?(levelup|левелап|повысить уровень|уровень\+)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def levelup_business(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute('SELECT * FROM businesses WHERE user_id = ?', (user_id, ))
    business = cursor.fetchone()

    if (business is None):
        bot.send_message(chat_id, "\U0001F937 У вас пока что нет бизнеса.\n\n\U00002754 Но вы в любой момент можете его создать, написав: \'<b>бизнес создать</b>\' (стоимость - \U0001FA99 75к ₺)", parse_mode="HTML")
        conn.close()
        return
    elif (business[2] == 0):
        bot.send_message(chat_id, "\U0001F937 У вас пока что нет бизнеса.\n\n\U00002754 Но вы в любой момент можете его создать, написав: \'<b>бизнес создать</b>\' (стоимость - \U0001FA99 75к ₺)", parse_mode="HTML")
        conn.close()
        return

    current_level = business[4]

    current_xp = business[5]
    level_xp = (100 + 50 * current_level ** 3)
    required_xp = level_xp - current_xp

    cursor.execute(
        "SELECT current_income FROM businesses WHERE user_id = ?", (user_id, ))
    current_income = cursor.fetchone()[0]

    if (required_xp <= 0):
        cursor.execute(
            "UPDATE businesses SET experience = experience - ?, level = level + 1 WHERE user_id = ?", (level_xp, user_id))
    else:
        bot.send_message(
            chat_id, "\U0001F937 Недостаточно опыта для повышения уровня")
        conn.close()
        return

    last_withdraw_time = business[8]
    ellapsed_time = time.time() - last_withdraw_time
    hours = int(ellapsed_time // 3600)

    income_per_hour = int(
        (100 * current_level ** 3) - (100 * current_level ** 3 * 0.5))

    current_income = income_per_hour * hours
    cursor.execute("UPDATE businesses SET current_income = current_income + ?, withdraw_time = ? WHERE user_id = ?",
                   (current_income, int(time.time()), user_id))
    conn.commit()

    conn.commit()
    conn.close()

    bot.send_message(
        chat_id, f"\U0001F4C8 Вы успешно увеличили свой уровень\n\n\U0000303D Текущий уровень — {current_level + 1}")


@bot.message_handler(regexp="^(?:\/?(\+бизнес|стать сотрудником|\+business|become employee)(@crqrbot)?(\s\S+)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def join_business(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute(
        'SELECT created FROM businesses WHERE user_id = ?', (user_id, ))
    has_business = cursor.fetchone()

    if (has_business is not None and has_business[0] == 1):
        bot.send_message(
            chat_id, "\U0001F937 У вас есть бизнес. Нельзя вести собственное дело и работать на кого-то одновременно.\n\n\U00002754 Посмотреть информацию можно, написав: \'<b>мой бизнес</b>\'", parse_mode="HTML")
        conn.close()
        return

    has_cooldown = is_on_cooldown(
        cursor, user_id, 86400, "get_job_cooldown", "cooldowns")

    if (has_cooldown[1]):
        bot.send_message(chat_id, "\U0001F616 Вы недавно уже устраивались на работу, либо вас уволили\n\n" +
                         has_cooldown[0], parse_mode="HTML")
        conn.close()
        return

    business_to_join = re.search(r'(?<=\s)\S+', message.text)
    business_to_join = business_to_join.group() if business_to_join else ""

    if (business_to_join == ""):
        bot.send_message(
            chat_id, "\U0001F4B3 Чтобы устроиться на работу, необходимо ввести номер бизнеса")
        conn.close()
        return

    try:
        int_business_to_join = int(business_to_join)
    except ValueError:
        bot.send_message(
            chat_id, "\U0001F477 Чтобы устроиться на работу, необходимо ввести целое число...")
        conn.close()
        return

    if (int_business_to_join < 0):
        bot.send_message(
            chat_id, "\U0001F477 Номера бизнесов — целые неотрицательные числа.")
        conn.close()
        return

    cursor.execute(
        "SELECT business_name, created FROM businesses WHERE id = ?", (int_business_to_join, ))
    business_name = cursor.fetchone()

    if (business_name is None):
        bot.send_message(
            chat_id, f"\U0001F937 Не существует бизнеса с номером {int_business_to_join}")
        conn.close()
        return

    if (business_name[1] == 0):
        bot.send_message(
            chat_id, f"\U0001F937 Не существует бизнеса с номером {int_business_to_join}")
        conn.close()
        return

    business_name = business_name[0]

    cursor.execute(
        'SELECT id, business_employee FROM businesses WHERE user_id = ?', (user_id, ))
    business_employee = cursor.fetchone()

    if (business_employee):
        if (business_employee[0] == int_business_to_join):
            bot.send_message(
                chat_id, f"\U0001F928 Вы и так работаете в компании \'{business_name}\'")
            conn.close()
            return
        cursor.execute("UPDATE businesses SET business_employee = ?, employee_status = 0, employee_productivity = 0 WHERE user_id = ?",
                       (int_business_to_join, user_id, ))
    else:
        cursor.execute("INSERT INTO businesses (user_id, business_employee, withdraw_time, created, employee_status, employee_productivity) VALUES (?, ?, ?, ?, ?, ?)",
                       (user_id, int_business_to_join, int(time.time()), 0, 0, 0, ))

    cursor.execute("UPDATE cooldowns SET get_job_cooldown = ? WHERE user_id = ?", (int(
        time.time()), user_id, ))
    conn.commit()
    conn.close()

    bot.send_message(
        chat_id, f"\U0001F477 Поздравляем! Вы устроились на работу в компанию \'{business_name}\'. Приступайте к работе.")


@bot.message_handler(regexp="^(?:\/?(повышение|тповысить|promote|promotion)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def promote_user(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute('SELECT * FROM businesses WHERE user_id = ?', (user_id, ))
    business = cursor.fetchone()

    if (business is None):
        bot.send_message(chat_id, "\U0001F937 У вас пока что нет бизнеса.\n\n\U00002754 Но вы в любой момент можете его создать, написав: \'<b>бизнес создать</b>\' (стоимость - \U0001FA99 75к ₺)", parse_mode="HTML")
        conn.close()
        return
    elif (business[2] == 0):
        bot.send_message(chat_id, "\U0001F937 У вас пока что нет бизнеса.\n\n\U00002754 Но вы в любой момент можете его создать, написав: \'<b>бизнес создать</b>\' (стоимость - \U0001FA99 75к ₺)", parse_mode="HTML")
        conn.close()
        return

    if (not message.reply_to_message):
        bot.send_message(
            chat_id, "\U0000274C Необходимо переслать сообщение пользователя, чтобы его повысить")
        conn.close()
        return

    user_to_promote = message.reply_to_message.from_user
    user_to_promote_id = message.reply_to_message.from_user.id

    if (is_restricted_user(user_to_promote_id)):
        bot.send_message(
            chat_id, "\U0001F645 Пользователь был исключен из базы.")
        conn.close()
        return

    if (user_id == user_to_promote_id):
        bot.send_message(
            chat_id, "\U0001F610 Нельзя повысить самого себя...")
        conn.commit()
        conn.close()
        return

    cursor.execute(
        'SELECT business_employee, employee_status FROM businesses WHERE user_id = ?', (user_to_promote_id, ))
    to_promote_company = cursor.fetchone()

    if (to_promote_company):
        if (to_promote_company[0] != business[0]):
            bot.send_message(
                chat_id, "\U0001F610 Пользователь у вас не работает")
            conn.close()
            return
    else:
        bot.send_message(chat_id, "\U0001F610 Пользователь у вас не работает")
        conn.close()
        return

    if (to_promote_company[1] >= max(employees_statuses)):
        bot.send_message(
            chat_id, "\U0001F418 Пользователь уже находится на максимальной должности")
        conn.close()
        return

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_to_promote_id, ))
    to_promote_is_banned = cursor.fetchone()[0]

    if (to_promote_is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Пользователь, которого вы хотите повысить, был забанен.")
        conn.close()
        return

    if user_to_promote.first_name is not None:
        employee_username = user_to_promote.first_name
        if user_to_promote.last_name is not None:
            employee_username += " " + user_to_promote.last_name
    else:
        employee_username = "безымянный"

    cursor.execute(
        "UPDATE businesses SET employee_status = employee_status + 1 WHERE user_id = ?", (user_to_promote_id, ))
    conn.commit()
    conn.close()

    bot.send_message(
        chat_id, f"\U000023EB Пользователь <a href='tg://user?id={user_to_promote_id}'>{employee_username}</a> повышен до должности {employees_statuses[to_promote_company[1] + 1]['emoji'] + employees_statuses[to_promote_company[1] + 1]['name'].capitalize()}", parse_mode="HTML")


@bot.message_handler(regexp="^(?:\/?(понижение|downgrade|тпонизить)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def downgrade_user(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute('SELECT * FROM businesses WHERE user_id = ?', (user_id, ))
    business = cursor.fetchone()

    if (business is None):
        bot.send_message(chat_id, "\U0001F937 У вас пока что нет бизнеса.\n\n\U00002754 Но вы в любой момент можете его создать, написав: \'<b>бизнес создать</b>\' (стоимость - \U0001FA99 75к ₺)", parse_mode="HTML")
        conn.close()
        return
    elif (business[2] == 0):
        bot.send_message(chat_id, "\U0001F937 У вас пока что нет бизнеса.\n\n\U00002754 Но вы в любой момент можете его создать, написав: \'<b>бизнес создать</b>\' (стоимость - \U0001FA99 75к ₺)", parse_mode="HTML")
        conn.close()
        return

    if (not message.reply_to_message):
        bot.send_message(
            chat_id, "\U0000274C Необходимо переслать сообщение пользователя, чтобы его понизить")
        conn.close()
        return

    user_to_downgrade = message.reply_to_message.from_user
    user_to_downgrade_id = message.reply_to_message.from_user.id

    if (is_restricted_user(user_to_downgrade_id)):
        bot.send_message(
            chat_id, "\U0001F645 Пользователь был исключен из базы.")
        conn.close()
        return

    if (user_id == user_to_downgrade_id):
        bot.send_message(
            chat_id, "\U0001F610 Нельзя понизить самого себя...")
        conn.commit()
        conn.close()
        return

    cursor.execute(
        'SELECT business_employee, employee_status FROM businesses WHERE user_id = ?', (user_to_downgrade_id, ))
    to_downgrade_company = cursor.fetchone()

    if (to_downgrade_company):
        if (to_downgrade_company[0] != business[0]):
            bot.send_message(
                chat_id, "\U0001F610 Пользователь у вас не работает")
            conn.close()
            return
    else:
        bot.send_message(chat_id, "\U0001F610 Пользователь у вас не работает")
        conn.close()
        return

    if (to_downgrade_company[1] <= min(employees_statuses)):
        bot.send_message(
            chat_id, "\U0001F401 Пользователь уже находится на минимальной должности")
        conn.close()
        return

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_to_downgrade_id, ))
    to_promote_is_banned = cursor.fetchone()[0]

    if (to_promote_is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Пользователь, которого вы хотите понизить, был забанен.")
        conn.close()
        return

    if user_to_downgrade.first_name is not None:
        employee_username = user_to_downgrade.first_name
        if user_to_downgrade.last_name is not None:
            employee_username += " " + user_to_downgrade.last_name
    else:
        employee_username = "безымянный"

    cursor.execute(
        "UPDATE businesses SET employee_status = employee_status - 1 WHERE user_id = ?", (user_to_downgrade_id, ))
    conn.commit()
    conn.close()

    bot.send_message(
        chat_id, f"\U000023EC Пользователь <a href='tg://user?id={user_to_downgrade_id}'>{employee_username}</a> понижен до должности {employees_statuses[to_downgrade_company[1] - 1]['emoji'] + employees_statuses[to_downgrade_company[1] - 1]['name'].capitalize()}", parse_mode="HTML")


@bot.message_handler(regexp="^(?:\/?(уволить|fire)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def fire_user(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute('SELECT * FROM businesses WHERE user_id = ?', (user_id, ))
    business = cursor.fetchone()

    if (business is None):
        bot.send_message(chat_id, "\U0001F937 У вас пока что нет бизнеса.\n\n\U00002754 Но вы в любой момент можете его создать, написав: \'<b>бизнес создать</b>\' (стоимость - \U0001FA99 75к ₺)", parse_mode="HTML")
        conn.close()
        return
    elif (business[2] == 0):
        bot.send_message(chat_id, "\U0001F937 У вас пока что нет бизнеса.\n\n\U00002754 Но вы в любой момент можете его создать, написав: \'<b>бизнес создать</b>\' (стоимость - \U0001FA99 75к ₺)", parse_mode="HTML")
        conn.close()
        return

    if (not message.reply_to_message):
        bot.send_message(
            chat_id, "\U0000274C Необходимо переслать сообщение пользователя, чтобы его уволить")
        conn.close()
        return

    user_to_fire = message.reply_to_message.from_user
    user_to_fire_id = message.reply_to_message.from_user.id

    if (is_restricted_user(user_to_fire_id)):
        bot.send_message(
            chat_id, "\U0001F645 Пользователь был исключен из базы.")
        conn.close()
        return

    if (user_id == user_to_fire_id):
        bot.send_message(
            chat_id, "\U0001F610 Нельзя уволить самого себя...")
        conn.commit()
        conn.close()
        return

    cursor.execute(
        'SELECT business_employee FROM businesses WHERE user_id = ?', (user_to_fire_id, ))
    to_fire_company = cursor.fetchone()

    if (to_fire_company):
        if (to_fire_company[0] != business[0]):
            bot.send_message(
                chat_id, "\U0001F610 Пользователь у вас не работает")
            conn.close()
            return
    else:
        bot.send_message(chat_id, "\U0001F610 Пользователь у вас не работает")
        conn.close()
        return

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_to_fire_id, ))
    to_promote_is_banned = cursor.fetchone()[0]

    if (to_promote_is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Пользователь, которого вы хотите повысить, был забанен.")
        conn.close()
        return

    if user_to_fire.first_name is not None:
        employee_username = user_to_fire.first_name
        if user_to_fire.last_name is not None:
            employee_username += " " + user_to_fire.last_name
    else:
        employee_username = "безымянный"

    cursor.execute(
        "UPDATE businesses SET business_employee = '', employee_status = 0, employee_productivity = 0 WHERE user_id = ?", (user_to_fire_id, ))
    cursor.execute("UPDATE cooldowns SET get_job_cooldown = ? WHERE user_id = ?", (int(
        time.time()), user_to_fire_id, ))
    conn.commit()
    conn.close()

    bot.send_message(
        chat_id, f"\U0001F4F4 Пользователь <a href='tg://user?id={user_to_fire_id}'>{employee_username}</a> был уволен", parse_mode="HTML")


@bot.message_handler(regexp="^(?:\/?(отчёт|отчет|бизстат|бизнес стат|business stat)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def business_stat(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute('SELECT * FROM businesses WHERE user_id = ?', (user_id, ))
    business = cursor.fetchone()

    if (business is None):
        bot.send_message(chat_id, "\U0001F937 У вас пока что нет бизнеса.\n\n\U00002754 Но вы в любой момент можете его создать, написав: \'<b>бизнес создать</b>\' (стоимость - \U0001FA99 75к ₺)", parse_mode="HTML")
        conn.close()
        return
    elif (business[2] == 0):
        bot.send_message(chat_id, "\U0001F937 У вас пока что нет бизнеса.\n\n\U00002754 Но вы в любой момент можете его создать, написав: \'<b>бизнес создать</b>\' (стоимость - \U0001FA99 75к ₺)", parse_mode="HTML")
        conn.close()
        return

    cursor.execute(
        "SELECT user_id, employee_productivity FROM businesses WHERE business_employee = ? ORDER BY employee_productivity DESC", (business[0], ))
    employees = cursor.fetchall()

    if (employees):
        employees_list = "\U0001F4CB Отчет по сотрудникам за сутки:\n\n"
        for employee in employees:
            try:
                cursor.execute(
                    "SELECT employee_status FROM businesses WHERE user_id = ?", (employee[0], ))
                status = cursor.fetchone()[0]
                employee_user = bot.get_chat_member(chat_id, employee[0]).user
                if employee_user.first_name is not None:
                    employee_username = employee_user.first_name
                    if employee_user.last_name is not None:
                        employee_username += " " + employee_user.last_name
                else:
                    employee_username = "безымянный"
                employees_list += f"{employees_statuses[status]['emoji']} <a href='tg://user?id={employee[0]}'>{employee_username}</a> — {employee[1]}\n"
            except Exception as e:
                employees_list += "неизвестный\n"
                print(e)
    else:
        employees_list = "\U0001F477 Сотрудников пока нет"

    bot.send_message(chat_id, employees_list, parse_mode="HTML")

# endregion

# region Троллито


@bot.message_handler(regexp="^(?:\/?(троллито|тролито|trollito|trolito)(@crqrbot)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def show_trollito(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    cursor.execute("SELECT * FROM trollito")
    items = cursor.fetchall()

    trollito = "\U0001F6CD Объявления на тролито:\n\n"

    if (items):
        for i, item in enumerate(items):
            seller_id = item[0]
            item_type = item[1]
            price = item[2]
            try:
                seller = bot.get_chat_member(chat_id, seller_id).user
                if seller.first_name is not None:
                    username = seller.first_name
                    if seller.last_name is not None:
                        username += " " + seller.last_name
                else:
                    username = "безымянный"
            except:
                username = "неизвестный"

            trollito += f"{i+1}. {item_type} — \U0001FA99 {format_money(price)} ₺\nПродавец: <a href='tg://user?id={seller_id}'>{username}</a>\n\n"

    else:
        trollito = "\U0001F937 На троллито нет ни одного объявления"

    bot.send_message(chat_id, trollito, parse_mode="HTML")


@bot.message_handler(regexp="^(?:\/?(выложить|продать|post|sell)(@crqrbot)?(\s\S+)?(\s\S+)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def sell_item(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    match = re.match(
        r'^\/?(выложить|продать|post|sell)(@crqrbot)?(\s+\S+){1,2}$', message.text)

    if match:
        items = match.group().split()[1:]
        item_to_sell = items[0]
        item_price = items[1] if len(items) == 2 else ""
    else:
        bot.send_message(
            chat_id, f"\U0001F6CD Чтобы продать предмет, нужно написать:\'продать <номер> <цена>\'")
        conn.close()
        return

    if (item_to_sell == ""):
        bot.send_message(
            chat_id, "\U0001F6CD Чтобы продать предмет, нужно написать: \'продать <номер> <цена>\'")
        conn.close()
        return

    if (item_price == ""):
        bot.send_message(
            chat_id, "\U0001F6CD Чтобы продать предмет, нужно написать: \'продать <номер> <цена>\'")
        conn.close()
        return

    try:
        int_item_to_sell = int(item_to_sell)
    except ValueError:
        bot.send_message(
            chat_id, "\U0000274C Номера предметов - целые числа...")
        conn.close()
        return

    if (int_item_to_sell < 0):
        bot.send_message(
            chat_id, "\U0001F928 Номер предмета не может быть отрицательным")
        conn.close()
        return

    if (int_item_to_sell == 0):
        bot.send_message(
            chat_id, "\U0001F928 Продавать воздух за деньги? Умно.")
        conn.close()
        return

    try:
        int_item_price = int(item_price)
    except ValueError:
        bot.send_message(
            chat_id, "\U0000274C Цена предмета - целое число...")
        conn.close()
        return

    if (int_item_price < 0):
        bot.send_message(
            chat_id, "\U0001F928 Цена предмета не может быть отрицательной")
        conn.close()
        return

    if (int_item_price == 0):
        bot.send_message(
            chat_id, "\U0001F928 Неужели ты хочешь отдать предмет бесплатно?")
        conn.close()
        return

    cursor.execute(
        "SELECT item_type, quantity FROM user_inventory WHERE user_id = ?  ORDER BY quantity DESC", (user_id,))
    inventory = cursor.fetchall()

    if (int_item_to_sell > len(inventory)):
        bot.send_message(
            chat_id, f"\U0000274C У вас нет предмета с номером {int_item_to_sell}")
        conn.close()
        return

    if (inventory[int_item_to_sell - 1][1] <= 0):
        cursor.execute("DELETE FROM user_inventory WHERE user_id = ? AND item_type = ?",
                       (user_id, inventory[int_item_to_sell - 1][0], ))
        conn.commit()
        conn.close()
        bot.send_message(
            chat_id, f"\U0000274C У вас нет предмета с номером {int_item_to_sell}")
        return

    cursor.execute("UPDATE user_inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_type = ?",
                   (user_id, inventory[int_item_to_sell - 1][0], ))

    cursor.execute("INSERT INTO trollito (user_id, item_type, price) VALUES (?, ?, ?)",
                   (user_id, inventory[int_item_to_sell - 1][0], int_item_price, ))

    conn.commit()
    conn.close()

    bot.send_message(
        chat_id, f"\U0001F6CD Вы успешно выложили {inventory[int_item_to_sell - 1][0]} на троллито за \U0001FA99 {format_money(int_item_price)} ₺")


@bot.message_handler(regexp="^(?:\/?(заказать|order)(@crqrbot)?(\s\S+)?)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def order_item(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user = message.from_user
    user_id = user.id

    if (is_restricted_user(user_id)):
        bot.send_message(
            chat_id, "\U0001F645 Вы были исключены из базы. Если хотите, чтобы вас вернули - свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_id, ))
    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, "\U0001F34C Вы были забанены в боте и не можете пользоваться его функциями. Свяжитесь с <a href='tg://user?id=633398015'>создателем</a>", parse_mode="HTML")
        conn.close()
        return

    item_to_order = re.search(r'(?<=\s)\S+', message.text)
    item_to_order = item_to_order.group() if item_to_order else ""

    try:
        int_item_to_order = int(item_to_order)
    except ValueError:
        bot.send_message(
            chat_id, "\U0000274C Чтобы купить предмет, необходимо указать его номер")
        conn.close()
        return

    if (int_item_to_order < 0):
        bot.send_message(
            chat_id, "\U0000274C Номера объявлений - положительные числа...")
        conn.close()
        return

    if (int_item_to_order == 0):
        bot.send_message(
            chat_id, "\U0001F928 Хочешь купить воздух?")
        conn.close()
        return

    cursor.execute("SELECT * FROM trollito")
    items = cursor.fetchall()

    if (int_item_to_order > len(items)):
        bot.send_message(
            chat_id, f"\U0000274C Нет объявления под номером {int_item_to_order}")
        conn.close()
        return

    cursor.execute("SELECT money FROM users WHERE user_id = ?", (user_id, ))
    current_money = cursor.fetchone()[0]

    item = items[int_item_to_order - 1]

    seller_id = item[0]
    item_type = item[1]
    item_price = item[2]

    if (current_money < item_price):
        bot.send_message(
            chat_id, "\U0001F62C Недостаточно денег в кошельке...\n\nПроверить баланс - /tbalance")
        conn.close()
        return

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    try:
        seller = bot.get_chat_member(chat_id, seller_id).user
        if seller.first_name is not None:
            seller_username = seller.first_name
            if seller.last_name is not None:
                seller_username += " " + seller.last_name
        else:
            seller_username = "безымянный"
    except Exception as e:
        seller_username = "неизвестный"

    cursor.execute("SELECT quantity FROM user_inventory WHERE user_id = ? and item_type = ?",
                   (user_id, item_type))
    quantity = cursor.fetchone()

    if (quantity):
        cursor.execute("UPDATE user_inventory SET quantity = quantity + 1 WHERE user_id = ? AND item_type = ?",
                       (user_id, item_type, ))
    else:
        cursor.execute("INSERT INTO user_inventory (user_id, item_type, quantity) VALUES (?, ?, ?)",
                       (user_id, item_type, 1, ))

    cursor.execute("DELETE FROM trollito WHERE ROWID = (SELECT ROWID FROM trollito WHERE user_id = ? AND item_type = ? AND price = ? LIMIT 1)",
                   (seller_id, item_type, item_price,))

    cursor.execute("UPDATE users SET money = money - ? WHERE user_id = ?",
                   (item_price, user_id, ))

    cursor.execute(
        "UPDATE users SET money = money + ? WHERE user_id = ?", (item_price, seller_id, ))

    conn.commit()
    conn.close()

    bot.send_message(
        chat_id, f"\U0001F6CD <a href='tg://user?id={user_id}'>{username}</a> купил {item_type} у <a href='tg://user?id={seller_id}'>{seller_username}</a> за \U0001FA99 {format_money(item_price)} ₺", parse_mode="HTML")


# endregion

# region Администрирование


@bot.message_handler(regexp="^(?:/?проверить|/?обновить|/?update|/?checkusers)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def check_users(message):

    start_time = time.time()
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user_id = message.from_user.id

    if (not is_authorized_user(user_id)):
        bot.send_message(chat_id, "\U0001F645 Недостаточно прав")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()

    removed_users = ''

    for user in users:
        user_id = user[0]
        try:
            temp_user = bot.get_chat_member(chat_id, user_id)
            if ((temp_user.status == 'left' or temp_user.status == 'banned') or (temp_user.user.first_name == '' and temp_user.user.last_name is None) or (user_id in restricted_users_ids)):
                removed_users += "@" + temp_user.user.username + \
                    '\n' if temp_user.user.username is not None else str(
                        temp_user.user.id) + "\n"
                conn.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
                conn.execute(
                    'DELETE FROM cooldowns WHERE user_id =?', (user_id,))
                conn.execute(
                    'DELETE FROM user_inventory WHERE user_id =?', (user_id,))
                conn.execute(
                    'DELETE FROM businesses WHERE user_id =?', (user_id,))
                conn.commit()
        except Exception as e:
            removed_users += str(user_id) + "\n"
            conn.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM cooldowns WHERE user_id =?', (user_id,))
            conn.execute(
                'DELETE FROM user_inventory WHERE user_id =?', (user_id,))
            conn.execute('DELETE FROM businesses WHERE user_id =?', (user_id,))
            conn.commit()
            print(f"Пользователь {user_id} не найден в чате {chat_id}: {e}")

    if removed_users == '':
        removed_users = 'Никто'
    end_time = time.time()
    ellapsed_time = end_time - start_time
    bot.send_message(
        chat_id, f"\U00002705 Список пользователей обновлен успешно.\n\nБыло затрачено {format(ellapsed_time, '.2g')} секунд\n\nУдалены следующие пользователи:\n{removed_users}")


@bot.message_handler(regexp="^(?:/?нашелбаг|/?награда)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def give_reward(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user_id = message.from_user.id

    if (not is_authorized_user(user_id)):
        bot.send_message(chat_id, "\U0001F645 Недостаточно прав")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    if (not message.reply_to_message):
        bot.send_message(
            chat_id, "\U0001F645 Чтобы выдать награду, необходимо переслать сообщение пользователя")
        conn.close()
        return

    user_to_give = message.reply_to_message.from_user
    user_to_give_id = message.reply_to_message.from_user.id

    if user_to_give.first_name is not None:
        username = user_to_give.first_name
        if user_to_give.last_name is not None:
            username += " " + user_to_give.last_name
    else:
        username = "безымянный"

    cursor.execute(
        "UPDATE users SET money = money + 5000 WHERE user_id = ?", (user_to_give_id, ))

    bot.send_message(
        chat_id, f"\U0001F4BB <a href='tg://user?id={user_to_give_id}'>{escape(username)}</a> получил \U0001FA99 5000 ₺ за то, что нашёл баг!", parse_mode="HTML")

    conn.commit()
    conn.close()


@bot.message_handler(regexp="^(?:/?выключение|/?выключить бота)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def turn_off(message):
    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user_id = message.from_user.id

    if (not is_authorized_user(user_id)):
        bot.send_message(chat_id, "\U0001F645 Недостаточно прав")
        return

    message_id = bot.send_message(
        chat_id, "ВЫПОЛНЯЕТСЯ ВЫКЛЮЧЕНИЕ\n\n|——————————|0%").message_id
    time.sleep(2)
    bot.edit_message_text(
        "ВЫПОЛНЯЕТСЯ ВЫКЛЮЧЕНИЕ\n\n|■■■————————|25%", chat_id, message_id)
    time.sleep(2)
    bot.edit_message_text(
        "ВЫПОЛНЯЕТСЯ ВЫКЛЮЧЕНИЕ\n\n|■■■■■■■—————|50%", chat_id, message_id)
    time.sleep(2)
    bot.edit_message_text(
        "ВЫПОЛНЯЕТСЯ ВЫКЛЮЧЕНИЕ\n\n|■■■■■■■■■■———|75%", chat_id, message_id)
    time.sleep(2)
    bot.edit_message_text(
        "ВЫПОЛНЯЕТСЯ ВЫКЛЮЧЕНИЕ\n\n|■■■■■■■■■■■■■■■|100%", chat_id, message_id)
    time.sleep(2)
    bot.edit_message_text(
        "<b>БОТ УСПЕШНО ВЫКЛЮЧЕН</b>", chat_id, message_id, parse_mode="HTML")


# endregion

# region Ограничения пользователей


@bot.message_handler(regexp="^(?:/?банчик|/?banuser|/?банан|/?бананчик|/?тбан)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def ban_user(message):

    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user_id = message.from_user.id

    if (not is_authorized_user(user_id)):
        bot.send_message(chat_id, "\U0001F645 Недостаточно прав")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    user_to_ban = message.reply_to_message.from_user
    user_to_ban_id = message.reply_to_message.from_user.id

    if user_to_ban.first_name is not None:
        username = user_to_ban.first_name
        if user_to_ban.last_name is not None:
            username += " " + user_to_ban.last_name
    else:
        username = "безымянный"

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_to_ban_id,))

    is_banned = cursor.fetchone()[0]

    if (is_banned):
        bot.send_message(
            chat_id, f"\U0000274C Пользователь <a href='tg://user?id={user_id}'>{escape(username)}</a> уже забанен.", parse_mode="HTML")
    else:
        cursor.execute(
            'UPDATE users SET is_banned = 1 WHERE user_id = ?', (user_to_ban_id,))
        conn.commit()
        bot.send_message(
            chat_id, f"\U00002705 Пользователь <a href='tg://user?id={user_id}'>{escape(username)}</a> забанен. Посиди подумай.", parse_mode="HTML")

    conn.close()


@bot.message_handler(regexp="^(?:/?разбанчик|/?unbanuser|/?разбанан|/?разбананчик|/?тразбан)$",
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def unban_user(message):

    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        bot.send_message(
            chat_id, "Это тестовая версия бота и пока что он работает только тут: \nhttps://t.me/igravkalmaraotfcknastya")
        bot.leave_chat(chat_id)
        return

    user_id = message.from_user.id

    if (not is_authorized_user(user_id)):
        bot.send_message(chat_id, "\U0001F645 Недостаточно прав")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    user_to_unban = message.reply_to_message.from_user
    user_to_unban_id = message.reply_to_message.from_user.id

    if user_to_unban.first_name is not None:
        username = user_to_unban.first_name
        if user_to_unban.last_name is not None:
            username += " " + user_to_unban.last_name
    else:
        username = "безымянный"

    cursor.execute(
        'SELECT is_banned FROM users WHERE user_id = ?', (user_to_unban_id,))

    is_banned = cursor.fetchone()[0]

    if (not is_banned):
        bot.send_message(
            chat_id, f"\U0000274C Пользователь <a href='tg://user?id={user_id}'>{escape(username)}</a> не забанен.", parse_mode="HTML")
    else:
        cursor.execute(
            'UPDATE users SET is_banned = 0 WHERE user_id = ?', (user_to_unban_id,))
        conn.commit()
        bot.send_message(
            chat_id, f"\U00002705 Пользователь <a href='tg://user?id={user_id}'>{escape(username)}</a> разбанен. Больше не нарушай!", parse_mode="HTML")

    conn.close()

# endregion

# region Обработчик кнопок


@bot.callback_query_handler(func=lambda call: call.data.split(':')[1] in ['bribe', 'luck'])
def audit_query(call):
    call_data = call.data.split(':')

    chat_id = call.message.chat.id
    user_id = int(call_data[0])
    try:
        user = bot.get_chat_member(chat_id, user_id).user
        if user.first_name is not None:
            username = user.first_name
            if user.last_name is not None:
                username += " " + user.last_name
        else:
            username = "безымянный"
    except Exception as e:
        username = "безымянный"
        print(e)

    command = call_data[1]

    if (user_id != call.from_user.id):
        bot.answer_callback_query(call.id, "\U0001F620 Не твоё - не трожь.")
        return

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    if (command == 'bribe'):
        user_buttons[user_id] = True
        cursor.execute(
            "SELECT money FROM users WHERE user_id = ?", (user_id, ))
        user_money = cursor.fetchone()[0]
        bribe_money = int(call_data[2])
        if (bribe_money > user_money):
            bot.answer_callback_query(
                call.id, "\U000026A0 Недостаточно денег в кошельке")
            conn.commit()
            conn.close()
            return
        else:
            cursor.execute(
                "UPDATE users SET money = money - ? WHERE user_id = ?", (bribe_money, user_id, ))
            bot.edit_message_text(
                f"\U0001F9E7 <a href ='tg://user?id={user_id}'>{escape(username)}</a> заплатил(а) взятку в размере \U0001FA99 {bribe_money} ₺ и может быть свободен", chat_id, call.message.id, parse_mode="HTML")
            conn.commit()
            conn.close()
    elif (command == 'luck'):
        user_buttons[user_id] = True
        weights = [0.70, 0.30]
        outcomes = ['success', 'failure']

        result = random.choices(outcomes, weights)[0]

        if (result == 'success'):
            lost_xp = random.randint(100, 2000)
            bot.edit_message_text(
                f"\U0001F61E Проверка обнаружила весомые нарушения.\n\n\U0000303D Ваш бизнес потерял {lost_xp} XP", chat_id, call.message.id)
            cursor.execute(
                "UPDATE businesses SET experience = experience - ? WHERE user_id = ?", (lost_xp, user_id, ))
            conn.commit()
            conn.close()
            return
        else:
            bot.edit_message_text(
                "\U0001F389 Проверка ничего не обнаружила. Все остается на своих местах.", chat_id, call.message.id)
            conn.commit()
            conn.close()
            return


@bot.callback_query_handler(func=lambda call: call.data.split(':')[1] in ['employees', 'join'])
def business_query(call):
    call_data = call.data.split(':')

    chat_id = call.message.chat.id
    business = int(call_data[0])
    command = call_data[1]
    user_id = call.from_user.id

    user = bot.get_chat_member(chat_id, user_id).user

    if user.first_name is not None:
        username = user.first_name
        if user.last_name is not None:
            username += " " + user.last_name
    else:
        username = "безымянный"

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT business_name FROM businesses WHERE id = ?", (business, ))
    business_name = cursor.fetchone()[0]
    if (command == "employees"):
        cursor.execute(
            "SELECT user_id FROM businesses WHERE business_employee = ? ORDER BY employee_status DESC", (business, ))
        employees = cursor.fetchall()
        if (employees):
            employees_list = f"\U0001F477 Сотрудники \"{business_name}\":\n\n"
            for employee in employees:
                try:
                    cursor.execute(
                        "SELECT employee_status FROM businesses WHERE user_id = ?", (employee[0], ))
                    status = cursor.fetchone()[0]
                    employee_user = bot.get_chat_member(
                        chat_id, employee[0]).user
                    if employee_user.first_name is not None:
                        employee_username = employee_user.first_name
                        if employee_user.last_name is not None:
                            employee_username += " " + employee_user.last_name
                    else:
                        employee_username = "безымянный"
                    employees_list += f"{employees_statuses[status]['emoji']} <a href='tg://user?id={employee[0]}'>{employee_username}</a> — {employees_statuses[status]['name']}\n"
                except Exception as e:
                    employees_list += "неизвестный\n"
                    print(e)
        else:
            employees_list = f"\U0001F477 Сотрудников в \"{business_name}\" пока нет\n"

        employees_list += f"\n\U00002754 Вызвал: <a href='tg://user?id={user_id}'>{username}</a>"

        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, employees_list, parse_mode="HTML")
    elif (command == "join"):
        cursor.execute(
            'SELECT created FROM businesses WHERE user_id = ?', (user_id, ))
        has_business = cursor.fetchone()

        if (has_business is not None and has_business[0] == 1):
            bot.send_message(
                chat_id, f"\U0001F937 <a href='tg://user?id={user_id}'>{username}</a>, у вас есть бизнес. Нельзя вести собственное дело и работать на кого-то одновременно.\n\n\U00002754 Посмотреть информацию можно, написав: \'<b>мой бизнес</b>\'", parse_mode="HTML")
            conn.close()
            return

        has_cooldown = is_on_cooldown(
            cursor, user_id, 86400, "get_job_cooldown", "cooldowns")

        if (has_cooldown[1]):
            bot.send_message(chat_id, f"\U0001F616 <a href='tg://user?id={user_id}'>{username}</a>, вы недавно уже устраивались на работу, либо вас уволили\n\n" +
                             has_cooldown[0], parse_mode="HTML")
            conn.close()
            return

        cursor.execute(
            'SELECT id, business_employee FROM businesses WHERE user_id = ?', (user_id, ))
        business_employee = cursor.fetchone()

        if (business_employee):
            if (business_employee[1] == business):
                bot.send_message(
                    chat_id, f"\U0001F928 <a href='tg://user?id={user_id}'>{username}</a>, вы и так работаете в компании \'{business_name}\'", parse_mode="HTML")
                conn.close()
                return
            cursor.execute("UPDATE businesses SET business_employee = ?, employee_status = 0, employee_productivity = 0 WHERE user_id = ?",
                           (business, user_id, ))
        else:
            cursor.execute("INSERT INTO businesses (user_id, business_employee, withdraw_time, created, employee_status, employee_productivity) VALUES (?, ?, ?, ?, ?, ?)",
                           (user_id, business, int(time.time()), 0, 0, 0, ))

        cursor.execute("UPDATE cooldowns SET get_job_cooldown = ? WHERE user_id = ?", (int(
            time.time()), user_id, ))
        conn.commit()
        conn.close()

        bot.answer_callback_query(call.id)
        bot.send_message(
            chat_id, f"\U0001F477 <a href='tg://user?id={user_id}'>{username}</a>, поздравляем, вы устроились на работу в компанию \'{business_name}\'. Приступайте к работе.", parse_mode="HTML")


# endregion

# region Сбор информации


@bot.message_handler(content_types=['text', 'photo', 'video', 'voice', 'audio', 'document', 'sticker', 'location', 'contact'],
                     func=lambda message: message.chat.type in ['supergroup', 'group'])
def collect_ids(message):

    chat_id = message.chat.id

    if (not is_target_chat(chat_id)):
        print(chat_id)
        return

    user_id = message.from_user.id

    if (user_id in restricted_users_ids):
        return

    # Подключение к базе данных
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    # Проверка, есть ли id пользователя в базе данных
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    # Если id пользователя нет в базе данных, добавляем его
    if not result:
        cursor.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,))
        cursor.execute(
            'INSERT INTO cooldowns (user_id) VALUES (?)', (user_id,))
        conn.commit()

    # Закрытие подключения к базе данных
    cursor.close()
    conn.close()


# endregion


bot.infinity_polling()
