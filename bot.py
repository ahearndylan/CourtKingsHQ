import tweepy
import requests
from datetime import datetime, timedelta
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

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com"
}

def get_nba_game_date_str():
    est_now = datetime.utcnow() - timedelta(hours=5)  # crude UTC -> EST
    nba_date = est_now - timedelta(days=1)
    return nba_date.strftime("%Y-%m-%d")

def get_stat_leaders(date_str):
    url = f"https://api-nba-v1.p.rapidapi.com/games"
    params = {"date": date_str}
    game_response = requests.get(url, headers=HEADERS, params=params)
    games = game_response.json().get("response", [])

    if not games:
        raise Exception("No games found")

    player_stats = []
    for game in games:
        game_id = game["id"]
        stats_url = f"https://api-nba-v1.p.rapidapi.com/players/statistics"
        stats_params = {"game": game_id}
        stats_resp = requests.get(stats_url, headers=HEADERS, params=stats_params)
        player_stats.extend(stats_resp.json().get("response", []))

    top_points = {"name": "", "stat": 0}
    top_assists = {"name": "", "stat": 0}
    top_rebounds = {"name": "", "stat": 0}
    top_threes = {"name": "", "stat": 0}

    for stat in player_stats:
        name = f"{stat['player']['firstname']} {stat['player']['lastname']}"
        if stat["points"] > top_points["stat"]:
            top_points = {"name": name, "stat": stat["points"]}
        if stat["assists"] > top_assists["stat"]:
            top_assists = {"name": name, "stat": stat["assists"]}
        if stat["totReb"] > top_rebounds["stat"]:
            top_rebounds = {"name": name, "stat": stat["totReb"]}
        if stat["tpm"] > top_threes["stat"]:
            top_threes = {"name": name, "stat": stat["tpm"]}

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
