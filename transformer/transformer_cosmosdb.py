from itertools import islice
from azure.cosmos import ContainerProxy
from azure.cosmos import CosmosClient
from .transformer import Transformer


class CosmosdbTransformer(Transformer):
    def __init__(self, url: str, key: str, database: str, container: str):
        self.db_container: ContainerProxy = (
            CosmosClient(url, key)
            .get_database_client(database)
            .get_container_client(container)
        )

    def get_rules(self, max_rules=None):
        rules = []
        query = "SELECT * FROM rules order by rules.created"
        for rule in islice(
            self.db_container.query_items(
                query=query, enable_cross_partition_query=True
            ),
            max_rules,
        ):
            rule = {k: v for k, v in rule.items() if not k.startswith("_")}
            rules.append(rule)
        return rules

    def delete_rules(self):
        for rule in self.db_container.read_all_items():
            self.db_container.delete_item(rule, rule["id"])

    def add_rules(self, rules):
        for rule in rules:
            self.db_container.create_item(rule)

    def replace_rule(self, rule):
        self.db_container.replace_item(rule["id"], rule)

    def max_core_id(self):
        query = """
            SELECT VALUE root
            FROM (
            SELECT MAX(rules.json.Core.Id) ?? "CORE-000000"
            AS CoreId
            FROM rules
            WHERE rules.json.Core.Id 
            LIKE "CORE-______"
            ) root
        """
        return next(
            (
                rule["CoreId"]
                for rule in self.db_container.query_items(
                    query=query, enable_cross_partition_query=True
                )
            ),
        )
