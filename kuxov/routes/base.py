from flask import Flask, jsonify
from flasgger import Swagger

from .access import add_access_endpoints
from .apps import add_apps_endpoints
from .jobs import add_jobs_endpoints
from .facility_bind import add_facility_bind_endpoints
from .utils import CustomJSONEncoder


def create_app():
    app = Flask("Kuxov")
    app.json = CustomJSONEncoder(app)
    app.config['JSON_AS_ASCII'] = False
    # app.config["SECRET_KEY"] = SECRET
    Swagger(app)

    @app.route("/api/version", methods=["GET"])
    def version():
        return jsonify({'version': '0.0.1'})

    return app


def get_backend_app(no_key):
    app = create_app()
    app = add_jobs_endpoints(app, no_key)
    app = add_apps_endpoints(app, no_key)
    app = add_access_endpoints(app, no_key)
    app = add_facility_bind_endpoints(app, no_key)
    return app
