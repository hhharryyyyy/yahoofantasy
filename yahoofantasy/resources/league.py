from yahoofantasy.api.games import get_game_id
from yahoofantasy.api.parse import from_response_object, get_value, as_list
from yahoofantasy.util.persistence import DEFAULT_TTL
from yahoofantasy.util.logger import logger
from .team import Team
from .standings import Standings
from .week import Week
from .draft_result import DraftResult
from .transaction import Transaction
from .player import Player


class League:
    def __init__(self, ctx, league_id):
        self.ctx = ctx
        self.id = league_id

    def get_team(self, team_key):
        return next((t for t in self.teams() if t.team_key == team_key), None)

    def teams(self, persist_ttl=DEFAULT_TTL):
        logger.debug("Looking up teams")
        data = self.ctx._load_or_fetch("teams." + self.id, "teams", league=self.id)
        teams = []
        for team in data["fantasy_content"]["league"]["teams"]["team"]:
            t = Team(self.ctx, self, get_value(team["team_key"]))
            from_response_object(t, team)
            teams.append(t)
        return teams

    def players(
        self,
        position=None,
        status=None,
        search=None,
        sort=None,
        sort_type=None,
        start=0,
        count=25,
        persist_ttl=DEFAULT_TTL,
    ):
        """
        Retrieve players for a given league context with filters.

        Filters:
            position: One of 'G', 'F', 'C'
            status: One of 'A', 'FA', 'W', 'T', 'K'
            search: Free text search
            sort: Sort key per Yahoo API
            sort_type: Sort type per Yahoo API
            start: Pagination start index
            count: Pagination size
        """
        logger.debug("Looking up players")

        VALID_STATUSES = {"A", "FA", "W", "T", "K"}
        VALID_POSITIONS = {"G", "F", "C"}
        if status is not None and status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status given. Must be one of the following: {', '.join(sorted(VALID_STATUSES))}"
            )
        if position is not None and position not in VALID_POSITIONS:
            raise ValueError(
                f"Invalid position given. Must be one of: {', '.join(sorted(VALID_POSITIONS))}"
            )

        # Build ordered filter pairs for deterministic query and cache keys
        filter_pairs = []
        if position is not None:
            filter_pairs.append(("position", position))
        if status is not None:
            filter_pairs.append(("status", status))
        if search is not None:
            filter_pairs.append(("search", search))
        if sort is not None:
            filter_pairs.append(("sort", sort))
        if sort_type is not None:
            filter_pairs.append(("sort_type", sort_type))

        def build_query(curr_start):
            params = [("count", count), ("start", curr_start)] + filter_pairs
            params_str = ";".join(f"{k}={v}" for k, v in params)
            return f"players;{params_str}"

        def build_cache_key(curr_start):
            base_key = f"players.{self.id}"
            if filter_pairs:
                param_key = ".".join(f"{k}-{v}" for k, v in filter_pairs)
                return f"{base_key}.{param_key}.{curr_start}"
            else:
                return f"{base_key}.{curr_start}"

        data = self.ctx._load_or_fetch(
            build_cache_key(start), build_query(start), league=self.id
        )

        players = []
        while "player" in data["fantasy_content"]["league"]["players"]:
            for player in data["fantasy_content"]["league"]["players"]["player"]:
                p = Player(self)
                from_response_object(p, player)
                players.append(p)
            start += count
            data = self.ctx._load_or_fetch(
                build_cache_key(start), build_query(start), league=self.id
            )
        return players

    def standings(self, persist_ttl=DEFAULT_TTL):
        logger.debug("Looking up standings")
        data = self.ctx._load_or_fetch(
            "standings." + self.id, "standings", league=self.id
        )
        standings = []
        for team in data["fantasy_content"]["league"]["standings"]["teams"]["team"]:
            standing = Standings(self.ctx, self, get_value(team["team_key"]))
            from_response_object(standing, team)
            standings.append(standing)
        return standings

    def weeks(self, persist_ttl=DEFAULT_TTL):
        if not self.start_week or not self.end_week:
            raise AttributeError(
                "Can't fetch weeks for a league without start/end weeks. Is it a "
                "head-to-head league? Did you sync your league already?"
            )
        logger.debug("Looking up weeks")
        out = []
        for week_num in range(self.start_week, self.end_week + 1):
            week = Week(self.ctx, self, week_num)
            week.sync()
            out.append(week)
        return out

    def draft_results(self, persist_ttl=DEFAULT_TTL):
        results = []
        for team in self.teams(persist_ttl):
            data = self.ctx._load_or_fetch(
                "draftresults." + team.id, f"team/{team.id}/draftresults;out=players"
            )
            for result in data["fantasy_content"]["team"]["draft_results"][
                "draft_result"
            ]:
                dr = DraftResult(self, team)
                from_response_object(dr, result)
                results.append(dr)
        return results

    def transactions(self, persist_ttl=DEFAULT_TTL):
        results = []
        data = self.ctx._load_or_fetch(
            "transactions." + self.id, "transactions", league=self.id
        )
        for result in data["fantasy_content"]["league"]["transactions"]["transaction"]:
            trans = Transaction.from_response(result, self)
            results.append(trans)
        return results

    def settings(self, persist_ttl=DEFAULT_TTL):
        """Fetch league settings (scoring type, stat categories, positions, playoffs, etc)."""
        logger.debug("Looking up league settings")
        data = self.ctx._load_or_fetch(
            "settings." + self.id, "settings", league=self.id
        )
        settings_data = data["fantasy_content"]["league"]["settings"]
        # Convert to attribute-style object for convenient access
        from yahoofantasy.api.attr import APIAttr

        return from_response_object(APIAttr(), settings_data)

    def stat_categories(self, persist_ttl=DEFAULT_TTL):
        """Return list of stat category objects for this league."""
        s = self.settings(persist_ttl)
        categories = []
        sc = getattr(s, "stat_categories", None)
        if sc is None:
            return categories
        # Some responses nest under stats.stat, others directly under stat
        if hasattr(sc, "stats") and hasattr(sc.stats, "stat"):
            categories = as_list(sc.stats.stat)
        elif hasattr(sc, "stat"):
            categories = as_list(sc.stat)
        return categories

    def position_types(self, persist_ttl=DEFAULT_TTL):
        """Return list of position type objects (e.g., G, F, C)."""
        s = self.settings(persist_ttl)
        pt = getattr(s, "position_types", None)
        if pt and hasattr(pt, "position_type"):
            return as_list(pt.position_type)
        return []

    def roster_positions(self, persist_ttl=DEFAULT_TTL):
        """Return list of roster position objects (e.g., PG, SG, SF, etc)."""
        s = self.settings(persist_ttl)
        rp = getattr(s, "roster_positions", None)
        if rp and hasattr(rp, "roster_position"):
            return as_list(rp.roster_position)
        return []

    def __repr__(self):
        return "League: {}".format(getattr(self, "name", "Unnamed League"))

    @property
    def past_league_id(self):
        """Get this league's previous year's league ID and game code

        If the commissioner has configured this, return a tuple of
        (game_code, league_id) for the previous season for this league

        Returns None if the league is not configured for league history

        Example:
        >>> lg = ctx.get_leagues(2022)[0]
        >>> lg.past_league_id
        (410, 12345)

        410 represents the NBA game code for 2021, 12345 is the league ID
        """
        full_league_key = getattr(self, "renew", None)
        if not full_league_key:
            return None
        full_league_key = str(full_league_key)
        # Full league keys are a combination of the game code and the league ID
        # In the raw response they look like 333_12345 where 333 is the game code and
        # 12345 is the league ID. However, due to how python ignores underscores in
        # numbers, specifically in the XML parsing library, it will come through as
        # a single integer that looks like 33312345
        # We can make an educated guess about what the league ID actually is though
        # given reasonable game codes based on our current league. We'll do that here
        current_season = self.season
        while True:
            try:
                last_years_game_code = get_game_id(self.game_code, current_season - 1)
            except ValueError:
                # We don't have any information about the previous year, give up
                return None
            last_years_game_code = str(last_years_game_code)
            if full_league_key.startswith(last_years_game_code):
                return (
                    int(last_years_game_code),
                    int(full_league_key[len(last_years_game_code) :]),
                )
            else:
                # Try the previous year
                current_season -= 1
