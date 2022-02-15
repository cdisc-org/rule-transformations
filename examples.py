from auth import get_token
from scripts import get_rule_ids, set_attribute, transform_yaml
from transformations import (
    convert_reference_to_references,
    move_check_to_root,
    standardize_reference_origin,
)


current_token = get_token()
# resp = set_attribute(current_token, get_rule_ids(current_token), "status", False)
# Dev - CDISC.SDTMIG.CG0001
# resp = set_attribute(current_token, ["95049bd4-3e9e-43b9-b40a-09ab0a4ebae5"], "status", True)
resp = transform_yaml(
    current_token,
    get_rule_ids(current_token),
    # ["95049bd4-3e9e-43b9-b40a-09ab0a4ebae5"],
    [move_check_to_root, convert_reference_to_references, standardize_reference_origin],
)
# Prod
# resp = set_attribute(current_token, ["07ab7953-20b0-449e-9c71-ed422dde7a95"], "status", True)
print(resp)
