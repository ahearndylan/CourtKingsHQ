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

def get_yesterday_date_str():
    est_now = datetime.now(timezone.utc) - timedelta(hours=4)
    yesterday = est_now - timedelta(days=1)
    return yesterday.strftime("%m/%d/%Y")

def get_game_ids_for_date(date_str, max_retries=3):
    for attempt in range(max_retries):
        try:
            scoreboard = scoreboardv2.ScoreboardV2(game_date=date_str)
            games = scoreboard.get_normalized_dict()["GameHeader"]
            return [game["GAME_ID"] for game in games]
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2)
    raise Exception("Failed to fetch game IDs after multiple attempts.")

def get_stat_leaders(game_ids):
    top_points = {"name": "", "stat": 0, "team": ""}
    top_assists = {"name": "", "stat": 0, "team": ""}
    top_rebounds = {"name": "", "stat": 0, "team": ""}
    top_threes = {"name": "", "stat": 0, "team": ""}

    for game_id in game_ids:
        time.sleep(0.6)
        boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
        players = boxscore.get_normalized_dict()["PlayerStats"]

        for p in players:
            name = p["PLAYER_NAME"]
            team = p["TEAM_ABBREVIATION"]
            if p["PTS"] is not None and p["PTS"] > top_points["stat"]:
                top_points = {"name": name, "stat": p["PTS"], "team": team}
            if p["AST"] is not None and p["AST"] > top_assists["stat"]:
                top_assists = {"name": name, "stat": p["AST"], "team": team}
            if p["REB"] is not None and p["REB"] > top_rebounds["stat"]:
                top_rebounds = {"name": name, "stat": p["REB"], "team": team}
            if p["FG3M"] is not None and p["FG3M"] > top_threes["stat"]:
                top_threes = {"name": name, "stat": p["FG3M"], "team": team}

    return top_points, top_assists, top_rebounds, top_threes

def compose_tweet(date_str, points, assists, rebounds, threes):
    return f"""🏀 Stat Kings – {date_str}

🔥 Points Leader
{points['name']} ({points['team']}): {points['stat']} PTS

🎯 Assists Leader
{assists['name']} ({assists['team']}): {assists['stat']} AST

💪 Rebounds Leader
{rebounds['name']} ({rebounds['team']}): {rebounds['stat']} REB

🏹 3PT Leader
{threes['name']} ({threes['team']}): {threes['stat']} 3PM

#NBA #NBAStats #StatKingsHQ"""

# ======================= #
#        MAIN BOT         #
# ======================= #

def run_bot():
    date_str = get_yesterday_date_str()
    try:
        game_ids = get_game_ids_for_date(date_str)
        if not game_ids:
            print("No games found for", date_str)
            return

        points, assists, rebounds, threes = get_stat_leaders(game_ids)
        tweet = compose_tweet(date_str, points, assists, rebounds, threes)
        print("Tweeting:\n", tweet)
        client.create_tweet(text=tweet)

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    run_bot()
