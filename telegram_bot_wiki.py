import telegram
import time
import logging
from secret_information import (my_token, chat_ids, chat_ids_internal, host, port, 
                                user, password, database, sitename, time_sleep)
import sqlalchemy
from sqlalchemy import select, and_, not_, insert, Table, Column, Integer


engine = sqlalchemy.create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}")
metadata = sqlalchemy.MetaData(engine)

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
    telegram_hyperlink = create_link(link, title)
    response = "Товарищи, новое изменение на вики!\n{}: {} от {}.".format(
        telegram_hyperlink, bold(summary_comment), bold(author_wiki))
    return response


def create_message_wiki_internal(log_type, log_action, log_title, log_page, log_params, comment_text, actor_name):
    """
    Creates a message to be sent to internal a Telegram group or user.

    Args:
        rc_title (str): The title of the wiki page that was changed
        summary_comment (str): A summary of the changes made to the page
        author_wiki (str): The username of the person who made the changes
        rc_cur_id (int): The current revision ID of the page (ID of the change)

    Returns:
        str: The message to send
    """
    title = log_title.replace('_', ' ')
    link = f'https://{sitename}/wiki/?curid={log_page}'
    telegram_hyperlink = create_link(link, title)
    response = "Новое изменение на вики!\n{}: {} от {}. {}: {}. Params: {}".format(
        telegram_hyperlink, bold(comment_text), bold(actor_name), 
        log_type, log_action, log_params)
    return response


def get_activity_wiki():
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
    recentchanges = Table("recentchanges", metadata, autoload=True, autoload_with=engine)
    comment = Table("comment", metadata, autoload=True, autoload_with=engine)
    actor = Table("actor", metadata, autoload=True, autoload_with=engine)
    recentchangesposted = Table("recentchangesposted", metadata, autoload=True, autoload_with=engine)
    logging_table = Table("logging", metadata, autoload=True, autoload_with=engine)
    loggingposted = Table("loggingposted", metadata, autoload=True, autoload_with=engine)
    
    query_get_activity = (
        select(
            recentchanges.c.rc_title,
            recentchanges.c.rc_timestamp,
            recentchanges.c.rc_id,
            recentchanges.c.rc_cur_id,
            recentchanges.c.rc_new,
            recentchanges.c.rc_minor,
            comment.c.comment_text,
            actor.c.actor_name
        )
        .select_from(recentchanges)
        .join(comment, recentchanges.c.rc_comment_id == comment.c.comment_id)
        .join(actor, recentchanges.c.rc_actor == actor.c.actor_id)
        .where(
            and_(
                recentchanges.c.rc_log_type.is_(None),
                ~recentchanges.c.rc_id.in_(
                    select(recentchangesposted.c.posted_act_id)
                ),

                )
            )
        )
    
    query_get_logging_activity = (
        select(
            logging_table.c.log_id,
            logging_table.c.log_type,
            logging_table.c.log_action,
            logging_table.c.log_title,
            logging_table.c.log_page,
            logging_table.c.log_params,
            comment.c.comment_text,
            actor.c.actor_name
        )
        .select_from(logging_table)
        .join(comment, logging_table.c.log_comment_id == comment.c.comment_id)
        .join(actor, logging_table.c.log_actor == actor.c.actor_id)
        .where(
                not_(logging_table.c.log_id.in_(select(loggingposted.c.posted_act_id)))
        )
    )
    
    with engine.connect() as connection:
        act_main = connection.execute(query_get_activity).all()
        act_internal = connection.execute(query_get_logging_activity).all()
    return act_main, act_internal


def post_if_new_activity_wiki():
    """
    Parses SQL query and sends a message if new activity is found.
    Adds information about posted change in database.
    """
    act_main, act_internal = get_activity_wiki()
    for i in range(len(act_main)):
        rc_title        = act_main[i][0].decode('utf-8')
        rc_timestamp    = act_main[i][1].decode('utf-8')
        rc_id           = act_main[i][2]
        rc_cur_id       = act_main[i][3]
        rc_new          = act_main[i][4]
        rc_minor        = act_main[i][5]
        comment_text    = act_main[i][6].decode('utf-8')
        actor_name      = act_main[i][7].decode('utf-8')

        logging.info(f'{rc_title}, {rc_timestamp}, {rc_id}, \
                    {rc_cur_id}, {comment_text}, {actor_name}')

        msg = create_message_wiki(rc_title, comment_text, actor_name, rc_cur_id)

        if (rc_new == 0) and (rc_minor == 0):
            for chat_id in chat_ids:
                send(msg, chat_id)
        else:
            for chat_id in chat_ids_internal:
                send(msg, chat_id)
        

        with engine.begin() as connection:
            recentchangesposted = Table("recentchangesposted", metadata, autoload=True, autoload_with=engine)
            insert_statement_rc = recentchangesposted.insert().values(posted_act_id=rc_id, post_id=rc_cur_id)
            connection.execute(insert_statement_rc)

    for i in range(len(act_internal)):
        log_id          = act_internal[i][0]
        log_type        = act_internal[i][1].decode('utf-8')
        log_action      = act_internal[i][2].decode('utf-8')
        log_title       = act_internal[i][3].decode('utf-8')
        log_page        = act_internal[i][4]
        log_params      = act_internal[i][5].decode('utf-8')
        comment_text    = act_internal[i][6].decode('utf-8')
        actor_name      = act_internal[i][7].decode('utf-8')

        logging.info(f'{log_id}, {log_type}, {log_action}, {log_title}, \
                     {log_page}, {log_params}, {comment_text}, {actor_name}')
        
        msg = create_message_wiki_internal(log_type, log_action, log_title, log_page,
                                           log_params, comment_text, actor_name)
        
        for chat_id in chat_ids_internal:
            send(msg, chat_id)

        with engine.begin() as connection:
            loggingposted = Table("loggingposted", metadata, autoload=True, autoload_with=engine)
            insert_statement_log = loggingposted.insert().values(posted_act_id=log_id, post_id=log_page)
            connection.execute(insert_statement_log)


def create_posted_activity_db():
    """
    Creates the recentchangesposted and loggingposted table in the database 
    if they do not already exist.
    """
    recentchangesposted = Table(
        'recentchangesposted',
        metadata,
        Column('posted_act_id', Integer),
        Column('post_id', Integer)
    )
    loggingposted = Table(
        'loggingposted',
        metadata,
        Column('posted_act_id', Integer),
        Column('post_id', Integer)
    )

    if recentchangesposted.exists(bind=engine) and loggingposted.exists(bind=engine):
        logging.info('DB is already created!')
    else:
        metadata.create_all(bind=engine)
        logging.info('DB is created!')


def main():
    """
    The main function of the program that runs the 
    function in a loop every time_sleep number of seconds.
    """
    while True:
        try:
            time.sleep(time_sleep)
            post_if_new_activity_wiki()
        except Exception as e:
            logging.info(e)
            for chat_id in chat_ids_internal:
                send("wiki-telegram bot is down. " + e, chat_id)
            raise SystemExit
            



if __name__ == '__main__':
    # Wait for database initialization
    time.sleep(1)
    # Create recentchangesposted/loggingposted table if not exists 
    create_posted_activity_db()

    main()