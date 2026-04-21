from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playercareerstats, teaminfocommon, teamyearbyyearstats, leaguestandings, leagueleaders
from flask import Flask, render_template, request, jsonify
from urllib.parse import unquote
import os
from datetime import datetime

# set up app
app = Flask(__name__)

player_stats_cache = {}

ALL_PLAYERS = players.get_players()

ALL_PLAYER_NAMES = sorted(
    [player["full_name"] for player in ALL_PLAYERS],
    key=lambda name: (name.split()[-1], name.split()[0])
)

team_stats_cache = {}

ALL_TEAMS = teams.get_teams()

ALL_TEAM_NAMES = sorted([team["full_name"] for team in ALL_TEAMS])

TEAM_LOOKUP = {
    team["full_name"].lower(): team
    for team in ALL_TEAMS
}

standings_cache = None
standings_cache_season = None

leaders_cache = None
leaders_cache_season = None

def get_all_player_names():
    return ALL_PLAYER_NAMES

def get_all_team_names():
    return ALL_TEAM_NAMES

def get_current_season_string():
    return str(int(datetime.now().year) - 1) + "-" + datetime.now().strftime("%y")

def get_leaders_for_category(stat_category):
    leaders_data = leagueleaders.LeagueLeaders(
        season=get_current_season_string(),
        stat_category_abbreviation=stat_category,
        per_mode48="PerGame",
        scope="S",
        season_type_all_star="Regular Season"
    )

    leaders_dict = leaders_data.get_dict()
    leaders_rows = []

    # LeagueLeaders often comes back as a single resultSet, not resultSets
    if "resultSet" in leaders_dict:
        headers = leaders_dict["resultSet"]["headers"]
        rows = leaders_dict["resultSet"]["rowSet"]

        for row in rows:
            leaders_rows.append(dict(zip(headers, row)))

    elif "resultSets" in leaders_dict:
        for result_set in leaders_dict["resultSets"]:
            if result_set.get("name") == "LeagueLeaders":
                headers = result_set["headers"]
                rows = result_set["rowSet"]

                for row in rows:
                    leaders_rows.append(dict(zip(headers, row)))
                break

    return leaders_rows[:10]

# serve index page
@app.route("/")
def index():
    return render_template("index.html")


# route to players
@app.route("/players")
@app.route("/players/<letter>")
def playersPage(letter="A"):
    letter = letter.upper()
    all_players = get_all_player_names()

    filtered_players = [
        p for p in all_players
        if p.split()[-1][0].upper() == letter
    ]

    alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    return render_template(
        "players.html",
        players=filtered_players,
        alphabet=alphabet,
        selected_letter=letter
    )

@app.route("/player/<path:name>")
def playerPage(name):
    name = unquote(name)

    found_players = players.find_players_by_full_name(name)
    if not found_players:
        return render_template("player.html", error="Player not found", player_name=name)

    player = found_players[0]

    if player["full_name"].lower() != name.lower():
        return render_template("player.html", error="Player not found", player_name=name)

    player_id = player["id"]

    if player_id in player_stats_cache:
        season_stats = player_stats_cache[player_id]
    else:
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        career_data = career.get_dict()

        season_stats = []
        if "resultSets" in career_data:
            for result_set in career_data["resultSets"]:
                if result_set.get("name") == "SeasonTotalsRegularSeason":
                    headers = result_set["headers"]
                    rows = result_set["rowSet"]

                    for row in rows:
                        season_stats.append(dict(zip(headers, row)))
                    break

        player_stats_cache[player_id] = season_stats

    return render_template(
        "player.html",
        player_name=player["full_name"],
        season_stats=season_stats
    )


# route to teams
@app.route("/teams")
def teamsPage():
    all_teams = get_all_team_names()

    return render_template(
        "teams.html",
        teams=all_teams
    )

@app.route("/team/<path:name>")
def teamPage(name):
    name = unquote(name)

    team = TEAM_LOOKUP.get(name.lower())
    if not team:
        return render_template("team.html", error="Team not found", team_name=name)

    team_id = team["id"]

    if team_id in team_stats_cache:
        season_stats = team_stats_cache[team_id]
    else:
        team_data = teamyearbyyearstats.TeamYearByYearStats(team_id=team_id)
        stats_dict = team_data.get_dict()

        season_stats = []
        if "resultSets" in stats_dict:
            for result_set in stats_dict["resultSets"]:
                if result_set.get("name") == "TeamStats":
                    headers = result_set["headers"]
                    rows = result_set["rowSet"]

                    for row in rows:
                        season_stats.append(dict(zip(headers, row)))
                    break

        team_stats_cache[team_id] = season_stats

    return render_template(
        "team.html",
        team_name=team["full_name"],
        season_stats=season_stats
    )


# route to search
@app.route("/search")
def search():
    query = request.args.get("q", "").strip()

    player_results = []
    team_results = []

    if query:
        lower_query = query.lower()

        all_players = get_all_player_names()
        all_teams = get_all_team_names()

        player_results = [
            player for player in all_players
            if lower_query in player.lower()
        ]

        team_results = [
            team for team in all_teams
            if lower_query in team.lower()
        ]

    return render_template(
        "search_results.html",
        query=query,
        player_results=player_results,
        team_results=team_results
    )

# route to standings
@app.route("/standings")
def standingsPage():
    global standings_cache, standings_cache_season

    current_season = get_current_season_string()

    if standings_cache is not None and standings_cache_season == current_season:
        east_standings, west_standings = standings_cache
    else:
        standings_data = leaguestandings.LeagueStandings(
            league_id="00",
            season=current_season
        )
        standings_dict = standings_data.get_dict()

        standings_rows = []
        if "resultSets" in standings_dict:
            for result_set in standings_dict["resultSets"]:
                headers = result_set["headers"]
                rows = result_set["rowSet"]

                for row in rows:
                    standings_rows.append(dict(zip(headers, row)))
                break

        east_standings = [team for team in standings_rows if team["Conference"] == "East"]
        west_standings = [team for team in standings_rows if team["Conference"] == "West"]

        east_standings.sort(key=lambda team: int(team["PlayoffRank"]))
        west_standings.sort(key=lambda team: int(team["PlayoffRank"]))

        standings_cache = (east_standings, west_standings)
        standings_cache_season = current_season

    return render_template(
        "standings.html",
        east_standings=east_standings,
        west_standings=west_standings,
        season=current_season
    )

# route to leaders
@app.route("/leaders")
def leadersPage():
    global leaders_cache, leaders_cache_season

    current_season = get_current_season_string()

    if leaders_cache is not None and leaders_cache_season == current_season:
        leaders_data = leaders_cache
    else:
        leaders_data = {
            "points": get_leaders_for_category("PTS"),
            "rebounds": get_leaders_for_category("REB"),
            "assists": get_leaders_for_category("AST"),
            "steals": get_leaders_for_category("STL"),
            "blocks": get_leaders_for_category("BLK")
        }

        leaders_cache = leaders_data
        leaders_cache_season = current_season

    return render_template(
        "leaders.html",
        season=current_season,
        leaders_data=leaders_data
    )

# returns list of player names
@app.route("/api/players", methods=["GET"])
def listPlayers():
    all_players = players.get_players()
    return jsonify([player["full_name"] for player in all_players])


# returns list of team names
@app.route("/api/teams", methods=["GET"])
def listTeams():
    all_teams = teams.get_teams()
    return jsonify([team["full_name"] for team in all_teams])


# returns data for given player by full player name
@app.route("/api/player/<name>", methods=["GET"])
def getPlayerData(name):
    found_players = players.find_players_by_full_name(name)

    if not found_players:
        return jsonify({"error": "Player not found"}), 404

    player = found_players[0]

    if player["full_name"].lower() == name.lower():
        career = playercareerstats.PlayerCareerStats(player_id=player["id"])
        return jsonify(career.get_dict())

    return jsonify({"error": "Player not found"}), 404


# returns data for given team
@app.route("/api/team/<name>", methods=["GET"])
def getTeamData(name):
    found_teams = teams.find_teams_by_full_name(name)

    if not found_teams:
        return jsonify({"error": "Team not found"}), 404

    team = found_teams[0]

    if team["full_name"].lower() == name.lower():
        info = teaminfocommon.TeamInfoCommon(team_id=team["id"])
        return jsonify(info.get_dict())

    return jsonify({"error": "Team not found"}), 404


# search players and teams using a given query and show top results
@app.route("/api/search/<query>", methods=["GET"])
def getSearchSuggestions(query):
    search_players = players.find_players_by_full_name(query)
    search_teams = teams.find_teams_by_full_name(query)

    return jsonify(
        [player["full_name"] for player in search_players[:5]] +
        [team["full_name"] for team in search_teams[:5]]
    )

# return standings for current season
@app.route("/api/standings", methods=["GET"])
def getCurrentStandings():
    standings = leaguestandings.LeagueStandings(league_id = "00", season = str(int(datetime.now().year) - 1) + "-" + datetime.now().strftime("%y"))
    return jsonify(standings.get_dict())

# return leaders for current season
@app.route("/api/leaders", methods=["GET"])
def getCurrentLeaders():
    leaders = leagueleaders.LeagueLeaders(season = str(int(datetime.now().year) - 1) + "-" + datetime.now().strftime("%y"))
    return jsonify(leaders.get_dict())


if __name__ == "__main__":
    app.run(debug=True, port=8000)
