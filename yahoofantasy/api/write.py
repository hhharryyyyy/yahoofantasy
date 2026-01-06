"""HTTP write operations (POST/PUT) for Yahoo Fantasy API."""

import time
import requests

from yahoofantasy.util.logger import logger
from yahoofantasy.api.fetch import YURL, _get_retry_config
from yahoofantasy.exceptions import (
    YahooFantasyError,
    RosterError,
    TransactionError,
    InvalidPositionError,
    RosterFullError,
    PlayerNotAvailableError,
    InsufficientFAABError,
    InsufficientScopeError,
)


def _parse_error_response(response_text):
    """Parse Yahoo API error response and return error description.

    Yahoo returns XML errors like:
    <?xml version="1.0" encoding="UTF-8"?>
    <error xml:lang="en-us">
        <description>Player 'nba.p.5007' is not available</description>
        <detail/>
    </error>
    """
    try:
        # Simple XML parsing for error description
        import re

        match = re.search(r"<description>(.*?)</description>", response_text, re.DOTALL)
        if match:
            return match.group(1).strip()
    except Exception:
        pass
    return response_text


def _map_error_to_exception(status_code, error_msg, raw_response):
    """Map error message to appropriate exception type."""
    error_lower = error_msg.lower()

    # Check for scope/permission issues
    if status_code == 401 or "unauthorized" in error_lower:
        if "scope" in error_lower or "permission" in error_lower:
            return InsufficientScopeError(
                "OAuth token does not have write permissions. "
                "Re-run 'yahoofantasy login' with write access enabled.",
                code=status_code,
                raw_response=raw_response,
            )
        return YahooFantasyError(error_msg, code=status_code, raw_response=raw_response)

    # Transaction errors
    if "not available" in error_lower or "already owned" in error_lower:
        return PlayerNotAvailableError(error_msg, code=status_code, raw_response=raw_response)

    if "roster is full" in error_lower or "no room" in error_lower:
        return RosterFullError(error_msg, code=status_code, raw_response=raw_response)

    if "faab" in error_lower or "budget" in error_lower or "insufficient" in error_lower:
        return InsufficientFAABError(error_msg, code=status_code, raw_response=raw_response)

    # Roster errors
    if "position" in error_lower and ("invalid" in error_lower or "cannot" in error_lower):
        return InvalidPositionError(error_msg, code=status_code, raw_response=raw_response)

    if "roster" in error_lower or "lineup" in error_lower:
        return RosterError(error_msg, code=status_code, raw_response=raw_response)

    # Generic transaction error for transaction-related messages
    if "transaction" in error_lower or "claim" in error_lower or "waiver" in error_lower:
        return TransactionError(error_msg, code=status_code, raw_response=raw_response)

    # Default to base exception
    return YahooFantasyError(error_msg, code=status_code, raw_response=raw_response)


def make_write_request(url, token, data, method="POST", league=None):
    """Make a write request (POST/PUT) to the Yahoo Fantasy API.

    Args:
        url: The API endpoint (relative to YURL, or full URL)
        token: OAuth access token
        data: XML payload as string
        method: HTTP method ("POST" or "PUT")
        league: Optional league key for URL construction

    Returns:
        Response text (XML) on success

    Raises:
        YahooFantasyError: On API errors with parsed error message
        InsufficientScopeError: If OAuth token lacks write permissions
        RosterError: On roster-related errors
        TransactionError: On transaction-related errors
    """
    if league:
        url = "league/{}/{}".format(league, url)

    full_url = "{}/{}".format(YURL, url)
    logger.debug("Making {} request to {}".format(method, full_url))

    headers = {
        "Authorization": "Bearer {}".format(token),
        "Content-Type": "application/xml",
        "User-Agent": "Mozilla/5.0",
    }

    max_retries, _ = _get_retry_config()

    # For write operations, we only retry on 429 (rate limit)
    # We do NOT retry on 5xx to avoid duplicate transactions
    attempt = 0
    while True:
        if method.upper() == "PUT":
            resp = requests.put(full_url, headers=headers, data=data)
        else:
            resp = requests.post(full_url, headers=headers, data=data)

        status = resp.status_code

        # Only retry on 429 for write operations
        if status == 429:
            if attempt >= max_retries:
                error_msg = _parse_error_response(resp.text)
                raise YahooFantasyError(
                    "Rate limited after {} retries: {}".format(max_retries, error_msg),
                    code=status,
                    raw_response=resp.text,
                )

            # Honor Retry-After header
            retry_after = 1.0
            try:
                ra = resp.headers.get("Retry-After")
                if ra is not None:
                    retry_after = float(ra)
            except Exception:
                pass

            logger.warning(
                "Rate limited (429), waiting {} seconds (attempt {}/{})".format(
                    retry_after, attempt + 1, max_retries
                )
            )
            time.sleep(retry_after)
            attempt += 1
            continue

        # Handle error responses
        if status >= 400:
            error_msg = _parse_error_response(resp.text)
            logger.error("Write request failed ({}): {}".format(status, error_msg))
            raise _map_error_to_exception(status, error_msg, resp.text)

        # Success
        logger.debug("Write request successful")
        return resp.text
