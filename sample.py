from auth import get_token
from scripts import get_rule_ids, set_attribute, transform_yaml


def update_rule_type(yaml: object) -> object:
    rule_type = yaml["Rule Type"]
    if isinstance(rule_type, dict) and len(rule_type) == 1:
        yaml["Check"] = list(rule_type.values())[0]["Check"]
        yaml["Rule Type"] = list(rule_type.keys())[0]
    return yaml


current_token = get_token()
# resp = set_attribute(current_token, get_rule_ids(current_token), "status", False)
# Dev - CDISC.SDTMIG.CG0001
# resp = set_attribute(current_token, ["95049bd4-3e9e-43b9-b40a-09ab0a4ebae5"], "status", True)
resp = transform_yaml(
    current_token, ["95049bd4-3e9e-43b9-b40a-09ab0a4ebae5"], update_rule_type
)
# Prod
# resp = set_attribute(current_token, ["07ab7953-20b0-449e-9c71-ed422dde7a95"], "status", True)
print(resp)
