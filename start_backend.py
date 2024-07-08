import argparse
from kuxov.routes.base import get_backend_app


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host',
                        default='0.0.0.0',
                        type=str)
    parser.add_argument("--port",
                        default=5040,
                        type=int)
    parser.add_argument("--debug",
                        action="store_true")
    args = parser.parse_args()
    return args


def run_backend():
    app = get_backend_app()
    app.run(host="0.0.0.0",
            port=5000)


if __name__ == "__main__":
    run_backend()
