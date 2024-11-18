import datetime

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from kuxov.scenario import SPREADSHEET_ID, SPREADSHEET_RANGE, SPREADSHEET_RANGE_LOGS, SPREADSHEET_RANGE_ERRORS


def calculate_age(born):
    today = datetime.date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def update_table(range_name, application=None, access_db=None, users_db=None, trcbck=None, func_name=None, args=None, kwargs=None):
    creds = Credentials.from_service_account_file("credentials.json",
                                                  scopes=["https://www.googleapis.com/auth/spreadsheets"])
    value_input_option = "RAW"

    try:
        service = build("sheets", "v4", credentials=creds)

        if range_name == SPREADSHEET_RANGE:
            if "status" not in application:
                return
            access_name = access_db.get_name(application["user_id"])
            if not access_name:
                return
            application_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            status = "Принят" if application["status"] == "accepted" else "Отклонен"
            if application.get("edited") is True:
                status += " (ред.)"
            reason = application.get("reason", "")

            values = [
                [application_time, access_name, application["name"], status, reason]
            ]
        elif range_name == SPREADSHEET_RANGE_LOGS:
            application_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            application_id = str(application.get("_id", ""))
            access_id = users_db.get_user_from_application(application_id)
            if not access_id:
                access_id = application.get("user_id", "")
            access_name = access_db.get_name(access_id) if access_id else ""
            job_info = ""
            if application.get("job", ""):
                job_info = f"{application['job']['объект']}|{application['job']['должность']}|{application['job']['пол']}|от {application['job']['возраст_от']} до {application['job']['возраст_до']}"
            name = application.get("name", "")
            gender = application.get("gender", "")
            phone = application.get("phone", "")
            age = f"{application.get('age', '').strftime('%d.%m.%Y')}" if application.get("age", "") else ""
            date_on_object = f"{application.get('date_on_object', '').strftime('%d.%m.%Y')}" if application.get("date_on_object", "") else ""
            residence = application.get("residence", "")
            comment = application.get("comment", "")
            # status = ""
            # reason = ""
            # if application.get("status", "") in ["accepted", "declined"]:
            #     status = "Принят" if application.get("status", "") == "accepted" else "Отклонен"
            #     if application.get("edited") is True:
            #         status += " (ред.)"
            #     reason = application.get("reason", "")
            submitted = "Да" if application.get("submitted", False) else "Нет"

            values = [
                [application_time, application_id, access_name, job_info, name, gender, phone, age, date_on_object, residence, comment, submitted]
            ]
        elif range_name == SPREADSHEET_RANGE_ERRORS:
            values = [
                [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), trcbck, func_name, args, kwargs]
            ]
        else:
            raise NotImplementedError()
        body = {"values": values}

        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=SPREADSHEET_ID,
                range=range_name,
                valueInputOption=value_input_option,
                body=body,
            )
            .execute()
        )
    except HttpError as error:
        print(f"An error occurred: {error}")