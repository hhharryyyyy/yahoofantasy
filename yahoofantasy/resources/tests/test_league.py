from unittest import TestCase

from yahoofantasy.resources.league import League


class DummyCtx:
    def __init__(self):
        self.calls = 0

    def _load_or_fetch(self, key, url, league=None):
        # Page 1: 25 players
        self.calls += 1
        if self.calls == 1:
            players = [
                {
                    "player_key": f"nba.p.{i}",
                    "selected_position": {"position": "G"},
                }
                for i in range(25)
            ]
            return {
                "fantasy_content": {"league": {"players": {"player": players}}}
            }
        # Page 2: 5 players
        if self.calls == 2:
            players = [
                {
                    "player_key": f"nba.p.{i}",
                    "selected_position": {"position": "BN"},
                }
                for i in range(25, 30)
            ]
            return {
                "fantasy_content": {"league": {"players": {"player": players}}}
            }
        # Page 3: no player key indicates end
        return {"fantasy_content": {"league": {"players": {}}}}


class TestLeague(TestCase):
    def test_players_status_validation(self):
        lg = League(DummyCtx(), "428.l.25000")
        with self.assertRaises(ValueError):
            lg.players(status="BAD")

    def test_players_pagination(self):
        lg = League(DummyCtx(), "428.l.25000")
        players = lg.players()
        self.assertEqual(len(players), 30)
        self.assertTrue(hasattr(players[0], "player_key"))

    def test_past_league_id(self):
        lg = League(None, "428.l.25000")
        lg.season = 2024
        lg.game_code = "nba"
        # Happy path: previous year mapping
        lg.renew = 42812345  # 2023 NBA game code is 428
        self.assertEqual(lg.past_league_id, (428, 12345))
        # No renew configured
        lg2 = League(None, "428.l.25000")
        lg2.season = 2024
        lg2.game_code = "nba"
        self.assertIsNone(lg2.past_league_id)
        # Renew from an older year than previous
        lg3 = League(None, "428.l.25000")
        lg3.season = 2024
        lg3.game_code = "nba"
        lg3.renew = 41022222  # 2021 NBA game code is 410
        self.assertEqual(lg3.past_league_id, (410, 22222))


