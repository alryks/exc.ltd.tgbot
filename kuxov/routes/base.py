import os
from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger

from .access import add_access_endpoints
from .apps import add_apps_endpoints
# from ..utils import CustomJSONEncoder
# from ..settings import SECRET
from .jobs import add_jobs_endpoints
from .utils import CustomJSONEncoder


def create_app():
    app = Flask("Kuxov")
    app.json_encoder = CustomJSONEncoder
    app.config['JSON_AS_ASCII'] = False
    # app.config["SECRET_KEY"] = SECRET
    Swagger(app)

    @app.route("/api/version", methods=["GET"])
    def version():
        return jsonify({'version': '0.0.1'})

    return app


def get_backend_app():
    app = create_app()
    app = add_jobs_endpoints(app)
    app = add_apps_endpoints(app)
    app = add_access_endpoints(app)
    return app
