import os

import pytest


REQUIRED_VARS = [
    "YAHOO_CLIENT_ID",
    "YAHOO_CLIENT_SECRET",
    "YAHOO_REFRESH_TOKEN",
]


def _env_missing():
    return any(not os.getenv(k) for k in REQUIRED_VARS)


@pytest.mark.integration
@pytest.mark.skipif(
    _env_missing() or os.getenv("YF_RUN_LIVE") != "1",
    reason=(
        "Set YF_RUN_LIVE=1 and provide YAHOO_CLIENT_ID, YAHOO_CLIENT_SECRET, "
        "YAHOO_REFRESH_TOKEN env vars to run live API test"
    ),
)
def test_can_refresh_and_call_users_games():
    import logging
    # Lazy-import so this file can be collected even when requests isn't installed
    import requests
    from yahoofantasy.api.fetch import make_request

    client_id = os.environ["YAHOO_CLIENT_ID"]
    client_secret = os.environ["YAHOO_CLIENT_SECRET"]
    refresh_token = os.environ["YAHOO_REFRESH_TOKEN"]

    # 1) Exchange refresh token for access token
    logging.info("integration: requesting OAuth access token via refresh token")
    resp = requests.post(
        "https://api.login.yahoo.com/oauth2/get_token",
        auth=(client_id, client_secret),
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )
    resp.raise_for_status()
    access_token = resp.json()["access_token"]

    # 2) Make a simple Yahoo Fantasy API request using the library helper
    # Users API tied to the logged-in account; games is a stable, low-risk fetch
    logging.info("integration: calling Yahoo Fantasy users/games endpoint")
    xml_text = make_request("users;use_login=1/games", token=access_token)

    # Sanity-check the response looks like Fantasy API output
    assert "<fantasy_content" in xml_text
    logging.info("integration: successful Yahoo Fantasy API response received")


