import json

from flask import jsonify, request

from .errors import OK, ERROR, MISSING_PARAMETER_ERROR_TG_ID, BAD_TG_ID_ERROR, MISSING_PARAMETER_ERROR_STATUS, \
    BAD_APPLICATION_ID_ERROR, MISSING_PARAMETER_ERROR_APPLICATION_ID, BAD_STATUS_ERROR, MISSING_PARAMETER_ERROR_APPS
from .utils import describe, print_output_json, check_missing_keys
from ..application import Application
from ..state import Status


def add_apps_endpoints(app):

    @app.route('/get_apps', methods=['POST'])
    @describe(["apps"],
              name="get_apps",
              description="""Get applications from bot""",
              inputs={
                  "tg_id": 1124414212412421
              },
              outputs={
                  "status": OK,
                  "applications": """[{{'_id': ObjectId('6670b8bd7b24be8bc6dc7132'), 'gender': 'Мужской', 'job': {'объект': 'Восток-Запад СПБ', 'должность': 'Комплект
 вщик', 'возраст_от': 18, 'возраст_до': 45, 'гражданство': 'РФ, РБ, Казахстан, Киргизия', 'пол': 'Мужской', 'тип_работы': 'Вахта', 'вид_вне
 ности': 'славянская и не славянская внешность'}, 'name': 'Каспарьянц Георгий Григорьевич', 'phone': '+79263455382', 'age': datetime.datetime(1997, 11, 19, 0, 0), 'residence': 'Россия', 'photo_ids': []}}, ...]"""
              })
    def get_apps():
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
        return jsonify([Application.remain_basic_job_fields(app.data)
                        for app in apps])

    @app.route('/mark_app', methods=['POST'])
    @describe(["apps"],
              name="mark_app",
              description="""Mark application accept/decline""",
              inputs={
                  "application_id": "_id from previous call",
                  "status": "accepted | declined",
                  "reason": "no reason"
              },
              outputs={
                  "status": OK,
              })
    @check_missing_keys([
        ("application_id", {"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_APPLICATION_ID}),
        ("status", {"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_STATUS}),
    ])
    def mark_app():
        application_id = request.json["application_id"]
        try:
            application = Application(application_id)
        except:
            return jsonify({"status": ERROR, "status_code": BAD_APPLICATION_ID_ERROR})
        try:
            status = Status(request.json["status"])
        except:
            return jsonify({"status": ERROR, "status_code": BAD_STATUS_ERROR})

        reason = str(request.json.get("reason", ""))
        if status == Status.ACCEPTED:
            application.accept(reason=reason)
        elif status == Status.DECLINED:
            application.decline(reason=reason)

        return jsonify({
            "status": OK
        })

    @app.route('/mark_apps', methods=['POST'])
    @describe(["apps"],
              name="mark_apps",
              description="""Mark list of applications accept/decline""",
              inputs={
                  "apps": """
{"application_id": "_id from previous call",
 "status": "accept",
 "reason": "no reason"}
"""
              },
              outputs={
                  "status": OK,
              })
    @check_missing_keys([
        ("apps", {"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_APPS}),
    ])
    def mark_apps():
        apps = request.json["apps"]
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

        return jsonify({
            "status": OK
        })
    return app
