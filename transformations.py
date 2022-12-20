from users import get_user_id_from_name
from cosmosdb_scripts import CosmosdbTransformer
from copy import deepcopy


def move_check_to_root(yaml: dict) -> None:
    rule_type = yaml.get("Rule Type")
    if isinstance(rule_type, dict) and len(rule_type) == 1:
        yaml["Check"] = list(rule_type.values())[0]["Check"]
        yaml["Rule Type"] = list(rule_type.keys())[0]


def convert_reference_to_references(yaml: dict) -> None:
    if "Reference" in yaml and "References" not in yaml:
        if "Id" in yaml["Reference"] and "Rule Identifier" not in yaml["Reference"]:
            yaml["Reference"]["Rule Identifier"] = {"Id": yaml["Reference"].pop("Id")}
        yaml["References"] = [yaml.pop("Reference")]


def standardize_reference_origin(yaml: dict) -> None:
    for reference in yaml.get("References", []):
        if reference.get("Origin") == "SDTM Conformance Rules":
            reference["Origin"] = "SDTM and SDTMIG Conformance Rules"


def add_json_property(rule: dict) -> None:
    if "json" not in rule:
        rule["json"] = {}


def convert_creators(rule: dict) -> None:
    rule["creator"] = {"id": get_user_id_from_name(rule["creator"])["id"]}


# CROG transformations


def _standardize_classes(classes: list[str]) -> None:
    for i, item in enumerate(classes):
        classes[i] = item.upper()


def standardize_classes(
    yaml: dict, rule: dict, transformer: CosmosdbTransformer
) -> None:
    """Use standard terminology (https://library.cdisc.org/browser/#/mdr/ct/2022-09-30/packages/define-xmlct-2022-09-30/codelists/C103329). For the current classes, this just means they will need to be converted to all-caps.
    `Scopes.Classes.Include`
    `Scopes.Classes.Exclude`
    """
    _standardize_classes(yaml.get("Scopes", {}).get("Classes", {}).get("Include", []))
    _standardize_classes(yaml.get("Scopes", {}).get("Classes", {}).get("Exclude", []))


def _capitalize_datasets_all_dict(datasets: dict, key: str):
    for item in datasets:
        if item.get(key) == "All":
            item[key] = "ALL"


def _capitalize_datasets_all_list(datasets: list[str]):
    for i, item in enumerate(datasets):
        if item == "All":
            datasets[i] = "ALL"


def capitalize_datasets_all(
    yaml: dict, rule: dict, transformer: CosmosdbTransformer
) -> None:
    """Change "All" keyword to "ALL"
    `Match Datasets.Name`
    `Operations.domain`
    `Scopes.Datasets.Include`
    `Scopes.Datasets.Exclude`
    `Scopes.Domains.Include`
    `Scopes.Domains.Exclude`
    """
    _capitalize_datasets_all_dict(yaml.get("Match Datasets", []), "Name")
    _capitalize_datasets_all_dict(yaml.get("Operations", []), "domain")
    _capitalize_datasets_all_list(
        yaml.get("Scopes", {}).get("Datasets", {}).get("Include", [])
    )
    _capitalize_datasets_all_list(
        yaml.get("Scopes", {}).get("Datasets", {}).get("Exclude", [])
    )
    _capitalize_datasets_all_list(
        yaml.get("Scopes", {}).get("Domains", {}).get("Include", [])
    )
    _capitalize_datasets_all_list(
        yaml.get("Scopes", {}).get("Domains", {}).get("Exclude", [])
    )


def _multi_and_unequal(l1: list, l2: list):
    return len(l1) > 1 and len(l2) > 1 and len(l1) != len(l2)


def move_citations(yaml: dict, rule: dict, transformer: CosmosdbTransformer) -> None:
    """Move to be a property of `Authority.Standards.References` items
    `Citations`
    """
    references = yaml.get("References", [])
    citations = yaml.pop("Citations", [])
    if _multi_and_unequal(references, citations):
        raise Exception(
            f"References and Citations counts don't match for: {rule['id']}"
        )
    elif not citations:
        return
    elif len(citations) == 1 and len(references) == 0:
        yaml["References"] = [{"Citations": citations}]
    elif len(citations) == 1 and len(references) > 0:
        references[0]["Citations"] = citations
    elif len(citations) > 1 and len(references) <= 1:
        yaml["References"] = [
            {**deepcopy(references.get(0, {})), "Citations": [citation]}
            for citation in citations
        ]
    elif len(citations) > 1 and len(references) > 1:
        for reference, citation in zip(references, citations):
            reference["Citations"] = citation


def move_references(yaml: dict, rule: dict, transformer: CosmosdbTransformer) -> None:
    """Move to be a property of `Authority.Standards` items
    `References`
    """
    standards = yaml.get("Scopes", {}).get("Standards", [])
    references = yaml.pop("References", [])
    if _multi_and_unequal(standards, references):
        raise Exception(
            f"Standards and References counts don't match for: {rule['id']}"
        )
    elif not references:
        return
    elif len(references) == 1 and len(standards) == 0:
        yaml["Scopes"] = {
            **yaml.get("Scopes", {}),
            "Standards": [{"References": references}],
        }
    elif len(references) == 1 and len(standards) > 0:
        standards[0]["References"] = references
    elif len(references) > 1 and len(standards) <= 1:
        yaml["Scopes"] = {
            **yaml.get("Scopes", {}),
            "Standards": [
                {**deepcopy(standards.get(0, {})), "References": [reference]}
                for reference in references
            ],
        }
    elif len(references) > 1 and len(standards) > 1:
        for standard, reference in zip(standards, references):
            standard["References"] = reference


def convert_authority_to_list(
    yaml: dict, rule: dict, transformer: CosmosdbTransformer
) -> None:
    """Convert value from object to list of objects
    `Authority`
    """
    authority = yaml.get("Authority")
    if authority and not (isinstance(authority, list)):
        yaml["Authority"] = [authority]


def move_standards(yaml: dict, rule: dict, transformer: CosmosdbTransformer) -> None:
    """Move to be a property of `Authority` items
    `Scopes.Standards`
    """
    standards = yaml.get("Scopes", {}).pop("Standards", None)
    if standards is not None:
        yaml["Authority"] = {
            **next(iter(yaml.get("Authority", [])), {}),
            "Standards": standards,
        }


def rename_scope(yaml: dict, rule: dict, transformer: CosmosdbTransformer) -> None:
    """Rename to `Scope`
    `Scopes`
    """
    if yaml.get("Scopes"):
        yaml["Scope"] = yaml.pop("Scopes")


def condense_rule_types(
    yaml: dict, rule: dict, transformer: CosmosdbTransformer
) -> None:
    """Replace the following Rule Types with new Rule Type `Record Data`:
    - `Consistency`
    - `Data Domain Aggregation`
    - `Data Pattern and Format`
    - `Date Arithmetic`
    - `External Dictionaries`
    - `Functional Dependency`
    - `Populated Values`
    - `Range & Limit`
    - `Relationship Integrity Check`
    - `Uniqueness`
    - `Value Presence`
    - `Variable Length`
    - `Variable Order`
    - `Variable Presence`
    `Rule Type`
    """
    old_rule_types = {
        "Consistency",
        "Data Domain Aggregation",
        "Data Pattern and Format",
        "Date Arithmetic",
        "External Dictionaries",
        "Functional Dependency",
        "Populated Values",
        "Range & Limit",
        "Relationship Integrity Check",
        "Uniqueness",
        "Value Presence",
        "Variable Length",
        "Variable Order",
        "Variable Presence",
    }
    if yaml.get("Rule Type", "") in old_rule_types:
        yaml["Rule Type"] = "Record Data"


def remove_severity(yaml: dict, rule: dict, transformer: CosmosdbTransformer) -> None:
    """`Severity` is removed from the root and is now an optional property under `Authority.Standards.References` for some authorities, like PMDA.
    `Severity`
    """
    yaml.pop("Severity", None)


def add_executability(yaml: dict, rule: dict, transformer: CosmosdbTransformer) -> None:
    """Added with following options:
    - `Fully Executable`
    - `Partially Executable - Possible Overreporting`
    - `Partially Executable - Possible Underreporting`
    `Executability`
    """
    pass  # No transformation required


def add_status(yaml: dict, rule: dict, transformer: CosmosdbTransformer) -> None:
    """
    Added with following options:
    - `Draft`
    - `Published`
    `Core.Status`
    """
    isPublished = rule.pop("isPublished", None)
    if isPublished is not None:
        yaml["Core"] = {
            **yaml.get("Core", {}),
            "Status": "Published" if isPublished else "Draft",
        }


def convert_rule_id(yaml: dict, rule: dict, transformer: CosmosdbTransformer) -> None:
    """
    Core id pattern is changing
    - from: `CDISC.<STANDARD NAME>.<ORIGINAL ID>` aka `CDISC.SDTMIG.CG0001`
    - to: a universal id like `CORE-000001`
    `Core.Id`
    """
    yaml["Core"] = {
        **yaml.get("Core", {}),
        "Id": transformer.next_core_id(),
    }
