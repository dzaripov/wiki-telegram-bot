import telegram_bot_qa
import sys


id = int(sys.argv[1])


if __name__ == '__main__':
    telegram_bot_qa.manual_post(id)