import argparse
import requests


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("application_id")
    parser.add_argument("status",
                        choices=["accepted", "declined"])
    parser.add_argument("--reason", default="")
    args = parser.parse_args()
    return args


def send_jobs(application_id,
              status: str,
              reason: str = ""):
    print(requests.post('http://213.219.215.209:6250/mark_app', json={
        "application_id": application_id,
        "status": status,
        "reason": reason
    }).json())


if __name__ == '__main__':
    send_jobs(**vars(parse_args()))
