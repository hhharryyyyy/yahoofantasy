## NBA Matchup Planner Roadmap (Read-only v1)

Reference: Yahoo Fantasy Sports API Guide: [link](https://developer.yahoo.com/fantasysports/guide/)

### Legend
- [x] Completed
- [ ] Planned
- [~] In progress

## v1 Essentials (Read-only, large initial sync + light refreshes)

### Core
- [x] NBA-only context and auth (OAuth2, token refresh)
- [x] Persistence cache with TTL; per-endpoint sensible defaults
- [x] Add request backoff/retries for 429/5xx (exponential with jitter; honor Retry-After)

### League configuration (required for 9-cat)
- [x] League.settings()
  - URI: `league/{league_key}/settings`
  - Returns: `scoring_type`, `stat_categories`, `position_types`, `roster_positions`, playoffs schedule, lineup lock policy
- [x] League.stat_categories() (explicit helper)
- [x] League.position_types() and League.roster_positions() (explicit helpers)

### Player discovery and filtering
- [x] League.players(position=None, status=None, search=None, sort=None, sort_type=None, start=0, count=25)
  - URI: `league/{league_key}/players;{filters}`
  - Filters: `position`(G/F/C), `status`(A/FA/W/T/K), `search`, `sort`, `sort_type`, pagination

### Ownership and extras
- [x] Player.ownership()
  - URI: `league/{league_key}/players;player_keys={player_key}/ownership`
- [ ] Player.draft_analysis() [optional for v1]

### Scoreboards, rosters, transactions
- [x] League.weeks() resilient behavior for NBA H2H
- [ ] Efficient initial sync plan:
  - leagues → teams → settings → scoreboard (needed weeks) → each team’s roster by week → league transactions (full)
- [ ] Efficient refresh plan (helpers):
  - transactions: pull newest since last timestamp
  - scoreboard: current and next week only
  - rosters: current week only (optionally next)
  - players list: on-demand or long TTL

### Incremental sync helpers
- [x] Context.sync_initial(season) → returns a structured snapshot for planner
- [x] League.sync_delta(last_tx_ts, current_week) → returns deltas to apply

### Testing and docs
- [ ] Unit tests for new endpoints (settings, players filters, ownership)
- [ ] Example script: print league settings and confirm 9-cat
- [ ] Document TTL policy and refresh strategy

## v1 Nice-to-haves (still read-only)
- [ ] Team.matchups(start_week=None, end_week=None)
- [ ] Team.stats(type='season'|'week', week=None)
- [ ] Player.injury()/notes() where supported

## v2 (post‑v1, optional)

### Write operations (not needed for initial planner)
- [ ] Transactions POST (add/drop/add-drop with FAAB)
- [ ] Trades (propose/accept/reject/cancel; league-dependent permissions)
- [ ] Edit/cancel waiver claims

### CLI enhancements
- [ ] yahoofantasy dump players --position/--status/--search/--sort
- [ ] yahoofantasy dump ownership
- [ ] yahoofantasy league settings

### Reliability and DX
- [~] Network backoff configuration via env (YF_MAX_RETRIES, YF_BACKOFF_BASE_SEC)
- [ ] Script to auto-update NBA game IDs for new seasons


