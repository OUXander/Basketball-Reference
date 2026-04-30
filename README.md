# Basketball Reference Redesign

## Overview

A redesign of http://basketballreference.com/ with the goal of a cleaner, simpler UI that is easier for the user to navigate. To accomplish this goal, the user is initially presented with a minimalistic search UI where they can request specific information or navigate to pages that relate to more general topics. The UI takes inspiration from ChatGPT and Google for their minimalistic design and focus on the search bar. The statistics are read from the Python package "nba_api", which utilizes the APIs directly from the NBA website, and formatted in Python. Python also serves the front end using Flask and Gunicorn to display the gathered data in web HTML/CSS/JS.
 
## Usage

The website is not hosted publicly; however, it can be hosted locally with Python. The Makefile contains the necessary commands to launch the website, given that the host machine has the necessary prerequisites installed:
- Make (e.g., `sudo apt install make`)
- Python (e.g., `sudo apt install python3`)
- Flask (e.g., `sudo apt install python3-flask`)
- nba_api (e.g., `python -m pip install nba_api`)
- Gunicorn (e.g., `sudo apt install gunicorn`)

Next, make sure no other application is running on port 8000, then run `make` to launch the application. Once running, visit http://localhost:8000/.

## Structure

All files for the application can be found under `/app`. Files not needed for the application itself but for administration are kept in the root directory for easy viewing. Inside `/app`, the central Python file `/app/main.py` handles the front and back ends with Flask. HTML files for webpages are stored in `/app/templates/` to be loaded as Flask templates. Every other website asset is stored in `/app/static/` and the respective folder for the file type: `/app/static/css` for the CSS files, `/app/static/js/` for the JS files, and `/app/static/img/` for the images. Make is used to easily launch the application with Gunicorn as the Python WSGI HTTP web server.
