from itertools import islice
from json import dump
from os import getenv
from typing import Callable
from azure.cosmos import CosmosClient

db_container = (
    CosmosClient(f"https://{getenv('COSMOS_BASE_URL')}", getenv("COSMOS_KEY"))
    .get_database_client(getenv("COSMOS_DATABASE"))
    .get_container_client(getenv("COSMOS_CONTAINER"))
)


def export_json(path: str, max_rules=None):
    rules = get_rules(max_rules)
    with open(path, "w") as file:
        dump({"rules": rules}, file, ensure_ascii=False, indent=4, sort_keys=True)
    return rules


def get_rules(max_rules=None):
    rules = []
    for rule in islice(db_container.read_all_items(), max_rules):
        rule = {k: v for k, v in rule.items() if not k.startswith("_")}
        rules.append(rule)
    return rules


def delete_rules():
    for rule in db_container.read_all_items():
        db_container.delete_item(rule, rule["id"])


def add_rules(rules):
    for rule in rules:
        db_container.create_item(rule)


def transform_yaml(
    transformations: list[Callable[[dict], None]],
) -> list:
    rules = get_rules()
    for rule in rules:
        for transformation in transformations:
            transformation(rule)
        db_container.replace_item(rule["id"], rule)
    return rules
