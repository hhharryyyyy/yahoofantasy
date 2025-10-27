from yahoofantasy.util.logger import logger
import os
import random
import time
import requests

YURL = "https://fantasysports.yahooapis.com/fantasy/v2"


def _get_retry_config():
    """Return retry configuration from environment variables.

    YF_MAX_RETRIES: number of retries on 429/5xx (default: 3)
    YF_BACKOFF_BASE_SEC: base seconds for exponential backoff (default: 0.5)
    """
    try:
        max_retries = int(os.getenv("YF_MAX_RETRIES", "3"))
    except Exception:
        max_retries = 3
    try:
        backoff_base = float(os.getenv("YF_BACKOFF_BASE_SEC", "0.5"))
    except Exception:
        backoff_base = 0.5
    if max_retries < 0:
        max_retries = 0
    if backoff_base < 0:
        backoff_base = 0.0
    return max_retries, backoff_base


def _sleep_with_backoff(attempt_number, backoff_base):
    """Sleep using exponential backoff with full jitter."""
    delay_cap = backoff_base * (2 ** attempt_number)
    # Full jitter: random between 0 and cap
    sleep_seconds = random.uniform(0, delay_cap)
    if sleep_seconds > 0:
        time.sleep(sleep_seconds)


def make_request(url, token, league=False, **kwargs):
    if league:
        url = "league/{}/{}".format(league, url)
    logger.debug("Making request to {}".format(url))

    headers = {
        "Authorization": "Bearer {}".format(token),
        "User-Agent": "Mozilla/5.0",
    }

    max_retries, backoff_base = _get_retry_config()

    # We attempt the initial request plus up to max_retries retries on retryable statuses
    attempt = 0
    while True:
        resp = requests.get("{}/{}".format(YURL, url), headers=headers)

        status = getattr(resp, "status_code", None)
        # Retry on 429 and 5xx statuses
        should_retry = status == 429 or (isinstance(status, int) and status >= 500)

        if not should_retry:
            # For non-retryable responses, raise for status and return on success
            try:
                resp.raise_for_status()
            except Exception:
                logger.exception(
                    "Bad response status ({}) for request".format(resp.status_code)
                )
                raise
            return resp.text

        # If we should retry but have exhausted attempts, raise
        if attempt >= max_retries:
            try:
                resp.raise_for_status()
            except Exception:
                logger.exception(
                    "Bad response status ({}) for request after retries".format(
                        resp.status_code
                    )
                )
                raise
            return resp.text

        # Honor Retry-After if present for 429
        retry_after = 0.0
        if status == 429:
            try:
                ra = resp.headers.get("Retry-After")
                if ra is not None:
                    retry_after = float(ra)
            except Exception:
                retry_after = 0.0

        if retry_after > 0:
            time.sleep(retry_after)
        else:
            _sleep_with_backoff(attempt, backoff_base)

        attempt += 1
