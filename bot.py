import tweepy
import os
import requests
from datetime import datetime, timedelta
import time

# ======================= #
# TWITTER AUTHENTICATION  #
# ======================= #
bearer_token = os.getenv("BEARER_TOKEN")
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
access_token = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

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
    est_now = datetime.utcnow() - timedelta(hours=5)
    nba_date = est_now - timedelta(days=1)
    return nba_date.strftime("%Y-%m-%d")  # Format for BallDontLie

def get_stat_leaders(date_str):
    url = f"https://www.balldontlie.io/api/v1/stats?start_date={date_str}&end_date={date_str}&per_page=100"
    leaders = {
        "points": {"name": "", "stat": 0},
        "assists": {"name": "", "stat": 0},
        "rebounds": {"name": "", "stat": 0},
        "threes": {"name": "", "stat": 0},
        "minutes": {"name": "", "stat": 0.0}
    }

    page = 1
    while True:
        response = requests.get(url + f"&page={page}")
        data = response.json()
        stats = data["data"]

        if not stats:
            break

        for p in stats:
            player_name = f"{p['player']['first_name']} {p['player']['last_name']}"
            if p["pts"] > leaders["points"]["stat"]:
                leaders["points"] = {"name": player_name, "stat": p["pts"]}
            if p["ast"] > leaders["assists"]["stat"]:
                leaders["assists"] = {"name": player_name, "stat": p["ast"]}
            if p["reb"] > leaders["rebounds"]["stat"]:
                leaders["rebounds"] = {"name": player_name, "stat": p["reb"]}
            if p["fg3m"] > leaders["threes"]["stat"]:
                leaders["threes"] = {"name": player_name, "stat": p["fg3m"]}
            if p["min"]:
                try:
                    minutes = float(p["min"].split(":")[0]) if ":" in p["min"] else float(p["min"])
                    if minutes > leaders["minutes"]["stat"]:
                        leaders["minutes"] = {"name": player_name, "stat": round(minutes, 1)}
                except:
                    pass

        if not data["meta"]["next_page"]:
            break
        page += 1
        time.sleep(0.4)  # Friendly API usage

    return leaders["points"], leaders["assists"], leaders["rebounds"], leaders["threes"], leaders["minutes"]

def compose_tweet(date_str, points, assists, rebounds, threes, minutes):
    tweet = f"""🏀 Stat Kings – {datetime.strptime(date_str, '%Y-%m-%d').strftime('%m/%d/%Y')}

🔥 Points Leader
{points['name']}: {points['stat']} PTS

🎯 Assists Leader
{assists['name']}: {assists['stat']} AST

💪 Rebounds Leader
{rebounds['name']}: {rebounds['stat']} REB

🏹 3PT Leader
{threes['name']}: {threes['stat']} 3PM

#NBA #NBATwitter #NBAStats #StatKingsHQ\n"""
    return tweet

# ======================= #
#        MAIN BOT         #
# ======================= #

def run_bot():
    date_str = get_nba_game_date_str()
    points, assists, rebounds, threes, minutes = get_stat_leaders(date_str)
    tweet = compose_tweet(date_str, points, assists, rebounds, threes, minutes)
    print("Tweeting:\n", tweet)
    client.create_tweet(text=tweet)

if __name__ == "__main__":
    run_bot()
