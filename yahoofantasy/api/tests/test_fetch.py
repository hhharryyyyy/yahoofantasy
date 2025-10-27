from unittest import TestCase
from unittest.mock import patch, MagicMock

from yahoofantasy.api.fetch import make_request, YURL


class TestFetch(TestCase):
    @patch("yahoofantasy.api.fetch.requests.get")
    def test_make_request_basic(self, m_get):
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
        resp = MagicMock()
        resp.raise_for_status.side_effect = Exception("bad")
        resp.status_code = 500
        m_get.return_value = resp

        with self.assertRaises(Exception):
            make_request("whatever", token="t")


