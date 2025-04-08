import tweepy
from nba_api.stats.endpoints import boxscoretraditionalv2, scoreboardv2
from datetime import datetime, timedelta, timezone
import time
import os
from supabase import create_client

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
#  SUPABASE CONNECTION   #
# ======================= #
supabase_url = "https://fjtxowbjnxclzcogostk.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZqdHhvd2JqbnhjbHpjb2dvc3RrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI2MDE5NTgsImV4cCI6MjA1ODE3Nzk1OH0.LPkFw-UX6io0F3j18Eefd1LmeAGGXnxL4VcCLOR_c1Q"
supabase = create_client(supabase_url, supabase_key)

# ======================= #
#     NBA STATS LOGIC     #
# ======================= #

def get_yesterday_date_str():
    est_now = datetime.now(timezone.utc) - timedelta(hours=4)
    yesterday = est_now - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")  # Use YYYY-MM-DD format for database

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
    top_points = {"player": "", "team": "", "value": 0}
    top_assists = {"player": "", "team": "", "value": 0}
    top_rebounds = {"player": "", "team": "", "value": 0}
    top_threes = {"player": "", "team": "", "value": 0}

    for game_id in game_ids:
        time.sleep(0.6)
        boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
        players = boxscore.get_normalized_dict()["PlayerStats"]

        for p in players:
            name = p["PLAYER_NAME"]
            team = p["TEAM_ABBREVIATION"]
            if p["PTS"] is not None and p["PTS"] > top_points["value"]:
                top_points = {"player": name, "team": team, "value": p["PTS"]}
            if p["AST"] is not None and p["AST"] > top_assists["value"]:
                top_assists = {"player": name, "team": team, "value": p["AST"]}
            if p["REB"] is not None and p["REB"] > top_rebounds["value"]:
                top_rebounds = {"player": name, "team": team, "value": p["REB"]}
            if p["FG3M"] is not None and p["FG3M"] > top_threes["value"]:
                top_threes = {"player": name, "team": team, "value": p["FG3M"]}

    return top_points, top_assists, top_rebounds, top_threes

def compose_tweet(date_str, points, assists, rebounds, threes):
    formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%m/%d/%Y")

    return f"""🏀 Court Kings – {formatted_date}

🔥 Points Leader
{points['player']} ({points['team']}): {points['value']} PTS

🎯 Assists Leader
{assists['player']} ({assists['team']}): {assists['value']} AST

💪 Rebounds Leader
{rebounds['player']} ({rebounds['team']}): {rebounds['value']} REB

🏹 3PT Leader
{threes['player']} ({threes['team']}): {threes['value']} 3PM

#NBA #NBAStats #CourtKingsHQ"""

# ============================= #
#   SAVE STATS TO SUPABASE      #
# ============================= #

def update_leaders_to_db(date_str, points, assists, rebounds, threes):
    payload = {
        "date": date_str,
        "data": {
            "points": points,
            "assists": assists,
            "rebounds": rebounds,
            "threept": threes
        }
    }

    try:
        # Upsert data into Supabase table "nightlykings" (overwrite if same date exists)
        response = supabase.table("nightlykings").upsert(payload, on_conflict="date").execute()
        print("✅ Supabase updated:", response)
    except Exception as e:
        print("❌ Supabase write error:", e)


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

        # Save stats to Supabase
        update_leaders_to_db(date_str, points, assists, rebounds, threes)

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    run_bot()
