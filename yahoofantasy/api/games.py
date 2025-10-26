from collections import defaultdict

# NBA-only game ID mapping
games = defaultdict(dict)
games["nba"]["2001"] = 16
games["nba"]["2002"] = 67
games["nba"]["2003"] = 95
games["nba"]["2004"] = 112
games["nba"]["2005"] = 131
games["nba"]["2006"] = 165
games["nba"]["2007"] = 187
games["nba"]["2008"] = 211
games["nba"]["2009"] = 234
games["nba"]["2010"] = 249
games["nba"]["2011"] = 265
games["nba"]["2012"] = 304
games["nba"]["2013"] = 322
games["nba"]["2014"] = 342
games["nba"]["2015"] = 353
games["nba"]["2016"] = 364
games["nba"]["2017"] = 375
games["nba"]["2018"] = 385
games["nba"]["2019"] = 395
games["nba"]["2020"] = 402
games["nba"]["2021"] = 410
games["nba"]["2022"] = 418
games["nba"]["2023"] = 428
games["nba"]["2024"] = 454
games["nba"]["2025"] = 466


def get_game_id(game, season):
    season = str(season)
    if game != "nba":
        raise ValueError("{} is not a valid game; NBA-only build".format(game))
    if season not in games["nba"]:
        raise ValueError("{} is not a valid season for nba".format(season))
    return games["nba"][season]
