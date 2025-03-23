import json
import base64
from datetime import datetime
from flask import jsonify, request
from bson import ObjectId

from .errors import OK, ERROR, MISSING_PARAMETER_ERROR_API_KEY, BAD_API_KEY_ERROR, BAD_APPLICATION_ID_ERROR
from .utils import describe, check_missing_keys, check_key
from ..application import Application
from ..scenario import SPREADSHEET_RANGE_LOGS
from ..db import AccessDb, UsersDb


def add_app_api_endpoints(app, no_key):
    @app.route('/create_app', methods=['POST'])
    @describe(["app_api"],
              name="create application",
              description="""Create a new application""",
              inputs={},
              outputs={
                  "status": OK,
                  "application_id": "6670b8bd7b24be8bc6dc7132"
              })
    def create_app():
        if not no_key:
            try:
                key = request.headers.get("X-API-KEY")
            except:
                return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_API_KEY})

            if not check_key(key):
                return jsonify({"status": ERROR, "status_code": BAD_API_KEY_ERROR})

        application = Application.new()
        
        return jsonify({
            "status": OK,
            "application_id": str(application.id)
        })

    @app.route('/add_app_photo', methods=['POST'])
    @describe(["app_api"],
              name="add application photo",
              description="""Add photo to an application""",
              inputs={
                  "application_id": "6670b8bd7b24be8bc6dc7132",
                  "photo": "base64 encoded image data"
              },
              outputs={
                  "status": OK
              })
    @check_missing_keys(
        [
            ("application_id", {"status": ERROR, "status_code": "missing_parameter_error_application_id"}),
            ("photo", {"status": ERROR, "status_code": "missing_parameter_error_photo"})
        ],
    )
    def add_app_photo():
        if not no_key:
            try:
                key = request.headers.get("X-API-KEY")
            except:
                return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_API_KEY})

            if not check_key(key):
                return jsonify({"status": ERROR, "status_code": BAD_API_KEY_ERROR})

        try:
            application_id = request.json["application_id"]
            application = Application(application_id)
        except:
            return jsonify({"status": ERROR, "status_code": BAD_APPLICATION_ID_ERROR})

        try:
            # Декодируем фото из base64
            photo_base64 = request.json["photo"]
            photo_content = base64.b64decode(photo_base64)
            
            # Добавляем фото к анкете
            application.add_passport_photo(photo_content=photo_content)
            application.add_passport_pdf()
            
            return jsonify({
                "status": OK
            })
        except Exception as e:
            return jsonify({
                "status": ERROR,
                "error": f"Error processing photo: {str(e)}"
            })

    @app.route('/get_app_photo', methods=['POST'])
    @describe(["app_api"],
              name="get application photos as PDF",
              description="""Get application photos as PDF in base64 format""",
              inputs={
                  "application_id": "6670b8bd7b24be8bc6dc7132"
              },
              outputs={
                  "status": OK,
                  "pdf_base64": "base64 encoded PDF data",
                  "pdf_url": "https://cdn.example.com/6670b8bd7b24be8bc6dc7132.pdf"
              })
    @check_missing_keys(
        [("application_id", {"status": ERROR, "status_code": "missing_parameter_error_application_id"})],
    )
    def get_app_photo():
        if not no_key:
            try:
                key = request.headers.get("X-API-KEY")
            except:
                return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_API_KEY})

            if not check_key(key):
                return jsonify({"status": ERROR, "status_code": BAD_API_KEY_ERROR})

        try:
            application_id = request.json["application_id"]
            application = Application(application_id)
        except:
            return jsonify({"status": ERROR, "status_code": BAD_APPLICATION_ID_ERROR})

        try:
            # Убедимся, что PDF существует
            if "photo_pdf" not in application.data or not application.data["photo_pdf"]:
                application.add_passport_pdf()
                
            # Получаем PDF в виде байтов
            pdf_bytes = application.passport_pdf.getvalue()
            
            # Кодируем в base64
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            # Получаем URL для прямого доступа к PDF
            pdf_url = application.passport_pdf_url
            
            return jsonify({
                "status": OK,
                "pdf_base64": pdf_base64,
                "pdf_url": pdf_url
            })
        except Exception as e:
            return jsonify({
                "status": ERROR,
                "error": f"Error getting application PDF: {str(e)}"
            })

    @app.route('/clear_app_photo', methods=['POST'])
    @describe(["app_api"],
              name="clear application photos",
              description="""Clear all photos of an application""",
              inputs={
                  "application_id": "6670b8bd7b24be8bc6dc7132"
              },
              outputs={
                  "status": OK
              })
    @check_missing_keys(
        [("application_id", {"status": ERROR, "status_code": "missing_parameter_error_application_id"})],
    )
    def clear_app_photo():
        if not no_key:
            try:
                key = request.headers.get("X-API-KEY")
            except:
                return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_API_KEY})

            if not check_key(key):
                return jsonify({"status": ERROR, "status_code": BAD_API_KEY_ERROR})

        try:
            application_id = request.json["application_id"]
            application = Application(application_id)
        except:
            return jsonify({"status": ERROR, "status_code": BAD_APPLICATION_ID_ERROR})

        application.delete_passport()

        return jsonify({
            "status": OK
        })

    @app.route('/set_app', methods=['POST'])
    @describe(["app_api"],
              name="set application data",
              description="""Set application data""",
              inputs={
                  "application_id": "6670b8bd7b24be8bc6dc7132",
                  "data": {
                      "name": "Иванов Иван Иванович",
                      "referral": "Петров Петр Петрович",
                      "gender": "Мужской",
                      "phone": "+7 (926) 123-45-67",
                      "age": "1990-01-01",
                      "date_on_object": "2024-05-01",
                      "residence": "Россия",
                      "job": {
                          "объект": "Восток-Запад СПБ",
                          "должность": "Комплектовщик",
                          "возраст_от": 18,
                          "возраст_до": 45,
                          "гражданство": "РФ, РБ, Казахстан, Киргизия",
                          "пол": "Мужской",
                          "тип_работы": "Вахта",
                          "вид_внешности": "славянская и не славянская внешность"
                      },
                      "comment": "Комментарий к анкете",
                      "user_id": 123456789
                  }
              },
              outputs={
                  "status": OK
              })
    @check_missing_keys(
        [
            ("application_id", {"status": ERROR, "status_code": "missing_parameter_error_application_id"}),
            ("data", {"status": ERROR, "status_code": "missing_parameter_error_data"})
        ],
    )
    def set_app():
        if not no_key:
            try:
                key = request.headers.get("X-API-KEY")
            except:
                return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_API_KEY})

            if not check_key(key):
                return jsonify({"status": ERROR, "status_code": BAD_API_KEY_ERROR})

        try:
            application_id = request.json["application_id"]
            application = Application(application_id)
        except:
            return jsonify({"status": ERROR, "status_code": BAD_APPLICATION_ID_ERROR})

        data = request.json["data"]
        
        # Обновляем данные анкеты
        if "name" in data:
            application.set_name(data["name"])
        if "referral" in data:
            application.set_referral(data["referral"])
        if "gender" in data:
            application.set_gender(data["gender"])
        if "phone" in data:
            application.set_phone(data["phone"])
        if "age" in data:
            application.set_age(datetime.strptime(data["age"], "%Y-%m-%d %H:%M:%S"))
        if "date_on_object" in data:
            application.set_date_on_object(datetime.strptime(data["date_on_object"], "%Y-%m-%d %H:%M:%S"))
        if "residence" in data:
            application.set_residence(data["residence"])
        if "job" in data:
            application.set_job(data["job"])
        if "comment" in data:
            application.set_comment(data["comment"])
        if "user_id" in data and "submitted" in data:
            application.save(data["user_id"])
            if application.status:
                application.reset_status()

        return jsonify({
            "status": OK
        })

    @app.route('/get_app', methods=['POST'])
    @describe(["app_api"],
              name="get application data",
              description="""Get application data""",
              inputs={
                  "application_id": "6670b8bd7b24be8bc6dc7132"
              },
              outputs={
                  "status": OK,
                  "data": {
                      "_id": "6670b8bd7b24be8bc6dc7132",
                      "name": "Иванов Иван Иванович",
                      "referral": "Петров Петр Петрович",
                      "gender": "Мужской",
                      "phone": "+7 (926) 123-45-67",
                      "age": "1990-01-01 00:00:00",
                      "date_on_object": "2024-05-01 00:00:00",
                      "residence": "Россия",
                      "job": {
                          "объект": "Восток-Запад СПБ",
                          "должность": "Комплектовщик",
                          "возраст_от": 18,
                          "возраст_до": 45,
                          "гражданство": "РФ, РБ, Казахстан, Киргизия",
                          "пол": "Мужской",
                          "тип_работы": "Вахта",
                          "вид_внешности": "славянская и не славянская внешность"
                      },
                      "comment": "Комментарий к анкете",
                      "photo_ids": [],
                      "photo_pdf": "6670b8bd7b24be8bc6dc7132"
                  }
              })
    @check_missing_keys(
        [("application_id", {"status": ERROR, "status_code": "missing_parameter_error_application_id"})],
    )
    def get_app():
        if not no_key:
            try:
                key = request.headers.get("X-API-KEY")
            except:
                return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_API_KEY})

            if not check_key(key):
                return jsonify({"status": ERROR, "status_code": BAD_API_KEY_ERROR})

        try:
            application_id = request.json["application_id"]
            application = Application(application_id)
        except:
            return jsonify({"status": ERROR, "status_code": BAD_APPLICATION_ID_ERROR})

        app_data = application.data

        return jsonify({
            "status": OK,
            "data": app_data
        })

    @app.route('/delete_app', methods=['POST'])
    @describe(["app_api"],
              name="delete application",
              description="""Delete an application completely""",
              inputs={
                  "application_id": "6670b8bd7b24be8bc6dc7132"
              },
              outputs={
                  "status": OK
              })
    @check_missing_keys(
        [("application_id", {"status": ERROR, "status_code": "missing_parameter_error_application_id"})],
    )
    def delete_app():
        if not no_key:
            try:
                key = request.headers.get("X-API-KEY")
            except:
                return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_API_KEY})

            if not check_key(key):
                return jsonify({"status": ERROR, "status_code": BAD_API_KEY_ERROR})

        try:
            application_id = request.json["application_id"]
            application = Application(application_id)
        except:
            return jsonify({"status": ERROR, "status_code": BAD_APPLICATION_ID_ERROR})

        # Удаляем анкету
        application.delete()

        return jsonify({
            "status": OK
        })

    return app 