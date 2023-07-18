from typing import Union
from ruamel.yaml import CommentedMap
from collections import OrderedDict
import json


def sort_deep_array(node):
    scalars = {str, int, float, bool}
    objects = {dict, CommentedMap}
    arrays = {list, tuple}
    if node is None or type(node) in scalars:
        pass
    if type(node) in objects:
        _sort_obj_values(node)
    if type(node) in arrays:
        _sort_array(node)
    return node


def sort_deep_obj(node):
    scalars = {str, int, float, bool}
    objects = {dict, CommentedMap}
    arrays = {list, tuple}
    if node is None or type(node) in scalars:
        pass
    if type(node) in objects:
        _sort_obj(node)
    if type(node) in arrays:
        _sort_array_values(node)
    return node


def _stringify(node):
    return json.dumps(node, sort_keys=True, separators=(",", ":"))


def _sort_array(node: Union[list, tuple]):
    for value in node:
        sort_deep_array(value)
    node.sort(key=_stringify)


def _sort_array_values(node: Union[list, tuple]):
    for value in node:
        sort_deep_obj(value)


def _sort_obj(node: OrderedDict):
    for value in node.values():
        sort_deep_obj(value)
    for key in sorted(node.keys()):
        node.move_to_end(key)


def _sort_obj_values(node: dict):
    for value in node.values():
        sort_deep_array(value)
