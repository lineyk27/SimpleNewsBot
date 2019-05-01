import constant
import psycopg2


def get_db_config(config):
    try:
        return 'host={0} port={1} user={2} dbname={3}'.format(config['host'],
                                                              config['port'],
                                                              config['user'],
                                                              config['db']
                                                              )
    except KeyError:
        raise Exception('Haven\'t found needed keys for database config config.')
        # TODO: need rewrite ex. message


def is_registered(chat_id, cursor=None):
    cursor = get_cursor(cursor)

    cursor.execute("""
        SELECT chatid
        FROM chats
        WHERE chatid=%s;
        """,
                   (chat_id,))

    return bool(cursor.fetchone())


# TODO: change funcs names, must be more simple convention

def register(chat_id, cursor=None):
    cursor = get_cursor(cursor)
    if is_registered(chat_id): return
    cursor.execute("""
    INSERT INTO chats(chatid)
    VALUES(%s);
    """,
                   (chat_id,))
    cursor.connection.commit()


def is_viewed(chat_id, url, cursor=None):
    cursor = get_cursor(cursor)

    cursor.execute("""
        SELECT views.chatid
        FROM views
        INNER JOIN news ON views.newsid=news.newsid
        WHERE views.chatid=%s AND news.url=%s ;
        """,
                   (chat_id, url))

    # TODO: need be retabulated

    return bool(cursor.fetchone())


def is_subscribed(chat_id, category, cursor=None):
    cursor = get_cursor(cursor)

    cursor.execute("""
        SELECT categories.name
        FROM categories
        INNER JOIN subscribes ON categories.categoryid=subscribes.categoryid
        WHERE subscribes.chatid=%s AND categories.name=%s;
        """,
                   (chat_id, category)
                   )

    return bool(cursor.fetchone())


def get_language(chat_id, cursor=None):
    cursor = get_cursor(cursor)

    cursor.execute("""
    SELECT languages.name
    FROM chats
    INNER JOIN languages ON languages.languageid=chats.languageid
    WHERE chats.chatid=%s;
    """,
                   (chat_id,)
                   )

    return cursor.fetchone()[0]


def set_language(chat_id, language, cursor=None):
    cursor = get_cursor(cursor)

    cursor.execute("""
        UPDATE chats
        SET languageid=(SELECT languageid FROM languages WHERE name=%s)
        WHERE chatid=%s;
        """,
                   (language, chat_id)
                   )
    cursor.connection.commit()


def get_country(chat_id, cursor=None):
    cursor = get_cursor(cursor)

    cursor.execute("""
    SELECT countries.name
    FROM countries
    INNER JOIN chats ON chats.countryid=countries.countryid
    WHERE chats.chatid=%s;
    """,
                   (chat_id,))
    try:
        return cursor.fetchone()[0]
    except TypeError:
        return None


def set_country(chat_id, country, cursor=None):
    cursor = get_cursor(cursor)

    cursor.execute("""
        UPDATE chats
        SET countryid=(SELECT countryid FROM countries WHERE name=%s)
        WHERE chatid=%s;
        """,
                   (country, chat_id)
                   )
    cursor.connection.commit()


def get_cursor(cursor=None):
    if cursor is None:
        return psycopg2.connect(get_db_config(constant.DB_CONFIG)).cursor()
    return cursor


def add_view(chat_id, url, cursor=None):
    cursor = get_cursor(cursor)

    if not is_news(url):
        add_news(url)

    cursor.execute("""
    INSERT INTO views
    VALUES(%s, (SELECT news.newsid FROM news WHERE news.url=%s));
    """,
                   (chat_id, url))

    cursor.connection.commit()


def add_news(url, cursor=None):
    cursor = get_cursor(cursor)

    cursor.execute("""
    INSERT INTO news(url)
    VALUES(%s);
    """,
                   (url,))

    cursor.connection.commit()


def is_news(url, cursor=None):
    cursor = get_cursor(cursor)

    cursor.execute("""
    SELECT url
    FROM news
    WHERE url=%s;
    """,
                   (url,))

    return bool(cursor.fetchone())


def get_subscribers(category, country, cursor=None):
    cursor = get_cursor(cursor)

    cursor.execute("""
    SELECT chats.chatid
    FROM (SELECT subscribes.chatid FROM subscribes
          INNER JOIN categories ON subscribes.categoryid=categories.categoryid
          WHERE categories.name=%s) AS temp
    INNER JOIN chats ON chats.chatid=temp.chatid
    WHERE chats.countryid=(SELECT countryid FROM countries WHERE name=%s);
    """,
                   (category, country))
    return [i[0] for i in cursor.fetchall()]


def subscribe(chat_id, category, cursor=None):
    cursor = get_cursor(cursor)

    cursor.execute("""
    INSERT INTO subscribes
    VALUES(%s, (SELECT categoryid FROM categories WHERE name=%s));
    """,
                   (chat_id, category))

    cursor.connection.commit()


def unsubscribe(chat_id, category, cursor=None):
    cursor = get_cursor(cursor)

    cursor.execute("""
    DELETE FROM subscribes
    WHERE chatid=%s AND categoryid=(SELECT categoryid FROM categories WHERE name=%s);
    """,
                   (chat_id, category))

    cursor.connection.commit()


def change_subscribe(chat_id, category, cursor=None):
    cursor = get_cursor(cursor)

    if is_subscribed(chat_id, category, cursor=cursor):
        unsubscribe(chat_id, category, cursor)
        return "Unsubscribed"
    else:
        subscribe(chat_id, category, cursor=cursor)
        return "Subscribed"


def get_last_news(category, country, cursor=None):
    cursor = get_cursor(cursor)

    cursor.execute("""
    SELECT news.url
    FROM news
    INNER JOIN last_news ON last_news.newsid=news.newsid
    WHERE last_news.countryid=(SELECT countryid FROM countries WHERE name=%s)
    AND last_news.categoryid=(SELECT categoryid FROM categories WHERE name=%s);
    """,
                   (country, category))

    return cursor.fetchone()[0]


def change_last_news(category, country, url, cursor=None):
    cursor = get_cursor(cursor)

    if not is_news(url):
        add_news(url)

    cursor.execute("""
    UPDATE last_news
    SET newsid=(SELECT newsid FROM news WHERE url=%s)
    WHERE categoryid=(SELECT countryid FROM countries WHERE name=%s)
    AND categoryid=(SELECT categoryid FROM categories WHERE name=%s);
    """,
                   (url, country, category))

    cursor.connection.commit()

