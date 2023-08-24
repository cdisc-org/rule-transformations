from typing import Callable
from ruamel.yaml import YAML, parser, scanner, safe_load
import yaml
from .each_deep import each_deep
from io import StringIO
from abc import ABC, abstractmethod
from difflib import SequenceMatcher
from collections import defaultdict
from .sorter import sort_deep_array


class Transformer(ABC):
    @abstractmethod
    def get_rules(self, max_rules=None):
        pass

    @abstractmethod
    def get_rule(self, uuid: str):
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

    @abstractmethod
    def get_ids(self):
        pass

    @abstractmethod
    def get_rules_list(self):
        pass

    @staticmethod
    def replace_rules(from_transformer: "Transformer", to_transformer: "Transformer"):
        to_transformer.delete_rules()
        to_transformer.add_rules(from_transformer.get_rules())

    @staticmethod
    def _get_id_to_rule(rules) -> dict:
        return {rule["id"]: rule for rule in rules}

    @staticmethod
    def merge_rules(
        from_transformer: "Transformer",
        to_transformer: "Transformer",
        match: Callable[[dict, "Transformer"], dict],
        transformations: list[Callable[[dict, dict], None]],
    ):
        # TODO: this should be part of init?
        yaml_loader = YAML()
        yaml_loader.indent(mapping=2, sequence=4, offset=2)
        for from_rule in from_transformer.get_rules():
            to_rule = match(from_rule, to_transformer)
            if to_rule:
                to_transformer.transform_rule(yaml_loader, to_rule, transformations)

    @staticmethod
    def _get_opcodes(base: str, comp: str) -> list[dict]:
        diffs = []
        for op, base1, base2, comp1, comp2 in SequenceMatcher(
            None,
            base,
            comp,
            False,
        ).get_opcodes():
            base_substring = base[base1:base2]
            comp_substring = comp[comp1:comp2]
            if op == "delete":
                diffs.append({"op": "remove", "value": base_substring})
            if op == "insert":
                diffs.append({"op": "add", "value": comp_substring})
            if op == "replace":
                diffs.append(
                    {
                        "op": "replace",
                        "value_base": base_substring,
                        "value_comp": comp_substring,
                    }
                )
        return diffs

    @staticmethod
    def diff_rules(base: "Transformer", comp: "Transformer"):
        json_adds = []
        yaml_adds = []
        json_removes = []
        yaml_removes = []
        json_diffs = defaultdict(list)
        yaml_diffs = defaultdict(list)
        base_rules = Transformer._get_id_to_rule(sort_deep_array(base.get_rules()))
        comp_rules = Transformer._get_id_to_rule(sort_deep_array(comp.get_rules()))
        base_ids = {*base_rules.keys()}
        comp_ids = {*comp_rules.keys()}
        for uuid in sorted(base_ids - comp_ids):
            base_rule_json = base_rules[uuid].get("json")
            base_rule_yaml = yaml.dump(base_rule_json, sort_keys=True)
            json_removes.append(f"id: {uuid}\n{base_rule_yaml}")
            yaml_removes.append(f"id: {uuid}\n{base_rules[uuid].get('content')}")
        for uuid in sorted(comp_ids - base_ids):
            comp_rule_json = comp_rules[uuid].get("json")
            comp_rule_yaml = yaml.dump(comp_rule_json, sort_keys=True)
            json_adds.append(f"id: {uuid}\n{comp_rule_yaml}")
            yaml_adds.append(f"id: {uuid}\n{comp_rules[uuid].get('content')}")
        for uuid in sorted(comp_ids.intersection(base_ids)):
            base_rule_json = base_rules[uuid].get("json")
            comp_rule_json = comp_rules[uuid].get("json")
            base_rule_yaml = yaml.dump(base_rule_json, sort_keys=True)
            comp_rule_yaml = yaml.dump(comp_rule_json, sort_keys=True)
            json_diffs[uuid] = Transformer._get_opcodes(base_rule_yaml, comp_rule_yaml)
            yaml_diffs[uuid] = Transformer._get_opcodes(
                base_rules[uuid].get("content"), comp_rules[uuid].get("content")
            )
        return {
            "json": {"adds": json_adds, "removes": json_removes, "diffs": json_diffs},
            "yaml": {"adds": yaml_adds, "removes": yaml_removes, "diffs": yaml_diffs},
        }

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

    @staticmethod
    def yaml_to_string(rule_yaml):
        yaml_loader = YAML()
        yaml_loader.indent(mapping=2, sequence=4, offset=2)
        content = StringIO()
        yaml_loader.dump(
            rule_yaml,
            content,
        )
        value = content.getvalue()
        content.close()
        return value

    def transform_rule(
        self, yaml_loader: YAML, rule, transformations: list[Callable[[dict], None]]
    ):
        try:
            rule_yaml = yaml_loader.load(rule["content"]) or {}
            for transformation in transformations:
                transformation(rule_yaml, rule, self)
            rule["content"] = Transformer.yaml_to_string(rule_yaml)
            rule["json"] = Transformer.spaces_to_underscores(safe_load(rule["content"]))
        except (scanner.ScannerError, parser.ParserError):
            rule_yaml = {}
            for transformation in transformations:
                transformation(rule_yaml, rule, self)
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

    @staticmethod
    def _filter_dict(rule: dict, criteria):
        return {k: v for k, v in rule.items() if criteria(k, v)}

    def get_rules_csv(self):
        return self.get_rules_list()
