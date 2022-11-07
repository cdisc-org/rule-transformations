from users import get_user_id_from_name


def move_check_to_root(yaml: dict) -> None:
    rule_type = yaml.get("Rule Type")
    if isinstance(rule_type, dict) and len(rule_type) == 1:
        yaml["Check"] = list(rule_type.values())[0]["Check"]
        yaml["Rule Type"] = list(rule_type.keys())[0]


def convert_reference_to_references(yaml: dict) -> None:
    if "Reference" in yaml and "References" not in yaml:
        if "Id" in yaml["Reference"] and "Rule Identifier" not in yaml["Reference"]:
            yaml["Reference"]["Rule Identifier"] = {"Id": yaml["Reference"]["Id"]}
            del yaml["Reference"]["Id"]
        yaml["References"] = [yaml["Reference"]]
        del yaml["Reference"]


def standardize_reference_origin(yaml: dict) -> None:
    for reference in yaml.get("References", []):
        if reference.get("Origin") == "SDTM Conformance Rules":
            reference["Origin"] = "SDTM and SDTMIG Conformance Rules"


def add_json_property(rule: dict) -> None:
    if "json" not in rule:
        rule["json"] = {}


def convert_creators(rule: dict) -> None:
    rule["creator"] = {"id": get_user_id_from_name(rule["creator"])["id"]}
