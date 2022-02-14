from json import dumps
from os import getenv
from typing import Callable
from yaml import safe_dump, safe_load
from requests import get, patch


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
    token: str, rule_ids: list[str], transformation: Callable[[object], object]
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
        body = json["data"]["attributes"]["body"]["value"]
        yaml = safe_load(body)
        transformed = transformation(yaml)
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
                            "body": {"value": safe_dump(transformed)},
                        },
                    },
                }
            ),
            verify=False,
        ).json()
        responses += [json]
    return responses
