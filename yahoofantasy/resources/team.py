from yahoofantasy.util.logger import logger
from yahoofantasy.api.parse import as_list, from_response_object
from yahoofantasy.util.persistence import DEFAULT_TTL
from .player import Player
from .roster import Roster


class Team:
    def __init__(self, ctx, league, team_id):
        self.ctx = ctx
        self.league = league
        self.id = team_id

    @property
    def manager(self):
        """We can have multiple managers, so here's a shortcut to get 1 manager"""
        return as_list(self.managers.manager)[0]

    def players(self, persist_ttl=DEFAULT_TTL):
        logger.debug("Looking up current players on team")
        data = self.ctx._load_or_fetch(
            f"team.{self.id}.players",
            f"team/{self.id}/players",
        )
        players = []
        for p in data["fantasy_content"]["team"]["players"]["player"]:
            player = Player(self.league)
            player = from_response_object(player, p)
            players.append(player)
        return players

    # TODO: Adjust this method to account for non-week based games
    def roster(self, week_num=None):
        """Fetch this team's roster for a given week

        If week_num is None fetch the live roster
        """
        # First item is the peristence key, second is the API filter
        keys = ("live", "")
        if week_num:
            keys = (str(week_num), f"week={week_num}")
        data = self.ctx._load_or_fetch(
            f"team.{self.id}.roster.{keys[0]}",
            f"team/{self.id}/roster;{keys[1]}",
        )
        roster_data = data["fantasy_content"]["team"]["roster"]
        roster = Roster(self, week_num)
        roster = from_response_object(roster, roster_data, set_raw=True)
        return roster

    def matchups(self, start_week=None, end_week=None, persist_ttl=DEFAULT_TTL):
        """Return list of matchup objects for this team over a week range."""
        # Resolve week range via league settings if not provided
        if start_week is None or end_week is None:
            s = self.league.settings(persist_ttl)
            if start_week is None:
                start_week = int(getattr(s, "start_week", 1))
            if end_week is None:
                end_week = int(getattr(s, "end_week", start_week))
        from .matchup import Matchup
        out = []
        for wk in range(int(start_week), int(end_week) + 1):
            week_data = self.ctx._load_or_fetch(
                f"weeks.{self.league.id}.{wk}", f"scoreboard;week={wk}", league=self.league.id
            )
            # Extract matchups that include this team id
            matchups = week_data["fantasy_content"]["league"]["scoreboard"]["matchups"].get("matchup", [])
            for m in matchups:
                participants = as_list(m["teams"]["team"]) if "teams" in m else []
                ids = {t["team_key"] for t in participants if "team_key" in t}
                if self.id in ids:
                    mo = Matchup(self.ctx, self.league, None)
                    out.append(from_response_object(mo, m))
        return out

    def stats(self, type="season", week=None, persist_ttl=DEFAULT_TTL):
        """Aggregate team stats by summing players' stats for a week or season.
        type: 'season' or 'week'; if 'week', week is required
        """
        if type not in ("season", "week"):
            raise ValueError("type must be 'season' or 'week'")
        if type == "week" and not week:
            raise ValueError("week is required when type='week'")
        # Fetch roster for the scope
        roster = self.roster(week if type == "week" else None)
        # Pre-fetch stats via roster helper if available
        try:
            roster.fetch_player_stats()
        except Exception:
            pass
        # Sum category values across all players
        from yahoofantasy.stats.utils import get_stat_from_value
        totals = {}
        for player in roster.players:
            stats = player.get_stats(week if type == "week" else None)
            for stat in stats:
                # stat is Stat object; ensure numeric
                try:
                    value = float(stat.value)
                except Exception:
                    continue
                totals[stat.display] = totals.get(stat.display, 0.0) + value
        return totals

    def __repr__(self):
        return f"Team {self.name}"
