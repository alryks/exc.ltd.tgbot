import argparse
import requests
from pprint import pprint


def parse_args():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    return args


def receive_list():
    data = requests.post("http://213.219.215.209:6250/get_apps",
                         json={},
                         headers={
                             "Content-Type": "application/json"
                         }).json()

    pprint(data)


if __name__ == '__main__':
    receive_list(**vars(parse_args()))
