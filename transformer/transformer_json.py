from json import dump, load
from re import fullmatch
from .transformer import Transformer
from pathlib import Path


class JSONTransformer(Transformer):
    def __init__(self, path: str):
        self.path = Path(path)

    def _load(self):
        return [load(open(file, "r")) for file in self.path.glob("*.json")]

    def _dump(self, rules):
        for rule in rules:
            with open(
                self.path.joinpath(f"{rule.get('id', Transformer.core_id(rule))}.json"),
                "w",
            ) as f:
                dump(rule, fp=f, indent=2)

    def get_rules(self, max_rules=None):
        return sorted(self._load(), key=lambda rule: rule["created"])[0:max_rules]

    def delete_rules(self):
        for f in self.path.glob("*.json"):
            f.unlink()

    def add_rules(self, rules):
        self._dump(rules)

    def replace_rule(self, rule):
        self._dump([rule])

    def max_core_id(self):
        return sorted(
            [
                Transformer.core_id(rule)
                if fullmatch(r"CORE-.{6}", Transformer.core_id(rule))
                else "CORE-000000"
                for rule in self._load()
            ],
            reverse=True,
        )[-1]
