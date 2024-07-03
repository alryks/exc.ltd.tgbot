import argparse
import requests


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    return args


def send_jobs(path):
    with open(path, 'r') as f:
        jobs_content = f.read()
    print(requests.post('http://213.219.215.209:6250/set_jobs', json={
        "jobs": jobs_content
    }).json())


if __name__ == '__main__':
    send_jobs(**vars(parse_args()))
