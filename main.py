from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playercareerstats, teaminfocommon, teamyearbyyearstats, leaguestandings, leagueleaders, scoreboardv2, boxscoretraditionalv2, playergamelog, commonplayoffseries, leaguegamelog, alltimeleadersgrids, drafthistory
from flask import Flask, render_template, request, jsonify, Response, send_from_directory, url_for
from urllib.parse import unquote
import os
from datetime import datetime, timedelta
from matplotlib.figure import Figure
import io

# set up app
app = Flask(__name__)

player_stats_cache = {}
game_log_cache = {}

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

PLAYER_LOOKUP = {
    player["full_name"].lower(): player
    for player in ALL_PLAYERS
}

TEAM_ABBR_LOOKUP = {
    team["abbreviation"].upper(): team
    for team in ALL_TEAMS
}

standings_cache = None
standings_cache_season = None

leaders_cache = None
leaders_cache_season = None
historical_leaders_cache = None

playoffs_cache = {}

AWARDS_BY_SEASON = {
    "2024-25": {
        "MVP":         {"name": "Shai Gilgeous-Alexander", "team": "Oklahoma City Thunder"},
        "Finals MVP":  {"name": "Shai Gilgeous-Alexander", "team": "Oklahoma City Thunder"},
        "DPOY":        {"name": "Evan Mobley",              "team": "Cleveland Cavaliers"},
        "ROY":         {"name": "Stephon Castle",           "team": "San Antonio Spurs"},
        "MIP":         {"name": "Dyson Daniels",            "team": "Atlanta Hawks"},
        "6MOY":        {"name": "Payton Pritchard",         "team": "Boston Celtics"},
        "COY":         {"name": "Mark Daigneault",          "team": "Oklahoma City Thunder"},
    },
    "2023-24": {
        "MVP":         {"name": "Nikola Jokic",             "team": "Denver Nuggets"},
        "Finals MVP":  {"name": "Jaylen Brown",             "team": "Boston Celtics"},
        "DPOY":        {"name": "Rudy Gobert",              "team": "Minnesota Timberwolves"},
        "ROY":         {"name": "Victor Wembanyama",        "team": "San Antonio Spurs"},
        "MIP":         {"name": "Tyrese Maxey",             "team": "Philadelphia 76ers"},
        "6MOY":        {"name": "Naz Reid",                 "team": "Minnesota Timberwolves"},
        "COY":         {"name": "Mark Daigneault",          "team": "Oklahoma City Thunder"},
    },
    "2022-23": {
        "MVP":         {"name": "Joel Embiid",              "team": "Philadelphia 76ers"},
        "Finals MVP":  {"name": "Nikola Jokic",             "team": "Denver Nuggets"},
        "DPOY":        {"name": "Jaren Jackson Jr.",        "team": "Memphis Grizzlies"},
        "ROY":         {"name": "Paolo Banchero",           "team": "Orlando Magic"},
        "MIP":         {"name": "Lauri Markkanen",          "team": "Utah Jazz"},
        "6MOY":        {"name": "Malcolm Brogdon",          "team": "Boston Celtics"},
        "COY":         {"name": "Mike Brown",               "team": "Sacramento Kings"},
    },
    "2021-22": {
        "MVP":         {"name": "Nikola Jokic",             "team": "Denver Nuggets"},
        "Finals MVP":  {"name": "Stephen Curry",            "team": "Golden State Warriors"},
        "DPOY":        {"name": "Marcus Smart",             "team": "Boston Celtics"},
        "ROY":         {"name": "Scottie Barnes",           "team": "Toronto Raptors"},
        "MIP":         {"name": "Ja Morant",                "team": "Memphis Grizzlies"},
        "6MOY":        {"name": "Tyler Herro",              "team": "Miami Heat"},
        "COY":         {"name": "Monty Williams",           "team": "Phoenix Suns"},
    },
    "2020-21": {
        "MVP":         {"name": "Nikola Jokic",             "team": "Denver Nuggets"},
        "Finals MVP":  {"name": "Giannis Antetokounmpo",   "team": "Milwaukee Bucks"},
        "DPOY":        {"name": "Rudy Gobert",              "team": "Utah Jazz"},
        "ROY":         {"name": "LaMelo Ball",              "team": "Charlotte Hornets"},
        "MIP":         {"name": "Julius Randle",            "team": "New York Knicks"},
        "6MOY":        {"name": "Jordan Clarkson",          "team": "Utah Jazz"},
        "COY":         {"name": "Quin Snyder",              "team": "Utah Jazz"},
    },
    "2019-20": {
        "MVP":         {"name": "Giannis Antetokounmpo",   "team": "Milwaukee Bucks"},
        "Finals MVP":  {"name": "LeBron James",             "team": "Los Angeles Lakers"},
        "DPOY":        {"name": "Giannis Antetokounmpo",   "team": "Milwaukee Bucks"},
        "ROY":         {"name": "Ja Morant",                "team": "Memphis Grizzlies"},
        "MIP":         {"name": "Brandon Ingram",           "team": "New Orleans Pelicans"},
        "6MOY":        {"name": "Montrezl Harrell",         "team": "Los Angeles Clippers"},
        "COY":         {"name": "Nick Nurse",               "team": "Toronto Raptors"},
    },
    "2018-19": {
        "MVP":         {"name": "Giannis Antetokounmpo",   "team": "Milwaukee Bucks"},
        "Finals MVP":  {"name": "Kawhi Leonard",            "team": "Toronto Raptors"},
        "DPOY":        {"name": "Rudy Gobert",              "team": "Utah Jazz"},
        "ROY":         {"name": "Luka Doncic",              "team": "Dallas Mavericks"},
        "MIP":         {"name": "Pascal Siakam",            "team": "Toronto Raptors"},
        "6MOY":        {"name": "Lou Williams",             "team": "Los Angeles Clippers"},
        "COY":         {"name": "Mike Budenholzer",         "team": "Milwaukee Bucks"},
    },
    "2017-18": {
        "MVP":         {"name": "James Harden",             "team": "Houston Rockets"},
        "Finals MVP":  {"name": "Kevin Durant",             "team": "Golden State Warriors"},
        "DPOY":        {"name": "Rudy Gobert",              "team": "Utah Jazz"},
        "ROY":         {"name": "Ben Simmons",              "team": "Philadelphia 76ers"},
        "MIP":         {"name": "Victor Oladipo",           "team": "Indiana Pacers"},
        "6MOY":        {"name": "Lou Williams",             "team": "Los Angeles Clippers"},
        "COY":         {"name": "Dwane Casey",              "team": "Toronto Raptors"},
    },
    "2016-17": {
        "MVP":         {"name": "Russell Westbrook",        "team": "Oklahoma City Thunder"},
        "Finals MVP":  {"name": "Kevin Durant",             "team": "Golden State Warriors"},
        "DPOY":        {"name": "Draymond Green",           "team": "Golden State Warriors"},
        "ROY":         {"name": "Malcolm Brogdon",          "team": "Milwaukee Bucks"},
        "MIP":         {"name": "Giannis Antetokounmpo",   "team": "Milwaukee Bucks"},
        "6MOY":        {"name": "Eric Gordon",              "team": "Houston Rockets"},
        "COY":         {"name": "Mike D'Antoni",            "team": "Houston Rockets"},
    },
    "2015-16": {
        "MVP":         {"name": "Stephen Curry",            "team": "Golden State Warriors"},
        "Finals MVP":  {"name": "LeBron James",             "team": "Cleveland Cavaliers"},
        "DPOY":        {"name": "Draymond Green",           "team": "Golden State Warriors"},
        "ROY":         {"name": "Karl-Anthony Towns",       "team": "Minnesota Timberwolves"},
        "MIP":         {"name": "C.J. McCollum",            "team": "Portland Trail Blazers"},
        "6MOY":        {"name": "Jamal Crawford",           "team": "Los Angeles Clippers"},
        "COY":         {"name": "Steve Kerr",               "team": "Golden State Warriors"},
    },
    "2014-15": {
        "MVP":         {"name": "Stephen Curry",            "team": "Golden State Warriors"},
        "Finals MVP":  {"name": "Andre Iguodala",           "team": "Golden State Warriors"},
        "DPOY":        {"name": "Kawhi Leonard",            "team": "San Antonio Spurs"},
        "ROY":         {"name": "Andrew Wiggins",           "team": "Minnesota Timberwolves"},
        "MIP":         {"name": "Jimmy Butler",             "team": "Chicago Bulls"},
        "6MOY":        {"name": "Lou Williams",             "team": "Toronto Raptors"},
        "COY":         {"name": "Mike Budenholzer",         "team": "Atlanta Hawks"},
    },
    "2013-14": {
        "MVP":         {"name": "Kevin Durant",             "team": "Oklahoma City Thunder"},
        "Finals MVP":  {"name": "Kawhi Leonard",            "team": "San Antonio Spurs"},
        "DPOY":        {"name": "Roy Hibbert",              "team": "Indiana Pacers"},
        "ROY":         {"name": "Michael Carter-Williams",  "team": "Philadelphia 76ers"},
        "MIP":         {"name": "Goran Dragic",             "team": "Phoenix Suns"},
        "6MOY":        {"name": "Jamal Crawford",           "team": "Los Angeles Clippers"},
        "COY":         {"name": "Gregg Popovich",           "team": "San Antonio Spurs"},
    },
    "2012-13": {
        "MVP":         {"name": "LeBron James",             "team": "Miami Heat"},
        "Finals MVP":  {"name": "LeBron James",             "team": "Miami Heat"},
        "DPOY":        {"name": "Marc Gasol",               "team": "Memphis Grizzlies"},
        "ROY":         {"name": "Damian Lillard",           "team": "Portland Trail Blazers"},
        "MIP":         {"name": "Paul George",              "team": "Indiana Pacers"},
        "6MOY":        {"name": "J.R. Smith",               "team": "New York Knicks"},
        "COY":         {"name": "George Karl",              "team": "Denver Nuggets"},
    },
    "2011-12": {
        "MVP":         {"name": "LeBron James",             "team": "Miami Heat"},
        "Finals MVP":  {"name": "LeBron James",             "team": "Miami Heat"},
        "DPOY":        {"name": "Tyson Chandler",           "team": "New York Knicks"},
        "ROY":         {"name": "Kyrie Irving",             "team": "Cleveland Cavaliers"},
        "MIP":         {"name": "Ryan Anderson",            "team": "New Orleans Hornets"},
        "6MOY":        {"name": "James Harden",             "team": "Oklahoma City Thunder"},
        "COY":         {"name": "Gregg Popovich",           "team": "San Antonio Spurs"},
    },
    "2010-11": {
        "MVP":         {"name": "Derrick Rose",             "team": "Chicago Bulls"},
        "Finals MVP":  {"name": "Dirk Nowitzki",            "team": "Dallas Mavericks"},
        "DPOY":        {"name": "Dwight Howard",            "team": "Orlando Magic"},
        "ROY":         {"name": "Blake Griffin",            "team": "Los Angeles Clippers"},
        "MIP":         {"name": "Kevin Love",               "team": "Minnesota Timberwolves"},
        "6MOY":        {"name": "Lamar Odom",               "team": "Los Angeles Lakers"},
        "COY":         {"name": "Tom Thibodeau",            "team": "Chicago Bulls"},
    },
    "2009-10": {
        "MVP":         {"name": "LeBron James",             "team": "Cleveland Cavaliers"},
        "Finals MVP":  {"name": "Kobe Bryant",              "team": "Los Angeles Lakers"},
        "DPOY":        {"name": "Dwight Howard",            "team": "Orlando Magic"},
        "ROY":         {"name": "Tyreke Evans",             "team": "Sacramento Kings"},
        "MIP":         {"name": "Aaron Brooks",             "team": "Houston Rockets"},
        "6MOY":        {"name": "Jamal Crawford",           "team": "Atlanta Hawks"},
        "COY":         {"name": "Scott Brooks",             "team": "Oklahoma City Thunder"},
    },
    "2008-09": {
        "MVP":         {"name": "LeBron James",             "team": "Cleveland Cavaliers"},
        "Finals MVP":  {"name": "Kobe Bryant",              "team": "Los Angeles Lakers"},
        "DPOY":        {"name": "Dwight Howard",            "team": "Orlando Magic"},
        "ROY":         {"name": "Derrick Rose",             "team": "Chicago Bulls"},
        "MIP":         {"name": "Danny Granger",            "team": "Indiana Pacers"},
        "6MOY":        {"name": "Jason Terry",              "team": "Dallas Mavericks"},
        "COY":         {"name": "Mike Brown",               "team": "Cleveland Cavaliers"},
    },
    "2007-08": {
        "MVP":         {"name": "Kobe Bryant",              "team": "Los Angeles Lakers"},
        "Finals MVP":  {"name": "Paul Pierce",              "team": "Boston Celtics"},
        "DPOY":        {"name": "Kevin Garnett",            "team": "Boston Celtics"},
        "ROY":         {"name": "Kevin Durant",             "team": "Seattle SuperSonics"},
        "MIP":         {"name": "Hedo Turkoglu",            "team": "Orlando Magic"},
        "6MOY":        {"name": "Manu Ginobili",            "team": "San Antonio Spurs"},
        "COY":         {"name": "Byron Scott",              "team": "New Orleans Hornets"},
    },
    "2006-07": {
        "MVP":         {"name": "Dirk Nowitzki",            "team": "Dallas Mavericks"},
        "Finals MVP":  {"name": "Tony Parker",              "team": "San Antonio Spurs"},
        "DPOY":        {"name": "Marcus Camby",             "team": "Denver Nuggets"},
        "ROY":         {"name": "Brandon Roy",              "team": "Portland Trail Blazers"},
        "MIP":         {"name": "Monta Ellis",              "team": "Golden State Warriors"},
        "6MOY":        {"name": "Leandro Barbosa",          "team": "Phoenix Suns"},
        "COY":         {"name": "Sam Mitchell",             "team": "Toronto Raptors"},
    },
    "2005-06": {
        "MVP":         {"name": "Steve Nash",               "team": "Phoenix Suns"},
        "Finals MVP":  {"name": "Dwyane Wade",              "team": "Miami Heat"},
        "DPOY":        {"name": "Ben Wallace",              "team": "Detroit Pistons"},
        "ROY":         {"name": "Andrew Bogut",             "team": "Milwaukee Bucks"},
        "MIP":         {"name": "Boris Diaw",               "team": "Phoenix Suns"},
        "6MOY":        {"name": "Mike Miller",              "team": "Memphis Grizzlies"},
        "COY":         {"name": "Avery Johnson",            "team": "Dallas Mavericks"},
    },
    "2004-05": {
        "MVP":         {"name": "Steve Nash",               "team": "Phoenix Suns"},
        "Finals MVP":  {"name": "Tim Duncan",               "team": "San Antonio Spurs"},
        "DPOY":        {"name": "Ben Wallace",              "team": "Detroit Pistons"},
        "ROY":         {"name": "Emeka Okafor",             "team": "Charlotte Bobcats"},
        "MIP":         {"name": "Bobby Simmons",            "team": "Los Angeles Clippers"},
        "6MOY":        {"name": "Ben Gordon",               "team": "Chicago Bulls"},
        "COY":         {"name": "Mike D'Antoni",            "team": "Phoenix Suns"},
    },
    "2003-04": {
        "MVP":         {"name": "Kevin Garnett",            "team": "Minnesota Timberwolves"},
        "Finals MVP":  {"name": "Chauncey Billups",         "team": "Detroit Pistons"},
        "DPOY":        {"name": "Ron Artest",               "team": "Indiana Pacers"},
        "ROY":         {"name": "LeBron James",             "team": "Cleveland Cavaliers"},
        "MIP":         {"name": "Zach Randolph",            "team": "Portland Trail Blazers"},
        "6MOY":        {"name": "Antawn Jamison",           "team": "Dallas Mavericks"},
        "COY":         {"name": "Hubie Brown",              "team": "Memphis Grizzlies"},
    },
    "2002-03": {
        "MVP":         {"name": "Tim Duncan",               "team": "San Antonio Spurs"},
        "Finals MVP":  {"name": "Tim Duncan",               "team": "San Antonio Spurs"},
        "DPOY":        {"name": "Ben Wallace",              "team": "Detroit Pistons"},
        "ROY":         {"name": "Amare Stoudemire",         "team": "Phoenix Suns"},
        "MIP":         {"name": "Gilbert Arenas",           "team": "Golden State Warriors"},
        "6MOY":        {"name": "Bobby Jackson",            "team": "Sacramento Kings"},
        "COY":         {"name": "Gregg Popovich",           "team": "San Antonio Spurs"},
    },
    "2001-02": {
        "MVP":         {"name": "Tim Duncan",               "team": "San Antonio Spurs"},
        "Finals MVP":  {"name": "Shaquille O'Neal",         "team": "Los Angeles Lakers"},
        "DPOY":        {"name": "Ben Wallace",              "team": "Detroit Pistons"},
        "ROY":         {"name": "Pau Gasol",                "team": "Memphis Grizzlies"},
        "MIP":         {"name": "Jalen Rose",               "team": "Chicago Bulls"},
        "6MOY":        {"name": "Rodney Rogers",            "team": "New Jersey Nets"},
        "COY":         {"name": "Byron Scott",              "team": "New Jersey Nets"},
    },
    "2000-01": {
        "MVP":         {"name": "Allen Iverson",            "team": "Philadelphia 76ers"},
        "Finals MVP":  {"name": "Shaquille O'Neal",         "team": "Los Angeles Lakers"},
        "DPOY":        {"name": "Dikembe Mutombo",          "team": "Philadelphia 76ers"},
        "ROY":         {"name": "Mike Miller",              "team": "Orlando Magic"},
        "MIP":         {"name": "Tracy McGrady",            "team": "Orlando Magic"},
        "6MOY":        {"name": "Aaron McKie",              "team": "Philadelphia 76ers"},
        "COY":         {"name": "Larry Brown",              "team": "Philadelphia 76ers"},
    },
    "1999-00": {
        "MVP":         {"name": "Shaquille O'Neal",         "team": "Los Angeles Lakers"},
        "Finals MVP":  {"name": "Shaquille O'Neal",         "team": "Los Angeles Lakers"},
        "DPOY":        {"name": "Alonzo Mourning",          "team": "Miami Heat"},
        "ROY":         {"name": "Elton Brand",              "team": "Chicago Bulls"},
        "MIP":         {"name": "Jalen Rose",               "team": "Indiana Pacers"},
        "6MOY":        {"name": "Rodney Rogers",            "team": "Phoenix Suns"},
        "COY":         {"name": "Doc Rivers",               "team": "Orlando Magic"},
    },
    "1998-99": {
        "MVP":         {"name": "Karl Malone",              "team": "Utah Jazz"},
        "Finals MVP":  {"name": "Tim Duncan",               "team": "San Antonio Spurs"},
        "DPOY":        {"name": "Alonzo Mourning",          "team": "Miami Heat"},
        "ROY":         {"name": "Vince Carter",             "team": "Toronto Raptors"},
        "MIP":         {"name": "Darrell Armstrong",        "team": "Orlando Magic"},
        "6MOY":        {"name": "Darrell Armstrong",        "team": "Orlando Magic"},
        "COY":         {"name": "Mike Dunleavy Sr.",        "team": "Portland Trail Blazers"},
    },
    "1997-98": {
        "MVP":         {"name": "Michael Jordan",           "team": "Chicago Bulls"},
        "Finals MVP":  {"name": "Michael Jordan",           "team": "Chicago Bulls"},
        "DPOY":        {"name": "Dikembe Mutombo",          "team": "Atlanta Hawks"},
        "ROY":         {"name": "Tim Duncan",               "team": "San Antonio Spurs"},
        "MIP":         {"name": "Alan Henderson",           "team": "Atlanta Hawks"},
        "6MOY":        {"name": "Danny Manning",            "team": "Phoenix Suns"},
        "COY":         {"name": "Larry Bird",               "team": "Indiana Pacers"},
    },
    "1996-97": {
        "MVP":         {"name": "Karl Malone",              "team": "Utah Jazz"},
        "Finals MVP":  {"name": "Michael Jordan",           "team": "Chicago Bulls"},
        "DPOY":        {"name": "Dikembe Mutombo",          "team": "Atlanta Hawks"},
        "ROY":         {"name": "Allen Iverson",            "team": "Philadelphia 76ers"},
        "MIP":         {"name": "Isaac Austin",             "team": "Miami Heat"},
        "6MOY":        {"name": "John Starks",              "team": "New York Knicks"},
        "COY":         {"name": "Pat Riley",                "team": "Miami Heat"},
    },
    "1995-96": {
        "MVP":         {"name": "Michael Jordan",           "team": "Chicago Bulls"},
        "Finals MVP":  {"name": "Michael Jordan",           "team": "Chicago Bulls"},
        "DPOY":        {"name": "Gary Payton",              "team": "Seattle SuperSonics"},
        "ROY":         {"name": "Damon Stoudamire",         "team": "Toronto Raptors"},
        "MIP":         {"name": "Gheorghe Muresan",         "team": "Washington Bullets"},
        "6MOY":        {"name": "Toni Kukoc",               "team": "Chicago Bulls"},
        "COY":         {"name": "Phil Jackson",             "team": "Chicago Bulls"},
    },
    "1994-95": {
        "MVP":         {"name": "David Robinson",           "team": "San Antonio Spurs"},
        "Finals MVP":  {"name": "Hakeem Olajuwon",          "team": "Houston Rockets"},
        "DPOY":        {"name": "David Robinson",           "team": "San Antonio Spurs"},
        "ROY":         {"name": "Jason Kidd",               "team": "Dallas Mavericks"},
        "MIP":         {"name": "Dana Barros",              "team": "Philadelphia 76ers"},
        "6MOY":        {"name": "Anthony Mason",            "team": "New York Knicks"},
        "COY":         {"name": "Del Harris",               "team": "Los Angeles Lakers"},
    },
    "1993-94": {
        "MVP":         {"name": "Hakeem Olajuwon",          "team": "Houston Rockets"},
        "Finals MVP":  {"name": "Hakeem Olajuwon",          "team": "Houston Rockets"},
        "DPOY":        {"name": "Hakeem Olajuwon",          "team": "Houston Rockets"},
        "ROY":         {"name": "Chris Webber",             "team": "Golden State Warriors"},
        "MIP":         {"name": "Don MacLean",              "team": "Washington Bullets"},
        "6MOY":        {"name": "Dell Curry",               "team": "Charlotte Hornets"},
        "COY":         {"name": "Lenny Wilkens",            "team": "Atlanta Hawks"},
    },
    "1992-93": {
        "MVP":         {"name": "Charles Barkley",          "team": "Phoenix Suns"},
        "Finals MVP":  {"name": "Michael Jordan",           "team": "Chicago Bulls"},
        "DPOY":        {"name": "Hakeem Olajuwon",          "team": "Houston Rockets"},
        "ROY":         {"name": "Shaquille O'Neal",         "team": "Orlando Magic"},
        "MIP":         {"name": "Mahmoud Abdul-Rauf",       "team": "Denver Nuggets"},
        "6MOY":        {"name": "Cliff Robinson",           "team": "Portland Trail Blazers"},
        "COY":         {"name": "Pat Riley",                "team": "New York Knicks"},
    },
    "1991-92": {
        "MVP":         {"name": "Michael Jordan",           "team": "Chicago Bulls"},
        "Finals MVP":  {"name": "Michael Jordan",           "team": "Chicago Bulls"},
        "DPOY":        {"name": "David Robinson",           "team": "San Antonio Spurs"},
        "ROY":         {"name": "Larry Johnson",            "team": "Charlotte Hornets"},
        "MIP":         {"name": "Pervis Ellison",           "team": "Washington Bullets"},
        "6MOY":        {"name": "Detlef Schrempf",          "team": "Indiana Pacers"},
        "COY":         {"name": "Don Nelson",               "team": "Golden State Warriors"},
    },
    "1990-91": {
        "MVP":         {"name": "Michael Jordan",           "team": "Chicago Bulls"},
        "Finals MVP":  {"name": "Michael Jordan",           "team": "Chicago Bulls"},
        "DPOY":        {"name": "Dennis Rodman",            "team": "Detroit Pistons"},
        "ROY":         {"name": "Dee Brown",                "team": "Boston Celtics"},
        "MIP":         {"name": "Scott Skiles",             "team": "Orlando Magic"},
        "6MOY":        {"name": "Detlef Schrempf",          "team": "Indiana Pacers"},
        "COY":         {"name": "Don Chaney",               "team": "Houston Rockets"},
    },
    "1989-90": {
        "MVP":         {"name": "Magic Johnson",            "team": "Los Angeles Lakers"},
        "Finals MVP":  {"name": "Isiah Thomas",             "team": "Detroit Pistons"},
        "DPOY":        {"name": "Dennis Rodman",            "team": "Detroit Pistons"},
        "ROY":         {"name": "David Robinson",           "team": "San Antonio Spurs"},
        "MIP":         {"name": "Rony Seikaly",             "team": "Miami Heat"},
        "6MOY":        {"name": "Ricky Pierce",             "team": "Milwaukee Bucks"},
        "COY":         {"name": "Pat Riley",                "team": "Los Angeles Lakers"},
    },
    "1988-89": {
        "MVP":         {"name": "Magic Johnson",            "team": "Los Angeles Lakers"},
        "Finals MVP":  {"name": "Joe Dumars",               "team": "Detroit Pistons"},
        "DPOY":        {"name": "Mark Eaton",               "team": "Utah Jazz"},
        "ROY":         {"name": "Mitch Richmond",           "team": "Golden State Warriors"},
        "MIP":         {"name": "Kevin Johnson",            "team": "Phoenix Suns"},
        "6MOY":        {"name": "Eddie Johnson",            "team": "Phoenix Suns"},
        "COY":         {"name": "Cotton Fitzsimmons",       "team": "Phoenix Suns"},
    },
    "1987-88": {
        "MVP":         {"name": "Michael Jordan",           "team": "Chicago Bulls"},
        "Finals MVP":  {"name": "James Worthy",             "team": "Los Angeles Lakers"},
        "DPOY":        {"name": "Michael Jordan",           "team": "Chicago Bulls"},
        "ROY":         {"name": "Mark Jackson",             "team": "New York Knicks"},
        "MIP":         {"name": "Kevin Duckworth",          "team": "Portland Trail Blazers"},
        "6MOY":        {"name": "Roy Tarpley",              "team": "Dallas Mavericks"},
        "COY":         {"name": "Doug Moe",                 "team": "Denver Nuggets"},
    },
    "1986-87": {
        "MVP":         {"name": "Magic Johnson",            "team": "Los Angeles Lakers"},
        "Finals MVP":  {"name": "Magic Johnson",            "team": "Los Angeles Lakers"},
        "DPOY":        {"name": "Michael Cooper",           "team": "Los Angeles Lakers"},
        "ROY":         {"name": "Chuck Person",             "team": "Indiana Pacers"},
        "MIP":         {"name": "Dale Ellis",               "team": "Seattle SuperSonics"},
        "6MOY":        {"name": "Ricky Pierce",             "team": "Milwaukee Bucks"},
        "COY":         {"name": "Mike Schuler",             "team": "Portland Trail Blazers"},
    },
    "1985-86": {
        "MVP":         {"name": "Larry Bird",               "team": "Boston Celtics"},
        "Finals MVP":  {"name": "Larry Bird",               "team": "Boston Celtics"},
        "DPOY":        {"name": "Alvin Robertson",          "team": "San Antonio Spurs"},
        "ROY":         {"name": "Patrick Ewing",            "team": "New York Knicks"},
        "MIP":         {"name": "Alvin Robertson",          "team": "San Antonio Spurs"},
        "6MOY":        {"name": "Bill Walton",              "team": "Boston Celtics"},
        "COY":         {"name": "Mike Fratello",            "team": "Atlanta Hawks"},
    },
}

AWARD_LABELS = {
    "MVP":        "Most Valuable Player",
    "Finals MVP": "Finals MVP",
    "DPOY":       "Defensive Player of the Year",
    "ROY":        "Rookie of the Year",
    "MIP":        "Most Improved Player",
    "6MOY":       "Sixth Man of the Year",
    "COY":        "Coach of the Year",
}

AWARD_ORDER = ["MVP", "Finals MVP", "DPOY", "ROY", "MIP", "6MOY", "COY"]

# data functions

def get_player_headshot_url(player_id):
    return f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"

def get_team_logo_url(team_id):
    return f"https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg"

def build_player_card(player_name):
    player = PLAYER_LOOKUP.get(player_name.lower())
    return {
        "name": player_name,
        "headshot_url": get_player_headshot_url(player["id"]) if player else ""
    }

def build_team_card(team_name):
    team = TEAM_LOOKUP.get(team_name.lower())
    return {
        "name": team_name,
        "logo_url": get_team_logo_url(team["id"]) if team else ""
    }

def add_visuals_to_leader_rows(rows):
    for row in rows:
        player_id = row.get("PLAYER_ID")
        team_abbr = row.get("TEAM", "").upper()
        team = TEAM_ABBR_LOOKUP.get(team_abbr)
        row["headshot_url"] = get_player_headshot_url(player_id) if player_id else ""
        row["team_logo_url"] = get_team_logo_url(team["id"]) if team else ""
    return rows

def add_headshots_to_historical_rows(rows):
    for row in rows:
        player_id = row.get("PLAYER_ID")
        row["headshot_url"] = get_player_headshot_url(player_id) if player_id else ""
    return rows

def convert_result_set_to_rows(leaders_dict, result_set_name):
    for result_set in leaders_dict.get("resultSets", []):
        if result_set.get("name") == result_set_name:
            headers = result_set.get("headers", [])
            return [dict(zip(headers, row)) for row in result_set.get("rowSet", [])]
    return []

def get_historical_leaders():
    leaders = alltimeleadersgrids.AllTimeLeadersGrids(
        league_id="00",
        per_mode_simple="Totals",
        season_type="Regular Season",
        topx=10
    )

    leaders_dict = leaders.get_dict()

    categories = {
        "points": {
            "title": "Points",
            "result_set": "PTSLeaders",
            "stat_key": "PTS",
            "rank_key": "PTS_RANK"
        },
        "rebounds": {
            "title": "Rebounds",
            "result_set": "REBLeaders",
            "stat_key": "REB",
            "rank_key": "REB_RANK"
        },
        "assists": {
            "title": "Assists",
            "result_set": "ASTLeaders",
            "stat_key": "AST",
            "rank_key": "AST_RANK"
        },
        "steals": {
            "title": "Steals",
            "result_set": "STLLeaders",
            "stat_key": "STL",
            "rank_key": "STL_RANK"
        },
        "blocks": {
            "title": "Blocks",
            "result_set": "BLKLeaders",
            "stat_key": "BLK",
            "rank_key": "BLK_RANK"
        },
        "threes": {
            "title": "3-Pointers Made",
            "result_set": "FG3MLeaders",
            "stat_key": "FG3M",
            "rank_key": "FG3M_RANK"
        }
    }

    historical_data = {}

    for category_key, category_info in categories.items():
        rows = convert_result_set_to_rows(leaders_dict, category_info["result_set"])
        rows = add_headshots_to_historical_rows(rows)

        historical_data[category_key] = {
            "title": category_info["title"],
            "stat_key": category_info["stat_key"],
            "rank_key": category_info["rank_key"],
            "rows": rows
        }

    return historical_data

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

# serve favicon
@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"), "favicon.ico", mimetype = "image/vnd.microsoft.icon")

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

    player_cards = [build_player_card(player_name) for player_name in filtered_players]

    return render_template(
        "players.html",
        players=player_cards,
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

    available_seasons = [s["SEASON_ID"] for s in season_stats]
    default_season = available_seasons[-1] if available_seasons else get_current_season_string()
    selected_season = request.args.get("season", default_season)
    if selected_season not in available_seasons and available_seasons:
        selected_season = default_season

    cache_key = (player_id, selected_season)
    if cache_key in game_log_cache:
        game_log = game_log_cache[cache_key]
    else:
        try:
            log = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=selected_season,
                season_type_all_star="Regular Season"
            )
            log_data = log.get_dict()
            game_log = []
            for result_set in log_data.get("resultSets", []):
                if result_set.get("name") == "PlayerGameLog":
                    headers = result_set["headers"]
                    for row in result_set["rowSet"]:
                        game_log.append(dict(zip(headers, row)))
                    break
        except Exception:
            game_log = []
        game_log_cache[cache_key] = game_log

    return render_template(
        "player.html",
        player_name=player["full_name"],
        player_headshot_url=get_player_headshot_url(player_id),
        season_stats=season_stats,
        game_log=game_log,
        selected_season=selected_season,
        available_seasons=available_seasons
    )


# route to teams
@app.route("/teams")
def teamsPage():
    all_teams = get_all_team_names()

    team_cards = [build_team_card(team_name) for team_name in all_teams]

    return render_template(
        "teams.html",
        teams=team_cards
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
        team_logo_url=get_team_logo_url(team_id),
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

    player_result_cards = [build_player_card(player_name) for player_name in player_results]
    team_result_cards = [build_team_card(team_name) for team_name in team_results]

    return render_template(
        "search_results.html",
        query=query,
        player_results=player_result_cards,
        team_results=team_result_cards
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

        for row in standings_rows:
            team_id = row.get("TeamID")
            row["logo_url"] = get_team_logo_url(team_id) if team_id else ""

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
            "points": add_visuals_to_leader_rows(get_leaders_for_category("PTS")),
            "rebounds": add_visuals_to_leader_rows(get_leaders_for_category("REB")),
            "assists": add_visuals_to_leader_rows(get_leaders_for_category("AST")),
            "steals": add_visuals_to_leader_rows(get_leaders_for_category("STL")),
            "blocks": add_visuals_to_leader_rows(get_leaders_for_category("BLK"))
        }

        leaders_cache = leaders_data
        leaders_cache_season = current_season

    return render_template(
        "leaders.html",
        season=current_season,
        leaders_data=leaders_data
    )

# route to historical leaders
@app.route("/historical-leaders")
def historicalLeadersPage():
    global historical_leaders_cache

    selected_category = request.args.get("category", "points")

    if historical_leaders_cache is None:
        historical_leaders_cache = get_historical_leaders()

    if selected_category not in historical_leaders_cache:
        selected_category = "points"

    selected_data = historical_leaders_cache[selected_category]

    chart_data = {
        "labels": [row.get("PLAYER_NAME", "") for row in selected_data["rows"]],
        "values": [row.get(selected_data["stat_key"], 0) for row in selected_data["rows"]]
    }

    return render_template(
        "historical_leaders.html",
        historical_data=historical_leaders_cache,
        selected_category=selected_category,
        selected_data=selected_data,
        chart_data=chart_data
    )

# route to scores/stats page
@app.route("/Scores")
def statsPage():
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        date_obj = datetime.now()
        date_str = date_obj.strftime("%Y-%m-%d")

    prev_date = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
    next_date = (date_obj + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        board = scoreboardv2.ScoreboardV2(game_date=date_str, league_id="00", day_offset=0)
        board_dict = board.get_dict()
    except Exception:
        return render_template("stats.html", games=[], date=date_str,
                               prev_date=prev_date, next_date=next_date, error="Could not load games.")

    games_header = {}
    games_scores = {}

    for result_set in board_dict.get("resultSets", []):
        if result_set["name"] == "GameHeader":
            headers = result_set["headers"]
            for row in result_set["rowSet"]:
                d = dict(zip(headers, row))
                games_header[d["GAME_ID"]] = d
        elif result_set["name"] == "LineScore":
            headers = result_set["headers"]
            for row in result_set["rowSet"]:
                d = dict(zip(headers, row))
                gid = d["GAME_ID"]
                if gid not in games_scores:
                    games_scores[gid] = []
                games_scores[gid].append(d)

    games = []
    for game_id, header in games_header.items():
        teams_data = games_scores.get(game_id, [])
        away = teams_data[0] if len(teams_data) > 0 else {}
        home = teams_data[1] if len(teams_data) > 1 else {}
        games.append({
            "game_id": game_id,
            "status": header.get("GAME_STATUS_TEXT", "").strip(),
            "away": away,
            "home": home,
        })

    return render_template(
        "stats.html",
        games=games,
        date=date_str,
        prev_date=prev_date,
        next_date=next_date
    )

# API: box score for a game
@app.route("/api/boxscore/<game_id>")
def boxscoreAPI(game_id):
    try:
        box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
        box_dict = box.get_dict()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    player_rows = []
    for result_set in box_dict.get("resultSets", []):
        if result_set["name"] == "PlayerStats":
            headers = result_set["headers"]
            for row in result_set["rowSet"]:
                player_rows.append(dict(zip(headers, row)))
            break

    teams_map = {}
    for p in player_rows:
        abbr = p.get("TEAM_ABBREVIATION", "")
        if abbr not in teams_map:
            team_id = p.get("TEAM_ID")
            teams_map[abbr] = {
                "abbreviation": abbr,
                "city": p.get("TEAM_CITY", ""),
                "logo_url": get_team_logo_url(team_id) if team_id else "",
                "players": []
            }
        teams_map[abbr]["players"].append({
            "name": p.get("PLAYER_NAME", ""),
            "headshot_url": get_player_headshot_url(p.get("PLAYER_ID")) if p.get("PLAYER_ID") else "",
            "position": p.get("START_POSITION", ""),
            "min": p.get("MIN", ""),
            "pts": p.get("PTS", 0),
            "reb": p.get("REB", 0),
            "ast": p.get("AST", 0),
            "stl": p.get("STL", 0),
            "blk": p.get("BLK", 0),
            "fg": f"{p.get('FGM', 0)}-{p.get('FGA', 0)}",
            "fg3": f"{p.get('FG3M', 0)}-{p.get('FG3A', 0)}",
            "plus_minus": p.get("PLUS_MINUS", 0),
        })

    return jsonify(list(teams_map.values()))

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

# return draft results by year
@app.route("/draft", methods=["GET"])
def draftPage():

    # get API data and attributes
    raw = drafthistory.DraftHistory().get_dict()
    result_set = raw["resultSets"][0]
    headers = result_set["headers"]
    rows = result_set["rowSet"]

    # prepare to parse
    data = [dict(zip(headers, row)) for row in rows]
    draftByYear = {}

    # parse data into neat rows to pass to front end
    for row in data:
        year = str(row["SEASON"])
        playerName = row["PLAYER_NAME"]
        card = build_player_card(playerName)
        row["headshot_url"] = card["headshot_url"]
        row["player_page_url"] = url_for("playerPage", name=playerName)
        draftByYear.setdefault(year, []).append(row)

    # sort parsed data
    availableYears = sorted(draftByYear.keys(), reverse=True)
    selectedYear = request.args.get("year")
    if selectedYear not in draftByYear:
        selectedYear = availableYears[0] if availableYears else None
    draftData = draftByYear.get(selectedYear, [])

    # returned parsed, sorted, and cleaned data
    return render_template("draft.html", available_years=availableYears, selected_year=selectedYear, draft_data=draftData)

# return points per game vs rebounds per game for given player id
@app.route("/api/ppg_rpg_<playerId>.png")
def getPointVsReboundChart(playerId):

    # check if given id is valid
    playerInfo = players.find_player_by_id(playerId)
    if not playerInfo:
         return jsonify({"error": "Player not found"}), 404

    # get data
    career = playercareerstats.PlayerCareerStats(playerId)
    df = career.get_data_frames()[0]

    # prepare plot
    fig = Figure(figsize = (10, 6))
    ax = fig.add_subplot(1, 1, 1)

    # plot data
    ax.plot(df["SEASON_ID"], df["PTS"] / df["GP"], label = "Points")
    ax.plot(df["SEASON_ID"], df["REB"] / df["GP"], label = "Rebounds")

    # add labels
    ax.set_title(playerInfo["full_name"] + " PPG vs RPG")
    ax.set_xlabel("Season")
    ax.set_ylabel("Average")
    ax.tick_params(rotation = 45)
    ax.legend()
    ax.grid(True)
    fig.tight_layout()

    # return chart
    output = io.BytesIO()
    fig.savefig(output, format = "png")
    return Response(output.getvalue(), mimetype= "image/png")

# route to awards page
@app.route("/awards")
def awardsPage():
    available_seasons = sorted(AWARDS_BY_SEASON.keys(), reverse=True)
    default_season = available_seasons[0] if available_seasons else "2024-25"
    selected_season = request.args.get("season", default_season)
    if selected_season not in AWARDS_BY_SEASON:
        selected_season = default_season

    awards = AWARDS_BY_SEASON.get(selected_season, {})

    award_list = []
    for key in AWARD_ORDER:
        if key in awards:
            name = awards[key]["name"]
            team = awards[key]["team"]

            headshot_url = None
            found = players.find_players_by_full_name(name)
            if found:
                player_id = found[0]["id"]
                headshot_url = f"https://cdn.nba.com/headshots/nba/latest/260x190/{player_id}.png"

            award_list.append({
                "key": key,
                "label": AWARD_LABELS.get(key, key),
                "name": name,
                "team": team,
                "headshot_url": headshot_url,
            })

    return render_template(
        "awards.html",
        award_list=award_list,
        selected_season=selected_season,
        available_seasons=available_seasons,
    )


# route to playoffs bracket page
@app.route("/playoffs")
def playoffsPage():
    current_year = datetime.now().year
    available_seasons = []
    for year in range(current_year - 1, 1995, -1):
        available_seasons.append(f"{year}-{str(year + 1)[-2:]}")

    default_season = available_seasons[0]
    selected_season = request.args.get("season", default_season)
    if selected_season not in available_seasons:
        selected_season = default_season

    if selected_season in playoffs_cache:
        return render_template(
            "playoffs.html",
            rounds=playoffs_cache[selected_season],
            selected_season=selected_season,
            available_seasons=available_seasons,
            error=None
        )

    rounds = []
    error = None
    try:
        series_resp = commonplayoffseries.CommonPlayoffSeries(season=selected_season).get_dict()
        series_rows = series_resp["resultSets"][0]["rowSet"]

        if not series_rows:
            error = "No playoff data available for this season yet."
        else:
            log_resp = leaguegamelog.LeagueGameLog(
                season=selected_season,
                season_type_all_star="Playoffs",
                league_id="00"
            ).get_dict()

            game_rows = []
            for rs in log_resp.get("resultSets", []):
                if rs["name"] == "LeagueGameLog":
                    hdrs = rs["headers"]
                    for row in rs["rowSet"]:
                        game_rows.append(dict(zip(hdrs, row)))
                    break

            game_scores = {}
            for row in game_rows:
                gid = row["GAME_ID"]
                if gid not in game_scores:
                    game_scores[gid] = {}
                game_scores[gid][row["TEAM_ID"]] = {
                    "pts": row["PTS"],
                    "wl": row["WL"],
                    "name": row["TEAM_NAME"],
                    "abbr": row["TEAM_ABBREVIATION"]
                }

            series_map = {}
            for row in series_rows:
                game_id, home_id, visitor_id, series_id, game_num = row
                if series_id not in series_map:
                    series_map[series_id] = {"home_id": home_id, "visitor_id": visitor_id, "game_ids": []}
                series_map[series_id]["game_ids"].append(game_id)

            rounds_map = {}
            for sid, info in series_map.items():
                round_num = int(sid[7])
                series_num = int(sid[8])
                if round_num not in rounds_map:
                    rounds_map[round_num] = {}

                home_id = info["home_id"]
                visitor_id = info["visitor_id"]

                home_name = home_abbr = ""
                visitor_name = visitor_abbr = ""
                for gid in info["game_ids"]:
                    if gid in game_scores:
                        gs = game_scores[gid]
                        if home_id in gs:
                            home_name = gs[home_id]["name"]
                            home_abbr = gs[home_id]["abbr"]
                        if visitor_id in gs:
                            visitor_name = gs[visitor_id]["name"]
                            visitor_abbr = gs[visitor_id]["abbr"]
                        if home_name and visitor_name:
                            break

                home_wins = visitor_wins = 0
                games_list = []
                for gid in sorted(info["game_ids"]):
                    if gid in game_scores:
                        gs = game_scores[gid]
                        if home_id in gs and visitor_id in gs:
                            h = gs[home_id]
                            v = gs[visitor_id]
                            home_win = h["wl"] == "W"
                            if home_win:
                                home_wins += 1
                            else:
                                visitor_wins += 1
                            games_list.append({
                                "home_pts": h["pts"],
                                "visitor_pts": v["pts"],
                                "home_win": home_win
                            })

                winner_id = None
                if home_wins > visitor_wins:
                    winner_id = home_id
                elif visitor_wins > home_wins:
                    winner_id = visitor_id

                rounds_map[round_num][series_num] = {
                    "home": {
                        "id": home_id, "name": home_name, "abbr": home_abbr,
                        "wins": home_wins,
                        "logo": f"https://cdn.nba.com/logos/nba/{home_id}/global/L/logo.svg"
                    },
                    "visitor": {
                        "id": visitor_id, "name": visitor_name, "abbr": visitor_abbr,
                        "wins": visitor_wins,
                        "logo": f"https://cdn.nba.com/logos/nba/{visitor_id}/global/L/logo.svg"
                    },
                    "total_games": len(info["game_ids"]),
                    "winner_id": winner_id,
                    "games": games_list
                }

            round_names = {
                1: "First Round",
                2: "Conf. Semifinals",
                3: "Conf. Finals",
                4: "NBA Finals"
            }
            for rnum in sorted(rounds_map.keys()):
                series_list = [rounds_map[rnum][s] for s in sorted(rounds_map[rnum].keys())]
                rounds.append({"name": round_names.get(rnum, f"Round {rnum}"), "number": rnum, "series": series_list})

            playoffs_cache[selected_season] = rounds

    except Exception:
        error = "Could not load playoff data. Please try again."

    return render_template(
        "playoffs.html",
        rounds=rounds,
        selected_season=selected_season,
        available_seasons=available_seasons,
        error=error
    )


if __name__ == "__main__":
    app.run(debug=True, port=8000)
