from json import dumps
from os import getenv
from typing import Callable
from yaml import Dumper, dump, parser, safe_load, scanner
from requests import get, patch

# The default Dumper does not indent list items.
# VSCode will not allow you to collapse these lists in the yaml editor because they aren't indented.
class IndentedListDumper(Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow=flow, indentless=False)


def get_rule_ids(token: str) -> list[str]:
    API_BASE_URL = getenv("API_BASE_URL", None)
    pagination = f"https://{API_BASE_URL}/jsonapi/node/conformance_rule?sort=id"
    rule_ids = []
    while pagination:
        json = get(
            pagination,
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/vnd.api+json",
                "Content-Type": "application/vnd.api+json",
            },
            verify=False,
        ).json()
        pagination = json["links"].get("next", {}).get("href")
        rule_ids += [rule["id"] for rule in json["data"]]
    return rule_ids


def set_attribute(
    token: str, rule_ids: list[str], attribute_name: str, attribute_value: any
) -> list:
    API_BASE_URL = getenv("API_BASE_URL", None)
    responses = []
    for rule_id in rule_ids:
        json = patch(
            f"https://{API_BASE_URL}/jsonapi/node/conformance_rule/{rule_id}",
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/vnd.api+json",
                "Content-Type": "application/vnd.api+json",
            },
            data=dumps(
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
        responses += [json]
    return responses


def transform_yaml(
    token: str,
    rule_ids: list[str],
    transformations: list[Callable[[dict], None]],
) -> list:
    API_BASE_URL = getenv("API_BASE_URL", None)
    responses = []
    for rule_id in rule_ids:
        json = get(
            f"https://{API_BASE_URL}/jsonapi/node/conformance_rule/{rule_id}",
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/vnd.api+json",
                "Content-Type": "application/vnd.api+json",
            },
            verify=False,
        ).json()
        try:
            body = json["data"]["attributes"]["body"]["value"]
            rule_yaml = safe_load(body)
            for transformation in transformations:
                transformation(rule_yaml)
            json = patch(
                f"https://{API_BASE_URL}/jsonapi/node/conformance_rule/{rule_id}",
                headers={
                    "Authorization": "Bearer " + token,
                    "Accept": "application/vnd.api+json",
                    "Content-Type": "application/vnd.api+json",
                },
                data=dumps(
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
            responses += [json]
        except (parser.ParserError, scanner.ScannerError, TypeError) as err:
            responses += [err]
    return responses
