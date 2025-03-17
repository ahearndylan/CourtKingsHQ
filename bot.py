import tweepy
import requests
from datetime import datetime
import os

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
    return "03/14/2025"  # ✅ Hardcoded for testing

def get_stat_leaders(date_str):
    formatted_date = datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
    url = f"https://www.balldontlie.io/api/v1/stats?start_date={formatted_date}&end_date={formatted_date}&per_page=100"
    response = requests.get(url)

    if response.status_code != 200 or not response.text:
        raise Exception("Failed to fetch stats from BallDontLie API")

    try:
        data = response.json()
    except Exception:
        raise Exception("Invalid JSON response from BallDontLie API")

    stats = data["data"]

    top_points = {"name": "", "stat": 0}
    top_assists = {"name": "", "stat": 0}
    top_rebounds = {"name": "", "stat": 0}
    top_threes = {"name": "", "stat": 0}

    for p in stats:
        player_name = f"{p['player']['first_name']} {p['player']['last_name']}"
        if p["pts"] > top_points["stat"]:
            top_points = {"name": player_name, "stat": p["pts"]}
        if p["ast"] > top_assists["stat"]:
            top_assists = {"name": player_name, "stat": p["ast"]}
        if p["reb"] > top_rebounds["stat"]:
            top_rebounds = {"name": player_name, "stat": p["reb"]}
        if p["fg3m"] > top_threes["stat"]:
            top_threes = {"name": player_name, "stat": p["fg3m"]}

    return top_points, top_assists, top_rebounds, top_threes

def compose_tweet(date_str, points, assists, rebounds, threes):
    tweet = f"""🏀 Stat Kings – {date_str}

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
    try:
        points, assists, rebounds, threes = get_stat_leaders(date_str)
    except Exception as e:
        print("Error fetching stats:", e)
        return

    tweet = compose_tweet(date_str, points, assists, rebounds, threes)
    print("Tweeting:\n", tweet)
    client.create_tweet(text=tweet)

if __name__ == "__main__":
    run_bot()
