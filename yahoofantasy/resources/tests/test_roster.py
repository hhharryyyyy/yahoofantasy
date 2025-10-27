from unittest import TestCase

from yahoofantasy.resources.roster import Roster
from yahoofantasy.resources.league import League


class DummyCtx:
    def __init__(self, players_resp):
        self.players_resp = players_resp

    def _load_or_fetch(self, key, url, league=None):
        return self.players_resp


def make_players_payload(positions):
    # positions: list of (player_key, selected_position)
    return {
        "fantasy_content": {
            "team": {
                "players": {
                    "player": [
                        {
                            "player_key": k,
                            "selected_position": {"position": pos},
                        }
                        for k, pos in positions
                    ]
                }
            }
        }
    }


class TestRoster(TestCase):
    def test_players_and_active_players(self):
        # Build the team/league context and payload
        positions = [
            ("nba.p.1", "G"),
            ("nba.p.2", "C"),
            ("nba.p.3", "BN"),
            ("nba.p.4", "IR"),
        ]
        payload = make_players_payload(positions)

        league = League(DummyCtx(payload), "428.l.25000")
        team = type("T", (), {"league": league, "id": "428.t.1"})()
        roster = Roster(team, week_num=5)

        # Mimic how Team.roster fills _raw and sets players
        roster = roster
        roster = roster
        roster = roster
        # Set _raw as Team.roster would
        roster = roster
        roster._raw = payload["fantasy_content"]["team"]["roster"] = payload["fantasy_content"]["team"]

        # Access players property, which materializes Player objects
        players = roster.players
        self.assertEqual(len(players), 4)
        self.assertTrue(hasattr(players[0], "player_key"))

        active = roster.active_players
        self.assertEqual(len(active), 2)
        self.assertEqual({p.selected_position.position for p in active}, {"G", "C"})


