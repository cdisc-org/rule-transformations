from .transformer import Transformer
from .sorter import sort_deep_obj


def format(yaml: dict, rule: dict, transformer: Transformer) -> None:
    """Format YAML"""
    # Handled by the yaml loader


def sort(yaml: dict, rule: dict, transformer: Transformer) -> None:
    """Sort YAML"""
    sort_deep_obj(yaml)


def create_history(yaml: dict, rule: dict, transformer: Transformer) -> None:
    del rule["changed"]
    history = rule.copy()
    del history["id"]
    history = transformer.history_container.create_item(
        history,
        enable_automatic_id_generation=True,
    )
    rule["history"] = [
        {"created": rule["created"], "creator": rule["creator"], "id": history["id"]}
    ]


def all_transformations():
    return [format, sort, create_history]
