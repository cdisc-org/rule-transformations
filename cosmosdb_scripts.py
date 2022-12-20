from itertools import islice
from json import dump as dump_json
from typing import Callable
from azure.cosmos import ContainerProxy
from ruamel.yaml import YAML
from azure.cosmos import CosmosClient
from each_deep import each_deep
from io import StringIO
from copy import deepcopy


class CosmosdbTransformer:
    def __init__(self, url: str, key: str, database: str, container: str):
        self.db_container: ContainerProxy = (
            CosmosClient(url, key)
            .get_database_client(database)
            .get_container_client(container)
        )

    def export_json(self, path: str, max_rules=None):
        rules = self.get_rules(max_rules)
        with open(path, "w") as file:
            dump_json(
                {"rules": rules}, file, ensure_ascii=False, indent=4, sort_keys=True
            )
        return rules

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

    @staticmethod
    def replace_rules(
        from_container: "CosmosdbTransformer", to_container: "CosmosdbTransformer"
    ):
        to_container.delete_rules()
        to_container.add_rules(from_container.get_rules())

    def transform_rules(
        self,
        transformations: list[Callable[[dict], None]],
    ) -> list:
        rules = self.get_rules()
        for rule in rules:
            for transformation in transformations:
                transformation(rule)
            self.db_container.replace_item(rule["id"], rule)
        return rules

    @staticmethod
    def _spaces_to_underscores(context, path, indexed_path):
        node = context[-1]
        if hasattr(node, "items"):
            for key, value in node.copy().items():
                del node[key]
                node[key.replace(" ", "_")] = value

    @staticmethod
    def spaces_to_underscores(json):
        return each_deep(node=json, after=CosmosdbTransformer._spaces_to_underscores)

    def transform_yaml(
        self,
        transformations: list[Callable[[dict], None]],
    ) -> list:
        yaml_loader = YAML()
        yaml_loader.indent(mapping=2, sequence=4, offset=2)
        rules = self.get_rules()
        for rule in rules:
            yaml = yaml_loader.load(rule["content"])
            for transformation in transformations:
                transformation(yaml, rule, self)
            rule["json"] = CosmosdbTransformer.spaces_to_underscores(deepcopy(yaml))
            content = StringIO()
            yaml_loader.dump(
                yaml,
                content,
            )
            rule["content"] = content.getvalue()
            content.close()
            self.db_container.replace_item(rule["id"], rule)
        return rules

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

    def next_core_id(self):
        return f"CORE-{(int(self.max_core_id()[-6:])+1):06}"
