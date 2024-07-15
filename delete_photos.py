from kuxov.application import Application

for application in Application.list():
    application.delete_passport()
