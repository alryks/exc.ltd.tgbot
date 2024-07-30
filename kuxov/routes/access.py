import json
from flask import jsonify, request
from .errors import OK, ERROR, MISSING_PARAMETER_ERROR_API_KEY, BAD_API_KEY_ERROR, MISSING_PARAMETER_ERROR_JOBS, MISSING_PARAMETER_ERROR_TG_ID, \
    MISSING_PARAMETER_ERROR_ACCESSES, MISSING_PARAMETER_ERROR_ACCESS, MISSING_PARAMETER_ERROR_NAME
from .utils import describe, print_output_json, check_missing_keys, check_key, set_key
from ..db import AccessDb


def add_access_endpoints(app, no_key):
    access_db = AccessDb()

    @app.route('/grant_access', methods=['POST'])
    @describe(["access"],
              name="grant access",
              description="""Grant access to user""",
              inputs={
                "accesses": [
                    {
                        "tg_id": 1214224,
                        "access": ["Восток-Запад СПБ", "Восток-Север СПБ"],
                        "name": "test"
                    },
                    {
                        "tg_id": 1214224,
                        "access": ["all"],
                        "name": "test"
                    },
                ]
            },
              outputs={
                  "status": OK,
              })
    @check_missing_keys(
        ("accesses", {"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_ACCESSES}),
    )
    def grant_access():
        if not no_key:
            try:
                key = request.headers.get("X-API-KEY")
            except:
                return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_API_KEY})

            if not check_key(key):
                return jsonify({"status": ERROR, "status_code": BAD_API_KEY_ERROR})

        try:
            accesses = request.json["accesses"]
        except:
            return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_ACCESSES})

        access_db.clear()
        for access in accesses:
            if "tg_id" not in access:
                return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_TG_ID})
            if "access" not in access:
                return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_ACCESS})
            if "name" not in access:
                return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_NAME})
            access_db.grant_access(access["tg_id"], access["access"], access["name"])
        return jsonify({
            "status": OK
        })

    if not no_key:
        @app.route('/get_api_key', methods=['POST'])
        @describe(["access"],
                  name="get api key",
                  description="""Get api key""",
                  inputs={},
                  outputs={
                      "status": OK,
                      "key": "j283fihOP984un93hojse2326LKlekk"
                  })
        @check_missing_keys([])
        def get_api_key():
            try:
                key = request.headers.get("X-API-KEY")
            except:
                return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_API_KEY})

            new_key = set_key(key)
            if not new_key:
                return jsonify({"status": ERROR, "status_code": BAD_API_KEY_ERROR})

            return jsonify({
                "status": OK,
                "key": new_key
            })

    return app
