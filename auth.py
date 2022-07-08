from json import loads
from os import getenv
from requests import post


def get_drupal_token():
    DRUPAL_BASE_URL = getenv("DRUPAL_BASE_URL")
    DRUPAL_CLIENT_ID = getenv("DRUPAL_CLIENT_ID")
    DRUPAL_CLIENT_SECRET = getenv("DRUPAL_CLIENT_SECRET")
    DRUPAL_GRANT_TYPE = getenv("DRUPAL_GRANT_TYPE")
    DRUPAL_PATH = getenv("DRUPAL_PATH")
    DRUPAL_SCOPE = getenv("DRUPAL_SCOPE")
    access_token_response = post(
        f"https://{DRUPAL_BASE_URL}{DRUPAL_PATH}",
        data={"grant_type": DRUPAL_GRANT_TYPE, "scope": DRUPAL_SCOPE},
        verify=False,
        allow_redirects=False,
        auth=(DRUPAL_CLIENT_ID, DRUPAL_CLIENT_SECRET),
    )
    tokens = loads(access_token_response.text)
    return tokens["access_token"]
