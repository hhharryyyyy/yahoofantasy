from unittest import TestCase
from unittest.mock import patch, MagicMock
import logging
import os

from yahoofantasy.api.fetch import make_request, YURL


class TestFetch(TestCase):
    @patch("yahoofantasy.api.fetch.requests.get")
    def test_make_request_basic(self, m_get):
        logging.info("fetch.make_request performs a basic GET and returns text")
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.text = "<xml>ok</xml>"
        m_get.return_value = resp

        out = make_request("standings", token="abc")

        m_get.assert_called_once_with(
            f"{YURL}/standings",
            headers={
                "Authorization": "Bearer abc",
                "User-Agent": "Mozilla/5.0",
            },
        )
        self.assertEqual(out, "<xml>ok</xml>")

    @patch("yahoofantasy.api.fetch.requests.get")
    def test_make_request_league_url(self, m_get):
        logging.info("fetch.make_request prefixes league path when league parameter is provided")
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.text = "<xml>ok</xml>"
        m_get.return_value = resp

        out = make_request("players", token="t", league="428.l.25000")

        m_get.assert_called_once_with(
            f"{YURL}/league/428.l.25000/players",
            headers={
                "Authorization": "Bearer t",
                "User-Agent": "Mozilla/5.0",
            },
        )
        self.assertEqual(out, "<xml>ok</xml>")

    @patch("yahoofantasy.api.fetch.requests.get")
    def test_make_request_raises_on_http_error(self, m_get):
        logging.info("fetch.make_request raises when non-retryable HTTP error occurs")
        resp = MagicMock()
        resp.raise_for_status.side_effect = Exception("bad")
        resp.status_code = 500
        m_get.return_value = resp

        with self.assertRaises(Exception):
            make_request("whatever", token="t")

    @patch("yahoofantasy.api.fetch.time.sleep")
    @patch("yahoofantasy.api.fetch.requests.get")
    def test_retries_on_429_honors_retry_after(self, m_get, m_sleep):
        logging.info("fetch.make_request honors Retry-After header on 429 and retries")
        first = MagicMock()
        first.status_code = 429
        first.headers = {"Retry-After": "0.01"}
        # raise_for_status should raise on final handling (we only raise when out of retries),
        # but during retryable path we do not call raise_for_status until out of retries or success
        second = MagicMock()
        second.status_code = 200
        second.text = "<xml>ok</xml>"
        second.raise_for_status.return_value = None
        m_get.side_effect = [first, second]

        with patch.dict(os.environ, {"YF_MAX_RETRIES": "3"}, clear=False):
            out = make_request("standings", token="abc")

        self.assertEqual(out, "<xml>ok</xml>")
        # Called twice: first 429 then success
        self.assertEqual(m_get.call_count, 2)
        # Should honor Retry-After
        m_sleep.assert_any_call(0.01)

    @patch("yahoofantasy.api.fetch.time.sleep")
    @patch("yahoofantasy.api.fetch.random.uniform")
    @patch("yahoofantasy.api.fetch.requests.get")
    def test_retries_on_500_with_exponential_backoff_and_jitter(self, m_get, m_rand, m_sleep):
        logging.info("fetch.make_request retries on 5xx with exponential backoff and jitter")
        # Force deterministic jitter
        m_rand.return_value = 0.05

        r1 = MagicMock(status_code=500)
        r2 = MagicMock(status_code=200)
        r2.text = "<xml>ok</xml>"
        r2.raise_for_status.return_value = None
        m_get.side_effect = [r1, r2]

        with patch.dict(os.environ, {"YF_MAX_RETRIES": "2", "YF_BACKOFF_BASE_SEC": "0.1"}, clear=False):
            out = make_request("standings", token="abc")

        self.assertEqual(out, "<xml>ok</xml>")
        # First attempt 500, second attempt 200 -> two calls
        self.assertEqual(m_get.call_count, 2)
        # For attempt 0, cap = 0.1, jitter used 0.05
        m_sleep.assert_any_call(0.05)

    @patch("yahoofantasy.api.fetch.requests.get")
    def test_non_retryable_400_raises_immediately(self, m_get):
        logging.info("fetch.make_request raises immediately on non-retryable 4xx")
        resp = MagicMock()
        resp.status_code = 400
        # raise_for_status is called immediately for non-retryable
        resp.raise_for_status.side_effect = Exception("bad request")
        m_get.return_value = resp

        with self.assertRaises(Exception):
            make_request("whatever", token="t")
        m_get.assert_called_once()

    @patch("yahoofantasy.api.fetch.requests.get")
    def test_retry_then_success_returns_text(self, m_get):
        logging.info("fetch.make_request returns response text after retry success")
        r1 = MagicMock(status_code=500)
        r2 = MagicMock(status_code=200)
        r2.text = "<xml>fine</xml>"
        r2.raise_for_status.return_value = None
        m_get.side_effect = [r1, r2]

        with patch.dict(os.environ, {"YF_MAX_RETRIES": "1"}, clear=False):
            out = make_request("standings", token="abc")

        self.assertEqual(out, "<xml>fine</xml>")
        self.assertEqual(m_get.call_count, 2)


