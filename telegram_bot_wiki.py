import telegram
import time
import datetime
import logging
from secret_information import my_token, chat_ids, host, user, password, database, sitename
from mysql.connector import connect, Error


CONFIG = {'host': host,
          'user': user,
          'password': password,
          'database': database}

logging.basicConfig(filename='/var/log/wiki.log', level=logging.INFO,
                    format='%(message)s')

time_sleep = 30  # seconds


def bold(text):
    return '<b>' + text + '</b>'


def create_link(link, title):
    return f'<a href="{link}">{title}</a>'


def send(msg, chat_id, token=my_token):
    """
    Send a message to a telegram user or group specified on chatId
    chat_id must be a number!
    """
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=msg, parse_mode='HTML')


def get_request_wiki(rc_comment_id, rc_actor):
    query_get_summary_comment = f"SELECT comment_text FROM comment \
                                  WHERE comment_id={rc_comment_id}"
    query_get_user_name = f"SELECT actor_name FROM actor \
                            WHERE actor_id={rc_actor}"

    with connect(**CONFIG) as cnx:
        with cnx.cursor(buffered=True) as cursor:
            cursor.execute(query_get_summary_comment)
            summary_comment = cursor.fetchall()[0][0].decode('utf-8')
            cursor.execute(query_get_user_name)
            author_wiki = cursor.fetchall()[0][0].decode('utf-8')
    return summary_comment, author_wiki


def create_message_wiki(rc_title, summary_comment, author_wiki, rc_cur_id):
    return f"Товарищи, новое изменение на вики!\n \
{create_link(f'https://{sitename}/wiki/?curid={rc_cur_id}', rc_title.replace('_', ' '))}: \
{bold(summary_comment)} от {bold(author_wiki)}."


def is_publishable(rc_minor, rc_new):
    if rc_minor == 0 and rc_new == 0:
        return True
    return False


def is_new_wiki(date):
    date_real = datetime.datetime.strptime(str(date), '%Y%m%d%H%M%S')
    # 3 hours of UTC difference
    time_delta = (datetime.datetime.now() - date_real).total_seconds() - 10800
    logging.info(time_delta, datetime.datetime.now(), date_real)

    if (time_delta < time_sleep):
        logging.info('True')
        return True
    logging.info('False, > time_sleep')
    return False


def get_activity_wiki(length_act=5):
    query_get_activity = "SELECT rc_title, rc_minor, rc_new, rc_comment_id, \
                          rc_timestamp, rc_actor, rc_id, rc_cur_id \
                          FROM recentchanges WHERE rc_log_type is NULL"

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
    act, activity_range = get_activity_wiki()
    for i in activity_range:
        rc_title      = act[i][0].decode('utf-8')
        rc_minor      = act[i][1]
        rc_new        = act[i][2]
        rc_comment_id = act[i][3]
        rc_timestamp  = act[i][4].decode('utf-8')
        rc_actor      = act[i][5]
        rc_id         = act[i][6]
        rc_cur_id     = act[i][7]

        logging.info(rc_title, rc_minor, rc_new, rc_comment_id, rc_timestamp, rc_actor, rc_id, rc_cur_id)
        if is_publishable(rc_minor, rc_new) and is_new_wiki(rc_timestamp):
            summary_comment, author_wiki = get_request_wiki(rc_comment_id, rc_actor)
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


def manual_post(rc_id_manual):
    act, activity_range = get_activity_wiki()
    for i in activity_range:
        rc_title      = act[i][0].decode('utf-8')
        rc_minor      = act[i][1]
        rc_new        = act[i][2]
        rc_comment_id = act[i][3]
        rc_timestamp  = act[i][4].decode('utf-8')
        rc_actor      = act[i][5]
        rc_id         = act[i][6]
        rc_cur_id     = act[i][7]

        if (rc_id == rc_id_manual):
            summary_comment, author_wiki = get_request_wiki(rc_comment_id, rc_actor)
            msg = create_message_wiki(rc_title, summary_comment, author_wiki)
            for chat_id in chat_ids:
                send(msg, chat_id)
            print(f'Posted! {msg}')


def get_activities(length_act=100):
    act, activity_range = get_activity_wiki(length_act)
    for i in activity_range:
        rc_title      = act[i][0].decode('utf-8')
        rc_minor      = act[i][1]
        rc_new        = act[i][2]
        rc_comment_id = act[i][3]
        rc_timestamp  = act[i][4].decode('utf-8')
        rc_actor      = act[i][5]
        rc_id         = act[i][6]
        rc_cur_id     = act[i][7]

        print(rc_title, rc_minor, rc_new, rc_comment_id, rc_timestamp, rc_actor, rc_id, rc_cur_id)


def is_db_created():
    with connect(**CONFIG) as cnx:
        with cnx.cursor(buffered=True) as cursor:
            cursor.execute('SHOW TABLES')
            tables = cursor.fetchall()
            logging.info(tables)

        for i in range(len(tables)):
            if tables[i][0] == 'recentchangesposted':
                return True

        return False


def create_posted_activity_db():
    sql_create_table = 'CREATE TABLE recentchangesposted (posted_act_id int, post_id int)'
    if is_db_created():
        logging.info('DB is already created!')
    else:
        with connect(**CONFIG) as cnx:
            with cnx.cursor(buffered=True) as cursor:
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
    main()
