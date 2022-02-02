from json import loads
from os import getenv
from requests import post


def get_token():
    API_BASE_URL = getenv("API_BASE_URL", None)
    API_CLIENT_ID = getenv("API_CLIENT_ID", None)
    API_CLIENT_SECRET = getenv("API_CLIENT_SECRET", None)
    API_GRANT_TYPE = getenv("API_GRANT_TYPE", None)
    API_PATH = getenv("API_PATH", None)
    API_SCOPE = getenv("API_SCOPE", None)
    access_token_response = post(
        f"https://{API_BASE_URL}{API_PATH}",
        data={"grant_type": API_GRANT_TYPE, "scope": API_SCOPE},
        verify=False,
        allow_redirects=False,
        auth=(API_CLIENT_ID, API_CLIENT_SECRET),
    )
    tokens = loads(access_token_response.text)
    return tokens["access_token"]
