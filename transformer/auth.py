from json import loads
from os import getenv
from requests import post


def get_B2C_token():
    B2C_BASE_URL = getenv("B2C_BASE_URL")
    B2C_CLIENT_ID = getenv("B2C_CLIENT_ID")
    B2C_CLIENT_SECRET = getenv("B2C_CLIENT_SECRET")
    B2C_GRANT_TYPE = getenv("B2C_GRANT_TYPE")
    B2C_PATH = getenv("B2C_PATH")
    B2C_SCOPE = getenv("B2C_SCOPE")
    access_token_response = post(
        f"https://{B2C_BASE_URL}{B2C_PATH}",
        data={"grant_type": B2C_GRANT_TYPE, "scope": B2C_SCOPE},
        verify=False,
        allow_redirects=False,
        auth=(B2C_CLIENT_ID, B2C_CLIENT_SECRET),
    )
    tokens = loads(access_token_response.text)
    return tokens["access_token"]
