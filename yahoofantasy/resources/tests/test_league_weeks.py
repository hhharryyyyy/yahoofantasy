from unittest import TestCase

from yahoofantasy.resources.league import League


class DummyCtx:
    def __init__(self, scoreboard_payload, settings_payload=None):
        self.scoreboard_payload = scoreboard_payload
        self.settings_payload = settings_payload
        self.calls = []

    def _load_or_fetch(self, key, url, league=None):
        self.calls.append((key, url))
        if url.startswith("scoreboard;week="):
            return self.scoreboard_payload
        if url == "settings":
            return self.settings_payload
        raise AssertionError(f"Unexpected call: key={key} url={url} league={league}")


def make_scoreboard_payload(with_matchups=True):
    mc = {"matchup": [{"week": 1}] } if with_matchups else {}
    return {
        "fantasy_content": {
            "league": {"scoreboard": {"matchups": mc}}
        }
    }


class TestLeagueWeeks(TestCase):
    def test_weeks_uses_league_start_end(self):
        ctx = DummyCtx(make_scoreboard_payload())
        lg = League(ctx, "428.l.25000")
        lg.start_week = 1
        lg.end_week = 3
        weeks = lg.weeks()
        self.assertEqual(len(weeks), 3)
        # Called for week 1..3
        urls = [u for _, u in ctx.calls]
        self.assertIn("scoreboard;week=1", urls)
        self.assertIn("scoreboard;week=2", urls)
        self.assertIn("scoreboard;week=3", urls)

    def test_weeks_falls_back_to_settings(self):
        settings_payload = {
            "fantasy_content": {
                "league": {"settings": {"start_week": 2, "end_week": 4}}
            }
        }
        ctx = DummyCtx(make_scoreboard_payload(), settings_payload)
        lg = League(ctx, "428.l.25000")
        weeks = lg.weeks()
        self.assertEqual(len(weeks), 3)
        urls = [u for _, u in ctx.calls]
        self.assertIn("scoreboard;week=2", urls)
        self.assertIn("scoreboard;week=3", urls)
        self.assertIn("scoreboard;week=4", urls)

