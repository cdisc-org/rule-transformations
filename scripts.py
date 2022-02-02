from json import dump, dumps
from os import getenv
from requests import get, patch
from auth import get_token


def get_rule_ids(token):
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


def set_status(token, rule_ids, status):
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
                            "status": status,
                        },
                    },
                }
            ),
            verify=False,
        ).json()
        responses += [json]
    return responses


current_token = get_token()
resp = set_status(current_token, get_rule_ids(current_token), True)
