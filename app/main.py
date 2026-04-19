from flask import Flask, render_template, request
from dotenv import load_dotenv
import os
import warnings

# set up app
load_dotenv()
API_KEY = os.getenv("API_KEY")
if API_KEY is None:
    warnings.warn("No API key found, statistics will be missing", FutureWarning)

app = Flask(__name__)

# Placeholder data
ALL_PLAYERS = [
    "LeBron James",
    "Kobe Bryant",
    "Stephen Curry",
    "Kevin Durant",
    "Nikola Jokic",
    "Giannis Antetokounmpo",
    "Kareem Abdul-Jabbar",
    "Shaquille O'Neal"
]

ALL_TEAMS = [
    "Atlanta Hawks",
    "Boston Celtics",
    "Brooklyn Nets",
    "Charlotte Hornets",
    "Chicago Bulls",
    "Cleveland Cavaliers",
    "Dallas Mavericks",
    "Denver Nuggets",
    "Detroit Pistons",
    "Golden State Warriors",
    "Houston Rockets",
    "Indiana Pacers",
    "Los Angeles Clippers",
    "Los Angeles Lakers",
    "Memphis Grizzlies",
    "Miami Heat",
    "Milwaukee Bucks",
    "Minnesota Timberwolves",
    "New Orleans Pelicans",
    "New York Knicks",
    "Oklahoma City Thunder",
    "Orlando Magic",
    "Philadelphia 76ers",
    "Phoenix Suns",
    "Portland Trail Blazers",
    "Sacramento Kings",
    "San Antonio Spurs",
    "Toronto Raptors",
    "Utah Jazz",
    "Washington Wizards"
]

# serve index page
@app.route("/")
def index():
    return render_template("index.html")

# route to players
@app.route("/players")
@app.route("/players/<letter>")
def players(letter="A"):
    letter = letter.upper()

    filtered_players = [
        p for p in ALL_PLAYERS if p.split()[-1][0].upper() == letter
    ]

    alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    return render_template(
        "players.html",
        players=filtered_players,
        alphabet=alphabet,
        selected_letter=letter
    )

# route to teams
@app.route("/teams")
@app.route("/teams/<letter>")
def teams(letter="A"):
    letter = letter.upper()

    filtered_teams = [
        team for team in ALL_TEAMS if team[0].upper() == letter
    ]

    alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    return render_template(
        "teams.html",
        teams=filtered_teams,
        alphabet=alphabet,
        selected_letter=letter
    )

# route to search
@app.route("/search")
def search():
    query = request.args.get("q", "").strip()

    player_results = []
    team_results = []

    if query:
        lower_query = query.lower()

        player_results = [
            player for player in ALL_PLAYERS
            if lower_query in player.lower()
        ]

        team_results = [
            team for team in ALL_TEAMS
            if lower_query in team.lower()
        ]

    return render_template(
        "search_results.html",
        query=query,
        player_results=player_results,
        team_results=team_results
    )

if __name__ == "__main__":
    app.run(debug=True, port=8000)