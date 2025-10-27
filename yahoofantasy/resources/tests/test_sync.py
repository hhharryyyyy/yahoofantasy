from unittest import TestCase

from yahoofantasy.resources.league import League


class DummyTeam:
    def __init__(self, league, team_id):
        self.league = league
        self.id = team_id

    def roster(self, week_num=None):
        return {"players": ["p1"], "week": week_num}


class DummyCtx:
    def __init__(self, settings_payload, teams_payload, transactions_payload, scoreboard_payload):
        self.settings_payload = settings_payload
        self.teams_payload = teams_payload
        self.transactions_payload = transactions_payload
        self.scoreboard_payload = scoreboard_payload

    def _load_or_fetch(self, key, url, league=None):
        if url == "settings":
            return self.settings_payload
        if url == "teams":
            return self.teams_payload
        if url == "transactions":
            return self.transactions_payload
        if url.startswith("scoreboard;week="):
            return self.scoreboard_payload
        raise AssertionError(f"Unexpected call: key={key} url={url} league={league}")


def make_base_payloads():
    settings = {"fantasy_content": {"league": {"settings": {"start_week": 1, "end_week": 2}}}}
    teams = {
        "fantasy_content": {
            "league": {
                "teams": {
                    "team": [
                        {"team_key": "428.l.25000.t.1", "name": "Team 1"},
                        {"team_key": "428.l.25000.t.2", "name": "Team 2"},
                    ]
                }
            }
        }
    }
    transactions = {
        "fantasy_content": {
            "league": {
                "transactions": {
                    "transaction": [
                        {"timestamp": 1000, "type": "add"},
                        {"timestamp": 900, "type": "drop"},
                    ]
                }
            }
        }
    }
    scoreboard = {"fantasy_content": {"league": {"scoreboard": {"matchups": {}}}}}
    return settings, teams, transactions, scoreboard


class TestSyncDelta(TestCase):
    def test_sync_delta_filters_transactions_and_builds_rosters(self):
        settings, teams, transactions, scoreboard = make_base_payloads()
        ctx = DummyCtx(settings, teams, transactions, scoreboard)
        lg = League(ctx, "428.l.25000")
        # Attach minimal state for teams() iteration
        teams_list = []
        def fake_teams(persist_ttl=None):
            return [DummyTeam(lg, "428.l.25000.t.1"), DummyTeam(lg, "428.l.25000.t.2")]
        lg.teams = fake_teams

        out = lg.sync_delta(last_tx_ts=950, current_week=1, include_next_week=True)
        # One transaction is newer than 950
        self.assertEqual(len(out["transactions"]), 1)
        # Rosters include both weeks for both teams
        self.assertIn(1, out["rosters"]["428.l.25000.t.1"])
        self.assertIn(2, out["rosters"]["428.l.25000.t.1"])
        self.assertIn(1, out["rosters"]["428.l.25000.t.2"])
        self.assertIn(2, out["rosters"]["428.l.25000.t.2"])

