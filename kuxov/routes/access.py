import json
from flask import jsonify, request
from .errors import OK, ERROR, MISSING_PARAMETER_ERROR_JOBS, MISSING_PARAMETER_ERROR_TG_ID, \
    MISSING_PARAMETER_ERROR_ACCESSES, MISSING_PARAMETER_ERROR_ACCESS
from .utils import describe, print_output_json, check_missing_keys
from ..db import AccessDb


def add_access_endpoints(app):
    access_db = AccessDb()

    @app.route('/grant_access', methods=['POST'])
    @describe(["access"],
              name="grant access",
              description="""Grant access to user""",
              inputs={
                    "accesses": """
[{"tg_id": 1214224, "access": ["Восток-Запад СПБ", "Восток-Север СПБ"]},
 {"tg_id": 1214224, "access": ["all"]}, ]
"""
              },
              outputs={
                  "status": OK,
              })
    @check_missing_keys([
        ("accesses", {"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_ACCESSES}),
    ])
    def grant_access():
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
            access_db.grant_access(access["tg_id"], access["access"])
        return jsonify({
            "status": OK
        })

    @app.route('/deny_access', methods=['POST'])
    @describe(["access"],
              name="deny access",
              description="""Deny access to user""",
              inputs={
                  "accesses": """
    [{"tg_id": 1214224, "access": ["Восток-Запад СПБ", "Восток-Север СПБ"]},
     {"tg_id": 1214224, "access": ["all"]}, ]
    """
              },
              outputs={
                  "status": OK,
              })
    @check_missing_keys([
        ("accesses", {"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_ACCESSES}),
    ])
    def deny_access():
        try:
            accesses = request.json["accesses"]
        except:
            return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_ACCESSES})

        for access in accesses:
            if "tg_id" not in access:
                return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_TG_ID})
            if "access" not in access:
                return jsonify({"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_ACCESS})
            access_db.deny_access(access["tg_id"], access["access"])
        return jsonify({
            "status": OK
        })

    return app
