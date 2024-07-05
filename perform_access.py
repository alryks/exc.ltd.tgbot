import argparse
import json

import requests
from pprint import pprint


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("command",
                        choices=["grant", "deny"])
    parser.add_argument("tg_id",
                        type=int)
    parser.add_argument("-o", "--obj",
                        action='append',
                        dest="access_list")
    args = parser.parse_args()
    return args


def perform_access(command, tg_id, access_list):
    print(command, tg_id, access_list)
    data = requests.post(f"http://213.219.215.209:6250/{command}_access",
                         json={
                             "accesses": json.dumps([{"tg_id": tg_id, "access": access_list}])
                         },
                         headers={
                             "Content-Type": "application/json"
                         }).json()
    pprint(data)


if __name__ == '__main__':
    perform_access(**vars(parse_args()))


