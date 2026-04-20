from nba_api.stats.static import players
from nba_api.stats.static import teams
from nba_api.stats.endpoints import playercareerstats
from nba_api.stats.endpoints import teaminfocommon
from flask import Flask, render_template, request, jsonify
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
def playersPage(letter="A"):
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
def teamsPage(letter="A"):
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

# returns list of player names
@app.route("/api/players", methods=["GET"])
def listPlayers():
    allPlayers = players.get_players()
    return jsonify([player["full_name"] for player in allPlayers])

# returns list of team names
@app.route("/api/teams", methods=["GET"])
def listTeams():
    allTeams = teams.get_teams()
    return jsonify([team["full_name"] for team in allTeams])

# returns data for given player by full player name
@app.route("/api/player/<name>", methods=["GET"])
def getPlayerData(name):

    # attempt to look up player and continue if names match
    player = players.find_players_by_full_name(name)[0]
    if player["full_name"].lower() == name.lower():
        career = playercareerstats.PlayerCareerStats(player["id"])
        return jsonify(career.get_dict()) # return player career data
    
    # return none if player not found 
    else: 
        return None

# returns data for given team and continue if names match
@app.route("/api/team/<name>", methods=["GET"])
def getTeamData(name):
    team = teams.find_teams_by_full_name(name)[0]
    if team["full_name"].lower() == name.lower():
        info = teaminfocommon.TeamInfoCommon(team["id"])
        return jsonify(info.get_dict())
    else:
        return None

# search players and teams using a given query and show top results
@app.route("/api/search/<query>", methods=["GET"])
def getSearchSuggestions(query):
    
    # search players and teams using query
    searchPlayers = players.find_players_by_full_name(query)
    searchTeams = teams.find_teams_by_full_name(query)

    # return up to five results from each category
    return jsonify([player["full_name"] for player in searchPlayers[:5]] + [team["full_name"] for team in searchTeams[:5]])

if __name__ == "__main__":
    app.run(debug=True, port=8000)
