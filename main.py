from threading import Thread

import telebot
from telebot import types

import tokens  # must contain TOKEN_NEWS and TOKEN_BOT
import constant
import db_funcs
import newsapi_funcs


bot = telebot.TeleBot(tokens.TOKEN_BOT)

INFO = 'Hello, i am SimpleNews bot, i can search, send news by category.\n\r\n\r' \
       'What i can:\n\r' \
       '  Search - search news by query, only write query\n\r' \
       '  Subscribe - subscribe for receive news by category, button\n\r' \
       '  Set country - country, for search news from there, button\n\r' \
       '  Information - get this info, button.\n\r'


buttons = {
    'subscribe': 'Subscribe',
    'country': 'Set country',
    'info': 'Information'
}


@bot.message_handler(commands=['start'])
def start(message):
    """Send message info, set main keybord, send country keyboard,
     register chat if isn't registered ."""
    db_funcs.register(message.chat.id)
    bot.send_message(message.chat.id, text=INFO, reply_markup=get_main_keyboard())
    if not db_funcs.get_country(message.chat.id):
        bot.send_message(message.chat.id,
                         text='For start, you must choose country: ',
                         reply_markup=get_country_keyboard()
                         )


@bot.callback_query_handler(lambda query: query.data.split(':')[0] == 'country')
def set_country(query):
    """Handle query with country info and set chat's country."""
    chat_id = query.message.chat.id
    country = query.data.split(':')[1]
    db_funcs.set_country(chat_id, country)
    bot.answer_callback_query(query.id, 'Country changed on: ' + country)


@bot.callback_query_handler(lambda query: query.data.split(':')[0] == 'subscribe')
def change_subscribe(query):
    """Handle query with subscribe info and (un)subscribe chat on given category."""
    category = query.data.split(':')[1]
    chat_id = query.message.chat.id
    action = db_funcs.change_subscribe(chat_id, category)
    bot.answer_callback_query(query.id, text=action + ' to ' + category)


@bot.message_handler(func=(lambda message: message.text == buttons['country']))
def main_menu(message):
    """Handle message send country keyboard that can set country."""
    bot.send_message(message.chat.id, text='Choose country: ', reply_markup=get_country_keyboard())


@bot.message_handler(func=(lambda message: message.text == buttons['subscribe']))
def subscribe(message):
    """Handle message for send subscribes keyboard that can add subscribe."""
    bot.send_message(message.chat.id, text='Choose category: ', reply_markup=get_subscribes_keyboard())


@bot.message_handler(func=(lambda message: message.text == buttons['info']))
def get_info(message):
    """Handle message for send main info message."""
    bot.send_message(message.chat.id, text=INFO)


@bot.message_handler(content_types=['text'])
def search(message):
    """Handle all other massages and get found news by query."""
    query = message.text
    chat_id = message.chat.id
    res = get_not_viewed_found(chat_id, query)

    if res is None:
        bot.send_message(chat_id, text='Nothing found!')
        return None

    db_funcs.add_view(chat_id, res)
    bot.send_message(chat_id, text=res)


def get_subscribes_keyboard():
    """Return keyboard with available subscribes."""
    markup = types.InlineKeyboardMarkup()
    markup.add(*[types.InlineKeyboardButton(text=i, callback_data='subscribe:' + i) for i in constant.CATEGORIES])
    return markup


def get_main_keyboard():
    """Return main keyboard."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*[types.KeyboardButton(text=buttons[i]) for i in buttons])
    return markup


def get_country_keyboard():
    """Return country keyboard with available countries."""
    markup = types.InlineKeyboardMarkup()
    markup.add(*[types.InlineKeyboardButton(text=i, callback_data='country:' + i) for i in constant.COUNTRIES])
    return markup


def send_news(category, country, new):
    """Send news for subscribers."""
    subscribers = db_funcs.get_subscribers(category, country)

    for i in subscribers:
        bot.send_message(i, text=new)
        db_funcs.add_view(i, new)


def get_not_viewed_found(chat_id, query):
    """Return not viewed latter by chat news urls."""
    found = newsapi_funcs.search_news(query, count=20)
    if not found:
        return None
    url = ''

    for i in found:
        if not db_funcs.is_viewed(chat_id, i):
            url = i
            break

    return None if not url else url


if __name__ == '__main__':
    # Will be rewritten with using multiprocessing for increase performance
    bot_run = Thread(target=bot.polling)
    sender_run = Thread(target=newsapi_funcs.notifier_news, args=(send_news, ))

    bot_run.start()
    sender_run.start()
