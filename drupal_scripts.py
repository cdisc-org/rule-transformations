import json
from os import getenv
from typing import Callable, TypedDict
from yaml import Dumper, dump, parser, safe_load, scanner
from requests import get, patch

# The default Dumper does not indent list items.
# VSCode will not allow you to collapse these lists in the yaml editor because they aren't indented.
class IndentedListDumper(Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow=flow, indentless=False)


def get_headers(
    token: str,
) -> TypedDict("Headers", {"Autorization": str, "Accept": str, "Content-Type": str}):
    return {
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
    }


def traverse_json(data, func):
    if isinstance(data, (dict, list)):
        for value in data.values() if isinstance(data, dict) else data:
            traverse_json(value, func)
    func(data)


def space_to_underscore(node):
    if isinstance(node, dict):
        for k, v in [(k, v) for k, v in node.items() if " " in k]:
            node[k.replace(" ", "_")] = v
            del node[k]


def spaces_to_underscores(data):
    traverse_json(data, space_to_underscore)
    return data


def export_json(token: str, path: str, max_rules=None) -> list:
    B2C_BASE_URL = getenv("B2C_BASE_URL")
    rule_ids = get_rule_ids(token)
    rules = []
    for rule_id in rule_ids[:max_rules]:
        rule_json = get(
            f"https://{B2C_BASE_URL}/jsonapi/node/conformance_rule/{rule_id}",
            headers=get_headers(token),
            verify=False,
        ).json()
        try:
            body = rule_json["data"]["attributes"]["body"]["value"]
        except (parser.ParserError, scanner.ScannerError, TypeError) as err:
            print(f"Rule ID:\n{rule_id}\nDrupal Error:\n{err}\n")
            body = ""
        try:
            rule_yaml = safe_load(body)
        except (parser.ParserError, scanner.ScannerError, TypeError) as err:
            print(f"Rule ID:\n{rule_id}\nYAML Parse Error:\n{err}\n")
            rule_yaml = {}
        rules.append(
            {
                "id": rule_json["data"]["id"],
                "changed": rule_json["data"]["attributes"]["changed"].replace(
                    "+00:00", "Z"
                ),
                "content": body,
                "created": rule_json["data"]["attributes"]["created"].replace(
                    "+00:00", "Z"
                ),
                "creator": rule_json["data"]["attributes"][
                    "field_conformance_rule_creator"
                ],
                "isPublished": rule_json["data"]["attributes"]["status"],
                "json": spaces_to_underscores(rule_yaml),
            }
        )
    with open(path, "w") as file:
        json.dump({"rules": rules}, file, ensure_ascii=False, indent=4, sort_keys=True)
    return rules


def get_rule_ids(token: str) -> list[str]:
    B2C_BASE_URL = getenv("B2C_BASE_URL")
    pagination = f"https://{B2C_BASE_URL}/jsonapi/node/conformance_rule?sort=id"
    rule_ids = []
    while pagination:
        rule_json = get(
            pagination,
            headers=get_headers(token),
            verify=False,
        ).json()
        pagination = rule_json["links"].get("next", {}).get("href")
        rule_ids += [rule["id"] for rule in rule_json["data"]]
    return rule_ids


def set_attribute(
    token: str, rule_ids: list[str], attribute_name: str, attribute_value: any
) -> list:
    B2C_BASE_URL = getenv("B2C_BASE_URL")
    responses = []
    for rule_id in rule_ids:
        rule_json = patch(
            f"https://{B2C_BASE_URL}/jsonapi/node/conformance_rule/{rule_id}",
            headers=get_headers(token),
            data=json.dumps(
                {
                    "data": {
                        "id": rule_id,
                        "type": "node--conformance_rule",
                        "attributes": {
                            attribute_name: attribute_value,
                        },
                    },
                }
            ),
            verify=False,
        ).json()
        responses += [rule_json]
    return responses


def transform_rule(
    token: str,
    rule_ids: list[str],
    transformations: list[Callable[[dict], None]],
) -> list:
    B2C_BASE_URL = getenv("B2C_BASE_URL")
    responses = []
    for rule_id in rule_ids:
        rule_json = get(
            f"https://{B2C_BASE_URL}/jsonapi/node/conformance_rule/{rule_id}",
            headers=get_headers(token),
            verify=False,
        ).json()
        try:
            body = rule_json["data"]["attributes"]["body"]["value"]
            rule_yaml = safe_load(body)
            for transformation in transformations:
                transformation(rule_yaml)
            rule_json = patch(
                f"https://{B2C_BASE_URL}/jsonapi/node/conformance_rule/{rule_id}",
                headers={
                    "Authorization": "Bearer " + token,
                    "Accept": "application/vnd.api+json",
                    "Content-Type": "application/vnd.api+json",
                },
                data=json.dumps(
                    {
                        "data": {
                            "id": rule_id,
                            "type": "node--conformance_rule",
                            "attributes": {
                                "body": {
                                    "value": dump(
                                        rule_yaml,
                                        Dumper=IndentedListDumper,
                                    )
                                },
                            },
                        },
                    }
                ),
                verify=False,
            ).json()
            responses += [rule_json]
        except (parser.ParserError, scanner.ScannerError, TypeError) as err:
            responses += [err]
    return responses
