from json import dump, load
from re import fullmatch
from .transformer import Transformer


class FileTransformer(Transformer):
    def __init__(self, path: str):
        self.path = path

    def _load(self):
        with open(self.path, "r") as f:
            return load(f)["rules"]

    def _dump(self, rules):
        with open(self.path, "w") as f:
            dump({"rules": rules}, fp=f, indent=2)

    def get_rules(self, max_rules=None):
        return sorted(self._load(), key=lambda rule: rule["created"])[0:max_rules]

    def delete_rules(self):
        self._dump([])

    def add_rules(self, rules):
        self._dump(self._load() + rules)

    def replace_rule(self, rule):
        self._dump(
            [
                rule if old_rule["id"] == rule["id"] else old_rule
                for old_rule in self._load()
            ]
        )

    @staticmethod
    def _core_id(rule):
        return ((rule.get("json", {}) or {}).get("Core", {}) or {}).get("Id", "") or ""

    def max_core_id(self):
        return sorted(
            [
                FileTransformer._core_id(rule)
                if fullmatch(r"CORE-.{6}", FileTransformer._core_id(rule))
                else "CORE-000000"
                for rule in self._load()
            ],
            reverse=True,
        )[-1]
