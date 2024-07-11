from pymongo import MongoClient
from pymongo.database import Database

SCENARIO = [

]

ADMIN_IDS = [
    111111111,

]

ALERT_ID = 111111111

BOT_TOKEN = ""

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