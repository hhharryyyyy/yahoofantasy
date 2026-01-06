from yahoofantasy.util.logger import logger
from yahoofantasy.api.parse import as_list, from_response_object, parse_response
from yahoofantasy.api.xml_builder import build_roster_change_xml
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

    # -------------------------------------------------------------------------
    # Write Operations - Lineup Management
    # -------------------------------------------------------------------------

    def set_lineup(self, player_positions, week=None, coverage_type="week"):
        """Set player positions for a given week.

        Args:
            player_positions: List of tuples or dicts specifying positions
                - Tuple: (player_or_key, position)
                - Dict: {"player_key": "nba.p.5007", "position": "PG"}
            week: Week number (defaults to current week)
            coverage_type: "week" or "date" (default: "week")

        Returns:
            Updated Roster object

        Raises:
            InvalidPositionError: If player cannot play the position
            RosterError: On other roster errors

        Example:
            team.set_lineup([
                ("nba.p.5007", "PG"),
                (player_obj, "BN"),
            ], week=16)
        """
        if week is None:
            week = self.league.current_week()

        # Normalize player_positions to list of dicts
        players_data = []
        for item in player_positions:
            if isinstance(item, dict):
                players_data.append(item)
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                player, position = item
                player_key = player.player_key if hasattr(player, "player_key") else str(player)
                players_data.append({"player_key": player_key, "position": position})
            else:
                raise ValueError(
                    "player_positions must be list of tuples (player, position) "
                    "or dicts with player_key and position"
                )

        logger.debug("Setting lineup for team {} week {}".format(self.id, week))
        xml = build_roster_change_xml(coverage_type, week, players_data)
        self.ctx._make_write_request(
            "team/{}/roster".format(self.id), xml, method="PUT"
        )

        # Invalidate cached roster and return fresh one
        return self.roster(week)

    def move_to_bench(self, player, week=None):
        """Move a player to the bench.

        Args:
            player: Player object or player_key
            week: Week number (defaults to current week)

        Returns:
            Updated Roster object
        """
        return self.set_lineup([(player, "BN")], week=week)

    def move_to_active(self, player, position, week=None):
        """Move a player from bench to an active position.

        Args:
            player: Player object or player_key
            position: Target position (e.g., "PG", "SG", "SF", "PF", "C", "G", "F", "UTIL")
            week: Week number (defaults to current week)

        Returns:
            Updated Roster object
        """
        return self.set_lineup([(player, position)], week=week)

    def move_to_ir(self, player, week=None):
        """Move an injured player to IR slot.

        Args:
            player: Player object or player_key
            week: Week number (defaults to current week)

        Returns:
            Updated Roster object
        """
        return self.set_lineup([(player, "IL")], week=week)

    # -------------------------------------------------------------------------
    # Write Operations - Add/Drop Players
    # -------------------------------------------------------------------------

    def add_player(self, player, drop_player=None):
        """Add a free agent to this team.

        Args:
            player: Player object or player_key to add
            drop_player: Optional player to drop (for add/drop combo)

        Returns:
            Transaction object representing the completed transaction

        Raises:
            PlayerNotAvailableError: If player is not a free agent
            RosterFullError: If roster is full and no drop specified
        """
        if drop_player:
            return self.league.add_drop_player(player, drop_player, self)
        return self.league.add_player(player, self)

    def drop_player(self, player):
        """Drop a player from this team.

        Args:
            player: Player object or player_key to drop

        Returns:
            Transaction object
        """
        return self.league.drop_player(player, self)

    def claim_player(self, player, faab_bid=None, drop_player=None):
        """Submit a waiver claim for a player.

        Args:
            player: Player object or player_key to claim
            faab_bid: Optional FAAB bid amount (for FAAB leagues)
            drop_player: Optional player to drop when claim processes

        Returns:
            Transaction object (with status='pending' for waivers)
        """
        return self.league.claim_player(player, self, faab_bid=faab_bid, drop_player=drop_player)
