from flask import jsonify, request
import json
import os

from .errors import OK, ERROR, MISSING_PARAMETER_ERROR_API_KEY, MISSING_PARAMETER_ERROR_JOBS
from .utils import describe, print_output_json, check_missing_keys, check_key


def add_jobs_endpoints(app, no_key):
    @app.route('/set_jobs', methods=['POST'])
    @describe(["jobs"],
              name="set jobs list",
              description="""Set jobs list in system""",
              inputs={
                  "jobs": [
                      {
                          "объект": "Восток-Запад СПБ",
                          "должность": "Комплектовщик",
                          "возраст_от": 18,
                          "возраст_до": 45,
                          "гражданство": "РФ, РБ, Казахстан, Киргизия",
                          "пол": "Мужской",
                          "тип_работы": "Вахта",
                          "вид_внешности": "славянская и не славянская внешность",
                          "удаленный_подбор": True
                      }
                  ]
              },
              outputs={
                  "status": OK,
              })
    @check_missing_keys(
        [("jobs", {"status": ERROR, "status_code": MISSING_PARAMETER_ERROR_JOBS})]
    )
    def set_jobs():
        if not no_key:
            if not check_key(request.headers.get("X-API-KEY")):
                return jsonify({"status": ERROR,
                                "status_code": MISSING_PARAMETER_ERROR_API_KEY})

        with open('jobs.json', 'w') as f:
            f.write(request.json['jobs'])
        return jsonify({
            "status": OK
        })
        
    @app.route('/get_jobs', methods=['POST'])
    @describe(["jobs"],
              name="get jobs list",
              description="""Get all available jobs in system""",
              inputs={},
              outputs={
                  "status": OK,
                  "jobs": [
                      {
                          "объект": "Восток-Запад СПБ",
                          "должность": "Комплектовщик",
                          "возраст_от": 18,
                          "возраст_до": 45,
                          "гражданство": "РФ, РБ, Казахстан, Киргизия",
                          "пол": "Мужской",
                          "тип_работы": "Вахта",
                          "вид_внешности": "славянская и не славянская внешность",
                          "удаленный_подбор": True
                      }
                  ]
              })
    def get_jobs():
        if not no_key:
            if not check_key(request.headers.get("X-API-KEY")):
                return jsonify({"status": ERROR,
                                "status_code": MISSING_PARAMETER_ERROR_API_KEY})
        
        try:
            if os.path.exists("jobs.json"):
                with open("jobs.json", 'r') as f:
                    jobs_list = json.load(f)
            else:
                from ..assets import JOBS_LIST
                jobs_list = JOBS_LIST
            
            return jsonify({
                "status": OK,
                "jobs": jobs_list
            })
        except Exception as e:
            return jsonify({
                "status": ERROR,
                "error": str(e)
            })

    return app
