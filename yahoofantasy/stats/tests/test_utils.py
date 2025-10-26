from collections import namedtuple
from unittest import TestCase
from yahoofantasy.stats.utils import get_stat_from_value, get_stat_from_stat_list


# An example of what an API matchup's stat looks like after being parsed
StatResult = namedtuple("StatObj", ["stat_id", "value"])


class TestStatUtils(TestCase):
    def test_get_stat_from_value(self):
        # String stat ID and stat value (NBA points)
        stat = get_stat_from_value(StatResult("12", 32.5))
        self.assertEqual(stat.display, "PTS")
        self.assertEqual(stat.value, 32.5)
        # Integer stat ID (3PTM) and stat value
        stat = get_stat_from_value(StatResult(10, 5))
        self.assertEqual(stat.display, "3PTM")
        self.assertEqual(stat.value, 5)

    def test_get_stat_from_stat_list(self):
        stat_list = [
            StatResult("12", 30.0),  # PTS
            StatResult("10", 4),     # 3PTM
            StatResult("5", 0.55),   # FG%
        ]
        self.assertEqual(get_stat_from_stat_list("PTS", stat_list), 30.0)
        self.assertEqual(get_stat_from_stat_list("3PTM", stat_list), 4)
        # Stat missing from stat list
        with self.assertRaises(ValueError):
            get_stat_from_stat_list("REB", [StatResult("12", 30.0)])
