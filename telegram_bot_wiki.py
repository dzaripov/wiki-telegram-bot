import telegram
import time
import logging
from secret_information import my_token, chat_ids, host, user, password, database, sitename, time_sleep
from mysql.connector import connect, Error


CONFIG = {'host': host,
          'user': user,
          'password': password,
          'database': database}

logging.basicConfig(filename='/var/log/wiki.log', 
                    level=logging.INFO,
                    format='%(message)s')


def bold(text):
    """
    Transfroms text to bold
    """
    return '<b>' + text + '</b>'


def create_link(link, title):
    """
    Telegram hyperlink creation
    """
    return f'<a href="{link}">{title}</a>'


def send(msg, chat_id, token=my_token):
    """
    Sends a message to a telegram user or group specified on chatId
    chat_id must be a number!
    """
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=msg, parse_mode='HTML')


def create_message_wiki(rc_title, summary_comment, author_wiki, rc_cur_id):
    """
    Creates a message to be sent to a telegram group or a user
    """
    title = rc_title.replace('_', ' ')
    link = f'https://{sitename}/wiki/?curid={rc_cur_id}'
    telegram_link = create_link(link, title)
    return f"Товарищи, новое изменение на вики!\n\
{telegram_link}: {bold(summary_comment)} от {bold(author_wiki)}."


def get_activity_wiki(length_act=5):
    """
    Get recent changes from wiki that dont minor (or page creation) and not posted earlier.
    Get title, timestamp, id of change, id of page that contain change,
    summary of change, name of author.
    Return list of tuples.
    """
    query_get_activity = f"""
    SELECT
        rc_title, 
        rc_timestamp, 
        rc_id,
        rc_cur_id,
        comment_text,
        actor_name
     FROM recentchanges
     LEFT JOIN comment ON rc_comment_id = comment_id
     LEFT JOIN actor ON rc_actor = actor_id
     WHERE rc_log_type is NULL and
           rc_id NOT IN (SELECT posted_act_id 
                     FROM recentchangesposted) and
           rc_new = 0 and
           rc_minor = 0"""

    with connect(**CONFIG) as cnx:
        with cnx.cursor(buffered=True) as cursor:
            cursor.execute(query_get_activity)
            act = cursor.fetchall()

            if len(act) >= length_act:
                activity_range = range(len(act) - length_act, len(act))
            else:
                activity_range = range(len(act))

    return act, activity_range


def post_if_new_activity_wiki():
    """
    Parses SQL query and sends a message if new activity is found.
    Adds information about posted change in database.
    """
    act, activity_range = get_activity_wiki()
    for i in activity_range:
        rc_title        = act[i][0].decode('utf-8')
        rc_timestamp    = act[i][1].decode('utf-8')
        rc_id           = act[i][2]
        rc_cur_id       = act[i][3]
        summary_comment = act[i][4].decode('utf-8')
        author_wiki     = act[i][5].decode('utf-8')

        logging.info(f'{rc_title}, {rc_timestamp}, {rc_id}, \
                       {rc_cur_id}, {summary_comment}, {author_wiki}')
        msg = create_message_wiki(rc_title, summary_comment, author_wiki, rc_cur_id)
        for chat_id in chat_ids:
            send(msg, chat_id)
        with connect(**CONFIG) as cnx:
            with cnx.cursor(buffered=True) as cursor:
                sql = "INSERT INTO recentchangesposted\
                (posted_act_id, post_id) VALUES (%s, %s)"
                val = (rc_id, rc_cur_id)
                cursor.execute(sql, val)
                cnx.commit()


def is_db_created():
    with connect(**CONFIG) as cnx:
        with cnx.cursor(buffered=True) as cursor:
            cursor.execute('SHOW TABLES')
            tables = cursor.fetchall()
            logging.info(f'{tables}')

        for i in range(len(tables)):
            if tables[i][0] == 'recentchangesposted':
                return True

        return False


def create_posted_activity_db():
    if is_db_created():
        logging.info('DB is already created!')
    else:
        with connect(**CONFIG) as cnx:
            with cnx.cursor(buffered=True) as cursor:
                sql_create_table = 'CREATE TABLE recentchangesposted\
                                    (posted_act_id int, post_id int)'
                cursor.execute(sql_create_table)
        logging.info('DB is created!')


def main():
    try:
        while True:
            post_if_new_activity_wiki()
            time.sleep(time_sleep)
    except Error as e:
        logging.info(e)


if __name__ == '__main__':
    # Wait for database initialization
    time.sleep(60)
    # Create recentchangesposted table if not exists 
    create_posted_activity_db()

    main()