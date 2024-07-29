import argparse
from kuxov.routes.base import get_backend_app


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host',
                        default='0.0.0.0',
                        type=str)
    parser.add_argument("--port",
                        default=8000,
                        type=int)
    parser.add_argument("--debug",
                        action="store_true")
    parser.add_argument("--no-key",
                        action="store_true")

    args = parser.parse_args()
    return args


def run_backend(host: str,
                port: int,
                debug: bool,
                no_key: bool):
    app = get_backend_app(no_key)
    app.run(host=host,
            port=port,
            debug=debug,
            threaded=True)


if __name__ == "__main__":
    run_backend(**vars(parse_args()))