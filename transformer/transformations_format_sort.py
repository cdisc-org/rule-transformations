from .transformer import Transformer
from .sorter import sort_deep_obj


def format(yaml: dict, rule: dict, transformer: Transformer) -> None:
    """Format YAML"""
    # Handled by the yaml loader


def sort(yaml: dict, rule: dict, transformer: Transformer) -> None:
    """Sort YAML"""
    sort_deep_obj(yaml)


def create_history(yaml: dict, rule: dict, transformer: Transformer) -> None:
    rule["history"] = [
        {
            "changed": rule["changed"],
            "content": Transformer.yaml_to_string(yaml),
            "creator": rule["creator"],
        }
    ]


def all_transformations():
    return [format, sort, create_history]
