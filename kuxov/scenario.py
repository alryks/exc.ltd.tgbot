from pymongo import MongoClient
from pymongo.database import Database

SCENARIO = [

]

ADMIN_IDS = [

]


BOT_TOKEN = ""

MONGO_HOST = "mongodb://localhost:27017/"
client = MongoClient(MONGO_HOST)
db: Database = client.TelegramBot

CDN_ENDPOINT = "https://storage.yandexcloud.net"
CDN_ACCESS_KEY_ID = ""
CDN_SECRET_ACCESS_KEY = ""
CDN_BUCKET = ""
CDN_REGION = "ru-central1"