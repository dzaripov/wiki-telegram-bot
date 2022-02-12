import telegram
import time
import datetime
from secret_information import my_token, chat_ids, mysql_password_wiki, sitename
from mysql.connector import connect, Error


time_sleep = 30 #seconds


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


## WIKI


def get_request_wiki(rc_comment_id, rc_actor):
    global summary_comment, author_wiki
    try:
        with connect(
            host="localhost",
            user="wiki",
            password=mysql_password_wiki,
            database="wikidb",
        ) as connection:
            query_get_summary_comment = f"select comment_text from comment where comment_id={rc_comment_id};"
            query_get_user_name = f"select actor_name from actor where actor_id={rc_actor};"
            with connection.cursor() as cursor:
                cursor.execute(query_get_summary_comment)
                summary_comment=cursor.fetchall()[0][0].decode('utf-8')
                cursor.execute(query_get_user_name)
                author_wiki=cursor.fetchall()[0][0].decode('utf-8')
    except Error as e:
        print(e)


def create_message_wiki(rc_title, summary_comment, author_wiki, rc_cur_id):
    return f"Товарищи, новое изменение на вики!\n{create_link(f'https://{sitename}/wiki/?curid={rc_cur_id}',rc_title.replace('_', ' '))}: {bold(summary_comment)} от {bold(author_wiki)}."


def is_publishable(rc_minor, rc_new):
    if rc_minor == 0 and rc_new == 0:
        return True
    else:
        return False


def is_new_wiki(date): #date
    date_real = datetime.datetime.strptime(str(date), '%Y%m%d%H%M%S')
    time_delta = (datetime.datetime.now() - date_real).total_seconds()-10800 #3 hours of UTC difference
    print(time_delta, datetime.datetime.now(), date_real)
    if (time_delta < time_sleep):
        print('True')
        return True
    elif time_delta > time_sleep:
        print('False, > time_sleep')
        return False


def insert_posted_activity(posted_id, post_name):
    sql = "INSERT INTO recentchangesposted (posted_id, post_name) VALUES (%s, %s)"
    val = (posted_id, post_name)
    cursor.execute(sql, val)


def post_if_new_activity_wiki():
    try:
        with connect(
            host="localhost",
            user="wiki",
            password=mysql_password_wiki,
            database="wikidb",
        ) as connection:

            query_get_activity = "select rc_title, rc_minor, rc_new, rc_comment_id, rc_timestamp, rc_actor, rc_id, rc_cur_id from recentchanges where rc_log_type is NULL"

            with connection.cursor() as cursor:

                cursor.execute(query_get_activity)
                act=cursor.fetchall()

                print('Length of activities (wiki):', len(act))

                if len(act)-5 >= 0:
                    activity_range = range(len(act)-5,len(act))
                else:
                    activity_range = range(len(act))
                
                for i in activity_range:
                    rc_title             = act[i][0].decode('utf-8')
                    rc_minor             = act[i][1]
                    rc_new               = act[i][2]
                    rc_comment_id        = act[i][3]
                    rc_timestamp         = act[i][4].decode('utf-8')
                    rc_actor             = act[i][5]
                    rc_id                = act[i][6]
                    rc_cur_id            = act[i][7]

                    print(rc_title, rc_minor, rc_new, rc_comment_id, rc_timestamp, rc_actor, rc_id, rc_cur_id)
                    
                    if is_publishable(rc_minor, rc_new) and is_new_wiki(rc_timestamp):

                        get_request_wiki(rc_comment_id, rc_actor)
                        msg = create_message_wiki(rc_title, summary_comment, author_wiki, rc_cur_id)

                        for chat_id in chat_ids:
                            send(msg, chat_id)

                        insert_posted_activity(rc_id, rc_title)

    except Error as e:
        print(e)


def manual_post(rc_id_manual):
    try:
        with connect(
            host="localhost",
            user="wiki",
            password=mysql_password_wiki,
            database="wikidb",
        ) as connection:

            query_get_activity = "select rc_title, rc_minor, rc_new, rc_comment_id, rc_timestamp, rc_actor, rc_id, rc_cur_id from recentchanges where rc_log_type is NULL"

            with connection.cursor() as cursor:

                cursor.execute(query_get_activity)
                act=cursor.fetchall()

                for i in range(len(act)):
                    rc_title             = act[i][0].decode('utf-8')
                    rc_minor             = act[i][1]
                    rc_new               = act[i][2]
                    rc_comment_id        = act[i][3]
                    rc_timestamp         = act[i][4].decode('utf-8')
                    rc_actor             = act[i][5]
                    rc_id                = act[i][6]
                    rc_cur_id            = act[i][7]

                    if (rc_id == rc_id_manual):
                        get_request_wiki(rc_comment_id, rc_actor)
                        msg = create_message_wiki(rc_title, summary_comment, author_wiki)

                        for chat_id in chat_ids:
                            send(msg, chat_id)
                            print(f'Posted! {msg}')

    except Error as e:
        print(e)


def get_activities():
    try:
        with connect(
            host="localhost",
            user="wiki",
            password=mysql_password_wiki,
            database="wikidb",
        ) as connection:

            query_get_activity = "select rc_title, rc_minor, rc_new, rc_comment_id, rc_timestamp, rc_actor, rc_id, rc_cur_id from recentchanges where rc_log_type is NULL"

            with connection.cursor() as cursor:

                cursor.execute(query_get_activity)
                act=cursor.fetchall()

                for i in range(len(act)):
                    rc_title             = act[i][0].decode('utf-8')
                    rc_minor             = act[i][1]
                    rc_new               = act[i][2]
                    rc_comment_id        = act[i][3]
                    rc_timestamp         = act[i][4].decode('utf-8')
                    rc_actor             = act[i][5]
                    rc_id                = act[i][6]
                    rc_cur_id            = act[i][7]

                    print(rc_title, rc_minor, rc_new, rc_comment_id, rc_timestamp, rc_actor, rc_id)

    except Error as e:
        print(e)



def is_db_created():

    with connect(
            host="localhost",
            user="wiki",
            password=mysql_password_wiki,
            database="wikidb",
        ) as connection:

        with connection.cursor() as cursor:
            cursor.execute('SHOW TABLES')
            
            tables = cursor.fetchall()
            print(tables)

        for i in range(len(tables)):
            if tables[i][0] == 'recentchangesposted':
                return True

        return False


def create_posted_activity_db():

    if is_db_created():

        print('DB is already created!')

    else:

        with connect(
            host="localhost",
            user="wiki",
            password=mysql_password_wiki,
            database="wikidb",
        ) as connection:

            with connection.cursor() as cursor:
                cursor.execute("CREATE TABLE recentchangesposted (posted_id int, post_name VARCHAR(255))")

        print('DB is created!')




#main
def main():
    while True:
        post_if_new_activity_wiki()
        time.sleep(time_sleep)


if __name__ == '__main__':
    main()
