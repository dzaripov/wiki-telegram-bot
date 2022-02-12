import telegram_bot_wiki
import sys


id = int(sys.argv[1])


if __name__ == '__main__':
    telegram_bot_wiki.manual_post(id)