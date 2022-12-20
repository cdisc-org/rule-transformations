from auth import get_B2C_token
from os import getenv
from cosmosdb_scripts import CosmosdbTransformer
from transformations import (
    standardize_classes,
    capitalize_datasets_all,
    move_citations,
    move_references,
    move_standards,
    convert_authority_to_list,
    rename_scope,
    condense_rule_types,
    remove_severity,
    add_executability,
    add_status,
    convert_rule_id,
)
from users import get_user_id_from_name, get_users_from_name
from azure.cosmos import CosmosClient
from json import dumps, load

dev_transformer = CosmosdbTransformer(
    getenv("DEV_COSMOS_URL"),
    getenv("DEV_COSMOS_KEY"),
    getenv("DEV_COSMOS_DATABASE"),
    getenv("DEV_COSMOS_CONTAINER"),
)
training_transformer = CosmosdbTransformer(
    getenv("TRAINING_COSMOS_URL"),
    getenv("TRAINING_COSMOS_KEY"),
    getenv("TRAINING_COSMOS_DATABASE"),
    getenv("TRAINING_COSMOS_CONTAINER"),
)
prod_transformer = CosmosdbTransformer(
    getenv("PROD_COSMOS_URL"),
    getenv("PROD_COSMOS_KEY"),
    getenv("PROD_COSMOS_DATABASE"),
    getenv("PROD_COSMOS_CONTAINER"),
)

# replace_rules(from_container=prod_container, to_container=dev_container)

# test rule: CDISC.SENDIG.74

dev_transformer.delete_rules()

with open("./tests/sendig.73.transformed.json") as rule_file:
    rule = load(rule_file)

dev_transformer.add_rules([rule])

dev_transformer.transform_yaml(
    [
        standardize_classes,
        capitalize_datasets_all,
        move_citations,
        move_references,
        convert_authority_to_list,
        move_standards,
        rename_scope,
        condense_rule_types,
        remove_severity,
        add_executability,
        add_status,
        convert_rule_id,
    ],
)

rule["id"] = "809bc8b9-39a9-4e29-bd5a-d9aca518257g"

dev_transformer.add_rules([rule])


# all_users = set()
# bad_users = {}
# rules = get_rules(dev_container)
# for rule in rules:
#     all_users.add(rule["creator"])
# for user in all_users:
#     users = get_users_from_name(user)
#     if len(users) != 1:
#         bad_users[user] = users
# print(dumps(bad_users))

# replace_rules(from_container=prod_container, to_container=dev_container)

# transform_rules(prod_container, [convert_creators])


# rules = export_json(prod_container, f"{getenv('WORKING_DIR')}/rules.json")

# transform_rule([add_json_property])
# rules = export_json(f"{getenv('WORKING_DIR')}/rules.json")


# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# token = get_B2C_token()

# rules = export_json(token, f"{getenv('WORKING_DIR')}/rules.json")
# add_rules(rules)


# resp = set_attribute(token, get_rule_ids(token), "status", False)
# Dev - CDISC.SDTMIG.CG0001
# resp = set_attribute(token, ["95049bd4-3e9e-43b9-b40a-09ab0a4ebae5"], "status", True)
# resp = transform_rule(
#     token,
#     # get_rule_ids(token),
#     ["95049bd4-3e9e-43b9-b40a-09ab0a4ebae5"],
#     [move_check_to_root, convert_reference_to_references, standardize_reference_origin],
# )
# Prod
# resp = set_attribute(token, ["07ab7953-20b0-449e-9c71-ed422dde7a95"], "status", True)
# print(resp)
