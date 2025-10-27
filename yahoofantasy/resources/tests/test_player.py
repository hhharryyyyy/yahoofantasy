from unittest import TestCase

from yahoofantasy.resources.league import League
from yahoofantasy.resources.player import Player


class DummyCtx:
    def __init__(self, payload):
        self.payload = payload

    def _load_or_fetch(self, key, url, league=None):
        return self.payload


class TestPlayerOwnership(TestCase):
    def test_player_ownership_parses(self):
        payload = {
            "fantasy_content": {
                "league": {
                    "players": {
                        "player": {
                            "player_key": "nba.p.1",
                            "ownership": {
                                "ownership_type": "team",
                                "owner_team_key": "428.l.25000.t.1",
                                "owner_team_name": "My Team",
                            },
                        }
                    }
                }
            }
        }
        ctx = DummyCtx(payload)
        lg = League(ctx, "428.l.25000")
        p = Player(lg)
        p.player_id = "1"
        p.player_key = "nba.p.1"

        own = p.ownership()
        self.assertEqual(str(own.ownership_type), "team")
        self.assertEqual(str(own.owner_team_key), "428.l.25000.t.1")
        self.assertEqual(str(own.owner_team_name), "My Team")


