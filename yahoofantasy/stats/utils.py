from .nba import stats as stats_nba


def get_stat_from_value(stat_obj):
    """Given a stat_obj, get a Stat object with an associated value (NBA only)"""
    stats = stats_nba

    stat_id = str(stat_obj.stat_id)
    stat_lookup = stats.get(stat_id)
    if not stat_lookup:
        raise ValueError("Stat ID {} not found in NBA stats".format(stat_id))

    from .stat import Stat

    stat = Stat.from_dict(stat_id, stat_lookup)
    stat.value = stat_obj.value
    return stat


def get_stat_from_stat_list(stat_display, stat_list):
    """Resolve a stat value from a list by display name (NBA only)."""
    stats = stats_nba

    target_stat_id = None
    for stat_id, stat_data in stats.items():
        if stat_data["display"] == stat_display:
            target_stat_id = stat_id
            break
    else:
        raise ValueError("Stat {} not found in NBA stats".format(stat_display))

    for stat in stat_list:
        if str(stat.stat_id) == str(target_stat_id):
            return stat.value
    else:
        raise ValueError(
            "Stat {}(id:{}) not found in input stat list".format(stat_display, target_stat_id)
        )
