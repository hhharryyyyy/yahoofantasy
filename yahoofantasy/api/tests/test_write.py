"""Tests for write operations (POST/PUT)."""

from unittest import TestCase
from unittest.mock import patch, MagicMock
import logging
import os

from yahoofantasy.api.write import make_write_request, YURL
from yahoofantasy.exceptions import (
    YahooFantasyError,
    PlayerNotAvailableError,
    RosterFullError,
    InvalidPositionError,
    InsufficientScopeError,
)


class TestWriteRequest(TestCase):
    @patch("yahoofantasy.api.write.requests.post")
    def test_make_write_request_basic_post(self, m_post):
        logging.info("write.make_write_request performs a basic POST and returns text")
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "<fantasy_content>ok</fantasy_content>"
        m_post.return_value = resp

        result = make_write_request(
            "transactions",
            token="abc",
            data="<xml>payload</xml>",
            method="POST",
            league="428.l.25000",
        )

        m_post.assert_called_once_with(
            f"{YURL}/league/428.l.25000/transactions",
            headers={
                "Authorization": "Bearer abc",
                "Content-Type": "application/xml",
                "User-Agent": "Mozilla/5.0",
            },
            data="<xml>payload</xml>",
        )
        self.assertEqual(result, "<fantasy_content>ok</fantasy_content>")

    @patch("yahoofantasy.api.write.requests.put")
    def test_make_write_request_put_method(self, m_put):
        logging.info("write.make_write_request uses PUT when method='PUT'")
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "<fantasy_content>ok</fantasy_content>"
        m_put.return_value = resp

        result = make_write_request(
            "team/418.l.12345.t.1/roster",
            token="abc",
            data="<xml>roster</xml>",
            method="PUT",
        )

        m_put.assert_called_once()
        self.assertEqual(result, "<fantasy_content>ok</fantasy_content>")

    @patch("yahoofantasy.api.write.requests.post")
    def test_player_not_available_error(self, m_post):
        logging.info("write.make_write_request raises PlayerNotAvailableError on player unavailable")
        resp = MagicMock()
        resp.status_code = 400
        resp.text = "<error><description>Player 'nba.p.5007' is not available</description></error>"
        m_post.return_value = resp

        with self.assertRaises(PlayerNotAvailableError) as ctx:
            make_write_request("transactions", token="abc", data="<xml/>")

        self.assertIn("not available", str(ctx.exception))

    @patch("yahoofantasy.api.write.requests.post")
    def test_roster_full_error(self, m_post):
        logging.info("write.make_write_request raises RosterFullError when roster is full")
        resp = MagicMock()
        resp.status_code = 400
        resp.text = "<error><description>Your roster is full</description></error>"
        m_post.return_value = resp

        with self.assertRaises(RosterFullError):
            make_write_request("transactions", token="abc", data="<xml/>")

    @patch("yahoofantasy.api.write.requests.put")
    def test_invalid_position_error(self, m_put):
        logging.info("write.make_write_request raises InvalidPositionError on position error")
        resp = MagicMock()
        resp.status_code = 400
        resp.text = "<error><description>Invalid position for player</description></error>"
        m_put.return_value = resp

        with self.assertRaises(InvalidPositionError):
            make_write_request("team/t1/roster", token="abc", data="<xml/>", method="PUT")

    @patch("yahoofantasy.api.write.requests.post")
    def test_insufficient_scope_error(self, m_post):
        logging.info("write.make_write_request raises InsufficientScopeError on 401 with scope message")
        resp = MagicMock()
        resp.status_code = 401
        resp.text = "<error><description>Insufficient scope for this request</description></error>"
        m_post.return_value = resp

        with self.assertRaises(InsufficientScopeError):
            make_write_request("transactions", token="abc", data="<xml/>")

    @patch("yahoofantasy.api.write.time.sleep")
    @patch("yahoofantasy.api.write.requests.post")
    def test_retries_on_429(self, m_post, m_sleep):
        logging.info("write.make_write_request retries on 429 rate limit")
        first = MagicMock()
        first.status_code = 429
        first.headers = {"Retry-After": "0.01"}

        second = MagicMock()
        second.status_code = 200
        second.text = "<fantasy_content>ok</fantasy_content>"

        m_post.side_effect = [first, second]

        with patch.dict(os.environ, {"YF_MAX_RETRIES": "3"}, clear=False):
            result = make_write_request("transactions", token="abc", data="<xml/>")

        self.assertEqual(result, "<fantasy_content>ok</fantasy_content>")
        self.assertEqual(m_post.call_count, 2)
        m_sleep.assert_called_once_with(0.01)

    @patch("yahoofantasy.api.write.requests.post")
    def test_no_retry_on_500(self, m_post):
        logging.info("write.make_write_request does NOT retry on 5xx to avoid duplicate transactions")
        resp = MagicMock()
        resp.status_code = 500
        resp.text = "<error><description>Internal server error</description></error>"
        m_post.return_value = resp

        with self.assertRaises(YahooFantasyError):
            make_write_request("transactions", token="abc", data="<xml/>")

        # Should only be called once - no retry on 5xx for writes
        m_post.assert_called_once()

    @patch("yahoofantasy.api.write.requests.post")
    def test_generic_error_mapping(self, m_post):
        logging.info("write.make_write_request maps unknown errors to YahooFantasyError")
        resp = MagicMock()
        resp.status_code = 400
        resp.text = "<error><description>Some unknown error</description></error>"
        m_post.return_value = resp

        with self.assertRaises(YahooFantasyError) as ctx:
            make_write_request("transactions", token="abc", data="<xml/>")

        self.assertIn("unknown error", str(ctx.exception))

    @patch("yahoofantasy.api.write.requests.post")
    def test_raw_response_included_in_exception(self, m_post):
        logging.info("write.make_write_request includes raw response in exception")
        resp = MagicMock()
        resp.status_code = 400
        resp.text = "<error><description>Test error</description></error>"
        m_post.return_value = resp

        with self.assertRaises(YahooFantasyError) as ctx:
            make_write_request("transactions", token="abc", data="<xml/>")

        self.assertEqual(ctx.exception.raw_response, resp.text)
        self.assertEqual(ctx.exception.code, 400)
