from telebot import TeleBot

from pymongo import MongoClient
from pymongo.database import Database

SCENARIO = [

]

ADMIN_IDS = [

]

ACCEPT_ID = []
DECLINE_ID = []

BOT_TOKEN = ""
bot = TeleBot(token=BOT_TOKEN, parse_mode="Markdown")

MONGO_USER = ""
MONGO_PASSWORD = ""

MONGO_HOST = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@localhost:27017/"
client = MongoClient(MONGO_HOST)
db: Database = client.SNPBot

CDN_ENDPOINT = "https://storage.yandexcloud.net"
CDN_ACCESS_KEY_ID = ""
CDN_SECRET_ACCESS_KEY = ""
CDN_BUCKET = ""
CDN_REGION = "ru-central1"

SPREADSHEET_ID = ""
SPREADSHEET_RANGE = ""