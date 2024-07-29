from flask import jsonify, request

from .errors import OK, ERROR, MISSING_PARAMETER_ERROR_API_KEY, MISSING_PARAMETER_ERROR_JOBS
from .utils import describe, print_output_json, check_missing_keys, check_key


def add_jobs_endpoints(app, no_key):
    missing_keys = [
        ("jobs", {"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_JOBS}),
    ]
    if not no_key:
        missing_keys.append(("key", {"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_API_KEY}))

    inputs = {
        "jobs": """[
            {
                "объект": "Восток-Запад СПБ",
                "должность": "Комплектовщик",
                "возраст_от": 18,
                "возраст_до": 45,
                "гражданство": "РФ, РБ, Казахстан, Киргизия",
                "пол": "Мужской",
                "тип_работы": "Вахта",
                "вид_внешности": "славянская и не славянская внешность"
            },
        ]"""
    }
    if not no_key:
        inputs["key"] = "j283fihOP984un93hojse2326LKlekk"

    @app.route('/set_jobs', methods=['POST'])
    @describe(["jobs"],
              name="set jobs list",
              description="""Set jobs list in system""",
              inputs=inputs,
              outputs={
                  "status": OK,
              })
    @check_missing_keys(missing_keys)
    def set_jobs():
        if not no_key:
            if not check_key(request.json.get("key")):
                return jsonify({"status": ERROR,
                                "status_code": MISSING_PARAMETER_ERROR_API_KEY})

        with open('jobs.json', 'w') as f:
            f.write(request.json['jobs'])
        return jsonify({
            "status": OK
        })

    return app
