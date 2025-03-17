import tweepy
from nba_api.stats.endpoints import boxscoretraditionalv2, scoreboardv2
from datetime import datetime, timedelta, timezone
import time
import os

# ======================= #
# TWITTER AUTHENTICATION  #
# ======================= #
bearer_token = "AAAAAAAAAAAAAAAAAAAAAPztzwEAAAAAvBGCjApPNyqj9c%2BG7740SkkTShs%3DTCpOQ0DMncSMhaW0OA4UTPZrPRx3BHjIxFPzRyeoyMs2KHk6hM"
api_key = "uKyGoDr5LQbLvu9i7pgFrAnBr"
api_secret = "KGBVtj1BUmAEsyoTmZhz67953ItQ8TIDcChSpodXV8uGMPXsoH"
access_token = "1901441558596988929-WMdEPOtNDj7QTJgLHVylxnylI9ObgD"
access_token_secret = "9sf83R8A0MBdijPdns6nWaG7HF47htcWo6oONPmMS7o98"

client = tweepy.Client(
    bearer_token=bearer_token,
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)

# ======================= #
#     NBA STATS LOGIC     #
# ======================= #

def get_nba_game_date_str():
    # Convert UTC to EST (UTC-5)
    utc_now = datetime.now(timezone.utc)
    est_now = utc_now - timedelta(hours=5)

    # Always get the previous day's date to ensure games are finished
    nba_date = est_now - timedelta(days=1)
    return nba_date.strftime("%m/%d/%Y")


def get_game_ids_for_date(date_str):
    scoreboard = scoreboardv2.ScoreboardV2(game_date=date_str)
    games = scoreboard.get_normalized_dict()["GameHeader"]
    return [game["GAME_ID"] for game in games]

def get_stat_leaders(game_ids):
    top_points = {"name": "", "stat": 0}
    top_assists = {"name": "", "stat": 0}
    top_rebounds = {"name": "", "stat": 0}
    top_threes = {"name": "", "stat": 0}
    top_minutes = {"name": "", "stat": 0.0}

    for game_id in game_ids:
        time.sleep(0.6)
        boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
        players = boxscore.get_normalized_dict()["PlayerStats"]

        for p in players:
            if p["PTS"] is not None and p["PTS"] > top_points["stat"]:
                top_points = {"name": p["PLAYER_NAME"], "stat": p["PTS"]}
            if p["AST"] is not None and p["AST"] > top_assists["stat"]:
                top_assists = {"name": p["PLAYER_NAME"], "stat": p["AST"]}
            if p["REB"] is not None and p["REB"] > top_rebounds["stat"]:
                top_rebounds = {"name": p["PLAYER_NAME"], "stat": p["REB"]}
            if p["FG3M"] is not None and p["FG3M"] > top_threes["stat"]:
                top_threes = {"name": p["PLAYER_NAME"], "stat": p["FG3M"]}
            if p["MIN"]:
                try:
                    min_val = p["MIN"]
                    if ":" in min_val:
                        minutes_part = min_val.split(":")[0]
                        total_minutes = float(minutes_part)
                    else:
                        total_minutes = float(min_val)
                    if total_minutes > top_minutes["stat"]:
                        top_minutes = {"name": p["PLAYER_NAME"], "stat": round(total_minutes, 1)}
                except:
                    pass

    return top_points, top_assists, top_rebounds, top_threes, top_minutes

def compose_tweet(date_str, points, assists, rebounds, threes, minutes):
    tweet = f"""🏀 Stat Kings – {date_str}

🔥 Points Leader
{points['name']}: {points['stat']} PTS

🎯 Assists Leader
{assists['name']}: {assists['stat']} AST

💪 Rebounds Leader
{rebounds['name']}: {rebounds['stat']} REB

🏹 3PT Leader
{threes['name']}: {threes['stat']} 3PM

#NBA #NBATwitter #NBAStats #StatKingsHQ"""
    return tweet

# ======================= #
#        MAIN BOT         #
# ======================= #

def run_bot():
    date_str = get_nba_game_date_str()
    game_ids = get_game_ids_for_date(date_str)
    if not game_ids:
        print("No games found for", date_str)
        return

    points, assists, rebounds, threes, minutes = get_stat_leaders(game_ids)
    tweet = compose_tweet(date_str, points, assists, rebounds, threes, minutes)
    print("Tweeting:\n", tweet)
    client.create_tweet(text=tweet)

if __name__ == "__main__":
    run_bot()
