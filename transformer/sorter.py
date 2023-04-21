from typing import Union
import json


def sort_deep(node):
    scalars = {str, int, float, bool}
    objects = {dict}
    arrays = {list, tuple}
    if node is None or type(node) in scalars:
        pass
    if type(node) in objects:
        _sort_obj(node)
    if type(node) in arrays:
        _sort_array(node)
    return node


def _stringify(node):
    return json.dumps(node, sort_keys=True, separators=(",", ":"))


def _sort_array(node: Union[list, tuple]):
    for value in node:
        sort_deep(value)
    node.sort(key=_stringify)


def _sort_obj(node: dict):
    for value in node.values():
        sort_deep(value)
