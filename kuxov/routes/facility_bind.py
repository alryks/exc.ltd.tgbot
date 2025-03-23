import json
from flask import jsonify, request
from .errors import OK, ERROR, MISSING_PARAMETER_ERROR_API_KEY, BAD_API_KEY_ERROR, MISSING_PARAMETER_ERROR_BINDS
from .utils import describe, check_missing_keys, check_key
from ..db import FacilityBindDb


def add_facility_bind_endpoints(app, no_key):
    facility_bind_db = FacilityBindDb()

    @app.route('/set_facility_binds', methods=['POST'])
    @describe(["facility_bind"],
              name="set facility binds",
              description="""Set facility binds in system""",
              inputs={
                  "binds": [
                      {
                          "name": "Иванов Иван Иванович",
                          "facility": "Восток-Запад СПБ"
                      }
                  ]
              },
              outputs={
                  "status": OK,
              })
    @check_missing_keys(
        [("binds", {"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_BINDS})],
    )
    def set_facility_binds():
        if not no_key:
            try:
                key = request.headers.get("X-API-KEY")
            except:
                return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_API_KEY})

            if not check_key(key):
                return jsonify({"status": ERROR, "status_code": BAD_API_KEY_ERROR})

        try:
            binds = request.json["binds"]
        except:
            return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_BINDS})

        facility_bind_db.clear()
        for bind in binds:
            if "name" not in bind or "facility" not in bind:
                return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_BINDS})
            facility_bind_db.add_bind(bind["name"], bind["facility"])

        return jsonify({
            "status": OK
        })

    @app.route('/get_facility_binds', methods=['POST'])
    @describe(["facility_bind"],
              name="get facility binds",
              description="""Get all facility binds from system""",
              inputs={},
              outputs={
                  "status": OK,
                  "binds": [
                      {
                          "name": "Иванов Иван Иванович",
                          "facility": "Восток-Запад СПБ"
                      }
                  ]
              })
    def get_facility_binds():
        if not no_key:
            try:
                key = request.headers.get("X-API-KEY")
            except:
                return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_API_KEY})

            if not check_key(key):
                return jsonify({"status": ERROR, "status_code": BAD_API_KEY_ERROR})

        try:
            # Получаем все привязки из базы данных
            binds = facility_bind_db.get_all_binds()
            
            # Форматируем данные для ответа
            formatted_binds = []
            for bind in binds:
                formatted_binds.append({
                    "name": bind["name"],
                    "facility": bind["facility"]
                })
                
            return jsonify({
                "status": OK,
                "binds": formatted_binds
            })
        except Exception as e:
            return jsonify({
                "status": ERROR,
                "error": str(e)
            })

    return app 