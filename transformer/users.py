from azure.identity import ClientSecretCredential
from msgraph.core import GraphClient
from os import getenv


app_client = GraphClient(
    credential=ClientSecretCredential(
        getenv("GRAPH_TENANT_ID"),
        getenv("GRAPH_CLIENT_ID"),
        getenv("GRAPH_CLIENT_SECRET"),
    ),
    scopes=["https://graph.microsoft.com/.default"],
)


def get_users_from_name(username: str):
    return app_client.get(
        f"/users?$select=id,displayName,userType,userPrincipalName,createdDateTime&$filter=displayName eq '{username}' and userType eq 'Member'"
    ).json()["value"]


def get_user_id_from_name(username: str):
    return max(get_users_from_name(username), key=lambda user: user["createdDateTime"])
