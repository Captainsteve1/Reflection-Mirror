from logging import getLogger, FileHandler, StreamHandler, INFO, basicConfig, error as log_error, info as log_info, warning as log_warning
from socket import setdefaulttimeout
from faulthandler import enable as faulthandler_enable
from telegram.ext import Updater as tgUpdater
from qbittorrentapi import Client as qbClient
from aria2p import API as ariaAPI, Client as ariaClient
from os import remove as osremove, path as ospath, environ
from requests import get as rget
from json import loads as jsnloads
from subprocess import Popen, run as srun, check_output
from time import sleep, time
from threading import Thread, Lock
from dotenv import load_dotenv
from pyrogram import Client, enums
from asyncio import get_event_loop
from megasdkrestclient import MegaSdkRestClient, errors as mega_err

main_loop = get_event_loop()

faulthandler_enable()

setdefaulttimeout(600)

botStartTime = time()

basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[FileHandler('log.txt'), StreamHandler()],
            level=INFO)

LOGGER = getLogger(__name__)

load_dotenv('config.env', override=True)


def getConfig(name: str):
    return environ[name]


try:
    NETRC_URL = getConfig('NETRC_URL')
    if len(NETRC_URL) == 0:
        raise KeyError
    try:
        res = rget(NETRC_URL)
        if res.status_code == 200:
            with open('.netrc', 'wb+') as f:
                f.write(res.content)
        else:
            log_error(f"Failed to download .netrc {res.status_code}")
    except Exception as e:
        log_error(f"NETRC_URL: {e}")
except BaseException:
    pass
try:
    HEROKU_API_KEY = getConfig('HEROKU_API_KEY')
    HEROKU_APP_NAME = getConfig('HEROKU_APP_NAME')
    if len(HEROKU_API_KEY) == 0 or len(HEROKU_APP_NAME) == 0:
        raise KeyError
except BaseException:
    HEROKU_APP_NAME = None
    HEROKU_API_KEY = None
try:
    TORRENT_TIMEOUT = getConfig('TORRENT_TIMEOUT')
    if len(TORRENT_TIMEOUT) == 0:
        raise KeyError
    TORRENT_TIMEOUT = int(TORRENT_TIMEOUT)
except BaseException:
    TORRENT_TIMEOUT = None
try:
    SERVER_PORT = getConfig('SERVER_PORT')
    if len(SERVER_PORT) == 0:
        raise KeyError
except:
    SERVER_PORT = 80

Popen(f"gunicorn web.wserver:app --bind 0.0.0.0:{SERVER_PORT}", shell=True)
srun(["qbittorrent-nox", "-d", "--profile=."])
if not ospath.exists('.netrc'):
    srun(["touch", ".netrc"])
srun(["cp", ".netrc", "/root/.netrc"])
srun(["chmod", "600", ".netrc"])
srun(["chmod", "+x", "aria.sh"])
srun("./aria.sh", shell=True)
sleep(0.5)

Interval = []
DRIVES_NAMES = []
DRIVES_IDS = []
INDEX_URLS = []

try:
    if bool(getConfig('_____REMOVE_THIS_LINE_____')):
        log_error('The README.md file there to be read! Exiting now!')
        exit()
except BaseException:
    pass

aria2 = ariaAPI(
    ariaClient(
        host="http://localhost",
        port=6800,
        secret="",
    )
)


def get_client():
    return qbClient(host="localhost", port=8090)


DOWNLOAD_DIR = None
BOT_TOKEN = None

download_dict_lock = Lock()
status_reply_dict_lock = Lock()
# Key: update.effective_chat.id
# Value: telegram.Message
status_reply_dict = {}
# Key: update.message.message_id
# Value: An object of Status
download_dict = {}
# key: rss_title
# value: [rss_feed, last_link, last_title, filter]
rss_dict = {}

AUTHORIZED_CHATS = set()
SUDO_USERS = set()
AS_DOC_USERS = set()
AS_MEDIA_USERS = set()
EXTENSION_FILTER = set(['.aria2'])
LEECH_LOG = set()
MIRROR_LOGS = set()
LINK_LOGS = set()

try:
    aid = getConfig('AUTHORIZED_CHATS')
    aid = aid.split()
    for _id in aid:
        AUTHORIZED_CHATS.add(int(_id.strip()))
except BaseException:
    pass
try:
    aid = getConfig('SUDO_USERS')
    aid = aid.split()
    for _id in aid:
        SUDO_USERS.add(int(_id.strip()))
except BaseException:
    pass
try:
    fx = getConfig('EXTENSION_FILTER')
    if len(fx) > 0:
        fx = fx.split()
        for x in fx:
            EXTENSION_FILTER.add(x.strip().lower())
except BaseException:
    pass
try:
    mchats = getConfig("MIRROR_LOGS")
    mchats = mchats.split()
    for chats in mchats:
        MIRROR_LOGS.add(int(chats.strip()))
    try:
        MIRROR_LOGS_CHANNEL_LINK = getConfig("MIRROR_LOGS_CHANNEL_LINK")
        if len(MIRROR_LOGS_CHANNEL_LINK) == 0:
            raise KeyError
    except KeyError:
        log_warning("Telegram Link For Mirror/Clone Logs Channel is not given")
        MIRROR_LOGS_CHANNEL_LINK = None
except Exception:
    log_warning("Logs Chat Details not provided!")

try:
    linkchats = getConfig("LINK_LOGS")
    linkchats = linkchats.split()
    for chats in linkchats:
        LINK_LOGS.add(int(chats.strip()))
except Exception:
    log_warning("LINK_LOGS Chat id not provided, Proceeding Without it")

try:
    leechchats = getConfig("LEECH_LOG")
    leechchats = leechchats.split()
    for chats in leechchats:
        LEECH_LOG.add(int(chats.strip()))
    try:
        LEECH_LOG_CHANNEL_LINK = getConfig("LEECH_LOG_CHANNEL_LINK")
        if len(LEECH_LOG_CHANNEL_LINK) == 0:
            raise KeyError
    except KeyError:
        log_warning("Telegram Link For Leech Logs Channel is not given")
        LEECH_LOG_CHANNEL_LINK = None
except Exception:
    log_warning("Leech Log Channel ID not Provided!")

try:
    BOT_TOKEN = getConfig('BOT_TOKEN')
    parent_id = getConfig('GDRIVE_FOLDER_ID')
    DOWNLOAD_DIR = getConfig('DOWNLOAD_DIR')
    if not DOWNLOAD_DIR.endswith("/"):
        DOWNLOAD_DIR = DOWNLOAD_DIR + '/'
    DOWNLOAD_STATUS_UPDATE_INTERVAL = int(
        getConfig('DOWNLOAD_STATUS_UPDATE_INTERVAL'))
    OWNER_ID = int(getConfig('OWNER_ID'))
    AUTO_DELETE_MESSAGE_DURATION = int(
        getConfig('AUTO_DELETE_MESSAGE_DURATION'))
    TELEGRAM_API = getConfig('TELEGRAM_API')
    TELEGRAM_HASH = getConfig('TELEGRAM_HASH')
except BaseException:
    log_error("One or more env variables missing! Exiting now")
    exit(1)
try:
    AUTO_DELETE_UPLOAD_MESSAGE_DURATION = int(
        getConfig('AUTO_DELETE_UPLOAD_MESSAGE_DURATION'))
except KeyError:
    AUTO_DELETE_UPLOAD_MESSAGE_DURATION = -1
    LOGGER.warning("AUTO_DELETE_UPLOAD_MESSAGE_DURATION var missing!")
    app = Client(
        name='pyrogram',
        api_id=int(TELEGRAM_API),
        api_hash=TELEGRAM_HASH,
        bot_token=BOT_TOKEN,
        parse_mode=enums.ParseMode.HTML,
        no_updates=True)
try:
    IS_PREMIUM_USER = False
    USER_SESSION_STRING = getConfig("USER_SESSION_STRING")
    if len(USER_SESSION_STRING) == 0:
        raise KeyError
    app = Client(
        name='pyrogram',
        api_id=int(TELEGRAM_API),
        api_hash=TELEGRAM_HASH,
        session_string=USER_SESSION_STRING,
        parse_mode=enums.ParseMode.HTML,
        no_updates=True)
    with app:
        IS_PREMIUM_USER = app.get_me().is_premium
except BaseException:
    app = Client(
        name='pyrogram',
        api_id=int(TELEGRAM_API),
        api_hash=TELEGRAM_HASH,
        bot_token=BOT_TOKEN,
        parse_mode=enums.ParseMode.HTML,
        no_updates=True)
try:
    IS_PREMIUM_USER = False
    USER_SESSION_STRING = getConfig("USER_SESSION_STRING")
    if len(USER_SESSION_STRING) == 0:
        raise KeyError
    app = Client(
        name='pyrogram',
        api_id=int(TELEGRAM_API),
        api_hash=TELEGRAM_HASH,
        session_string=USER_SESSION_STRING,
        parse_mode=enums.ParseMode.HTML,
        no_updates=True)
    with app:
        IS_PREMIUM_USER = app.get_me().is_premium
except BaseException:
    app = Client(
        name='pyrogram',
        api_id=int(TELEGRAM_API),
        api_hash=TELEGRAM_HASH,
        bot_token=BOT_TOKEN,
        parse_mode=enums.ParseMode.HTML,
        no_updates=True)


try:
    RSS_USER_SESSION_STRING = getConfig('RSS_USER_SESSION_STRING')
    if len(RSS_USER_SESSION_STRING) == 0:
        raise KeyError
    log_info("Creating client from RSS_USER_SESSION_STRING")
    rss_session = Client(
        name='rss_session',
        api_id=int(TELEGRAM_API),
        api_hash=TELEGRAM_HASH,
        session_string=RSS_USER_SESSION_STRING,
        parse_mode=enums.ParseMode.HTML,
        no_updates=True)
except BaseException:
    rss_session = None


def aria2c_init():
    try:
        log_info("Initializing Aria2c")
        link = "https://linuxmint.com/torrents/lmde-5-cinnamon-64bit.iso.torrent"
        dire = DOWNLOAD_DIR.rstrip("/")
        aria2.add_uris([link], {'dir': dire})
        sleep(3)
        downloads = aria2.get_downloads()
        sleep(20)
        for download in downloads:
            aria2.remove([download], force=True, files=True)
    except Exception as e:
        log_error(f"Aria2c initializing error: {e}")


Thread(target=aria2c_init).start()

try:
    MEGA_KEY = getConfig('MEGA_API_KEY')
    if len(MEGA_KEY) == 0:
        raise KeyError
except BaseException:
    MEGA_KEY = None
    log_info('MEGA_API_KEY not provided!')
if MEGA_KEY is not None:
    # Start megasdkrest binary
    Popen(["megasdkrest", "--apikey", MEGA_KEY])
    sleep(3)  # Wait for the mega server to start listening
    mega_client = MegaSdkRestClient('http://localhost:6090')
    try:
        MEGA_USERNAME = getConfig('MEGA_EMAIL_ID')
        MEGA_PASSWORD = getConfig('MEGA_PASSWORD')
        if len(MEGA_USERNAME) > 0 and len(MEGA_PASSWORD) > 0:
            try:
                mega_client.login(MEGA_USERNAME, MEGA_PASSWORD)
            except mega_err.MegaSdkRestClientException as e:
                log_error(e.message['message'])
                exit(0)
        else:
            log_info(
                "Mega API KEY provided but credentials not provided. Starting mega in anonymous mode!")
    except BaseException:
        log_info(
            "Mega API KEY provided but credentials not provided. Starting mega in anonymous mode!")
else:
    sleep(1.5)

try:
    BASE_URL = getConfig('BASE_URL_OF_BOT').rstrip("/")
    if len(BASE_URL) == 0:
        raise KeyError
except BaseException:
    log_warning('BASE_URL_OF_BOT not provided!')
    BASE_URL = None
try:
    DB_URI = getConfig('DATABASE_URL')
    if len(DB_URI) == 0:
        raise KeyError
except BaseException:
    DB_URI = None
try:
    LEECH_SPLIT_SIZE = getConfig('LEECH_SPLIT_SIZE')
    if len(LEECH_SPLIT_SIZE) == 0 or (not IS_PREMIUM_USER and int(
            LEECH_SPLIT_SIZE) > 2097152000) or int(LEECH_SPLIT_SIZE) > 4194304000:
        raise KeyError
    LEECH_SPLIT_SIZE = int(LEECH_SPLIT_SIZE)
except BaseException:
    LEECH_SPLIT_SIZE = 4194304000 if IS_PREMIUM_USER else 2097152000
MAX_SPLIT_SIZE = 4194304000 if IS_PREMIUM_USER else 2097152000
try:
    STATUS_LIMIT = getConfig('STATUS_LIMIT')
    if len(STATUS_LIMIT) == 0:
        raise KeyError
    STATUS_LIMIT = int(STATUS_LIMIT)
except BaseException:
    STATUS_LIMIT = None
try:
    UPTOBOX_TOKEN = getConfig('UPTOBOX_TOKEN')
    if len(UPTOBOX_TOKEN) == 0:
        raise KeyError
except BaseException:
    UPTOBOX_TOKEN = None
try:
    INDEX_URL = getConfig('INDEX_URL').rstrip("/")
    if len(INDEX_URL) == 0:
        raise KeyError
    INDEX_URLS.append(INDEX_URL)
except BaseException:
    INDEX_URL = None
    INDEX_URLS.append(None)
try:
    SEARCH_API_LINK = getConfig('SEARCH_API_LINK').rstrip("/")
    if len(SEARCH_API_LINK) == 0:
        raise KeyError
except BaseException:
    SEARCH_API_LINK = None
try:
    SEARCH_LIMIT = getConfig('SEARCH_LIMIT')
    if len(SEARCH_LIMIT) == 0:
        raise KeyError
    SEARCH_LIMIT = int(SEARCH_LIMIT)
except BaseException:
    SEARCH_LIMIT = 0
try:
    RSS_COMMAND = getConfig('RSS_COMMAND')
    if len(RSS_COMMAND) == 0:
        raise KeyError
except BaseException:
    RSS_COMMAND = None
try:
    FSUB = getConfig('FSUB')
    FSUB = FSUB.lower() == 'true'
except BaseException:
    FSUB = False
    LOGGER.info("Force Subscribe is disabled")
try:
    CHANNEL_USERNAME = getConfig("CHANNEL_USERNAME")
    if len(CHANNEL_USERNAME) == 0:
        raise KeyError
except KeyError:
    log_info("CHANNEL_USERNAME not provided! Using default @dipeshmirror")
    CHANNEL_USERNAME = "dipeshmirror"
try:
    FSUB_CHANNEL_ID = getConfig("FSUB_CHANNEL_ID")
    if len(FSUB_CHANNEL_ID) == 0:
        raise KeyError
    FSUB_CHANNEL_ID = int(FSUB_CHANNEL_ID)
except KeyError:
    log_info("CHANNEL_ID not provided! Using default id of @Z_Mirror")
    FSUB_CHANNEL_ID = -1001232292892
try:
    CMD_INDEX = getConfig('CMD_INDEX')
    if len(CMD_INDEX) == 0:
        raise KeyError
except BaseException:
    CMD_INDEX = ''
try:
    STORAGE_THRESHOLD = getConfig('STORAGE_THRESHOLD')
    if len(STORAGE_THRESHOLD) == 0:
        raise KeyError
    STORAGE_THRESHOLD = float(STORAGE_THRESHOLD)
except:
    STORAGE_THRESHOLD = None
try:
    RSS_CHAT_ID = getConfig('RSS_CHAT_ID')
    if len(RSS_CHAT_ID) == 0:
        raise KeyError
    RSS_CHAT_ID = int(RSS_CHAT_ID)
except BaseException:
    RSS_CHAT_ID = None
try:
    RSS_DELAY = getConfig('RSS_DELAY')
    if len(RSS_DELAY) == 0:
        raise KeyError
    RSS_DELAY = int(RSS_DELAY)
except BaseException:
    RSS_DELAY = 900
try:
    SHORTENER = getConfig('SHORTENER')
    SHORTENER_API = getConfig('SHORTENER_API')
    if len(SHORTENER) == 0 or len(SHORTENER_API) == 0:
        raise KeyError
except BaseException:
    SHORTENER = None
    SHORTENER_API = None
try:
    INCOMPLETE_TASK_NOTIFIER = getConfig('INCOMPLETE_TASK_NOTIFIER')
    INCOMPLETE_TASK_NOTIFIER = INCOMPLETE_TASK_NOTIFIER.lower() == 'true'
except BaseException:
    INCOMPLETE_TASK_NOTIFIER = False
try:
    BUTTON_FOUR_NAME = getConfig('BUTTON_FOUR_NAME')
    BUTTON_FOUR_URL = getConfig('BUTTON_FOUR_URL')
    if len(BUTTON_FOUR_NAME) == 0 or len(BUTTON_FOUR_URL) == 0:
        raise KeyError
except BaseException:
    BUTTON_FOUR_NAME = None
    BUTTON_FOUR_URL = None
try:
    BUTTON_FIVE_NAME = getConfig('BUTTON_FIVE_NAME')
    BUTTON_FIVE_URL = getConfig('BUTTON_FIVE_URL')
    if len(BUTTON_FIVE_NAME) == 0 or len(BUTTON_FIVE_URL) == 0:
        raise KeyError
except BaseException:
    BUTTON_FIVE_NAME = None
    BUTTON_FIVE_URL = None
try:
    BUTTON_SIX_NAME = getConfig('BUTTON_SIX_NAME')
    BUTTON_SIX_URL = getConfig('BUTTON_SIX_URL')
    if len(BUTTON_SIX_NAME) == 0 or len(BUTTON_SIX_URL) == 0:
        raise KeyError
except BaseException:
    BUTTON_SIX_NAME = None
    BUTTON_SIX_URL = None
try:
    SET_BOT_COMMANDS = getConfig('SET_BOT_COMMANDS')
    SET_BOT_COMMANDS = SET_BOT_COMMANDS.lower() == 'true'
except BaseException:
    SET_BOT_COMMANDS = False
try:
    STOP_DUPLICATE = getConfig('STOP_DUPLICATE')
    STOP_DUPLICATE = STOP_DUPLICATE.lower() == 'true'
except BaseException:
    STOP_DUPLICATE = False
try:
    VIEW_LINK = getConfig('VIEW_LINK')
    VIEW_LINK = VIEW_LINK.lower() == 'true'
except BaseException:
    VIEW_LINK = False
try:
    IS_TEAM_DRIVE = getConfig('IS_TEAM_DRIVE')
    IS_TEAM_DRIVE = IS_TEAM_DRIVE.lower() == 'true'
except BaseException:
    IS_TEAM_DRIVE = False
try:
    USE_SERVICE_ACCOUNTS = getConfig('USE_SERVICE_ACCOUNTS')
    USE_SERVICE_ACCOUNTS = USE_SERVICE_ACCOUNTS.lower() == 'true'
except BaseException:
    USE_SERVICE_ACCOUNTS = False
try:
    WEB_PINCODE = getConfig('WEB_PINCODE')
    WEB_PINCODE = WEB_PINCODE.lower() == 'true'
except BaseException:
    WEB_PINCODE = False
try:
    IGNORE_PENDING_REQUESTS = getConfig("IGNORE_PENDING_REQUESTS")
    IGNORE_PENDING_REQUESTS = IGNORE_PENDING_REQUESTS.lower() == 'true'
except BaseException:
    IGNORE_PENDING_REQUESTS = False
try:
    AS_DOCUMENT = getConfig('AS_DOCUMENT')
    AS_DOCUMENT = AS_DOCUMENT.lower() == 'true'
except BaseException:
    AS_DOCUMENT = False
try:
    EQUAL_SPLITS = getConfig('EQUAL_SPLITS')
    EQUAL_SPLITS = EQUAL_SPLITS.lower() == 'true'
except BaseException:
    EQUAL_SPLITS = False
try:
    CUSTOM_FILENAME = getConfig('CUSTOM_FILENAME')
    if len(CUSTOM_FILENAME) == 0:
        raise KeyError
except BaseException:
    CUSTOM_FILENAME = None
try:
    MIRROR_ENABLED = getConfig("MIRROR_ENABLED")
    MIRROR_ENABLED = MIRROR_ENABLED.lower() == "true"
except BaseException:
    MIRROR_ENABLED = False
try:
    LEECH_ENABLED = getConfig("LEECH_ENABLED")
    LEECH_ENABLED = LEECH_ENABLED.lower() == "true"
except BaseException:
    LEECH_ENABLED = False
try:
    WATCH_ENABLED = getConfig("WATCH_ENABLED")
    WATCH_ENABLED = WATCH_ENABLED.lower() == "true"
except BaseException:
    WATCH_ENABLED = False
try:
    CLONE_ENABLED = getConfig("CLONE_ENABLED")
    CLONE_ENABLED = CLONE_ENABLED.lower() == "true"
except BaseException:
    CLONE_ENABLED = False
try:
    ANILIST_ENABLED = getConfig("ANILIST_ENABLED")
    ANILIST_ENABLED = ANILIST_ENABLED.lower() == "true"
except BaseException:
    ANILIST_ENABLED = False
try:
    WAYBACK_ENABLED = getConfig("WAYBACK_ENABLED")
    WAYBACK_ENABLED = WAYBACK_ENABLED.lower() == "true"
except BaseException:
    WAYBACK_ENABLED = False
try:
    IMAGE_LEECH = getConfig("IMAGE_LEECH")
    IMAGE_LEECH = IMAGE_LEECH.lower() == "true"
except KeyError:
    IMAGE_LEECH = False
try:
    MEDIAINFO_ENABLED = getConfig("MEDIAINFO_ENABLED")
    MEDIAINFO_ENABLED = MEDIAINFO_ENABLED.lower() == "true"
except BaseException:
    MEDIAINFO_ENABLED = False
try:
    TIMEZONE = getConfig("TIMEZONE")
    if len(TIMEZONE) == 0:
        TIMEZONE = None
except BaseException:
    TIMEZONE = "Asia/Kolkata"
try:
    CRYPT = getConfig('CRYPT')
    if len(CRYPT) == 0:
        raise KeyError
except BaseException:
    CRYPT = None
try:
    APPDRIVE_EMAIL = getConfig('APPDRIVE_EMAIL')
    APPDRIVE_PASS = getConfig('APPDRIVE_PASS')
    if len(APPDRIVE_EMAIL) == 0 or len(APPDRIVE_PASS) == 0:
        raise KeyError
except KeyError:
    APPDRIVE_EMAIL = None
    APPDRIVE_PASS = None
try:
    SOURCE_LINK = getConfig('SOURCE_LINK')
    SOURCE_LINK = SOURCE_LINK.lower() == 'true'
except KeyError:
    SOURCE_LINK = False
try:
    BOT_PM = getConfig('BOT_PM')
    BOT_PM = BOT_PM.lower() == 'true'
except KeyError:
    BOT_PM = False
try:
    AUTHOR_NAME = getConfig('AUTHOR_NAME')
    if len(AUTHOR_NAME) == 0:
        AUTHOR_NAME = 'Dipesh'
except KeyError:
    AUTHOR_NAME = 'Dipesh'
try:
    AUTHOR_URL = getConfig('AUTHOR_URL')
    if len(AUTHOR_URL) == 0:
        AUTHOR_URL = 'https://t.me/dipeshmirror'
except KeyError:
    AUTHOR_URL = 'https://t.me/dipeshmirror'
try:
    CLONE_LIMIT = getConfig('CLONE_LIMIT')
    if len(CLONE_LIMIT) == 0:
        raise KeyError
    CLONE_LIMIT = float(CLONE_LIMIT)
except BaseException:
    CLONE_LIMIT = None
try:
    GD_INFO = getConfig('GD_INFO')
    if len(GD_INFO) == 0:
        GD_INFO = 'Uploaded by Reflection Mirror Bot'
except KeyError:
    GD_INFO = 'Uploaded by Reflection Mirror Bot'
try:
    TITLE_NAME = getConfig('TITLE_NAME')
    if len(TITLE_NAME) == 0:
        TITLE_NAME = 'Reflection-Mirror-Search'
except KeyError:
    TITLE_NAME = 'Reflection-Mirror-Search'
try:
    FINISHED_PROGRESS_STR = getConfig('FINISHED_PROGRESS_STR')
    UN_FINISHED_PROGRESS_STR = getConfig('UN_FINISHED_PROGRESS_STR')
except BaseException:
    FINISHED_PROGRESS_STR = '●'  # '■'
    UN_FINISHED_PROGRESS_STR = '○'  # '□'
try:
    TOKEN_PICKLE_URL = getConfig('TOKEN_PICKLE_URL')
    if len(TOKEN_PICKLE_URL) == 0:
        raise KeyError
    try:
        res = rget(TOKEN_PICKLE_URL)
        if res.status_code == 200:
            with open('token.pickle', 'wb+') as f:
                f.write(res.content)
        else:
            log_error(
                f"Failed to download token.pickle, link got HTTP response: {res.status_code}")
    except Exception as e:
        log_error(f"TOKEN_PICKLE_URL: {e}")
except BaseException:
    pass
try:
    ACCOUNTS_ZIP_URL = getConfig('ACCOUNTS_ZIP_URL')
    if len(ACCOUNTS_ZIP_URL) == 0:
        raise KeyError
    try:
        res = rget(ACCOUNTS_ZIP_URL)
        if res.status_code == 200:
            with open('accounts.zip', 'wb+') as f:
                f.write(res.content)
        else:
            log_error(
                f"Failed to download accounts.zip, link got HTTP response: {res.status_code}")
    except Exception as e:
        log_error(f"ACCOUNTS_ZIP_URL: {e}")
        raise KeyError
    srun(["unzip", "-q", "-o", "accounts.zip"])
    srun(["chmod", "-R", "777", "accounts"])
    osremove("accounts.zip")
except BaseException:
    pass
try:
    MULTI_SEARCH_URL = getConfig('MULTI_SEARCH_URL')
    if len(MULTI_SEARCH_URL) == 0:
        raise KeyError
    try:
        res = rget(MULTI_SEARCH_URL)
        if res.status_code == 200:
            with open('drive_folder', 'wb+') as f:
                f.write(res.content)
        else:
            log_error(
                f"Failed to download drive_folder, link got HTTP response: {res.status_code}")
    except Exception as e:
        log_error(f"MULTI_SEARCH_URL: {e}")
except BaseException:
    pass
try:
    YT_COOKIES_URL = getConfig('YT_COOKIES_URL')
    if len(YT_COOKIES_URL) == 0:
        raise KeyError
    try:
        res = rget(YT_COOKIES_URL)
        if res.status_code == 200:
            with open('cookies.txt', 'wb+') as f:
                f.write(res.content)
        else:
            log_error(
                f"Failed to download cookies.txt, link got HTTP response: {res.status_code}")
    except Exception as e:
        log_error(f"YT_COOKIES_URL: {e}")
except BaseException:
    pass

DRIVES_NAMES.append("Main")
DRIVES_IDS.append(parent_id)
if ospath.exists('drive_folder'):
    with open('drive_folder', 'r+') as f:
        lines = f.readlines()
        for line in lines:
            try:
                temp = line.strip().split()
                DRIVES_IDS.append(temp[1])
                DRIVES_NAMES.append(temp[0].replace("_", " "))
            except BaseException:
                pass
            try:
                INDEX_URLS.append(temp[2])
            except BaseException:
                INDEX_URLS.append(None)
try:
    SEARCH_PLUGINS = getConfig('SEARCH_PLUGINS')
    if len(SEARCH_PLUGINS) == 0:
        raise KeyError
    SEARCH_PLUGINS = jsnloads(SEARCH_PLUGINS)
except BaseException:
    SEARCH_PLUGINS = None
try:
    IMAGE_URL = getConfig('IMAGE_URL')
except KeyError:
    IMAGE_URL = 'http://telegra.ph/REFLECTION-07-18'


updater = tgUpdater(token=BOT_TOKEN, request_kwargs={'read_timeout': 20, 'connect_timeout': 15})
bot = updater.bot
dispatcher = updater.dispatcher
job_queue = updater.job_queue
botname = bot.username