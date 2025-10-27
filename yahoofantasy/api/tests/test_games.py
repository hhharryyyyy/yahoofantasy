from unittest import TestCase
import logging

from yahoofantasy.api.games import get_game_id


class TestGames(TestCase):
    def test_get_game_id_valid(self):
        logging.info("games.get_game_id returns correct NBA codes for known seasons")
        self.assertEqual(get_game_id("nba", 2021), 410)
        self.assertEqual(get_game_id("nba", "2025"), 466)

    def test_get_game_id_invalid_game(self):
        logging.info("games.get_game_id raises on non-NBA game")
        with self.assertRaises(ValueError):
            get_game_id("nfl", 2021)

    def test_get_game_id_invalid_season(self):
        logging.info("games.get_game_id raises on invalid NBA season")
        with self.assertRaises(ValueError):
            get_game_id("nba", 1999)


