from itertools import islice
from azure.cosmos import ContainerProxy
from azure.cosmos import CosmosClient
from .transformer import Transformer


class CosmosdbTransformer(Transformer):
    def __init__(self, url: str, key: str, database: str, container: str):
        self.db_container: ContainerProxy = (
            CosmosClient(url, key)
            .get_database_client(database)
            .get_container_client(container)
        )

    def get_rules(self, max_rules=None):
        rules = []
        query = "SELECT * FROM rules order by rules.created"
        for rule in islice(
            self.db_container.query_items(
                query=query, enable_cross_partition_query=True
            ),
            max_rules,
        ):
            rule = CosmosdbTransformer._remove_meta(rule)
            rules.append(rule)
        return rules

    def get_rule(self, uuid):
        query = "SELECT * FROM rules WHERE rules.id = @id"
        params = [{"name": "@id", "value": uuid}]
        return next(
            (
                CosmosdbTransformer._remove_meta(rule)
                for rule in self.db_container.query_items(
                    query=query, enable_cross_partition_query=True, parameters=params
                )
            ),
        )

    def delete_rules(self):
        for rule in self.db_container.read_all_items():
            self.db_container.delete_item(rule, rule["id"])

    def add_rules(self, rules):
        for rule in rules:
            self.db_container.create_item(rule)

    def replace_rule(self, rule):
        self.db_container.replace_item(rule["id"], rule)

    def max_core_id(self):
        query = """
            SELECT VALUE root
            FROM (
            SELECT MAX(rules.json.Core.Id) ?? "CORE-000000"
            AS CoreId
            FROM rules
            WHERE rules.json.Core.Id 
            LIKE "CORE-______"
            ) root
        """
        return next(
            (
                rule["CoreId"]
                for rule in self.db_container.query_items(
                    query=query, enable_cross_partition_query=True
                )
            ),
        )

    def get_ids(self):
        query = """
            SELECT VALUE rules.id
            FROM rules
            ORDER BY rules.id
        """
        return {
            *self.db_container.query_items(
                query=query, enable_cross_partition_query=True
            )
        }

    @staticmethod
    def _remove_meta(rule: dict):
        return Transformer._filter_dict(rule, lambda k, _: not k.startswith("_"))

    def get_rules_list(self):
        rules = []
        query = """
            SELECT DISTINCT
            Rule['Core']['Id'] ?? null as 'CORE-ID',
            udf.TO_STRING(ARRAY(SELECT DISTINCT VALUE Reference['Rule_Identifier']['Id'] FROM Authority IN Rule['Authorities'] JOIN Standard IN Authority['Standards'] JOIN Reference IN Standard['References'])) as 'CDISC Rule ID',
            Rule['Outcome']['Message'] ?? null as 'Error Message',
            Rule['Description'] ?? null as 'Description',
            udf.TO_STRING(ARRAY(SELECT DISTINCT VALUE Authority['Organization'] FROM Authority IN Rule['Authorities'])) as 'Organization',
            udf.TO_STRING(ARRAY(SELECT DISTINCT VALUE Standard['Name'] FROM Authority IN Rule['Authorities'] JOIN Standard IN Authority['Standards'])) as 'Standard Name',
            udf.TO_STRING(ARRAY(SELECT DISTINCT VALUE Standard['Version'] FROM Authority IN Rule['Authorities'] JOIN Standard IN Authority['Standards'])) as 'Standard Version',
            Rule['Executability'] ?? null as 'Executability',
            Rule['Core']['Status'] ?? null as 'Status',
            udf.TO_STRING(Rule['Check']) as 'Check'
            FROM Rules['json'] as Rule
            ORDER BY Rule['Core']['Id'] ASC
        """
        for rule in self.db_container.query_items(
            query=query, enable_cross_partition_query=True
        ):
            rules.append(rule)
        return rules
