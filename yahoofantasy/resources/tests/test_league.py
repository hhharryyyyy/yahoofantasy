from unittest import TestCase
import logging

from yahoofantasy.resources.league import League


class DummyCtx:
    def __init__(self):
        self.calls = 0
        self.settings_payload = None

    def _load_or_fetch(self, key, url, league=None):
        # Route by URL endpoints under test
        if url == "players;count=25;start=0":
            # Page 1: 25 players
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
        if url == "players;count=25;start=25":
            # Page 2: 5 players
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
        if url.startswith("players;count=25;start="):
            # End of pagination
            return {"fantasy_content": {"league": {"players": {}}}}
        if url == "settings":
            return self.settings_payload
        raise AssertionError(f"Unexpected call: key={key} url={url} league={league}")


class TestLeague(TestCase):
    def test_players_status_validation(self):
        logging.info("league.players validates status and raises on invalid values")
        lg = League(DummyCtx(), "428.l.25000")
        with self.assertRaises(ValueError):
            lg.players(status="BAD")

    def test_players_pagination(self):
        logging.info("league.players paginates until no players key in response")
        lg = League(DummyCtx(), "428.l.25000")
        players = lg.players()
        self.assertEqual(len(players), 30)
        self.assertTrue(hasattr(players[0], "player_key"))

    def test_past_league_id(self):
        logging.info("league.past_league_id parses combined renew key across seasons")
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

    def test_settings_and_helpers(self):
        ctx = DummyCtx()
        ctx.settings_payload = {
            "fantasy_content": {
                "league": {
                    "settings": {
                        "scoring_type": "headpoint",
                        "stat_categories": {
                            "stats": {
                                "stat": [
                                    {"stat_id": 0, "display_name": "GP"},
                                    {"stat_id": 5, "display_name": "FG%"},
                                ]
                            }
                        },
                        "position_types": {
                            "position_type": [
                                {"type": "G"},
                                {"type": "F"},
                                {"type": "C"},
                            ]
                        },
                        "roster_positions": {
                            "roster_position": [
                                {"position": "PG"},
                                {"position": "SG"},
                                {"position": "SF"},
                            ]
                        },
                    }
                }
            }
        }
        lg = League(ctx, "428.l.25000")
        settings = lg.settings()
        self.assertEqual(settings.scoring_type, "headpoint")
        cats = lg.stat_categories()
        self.assertEqual(len(cats), 2)
        self.assertEqual(str(cats[1].display_name), "FG%")
        pos_types = lg.position_types()
        self.assertEqual([str(p.type) for p in pos_types], ["G", "F", "C"])
        roster_pos = lg.roster_positions()
        self.assertEqual([str(p.position) for p in roster_pos], ["PG", "SG", "SF"])


class TestLeaguePlayersFilters(TestCase):
    def test_players_filters_build_query_and_cache(self):
        class Ctx(DummyCtx):
            def __init__(self):
                super().__init__()
                self.calls = []

            def _load_or_fetch(self, key, url, league=None):
                self.calls.append((key, url))
                if url.startswith("players;count=10;start=0"):
                    return {
                        "fantasy_content": {
                            "league": {"players": {"player": [{"player_key": "nba.p.1"}]}}
                        }
                    }
                return {"fantasy_content": {"league": {"players": {}}}}

        ctx = Ctx()
        lg = League(ctx, "428.l.25000")
        players = lg.players(
            position="G",
            status="FA",
            search="smith",
            sort="AR",
            sort_type="season",
            start=0,
            count=10,
        )
        self.assertEqual(len(players), 1)
        first_key, first_url = ctx.calls[0]
        self.assertIn(
            "players.428.l.25000.position-G.status-FA.search-smith.sort-AR.sort_type-season.0",
            first_key,
        )
        self.assertEqual(
            first_url,
            "players;count=10;start=0;position=G;status=FA;search=smith;sort=AR;sort_type=season",
        )


