import telegram
import time
import logging
from secret_information import (my_token, chat_ids, host, user, 
                                password, database, sitename, time_sleep)
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
    Transform text to bold

    Args:
        text (str): The text to transform

    Returns:
        str: The bold text
    """
    return '<b>' + text + '</b>'


def create_link(link, title):
    """
    Create a Telegram hyperlink

    Args:
        link (str): The URL link
        title (str): The text to display as the link

    Returns:
        str: The HTML code for the hyperlink
    """
    return f'<a href="{link}">{title}</a>'


def send(msg, chat_id, token=my_token):
    """
    Sends a message to a Telegram user or group specified by chat_id

    Args:
        msg (str): The message to send
        chat_id (str): The ID of the chat to send the message to
        token (str, optional): The API token for the Telegram bot. Defaults to my_token.
    """
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=msg, parse_mode='HTML')


def create_message_wiki(rc_title, summary_comment, author_wiki, rc_cur_id):
    """
    Creates a message to be sent to a Telegram group or user

    Args:
        rc_title (str): The title of the wiki page that was changed
        summary_comment (str): A summary of the changes made to the page
        author_wiki (str): The username of the person who made the changes
        rc_cur_id (int): The current revision ID of the page (ID of the change)

    Returns:
        str: The message to send
    """
    title = rc_title.replace('_', ' ')
    link = f'https://{sitename}/wiki/?curid={rc_cur_id}'
    telegram_link = create_link(link, title)
    return f"Товарищи, новое изменение на вики!\n\
{telegram_link}: {bold(summary_comment)} от {bold(author_wiki)}."


def get_activity_wiki(length_act=5):
    """
    Gets recent changes from the wiki that aren't minor 
    (or page creation) and haven't been posted earlier.
    Returns a list of tuples containing the title, timestamp, 
    ID of the change, ID of the page that contains the change,
    summary of the change, and name of the author.

    Args:
        length_act (int, optional): The number of recent changes to get. 
        Defaults to 5.

    Returns:
        tuple: A tuple containing the list of recent changes 
        and the range of recent changes to process.
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
    """
    Checks if the recentchangesposted table exists in the database.

    Returns:
    bool: True if the table exists, False otherwise.
    """
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
    """
    Creates the recentchangesposted table in the database 
    if it does not already exist.
    """
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
    """
    The main function of the program that runs the 
    function in a loop every time_sleep number of seconds.
    """
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