import json
from os import getenv
from typing import Callable
from yaml import Dumper, dump, parser, safe_load, scanner
from requests import get, patch

# The default Dumper does not indent list items.
# VSCode will not allow you to collapse these lists in the yaml editor because they aren't indented.
class IndentedListDumper(Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow=flow, indentless=False)


def export_json(token: str, path: str) -> list:
    API_BASE_URL = getenv("API_BASE_URL", None)
    rule_ids = get_rule_ids(token)
    rules = []
    for rule_id in rule_ids:
        rule_json = get(
            f"https://{API_BASE_URL}/jsonapi/node/conformance_rule/{rule_id}",
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/vnd.api+json",
                "Content-Type": "application/vnd.api+json",
            },
            verify=False,
        ).json()
        try:
            body = rule_json["data"]["attributes"]["body"]["value"]
            rule_yaml = safe_load(body)
            rules.append(rule_yaml)
        except (parser.ParserError, scanner.ScannerError, TypeError) as err:
            print(f"Rule ID: {rule_id} Error: {err}")
    with open(path, "w") as file:
        json.dump({"rules": rules}, file, ensure_ascii=False, indent=4, sort_keys=True)
    return rules


def get_rule_ids(token: str) -> list[str]:
    API_BASE_URL = getenv("API_BASE_URL", None)
    pagination = f"https://{API_BASE_URL}/jsonapi/node/conformance_rule?sort=id"
    rule_ids = []
    while pagination:
        rule_json = get(
            pagination,
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/vnd.api+json",
                "Content-Type": "application/vnd.api+json",
            },
            verify=False,
        ).json()
        pagination = rule_json["links"].get("next", {}).get("href")
        rule_ids += [rule["id"] for rule in rule_json["data"]]
    return rule_ids


def set_attribute(
    token: str, rule_ids: list[str], attribute_name: str, attribute_value: any
) -> list:
    API_BASE_URL = getenv("API_BASE_URL", None)
    responses = []
    for rule_id in rule_ids:
        rule_json = patch(
            f"https://{API_BASE_URL}/jsonapi/node/conformance_rule/{rule_id}",
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
                            attribute_name: attribute_value,
                        },
                    },
                }
            ),
            verify=False,
        ).json()
        responses += [rule_json]
    return responses


def transform_yaml(
    token: str,
    rule_ids: list[str],
    transformations: list[Callable[[dict], None]],
) -> list:
    API_BASE_URL = getenv("API_BASE_URL", None)
    responses = []
    for rule_id in rule_ids:
        rule_json = get(
            f"https://{API_BASE_URL}/jsonapi/node/conformance_rule/{rule_id}",
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/vnd.api+json",
                "Content-Type": "application/vnd.api+json",
            },
            verify=False,
        ).json()
        try:
            body = rule_json["data"]["attributes"]["body"]["value"]
            rule_yaml = safe_load(body)
            for transformation in transformations:
                transformation(rule_yaml)
            rule_json = patch(
                f"https://{API_BASE_URL}/jsonapi/node/conformance_rule/{rule_id}",
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
