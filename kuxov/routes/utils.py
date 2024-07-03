import json
import sys
from datetime import datetime
import uuid
from functools import wraps
from time import time

from bson import ObjectId
from flask import request, jsonify, Response


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def check_missing_keys(keys_and_errors,
                       method="POST"):
    def check_missing_decorator(fn):
        @wraps(fn)
        def temp(*args, **kwargs):
            params = (request.json if request.is_json else request.form) if method == "POST" else request.args
            print(params, file=sys.stderr)
            for key, error in keys_and_errors:
                if key not in params:
                    if isinstance(error, Response):
                        return error
                    return jsonify(error)
            return fn(*args, **kwargs)

        return temp
    return check_missing_decorator


def print_output_json(marker=None):
    def print_output_json_decorator(fn):
        @wraps(fn)
        def temp(*args, **kwargs):
            t1 = time()
            output: Response = fn(*args, **kwargs)
            t2 = time()
            if marker is not None:
                print(f"MARKER ({t2 - t1:.3f}s)", marker, file=sys.stderr)
            print(output.json, file=sys.stderr)
            return output
        return temp
    return print_output_json_decorator


def timeit(marker=None):
    def timeit_decorator(fn):
        @wraps(fn)
        def temp(*args, **kwargs):
            t1 = time()
            output: Response = fn(*args, **kwargs)
            t2 = time()
            if marker is not None:
                print(f"MARKER ({t2 - t1:.3f}s)", marker, file=sys.stderr)
            return output
        return temp
    return timeit_decorator


from functools import wraps
from typing import Callable
import yaml
from flask import request, jsonify


def make_inputs_description(**kwargs):
    def get_value_type(v):
        if isinstance(v, dict):
            return 'object'
        elif isinstance(v, str):
            return 'string'
        elif isinstance(v, int):
            return 'int'
        elif isinstance(v, float):
            return 'float'
        elif isinstance(v, list):
            return 'object'
        else:
            print(v)
            raise NotImplementedError()

    inputs_description = []
    for name, value in kwargs.items():
        inputs_description.append({
            "name": name,
            "in": "body",
            "schema": {
                "type": get_value_type(value),
                "example": {name: value},
            }
        })

    return inputs_description


def make_method_description(name, description, tags,
                            inputs,
                            outputs):
    operationId = name.replace(' ', '_')
    summary = description
    method_description = {
        "tags": tags,
        "summary": summary,
        "description": description,
        "operationId": operationId,
        "parameters": make_inputs_description(**inputs),
        "responses": {
            200: {
                "description": "",
                "schema": {
                    "example": outputs,
                }
            }
        }
    }

    return f"""
{name}
---
{yaml.dump(method_description)}
"""


def describe(tags=tuple(),
             description="",
             name="",
             inputs={},
             outputs={}):

    def describe_decorator(fn):
        @wraps(fn)
        def temp(*args, **kwargs):
            return fn(*args, **kwargs)

        temp.__doc__ = f"""
        {make_method_description(name=name,
                                 description=description,
                                 tags=tags,
                                 inputs=inputs,
                                 outputs=outputs)}
        """
        return temp
    return describe_decorator
