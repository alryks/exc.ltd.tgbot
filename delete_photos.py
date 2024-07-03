from kuxov.application import Application

for application in Application.list():
    application.del_passport_photos()
