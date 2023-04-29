# Wiki-telegram-bot
A telegram bot to notify changes of private wikis. This telegram bot sends message, when new change on private wiki appears.
## Prerequisites
* Linux
* MySQL database for wiki
* python3 (this bot was tested on python3.6)
* mysql-connector-python and python-telegram-bot modules
## Installation & Configuration
You need to copy this repo: `git clone https://github.com/dzaripov/wiki-telegram-bot.git`

Then edit secret_information.py: \
my_token - Telegram Bot token that you can get from @BotFather \
chat_ids - Telegram chat ids in which bot works. Can be single chat id or muptiple. Chat id can be acquired using @RawDataBot \
host - hostname of MySQL wiki database \
user - name of MySQL wiki user \
database - name of MySQL wiki database \
password - password of MySQL wiki database\
sitename - domain name of site
time_sleep - time between checks for new changes in seconds

After editing, you need to setup bot.


Create file /etc/systemd/system/telegram-bot-wiki.service with content like this, but with paths replacement:
```
[Unit]
  Description=Telegram Bot for wiki

[Service]
  ExecStart=/PATH/TO/INTERPRETER/python3.6 -u /PATH/TO/BOT/wiki-telegram-bot/telegram_bot_wiki.py
  Type=simple
  KillMode=process

  SyslogIdentifier=telegram-bot-wiki
  SyslogFacility=daemon

  Restart=on-failure

[Install]
  WantedBy=multi-user.target
```
And then enable bot: `systemctl enable --now /etc/systemd/system/telegram-bot-wiki.service`

## Other
Bot won't notify a minor change or a creation of new page. 
