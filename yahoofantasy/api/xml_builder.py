"""XML payload builders for Yahoo Fantasy API write operations."""

from xml.etree.ElementTree import Element, SubElement, tostring


def _to_xml_string(root):
    """Convert ElementTree element to XML string with declaration."""
    xml_bytes = tostring(root, encoding="unicode")
    return '<?xml version="1.0" encoding="UTF-8"?>' + xml_bytes


def build_roster_change_xml(coverage_type, week, players):
    """Build XML for roster/lineup changes.

    Args:
        coverage_type: "week" or "date"
        week: Week number (for week-based coverage)
        players: List of dicts with player_key and position
            Example: [{"player_key": "nba.p.5007", "position": "PG"}]

    Returns:
        XML string for PUT to /team/{team_key}/roster
    """
    root = Element("fantasy_content")
    roster = SubElement(root, "roster")

    cov_type = SubElement(roster, "coverage_type")
    cov_type.text = str(coverage_type)

    if coverage_type == "week" and week is not None:
        week_elem = SubElement(roster, "week")
        week_elem.text = str(week)

    players_elem = SubElement(roster, "players")
    for p in players:
        player_elem = SubElement(players_elem, "player")

        pk = SubElement(player_elem, "player_key")
        pk.text = str(p["player_key"])

        pos = SubElement(player_elem, "position")
        pos.text = str(p["position"])

    return _to_xml_string(root)


def build_add_player_xml(player_key, destination_team_key):
    """Build XML for adding a single player (free agent pickup).

    Args:
        player_key: The player key to add (e.g., "nba.p.5007")
        destination_team_key: The team key adding the player

    Returns:
        XML string for POST to /league/{league_key}/transactions
    """
    root = Element("fantasy_content")
    transaction = SubElement(root, "transaction")

    tx_type = SubElement(transaction, "type")
    tx_type.text = "add"

    players_elem = SubElement(transaction, "players")
    player_elem = SubElement(players_elem, "player")

    pk = SubElement(player_elem, "player_key")
    pk.text = str(player_key)

    tx_data = SubElement(player_elem, "transaction_data")
    tx_type_inner = SubElement(tx_data, "type")
    tx_type_inner.text = "add"
    dest = SubElement(tx_data, "destination_team_key")
    dest.text = str(destination_team_key)

    return _to_xml_string(root)


def build_drop_player_xml(player_key, source_team_key):
    """Build XML for dropping a single player.

    Args:
        player_key: The player key to drop
        source_team_key: The team key dropping the player

    Returns:
        XML string for POST to /league/{league_key}/transactions
    """
    root = Element("fantasy_content")
    transaction = SubElement(root, "transaction")

    tx_type = SubElement(transaction, "type")
    tx_type.text = "drop"

    players_elem = SubElement(transaction, "players")
    player_elem = SubElement(players_elem, "player")

    pk = SubElement(player_elem, "player_key")
    pk.text = str(player_key)

    tx_data = SubElement(player_elem, "transaction_data")
    tx_type_inner = SubElement(tx_data, "type")
    tx_type_inner.text = "drop"
    src = SubElement(tx_data, "source_team_key")
    src.text = str(source_team_key)

    return _to_xml_string(root)


def build_add_drop_xml(add_player_key, destination_team_key, drop_player_key, source_team_key):
    """Build XML for add/drop combo transaction.

    Args:
        add_player_key: The player key to add
        destination_team_key: The team key adding the player
        drop_player_key: The player key to drop
        source_team_key: The team key dropping the player

    Returns:
        XML string for POST to /league/{league_key}/transactions
    """
    root = Element("fantasy_content")
    transaction = SubElement(root, "transaction")

    tx_type = SubElement(transaction, "type")
    tx_type.text = "add/drop"

    players_elem = SubElement(transaction, "players")

    # Add player
    add_player_elem = SubElement(players_elem, "player")
    pk_add = SubElement(add_player_elem, "player_key")
    pk_add.text = str(add_player_key)
    tx_data_add = SubElement(add_player_elem, "transaction_data")
    tx_type_add = SubElement(tx_data_add, "type")
    tx_type_add.text = "add"
    dest = SubElement(tx_data_add, "destination_team_key")
    dest.text = str(destination_team_key)

    # Drop player
    drop_player_elem = SubElement(players_elem, "player")
    pk_drop = SubElement(drop_player_elem, "player_key")
    pk_drop.text = str(drop_player_key)
    tx_data_drop = SubElement(drop_player_elem, "transaction_data")
    tx_type_drop = SubElement(tx_data_drop, "type")
    tx_type_drop.text = "drop"
    src = SubElement(tx_data_drop, "source_team_key")
    src.text = str(source_team_key)

    return _to_xml_string(root)


def build_waiver_claim_xml(
    player_key, destination_team_key, faab_bid=None, drop_player_key=None, source_team_key=None
):
    """Build XML for waiver claim with optional FAAB bid and drop.

    Args:
        player_key: The player key to claim
        destination_team_key: The team key claiming the player
        faab_bid: Optional FAAB bid amount (for FAAB leagues)
        drop_player_key: Optional player to drop when claim processes
        source_team_key: Required if drop_player_key is provided

    Returns:
        XML string for POST to /league/{league_key}/transactions
    """
    root = Element("fantasy_content")
    transaction = SubElement(root, "transaction")

    # Type depends on whether we're also dropping
    tx_type = SubElement(transaction, "type")
    if drop_player_key:
        tx_type.text = "add/drop"
    else:
        tx_type.text = "add"

    # FAAB bid if provided
    if faab_bid is not None:
        faab = SubElement(transaction, "faab_bid")
        faab.text = str(faab_bid)

    players_elem = SubElement(transaction, "players")

    # Player to add (waiver claim)
    add_player_elem = SubElement(players_elem, "player")
    pk_add = SubElement(add_player_elem, "player_key")
    pk_add.text = str(player_key)
    tx_data_add = SubElement(add_player_elem, "transaction_data")
    tx_type_add = SubElement(tx_data_add, "type")
    tx_type_add.text = "add"
    dest = SubElement(tx_data_add, "destination_team_key")
    dest.text = str(destination_team_key)

    # Player to drop if provided
    if drop_player_key and source_team_key:
        drop_player_elem = SubElement(players_elem, "player")
        pk_drop = SubElement(drop_player_elem, "player_key")
        pk_drop.text = str(drop_player_key)
        tx_data_drop = SubElement(drop_player_elem, "transaction_data")
        tx_type_drop = SubElement(tx_data_drop, "type")
        tx_type_drop.text = "drop"
        src = SubElement(tx_data_drop, "source_team_key")
        src.text = str(source_team_key)

    return _to_xml_string(root)


def build_cancel_waiver_xml(transaction_key):
    """Build XML for cancelling a pending waiver claim.

    Args:
        transaction_key: The transaction key to cancel

    Returns:
        XML string for PUT to /transaction/{transaction_key}
    """
    root = Element("fantasy_content")
    transaction = SubElement(root, "transaction")

    tk = SubElement(transaction, "transaction_key")
    tk.text = str(transaction_key)

    tx_type = SubElement(transaction, "type")
    tx_type.text = "pending_trade"  # Used for cancellation

    action = SubElement(transaction, "action")
    action.text = "cancel"

    return _to_xml_string(root)
