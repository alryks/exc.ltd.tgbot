import datetime
import asyncio
from functools import partial
from concurrent.futures import ThreadPoolExecutor

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from kuxov.scenario import SPREADSHEET_ID, SPREADSHEET_RANGE, SPREADSHEET_RANGE_LOGS, SPREADSHEET_RANGE_ERRORS


def calculate_age(born):
    today = datetime.date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def update_table(range_name, application=None, access_db=None, users_db=None, trcbck=None, func_name=None, args=None, kwargs=None):
    with ThreadPoolExecutor() as pool:
        pool.submit(_update_table_sync, range_name, application, access_db, users_db, trcbck, func_name, args, kwargs)


def _update_table_sync(range_name, application=None, access_db=None, users_db=None, trcbck=None, func_name=None, args=None, kwargs=None):
    try:
        creds = Credentials.from_service_account_file("credentials.json",
                                                      scopes=["https://www.googleapis.com/auth/spreadsheets"])
        value_input_option = "RAW"

        service = build("sheets", "v4", credentials=creds)

        if range_name == SPREADSHEET_RANGE:
            app_data = application.data
            if "status" not in app_data:
                return
            access_name = access_db.get_name(app_data["user_id"])
            if not access_name:
                return
            application_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            status = "Принят" if app_data["status"] == "accepted" else "Отклонен"
            if app_data.get("edited") is True:
                status += " (ред.)"
            reason = app_data.get("reason", "")

            values = [
                [application_time, access_name, app_data["name"], status, reason]
            ]
        elif range_name == SPREADSHEET_RANGE_LOGS:
            app_data = application.data
            application_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            application_id = str(app_data.get("_id", ""))
            access_id = users_db.get_user_from_application(application_id)
            if not access_id:
                access_id = app_data.get("user_id", "")
            access_name = access_db.get_name(access_id) if access_id else ""
            job_info = ""
            if app_data.get("job", ""):
                job_info = f"{app_data['job']['объект']}|{app_data['job']['должность']}|{app_data['job']['пол']}|от {app_data['job']['возраст_от']} до {app_data['job']['возраст_до']}"
            name = app_data.get("name", "")
            gender = app_data.get("gender", "")
            phone = app_data.get("phone", "")
            age = f"{app_data.get('age', '').strftime('%d.%m.%Y')}" if app_data.get("age", "") else ""
            date_on_object = f"{app_data.get('date_on_object', '').strftime('%d.%m.%Y')}" if app_data.get("date_on_object", "") else ""
            residence = app_data.get("residence", "")
            photo_pdf = app_data.get("photo_pdf", "")
            if photo_pdf:
                photo_pdf = application.passport_pdf_url
            comment = app_data.get("comment", "")
            # status = ""
            # reason = ""
            # if app_data.get("status", "") in ["accepted", "declined"]:
            #     status = "Принят" if app_data.get("status", "") == "accepted" else "Отклонен"
            #     if app_data.get("edited") is True:
            #         status += " (ред.)"
            #     reason = app_data.get("reason", "")
            submitted = "Да" if app_data.get("submitted", False) else "Нет"

            values = [
                [application_time, application_id, access_name, job_info, name, gender, phone, age, date_on_object, residence, comment, photo_pdf, submitted]
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
    except Exception as e:
        print(f"Error in update_table: {e}")