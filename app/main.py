from flask import Flask, render_template
from dotenv import load_dotenv
import os
import warnings

# set up app
load_dotenv()
API_KEY = os.getenv("API_KEY")
if API_KEY is None:
    warnings.warn("No API key found, statistics will be missing", FutureWarning)
app = Flask(__name__)

# serve index page
@app.route("/")
def index():
    return render_template("index.html")
