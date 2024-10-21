"""
create an xlsx file from mongodb with following structure:
datetime, user name, application name, application status
"""

import pandas as pd
from kuxov.scenario import db

data = []
applications = db.applications.find()

for application in applications:
    user = db.users.find_one({"tg_id": application["tg_id"]})
    if user is None:
        continue
    data.append({
        "Время": application["datetime"],
        "КА": user["name"],
        "Имя кандидата": application["name"],
        "Статус кандидата": "Принят" if application["status"] == "accept" else "Отклонен"
    })

df = pd.DataFrame(data)
