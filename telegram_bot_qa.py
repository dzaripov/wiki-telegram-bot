import telegram
import time
import datetime
from secrets import my_token, chat_ids, mysql_password_wordpress, sitename
from mysql.connector import connect, Error
import requests


time_sleep = 30 #seconds


def bold(text):
    return '<b>' + text + '</b>'


def send(msg, chat_id, token=my_token):
    """
    Send a message to a telegram user or group specified on chatId
    chat_id must be a number!
    """
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=msg, parse_mode='HTML')


##QA

#act[0] - первое действие
#act[0][0] - question, answer и т.д. первого действия
#act[0][1] - id первого действия
#act[0][2] - time первого действия
#act[0][3] - user_id первого действия


'''
Пофиксить
в date из MySQL используются целые секунды - не понятно, когда вышла правка: в начале секунды или в конце
текущее время берется в виде float
Происходят несостыковки

Создать таблицу в MySQL, с опубликованными правками
Обновлять каждые 5 секунд. Если 6 секунд назад появилась правка, которая не опубликована - опубликовать
'''
def is_new(type_act, id_act, date): #type of activity, id, date
    if (type_act == 'new_q') or (type_act == 'new_a') or (type_act == 'selected'):
        if id_act in posted_ids_tg:
            print('False, posted')
            return False
        else:
            time_delta = (datetime.datetime.now() - date).total_seconds()-10800 #3 hours of UTC difference
            print(time_delta, datetime.datetime.now(), date)
            if (time_delta < time_sleep) :
                print('True')
                return True

            elif time_delta > time_sleep:
                print('False, > time_sleep')
                return False

    else:
        print(f'False, not question or answer')
        return False


def get_activity_name(activity):
    activity_dict = {}
    activity_dict['new_q'] = 'Question'
    activity_dict['new_a'] = 'Answer'
    activity_dict['selected'] = 'Selected as Best Answer'
    return activity_dict[activity]


def get_request(post_id, user_id):
    global title, author
    with connect(
        host="localhost",
        user="wordpressuser",
        password=mysql_password_wordpress,
        database="wordpressdb",
    ) as connection:
        query_get_post_title = f"SELECT post_title FROM wp_4_posts WHERE ID={post_id}"
        query_get_user_name = f"SELECT display_name from wp_users WHERE id={user_id}"
        with connection.cursor() as cursor:
            cursor.execute(query_get_post_title)
            title=cursor.fetchall()
            cursor.execute(query_get_user_name)
            author=cursor.fetchall()


def post_if_new_activity_QA():
    try:
        with connect(
            host="localhost",
            user="wordpressuser",
            password=mysql_password_wordpress,
            database="wordpressdb",
        ) as connection:
            query_get_activity = "SELECT activity_action, activity_q_id, activity_date, activity_user_id FROM wp_4_ap_activity"
            with connection.cursor() as cursor:
                cursor.execute(query_get_activity)
                act=cursor.fetchall()
                print('Length of activities:', len(act))
                if len(act)-5 >= 0:
                    for i in range(len(act)-5,len(act)):
                        print(f'Activity number: {i}')
                        print(act[i][0], act[i][1], act[i][2])
                        if is_new(act[i][0], act[i][1], act[i][2]) == True:
                            get_request(act[i][1], act[i][3])
                            msg = f'New {get_activity_name(act[i][0])} on Q&A: {bold(title[0][0])} by {bold(author[0][0])}. Link: https://{sitename}/qa/question/{act[i][1]}/'
                            for chat_id in chat_ids:
                                send(msg, chat_id)
                else:
                    for i in range(len(act)):
                        print(f'Activity number: {i}')
                        print(act[i][0], act[i][1], act[i][2])
                        if is_new(act[i][0], act[i][1], act[i][2]) == True:
                            get_request(act[i][1], act[i][3])
                            msg = f'New {get_activity_name(act[i][0])} on Q&A: {bold(title[0][0])} by {bold(author[0][0])}. Link: https://{sitename}/qa/question/{act[i][1]}/'
                            for chat_id in chat_ids:
                                send(msg, chat_id)
    except Error as e:
        print(e)


#main
def main():
    while True:
        post_if_new_activity_QA()
        time.sleep(time_sleep)


if __name__ == '__main__':
    main()