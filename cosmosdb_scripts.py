from itertools import islice
from json import dump
from os import getenv
from typing import Callable
from azure.cosmos import ContainerProxy


def export_json(db_container: ContainerProxy, path: str, max_rules=None):
    rules = get_rules(db_container, max_rules)
    with open(path, "w") as file:
        dump({"rules": rules}, file, ensure_ascii=False, indent=4, sort_keys=True)
    return rules


def get_rules(db_container: ContainerProxy, max_rules=None):
    rules = []
    for rule in islice(db_container.read_all_items(), max_rules):
        rule = {k: v for k, v in rule.items() if not k.startswith("_")}
        rules.append(rule)
    return rules


def delete_rules(db_container: ContainerProxy):
    for rule in db_container.read_all_items():
        db_container.delete_item(rule, rule["id"])


def add_rules(db_container: ContainerProxy, rules):
    for rule in rules:
        db_container.create_item(rule)


def replace_rules(from_container: ContainerProxy, to_container: ContainerProxy):
    delete_rules(to_container)
    add_rules(to_container, get_rules(from_container))


def transform_rules(
    db_container: ContainerProxy,
    transformations: list[Callable[[dict], None]],
) -> list:
    rules = get_rules(db_container)
    for rule in rules:
        for transformation in transformations:
            transformation(rule)
        db_container.replace_item(rule["id"], rule)
    return rules
