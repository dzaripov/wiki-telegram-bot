# MediaWiki change notifyer in telegram
A telegram bot to notify changes of private wikis. This telegram bot sends message, when new change on private wiki appears.
![image](https://user-images.githubusercontent.com/15835291/235373926-59a6d8ed-0e5a-49af-bbf2-1c7e8e78ce37.png)
## Prerequisites
* Linux
* MySQL database for wiki
* python3 (this bot was tested on python3.8)
* SQLAlchemy and DPAPI (PyMySQL) and python-telegram-bot modules
## Installation & Configuration
You need to copy this repo: `git clone https://github.com/dzaripov/wiki-telegram-bot.git`

Then edit secret_information.py: \
my_token - Telegram Bot token that you can get from @BotFather \
chat_ids - Telegram chat ids in which bot works. Can be single chat id or muptiple. Chat id can be acquired using @RawDataBot \
chat_ids_internal - Telegram chad ids in which bot sends logging information (and minor changes or page creation) \ 
host - hostname of MySQL wiki database \
port - port of MySQL wiki database \
user - name of MySQL wiki user \
database - name of MySQL wiki database \
password - password of MySQL wiki database\
sitename - domain name of site\
time_sleep - time between checks for new changes in seconds

After editing, you need to setup bot.


Create file /etc/systemd/system/telegram-bot-wiki.service with content like this, but with paths replacement:
```
[Unit]
  Description=Telegram Bot for wiki
8
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
