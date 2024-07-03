from pymongo import MongoClient
from kuxov.scenario import db

db.drop_collection('applications')
db.drop_collection('users')
