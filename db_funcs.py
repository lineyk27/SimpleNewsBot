import mysql.connector as connector
import tokens


main_connection =  connector.connect(user=tokens.DB_CONFIG['user'],
                                     password=tokens.DB_CONFIG['password'],
                                     host=tokens.DB_CONFIG['host'],
                                     database=tokens.DB_CONFIG['database']
                                    )


def connect():
    main_connection =  connector.connect(user=tokens.DB_CONFIG['user'],
                                     password=tokens.DB_CONFIG['password'],
                                     host=tokens.DB_CONFIG['host'],
                                     database=tokens.DB_CONFIG['database']
                                    )


def get_cursor(cursor=None):
    """Returning cursor for connection to database."""
    if cursor is None:
        try:
            return main_connection.cursor()
        except:
            connect()
            return main_connection.cursor()
    return cursor


def is_registered(chat_id, cursor=None):
    """Return True if row with chat_id is in database, else False."""
    cursor = get_cursor(cursor)

    cursor.execute("""
        SELECT id
        FROM chats
        WHERE id=%d;
        """ % (chat_id,))

    return bool(cursor.fetchone())


# TODO: change funcs names, must be more simple convention

def register(chat_id, cursor=None):
    """Register chat in database."""
    cursor = get_cursor(cursor)
    if is_registered(chat_id):
        return None
    cursor.execute("""
        INSERT INTO chats(id)
        VALUES(%d);
        """ % (chat_id,))
    main_connection.commit()


def is_viewed(chat_id, url, cursor=None):
    """Return True if news was viewed by chat, else False."""
    cursor = get_cursor(cursor)

    cursor.execute("""
        SELECT views.chatid
        FROM views
        INNER JOIN news ON views.newsid=news.id
        WHERE views.chatid=%d AND news.url='%s';
        """ % (chat_id, url))

    return bool(cursor.fetchone())


def is_subscribed(chat_id, category, cursor=None):
    """Return True if chat is subscribed on category."""
    cursor = get_cursor(cursor)

    cursor.execute("""
        SELECT categories.name
        FROM categories
        INNER JOIN subscribes ON categories.id=subscribes.categoryid
        WHERE subscribes.chatid=%d AND categories.name='%s';
        """ % (chat_id, category))

    return bool(cursor.fetchone())


def get_language(chat_id, cursor=None):
    """Return language that chat choose.
    Now is not in using.
    """
    cursor = get_cursor(cursor)

    cursor.execute("""
        SELECT languages.name
        FROM chats
        INNER JOIN languages ON languages.languageid=chats.languageid
        WHERE chats.id=%d;
        """ % (chat_id,))

    return cursor.fetchone()


def set_language(chat_id, language, cursor=None):
    """Set language for chat.
    Now is not in using.
    """
    cursor = get_cursor(cursor)

    cursor.execute("""
        UPDATE chats
        SET languageid=(SELECT languageid FROM languages WHERE name='%s')
        WHERE id=%d;
        """ % (language, chat_id))

    main_connection.commit()


def get_country(chat_id, cursor=None):
    """Return name of country, chat have chosen."""
    cursor = get_cursor(cursor)

    cursor.execute("""
        SELECT countries.name
        FROM countries
        INNER JOIN chats ON chats.countryid=countries.id
        WHERE chats.id='%d';
        """ % (chat_id,))
    try:
        return cursor.fetchone()[0]
    except TypeError:
        return None


def set_country(chat_id, country, cursor=None):
    """Set country for chat."""
    cursor = get_cursor(cursor)

    cursor.execute("""
        UPDATE chats
        SET countryid=(SELECT id FROM countries WHERE name='%s')
        WHERE id=%d;
        """ % (country, chat_id)
                   )
    main_connection.commit()


def add_view(chat_id, url, cursor=None):
    """Add row that chat have received a news and read it."""
    cursor = get_cursor(cursor)

    if not is_news(url):
        add_news(url)

    cursor.execute("""
        INSERT INTO views
        VALUES(%d, (SELECT news.id FROM news WHERE news.url='%s'));
        """ % (chat_id, url))

    main_connection.commit()


def add_news(url, cursor=None):
    """Add row news in database."""
    cursor = get_cursor(cursor)

    cursor.execute("""
        INSERT INTO news(url)
        VALUES('%s');
        """ % (url,))

    main_connection.commit()


def is_news(url, cursor=None):
    """Return True if news is in database else False."""
    cursor = get_cursor(cursor)

    cursor.execute("""
        SELECT url
        FROM news
        WHERE url='%s';
        """ % (url,))

    return bool(cursor.fetchone())


def get_subscribers(category, country, cursor=None):
    """Return list of subscribers on certain category from certain country."""
    cursor = get_cursor(cursor)

    cursor.execute("""
        SELECT chats.id
        FROM (SELECT subscribes.chatid FROM subscribes
              INNER JOIN categories ON subscribes.categoryid=categories.id
              WHERE categories.name='%s') AS temp
        INNER JOIN chats ON chats.id=temp.chatid
        WHERE chats.countryid=(SELECT id FROM countries WHERE name='%s');
        """ % (category, country))
    return cursor.fetchall()


def subscribe(chat_id, category, cursor=None):
    """Subscribe chat on the given category."""
    cursor = get_cursor(cursor)

    cursor.execute("""
        INSERT INTO subscribes
        VALUES(%d, (SELECT id FROM categories WHERE name='%s'));
        """ % (chat_id, category))

    main_connection.commit()


def unsubscribe(chat_id, category, cursor=None):
    """Unsubscribe chat from given category."""
    cursor = get_cursor(cursor)

    cursor.execute("""
        DELETE FROM subscribes
        WHERE chatid=%d AND categoryid=(SELECT id FROM categories WHERE name='%s');
        """ % (chat_id, category))

    main_connection.commit()


def change_subscribe(chat_id, category, cursor=None):
    """Unsubscribe chat from given category if already subscribed,
    else subscribe.
    """
    cursor = get_cursor(cursor)

    if is_subscribed(chat_id, category, cursor=cursor):
        unsubscribe(chat_id, category, cursor)
        return "Unsubscribed"
    else:
        subscribe(chat_id, category, cursor=cursor)
        return "Subscribed"


def get_last_news(category, country, cursor=None):
    """Return last news was sent to chats who subscribed on given category
    and choose given country.
    """
    cursor = get_cursor(cursor)

    cursor.execute("""
        SELECT news.url
        FROM news
        INNER JOIN last_news ON last_news.newsid=news.id
        WHERE last_news.countryid=(SELECT id FROM countries WHERE name='%s')
        AND last_news.categoryid=(SELECT id FROM categories WHERE name='%s');
        """ % (country, category))

    return cursor.fetchall()


def change_last_news(category, country, url, cursor=None):
    """Change last news on given by given category and country."""
    cursor = get_cursor(cursor)

    if not is_news(url):
        add_news(url)

    cursor.execute("""
        UPDATE last_news
        SET newsid=(SELECT id FROM news WHERE url='%s')
        WHERE countryid=(SELECT id FROM countries WHERE name='%s')
        AND categoryid=(SELECT id FROM categories WHERE name='%s');
        """ % (url, country, category))

    main_connection.commit()
