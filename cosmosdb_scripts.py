from os import getenv
from azure.cosmos import CosmosClient

db_container = (
    CosmosClient(f"https://{getenv('COSMOS_BASE_URL')}", getenv("COSMOS_KEY"))
    .get_database_client(getenv("COSMOS_DATABASE"))
    .get_container_client(getenv("COSMOS_CONTAINER"))
)


def delete_rules():
    for rule in db_container.read_all_items():
        db_container.delete_item(rule, rule["id"])


def add_rules(rules):
    for rule in rules:
        db_container.create_item(rule)
