from datetime import datetime, timedelta

from bson import ObjectId
from kuxov.application import Application
from kuxov.state import Status


dt = ObjectId.from_datetime(datetime.now() - timedelta(days=2))
Application.applications.delete_many({"status": Status.ACCEPTED.value,
                                      "_id": {"$lt": dt}})
