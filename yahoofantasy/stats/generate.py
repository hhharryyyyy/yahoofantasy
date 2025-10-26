import json
from os.path import join, dirname
from yahoofantasy.api.fetch import make_request
from yahoofantasy.api.parse import parse_response


def generate_stats(token):
    """Generate a python file with NBA stat mapping

    Args:
        token: An access token to talk to the API

    Returns:
        None - writes a file called nba.py with a stats export
    """
    stats_resp = parse_response(
        make_request("game/nba/stat_categories", token=token)
    )
    stats = stats_resp["fantasy_content"]["game"]["stat_categories"]["stats"][
        "stat"
    ]  # noqa E501
    mapping = {}
    for stat in stats:
        mapping[stat["stat_id"]["$"]] = {
            "name": stat["name"]["$"],
            "display": stat["display_name"]["$"],
            "order": int(stat["sort_order"]["$"]),
        }
    with open(join(dirname(__file__), "nba.py"), "w+") as f:
        f.write("stats=")
        json.dump(mapping, f)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("token")
    args = parser.parse_args()
    generate_stats(args.token)
