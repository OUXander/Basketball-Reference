# Basketball Reference Redesign

## Overview

A redesign of http://basketballreference.com/ with the goal of cleaner, simpler UI that is easier for the user to navigate. To accomplish this goal, the user is initially presented with a minimalistic search UI where they can request specific information or navigate to general topics. The UI takes inspiration from ChatGPT and Google. The statistics are read from an API that can be switched out if needed.
 
## Usage

The website is not hosted publicly, however it can be hosted locally with Python. The Makefile contains the necessary commands to launch the website given that the host machine has the necessary prerequisites installed:
- Make (e.g. `sudo apt install make`)
- Python (e.g. `sudo apt install python3`)
- Flask (e.g. `sudo apt install python3-flask`)
- Dotenv (e.g. `sudo apt install python3-dotenv`)
- Gunicorn (e.g. `sudo apt install gunicorn`)
Make sure no other application is running on port 8000 then run `make` to launch the application. Once running, visit http://localhost:8000/.

## To-Do

- Implement functionality for remaining buttons.
- Implement remaining webpages.
- Implement functionality for the search bar.
- Implement handler for statistics API.
- Smooth UI transitions with CSS animations
