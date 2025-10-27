from unittest import TestCase

from yahoofantasy.resources.league import League
from yahoofantasy.resources.team import Team


def make_settings_payload(sw=1, ew=2, cw=1):
    return {"fantasy_content": {"league": {"settings": {"start_week": sw, "end_week": ew, "current_week": cw}}}}


def make_scoreboard_payload(team_key):
    return {
        "fantasy_content": {
            "league": {
                "scoreboard": {
                    "matchups": {
                        "matchup": [
                            {
                                "teams": {
                                    "team": [
                                        {"team_key": team_key},
                                        {"team_key": "428.l.25000.t.2"},
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        }
    }


class DummyCtx:
    def __init__(self, settings_payload, scoreboard_payload):
        self.settings_payload = settings_payload
        self.scoreboard_payload = scoreboard_payload

    def _load_or_fetch(self, key, url, league=None):
        if url == "settings":
            return self.settings_payload
        if url.startswith("scoreboard;week="):
            return self.scoreboard_payload
        raise AssertionError(f"Unexpected call: key={key} url={url} league={league}")


class TestTeamHelpers(TestCase):
    def test_current_week_from_settings(self):
        ctx = DummyCtx(make_settings_payload(sw=1, ew=20, cw=7), make_scoreboard_payload("428.l.25000.t.1"))
        lg = League(ctx, "428.l.25000")
        self.assertEqual(lg.current_week(), 7)

    def test_matchups_filters_for_team(self):
        ctx = DummyCtx(make_settings_payload(sw=1, ew=1, cw=1), make_scoreboard_payload("428.l.25000.t.1"))
        lg = League(ctx, "428.l.25000")
        tm = Team(ctx, lg, "428.l.25000.t.1")
        m = tm.matchups(1, 1)
        self.assertEqual(len(m), 1)


