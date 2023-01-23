from re import fullmatch
from .transformer import Transformer
from pathlib import Path
from yaml import safe_load
from datetime import datetime, timezone


class YAMLTransformer(Transformer):

    yaml_exts = ["*.yml", "*.yaml"]

    def __init__(self, path: str, creator_id: str):
        self.path = Path(path)
        self.creator_id = creator_id

    def _list_files(self):
        return [
            file for ext in YAMLTransformer.yaml_exts for file in self.path.glob(ext)
        ]

    def _load(self):
        return [
            {
                "content": file.read_text(),
                "json": safe_load(file.read_text()),
                "created": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "creator": {"id": self.creator_id},
            }
            for file in self._list_files()
        ]

    def _dump(self, rules):
        for rule in rules:
            filename = f"{Transformer.core_id(rule) or 'Missing Core-Id'}.yml"
            self.path.joinpath(filename).write_text(rule["content"])

    def get_rules(self, max_rules=None):
        return sorted(
            self._load(),
            key=Transformer.core_id,
        )[0:max_rules]

    def delete_rules(self):
        for file in self._list_files():
            file.unlink()

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
