import os
from pymongo import MongoClient
from pymongo.database import Database

SCENARIO = [

]

ADMIN_IDS = [

]


BOT_TOKEN = ""

MONGO_HOST = ""
client = MongoClient(MONGO_HOST)
db: Database = client.kuxov
