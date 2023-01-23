from json import dump as dump_json
from typing import Callable
from ruamel.yaml import YAML, parser, scanner
from yaml import safe_load
from .each_deep import each_deep
from io import StringIO
from abc import ABC, abstractmethod


class Transformer(ABC):
    @abstractmethod
    def get_rules(self, max_rules=None):
        pass

    @abstractmethod
    def delete_rules(self):
        pass

    @abstractmethod
    def add_rules(self, rules):
        pass

    @abstractmethod
    def replace_rule(self, rule):
        pass

    @abstractmethod
    def max_core_id(self):
        pass

    @staticmethod
    def replace_rules(from_transformer: "Transformer", to_transformer: "Transformer"):
        to_transformer.delete_rules()
        to_transformer.add_rules(from_transformer.get_rules())

    @staticmethod
    def _spaces_to_underscores(context, path, indexed_path):
        node = context[-1]
        if hasattr(node, "items"):
            for key, value in node.copy().items():
                del node[key]
                node[key.replace(" ", "_")] = value

    @staticmethod
    def spaces_to_underscores(json):
        return each_deep(node=json, after=Transformer._spaces_to_underscores)

    @staticmethod
    def core_id(rule):
        return ((rule.get("json", {}) or {}).get("Core", {}) or {}).get("Id", "") or ""

    def export_json(self, path: str, max_rules=None):
        rules = self.get_rules(max_rules)
        with open(path, "w") as file:
            dump_json(
                {"rules": rules}, file, ensure_ascii=False, indent=4, sort_keys=True
            )
        return rules

    def transform_rule(
        self, yaml_loader: YAML, rule, transformations: list[Callable[[dict], None]]
    ):
        try:
            yaml = yaml_loader.load(rule["content"]) or {}
            for transformation in transformations:
                transformation(yaml, rule, self)
            content = StringIO()
            yaml_loader.dump(
                yaml,
                content,
            )
            rule["content"] = content.getvalue()
            rule["json"] = Transformer.spaces_to_underscores(safe_load(rule["content"]))
            content.close()
        except (scanner.ScannerError, parser.ParserError):
            yaml = {}
            for transformation in transformations:
                transformation(yaml, rule, self)
        self.replace_rule(rule)

    def transform_rules(
        self,
        transformations: list[Callable[[dict], None]],
    ) -> list:
        yaml_loader = YAML()
        yaml_loader.indent(mapping=2, sequence=4, offset=2)
        rules = self.get_rules()
        for rule in rules:
            self.transform_rule(yaml_loader, rule, transformations)
        return rules

    def next_core_id(self):
        return f"CORE-{(int(self.max_core_id()[-6:])+1):06}"
