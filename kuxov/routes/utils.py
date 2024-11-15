from flask.json.provider import DefaultJSONProvider
import sys
from datetime import datetime
import uuid
from time import time

from bson import ObjectId
from flask import request, jsonify, Response

from secrets import token_urlsafe

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from kuxov.scenario import SPREADSHEET_ID, SPREADSHEET_RANGE, SPREADSHEET_RANGE_LOGS


class CustomJSONEncoder(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, ObjectId):
            return str(obj)
        return DefaultJSONProvider.default(obj)


def check_key(key):
    try:
        return open("key.txt", "r").read().strip() == key.strip()
    except:
        return False


def set_key(key):
    prev_key = open("key.txt", "r").read().strip()
    if prev_key == "" or prev_key == key.strip():
        new_key = token_urlsafe(32)
        open("key.txt", "w").write(new_key)
        return new_key

    return ""



def check_missing_keys(keys_and_errors,
                       method="POST"):
    def check_missing_decorator(fn):
        @wraps(fn)
        def temp(*args, **kwargs):
            params = (request.json if request.is_json else request.form) if method == "POST" else request.args
            print(params, file=sys.stderr)
            for key, error in keys_and_errors:
                if key not in params:
                    if isinstance(error, Response):
                        return error
                    return jsonify(error)
            return fn(*args, **kwargs)

        return temp
    return check_missing_decorator


def print_output_json(marker=None):
    def print_output_json_decorator(fn):
        @wraps(fn)
        def temp(*args, **kwargs):
            t1 = time()
            output: Response = fn(*args, **kwargs)
            t2 = time()
            if marker is not None:
                print(f"MARKER ({t2 - t1:.3f}s)", marker, file=sys.stderr)
            print(output.json, file=sys.stderr)
            return output
        return temp
    return print_output_json_decorator


def timeit(marker=None):
    def timeit_decorator(fn):
        @wraps(fn)
        def temp(*args, **kwargs):
            t1 = time()
            output: Response = fn(*args, **kwargs)
            t2 = time()
            if marker is not None:
                print(f"MARKER ({t2 - t1:.3f}s)", marker, file=sys.stderr)
            return output
        return temp
    return timeit_decorator


from functools import wraps
from typing import Callable
import yaml
from flask import request, jsonify


def make_inputs_description(**kwargs):
    def get_value_type(v):
        if isinstance(v, dict):
            return 'object'
        elif isinstance(v, str):
            return 'string'
        elif isinstance(v, int):
            return 'int'
        elif isinstance(v, float):
            return 'float'
        elif isinstance(v, list):
            return 'object'
        else:
            print(v)
            raise NotImplementedError()

    inputs_description = []
    for name, value in kwargs.items():
        inputs_description.append({
            "name": name,
            "in": "body",
            "schema": {
                "type": get_value_type(value),
                "example": {name: value},
            }
        })

    return inputs_description


def make_method_description(name, description, tags,
                            inputs,
                            outputs):
    operationId = name.replace(' ', '_')
    summary = description
    method_description = {
        "tags": tags,
        "summary": summary,
        "description": description,
        "operationId": operationId,
        "parameters": make_inputs_description(**inputs),
        "responses": {
            200: {
                "description": "",
                "schema": {
                    "example": outputs,
                }
            }
        }
    }

    return f"""
{name}
---
{yaml.dump(method_description)}
"""


def describe(tags=tuple(),
             description="",
             name="",
             inputs={},
             outputs={}):

    def describe_decorator(fn):
        @wraps(fn)
        def temp(*args, **kwargs):
            return fn(*args, **kwargs)

        temp.__doc__ = f"""
        {make_method_description(name=name,
                                 description=description,
                                 tags=tags,
                                 inputs=inputs,
                                 outputs=outputs)}
        """
        return temp
    return describe_decorator


def update_table(application, access_db, users_db, range_name):
    if "status" not in application and range_name == SPREADSHEET_RANGE:
        return

    creds = Credentials.from_service_account_file("credentials.json",
                                                  scopes=["https://www.googleapis.com/auth/spreadsheets"])
    value_input_option = "RAW"

    try:
        service = build("sheets", "v4", credentials=creds)

        if range_name == SPREADSHEET_RANGE:
            access_name = access_db.get_name(application["user_id"])
            if not access_name:
                return
            application_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            status = "Принят" if application["status"] == "accepted" else "Отклонен"
            if application.get("edited") is True:
                status += " (ред.)"
            reason = application.get("reason", "")

            values = [
                [application_time, access_name, application["name"], status, reason]
            ]
        elif range_name == SPREADSHEET_RANGE_LOGS:
            application_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
            status = ""
            reason = ""
            if application.get("status", "") in ["accepted", "declined"]:
                status = "Принят" if application.get("status", "") == "accepted" else "Отклонен"
                if application.get("edited") is True:
                    status += " (ред.)"
                reason = application.get("reason", "")

            values = [
                [application_time, application_id, access_name, job_info, name, gender, phone, age, date_on_object, residence, comment, status, reason]
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
