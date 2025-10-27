from unittest import TestCase

from yahoofantasy.api.games import get_game_id


class TestGames(TestCase):
    def test_get_game_id_valid(self):
        self.assertEqual(get_game_id("nba", 2021), 410)
        self.assertEqual(get_game_id("nba", "2025"), 466)

    def test_get_game_id_invalid_game(self):
        with self.assertRaises(ValueError):
            get_game_id("nfl", 2021)

    def test_get_game_id_invalid_season(self):
        with self.assertRaises(ValueError):
            get_game_id("nba", 1999)


