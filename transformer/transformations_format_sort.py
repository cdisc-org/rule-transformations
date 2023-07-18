from .transformer import Transformer
from .sorter import sort_deep_obj


def format(yaml: dict, rule: dict, transformer: Transformer) -> None:
    """Format YAML"""
    # Handled by the yaml loader


def sort(yaml: dict, rule: dict, transformer: Transformer) -> None:
    """Sort YAML"""
    sort_deep_obj(yaml)


def all_transformations():
    return [
        format,
        sort,
    ]
