import json

from flask import jsonify, request

from .errors import OK, ERROR, MISSING_PARAMETER_ERROR_API_KEY, BAD_API_KEY_ERROR, MISSING_PARAMETER_ERROR_TG_ID, BAD_TG_ID_ERROR, MISSING_PARAMETER_ERROR_STATUS, \
    BAD_APPLICATION_ID_ERROR, MISSING_PARAMETER_ERROR_APPLICATION_ID, BAD_STATUS_ERROR, MISSING_PARAMETER_ERROR_APPS
from .utils import describe, print_output_json, check_missing_keys, check_key
from ..utils import update_table
from ..application import Application
from ..state import Status

from kuxov.scenario import SPREADSHEET_RANGE

from kuxov.db import AccessDb, UsersDb


access_db = AccessDb()
users_db = UsersDb()


def add_apps_endpoints(app, no_key):
    @app.route('/get_apps', methods=['POST'])
    @describe(["apps"],
              name="get_apps",
              description="""Get applications from bot""",
              inputs={
                  "tg_id": 1124414212412421,
              },
              outputs={
                  "status": OK,
                  "applications": [{'_id': '6670b8bd7b24be8bc6dc7132',
                                     'gender': 'Мужской',
                                     'job': {'объект': 'Восток-Запад СПБ',
                                             'должность': 'Комплектовщик',
                                             'возраст_от': 18,
                                             'возраст_до': 45,
                                             'гражданство': 'РФ, РБ, Казахстан, Киргизия',
                                             'пол': 'Мужской',
                                             'тип_работы': 'Вахта',
                                             'вид_внешности': 'славянская и не славянская внешность'},
                                     'name': 'Каспарьянц Георгий Григорьевич',
                                     'phone': '+7 (926) 345-53-82',
                                     'age': '1997-11-19 00:00:00',
                                     'date_on_object': '2024-08-08 00:00:00',
                                     'residence': 'Россия',
                                     'photo_ids': [],
                                     'photo_pdf': '6670b8bd7b24be8bc6dc7132',
                                     'comment': 'Комментарий к анкете'}]
              })
    def get_apps():
        if not no_key:
            if not check_key(request.headers.get("X-API-KEY")):
                return jsonify({"status": ERROR,
                                "status_code": BAD_API_KEY_ERROR})

        tg_id = request.json.get("tg_id")
        if tg_id is not None:
            try:
                tg_id = int(tg_id)
            except:
                return jsonify({
                    "status": ERROR,
                    "status_code": BAD_TG_ID_ERROR
                })
        apps = Application.list_not_verified(user_id=tg_id)
        print(apps)
        print(tg_id)
        return jsonify([Application.prepare_for_api(app.data)
                        for app in apps])

    @app.route('/mark_apps', methods=['POST'])
    @describe(["apps"],
              name="mark_apps",
              description="""Mark list of applications accept/decline""",
              inputs={
            "apps": [
                {
                    "application_id": "6670b8bd7b24be8bc6dc7132",
                    "status": "accept",
                    "reason": "no reason"
                },
                {
                    "application_id": "7344fd7a102b6670b8bd7744",
                    "status": "decline",
                    "reason": "duplicate"
                }
            ]
        },
              outputs={
                  "status": OK,
              })
    @check_missing_keys(
        [("apps", {"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_APPS})],
    )
    def mark_apps():
        if not no_key:
            if not check_key(request.headers.get("X-API-KEY")):
                return jsonify({"status": ERROR,
                                "status_code": BAD_API_KEY_ERROR})

        apps = json.loads(request.json["apps"])
        for i, app in enumerate(apps):
            if "application_id" not in app:
                return jsonify({"status": ERROR,
                                "status_code": MISSING_PARAMETER_ERROR_APPLICATION_ID,
                                "application_index": i})
            application_id = app["application_id"]
            try:
                application = Application(application_id)
            except:
                return jsonify({"status": ERROR,
                                "status_code": BAD_APPLICATION_ID_ERROR})

            if "status" not in app:
                return jsonify({"status": ERROR,
                                "status_code": MISSING_PARAMETER_ERROR_STATUS,
                                "application_index": i})

            try:
                status = Status(app["status"])
            except:
                return jsonify({"status": ERROR,
                                "status_code": BAD_STATUS_ERROR})

            reason = str(app.get("reason", ""))
            if status == Status.ACCEPTED:
                application.accept(reason=reason)
            elif status == Status.DECLINED:
                application.decline(reason=reason)

            update_table(SPREADSHEET_RANGE, application, access_db, users_db)

        return jsonify({
            "status": OK
        })
    return app
