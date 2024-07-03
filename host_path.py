import argparse
from kuxov.cdn import CDN


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    return args


def host_path(path):
    cdn = CDN()
    print(cdn.url_for(cdn.host(path)))


if __name__ == "__main__":
    host_path(**vars(parse_args()))
