import os
import requests
import json

from flask import Flask, render_template, redirect, request, session, abort
from flask_login.utils import login_user, logout_user
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
from google.oauth2 import id_token
from flask_login import LoginManager, current_user
from pip._vendor import cachecontrol
from flask.helpers import url_for
import pandas

from user import User
from db_handler import db
import generate_random

app = Flask(__name__)
app.debug = True

login_manager = LoginManager()
with open("secure/app_secrets.json") as appSecrets:
    data = json.loads(appSecrets.read())
    app.secret_key = bytes(data["secret_key"], 'utf-8')

# Why is security such a nightmare to deal with 
login_manager.init_app(app)

database = db()

#CHANGE THIS ON RELEASE
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = '1'

CLIENT_ID = None

with open("secure/client_secrets.json") as file:
    data = json.loads(file.read())
    CLIENT_ID = data['web']['client_id'] 


flow = Flow.from_client_secrets_file(
    client_secrets_file='secure/client_secrets.json',
    scopes=["https://www.googleapis.com/auth/userinfo.profile", 
    "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://localhost:5000/signin/callback"
    )

@login_manager.user_loader
def loadUser(userid):
    return User.get(userid, database)


@app.route("/", methods=['GET'])
def index():
    return render_template('index.html')

@app.route("/get_handle", methods=['GET', 'POST'])
def get_handle():
    user = User.get(request.args['g_id'], database)
    return render_template("get_handle.html", id=request.args['g_id'], name=user._name, email=user._email)

@app.route("/submit", methods=["GET", "POST"])
def submit():
    id = request.form['id']
    handle = request.form['handle']
    name = request.form['name']
    email = request.form['email']
    user = User.update(id, name, email, handle, database)
    login_user(user)
    return redirect("/dashboard")


@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/compete", methods=['GET'])
def compete():
    return render_template('compete.html')

@app.route("/leaderboard")
def leaderboard():
    random_strings = generate_random.generate_strings(10)
    return render_template('leaderboard.html', data=random_strings)

@app.route("/practice")
def practice():
    filename = 'data/sorted_problems.csv'
    data = pandas.read_csv(filename, header=0)
    data.columns = data.columns.str.strip()
    easytbl = list(data[data['Rating']<=800].sample(20).values)
    midtbl = list(data[(data['Rating']<=1600) & (data['Rating']>800)].sample(20).values)
    hardtbl = list(data[(data['Rating']<=2500) & (data['Rating']>1600)].sample(20).values)
    insanetbl = list(data[data['Rating']>2500].sample(20).values)
    return render_template('practice.html', easytbl=easytbl, midtbl=midtbl, hardtbl=hardtbl, insanetbl=insanetbl)

@app.route("/profilepage")
def profilepage():
    return render_template('profilepage.html')

@app.route("/signin", methods=["GET", "POST"])
def signin():
    if current_user.is_authenticated:
        return redirect("/dashboard")
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/trending")
def trending():
    return render_template('trending.html')

@app.route("/dashboard", methods=['GET'])
def dashboard():
    if current_user.is_authenticated:
        return render_template("dashboard.html")

    return "Temp text to show user is not signed in"

@app.route("/signin/callback", methods=["GET"])
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)

    credentials = flow.credentials
    requestSession = requests.session()
    cache_session = cachecontrol.CacheControl(requestSession)
    token_request = google.auth.transport.requests.Request(session=cache_session)

    idToken = id_token.verify_oauth2_token(
        id_token=credentials.id_token,
        request=token_request,
        audience=CLIENT_ID
    )

    if not User.get(idToken["sub"], database): # Brand new user
        User.create_no_handle(idToken['sub'], idToken['name'], idToken['email'], database)
        return redirect(url_for("get_handle", g_id=idToken["sub"]))
    
    if not User.get_handle(idToken['sub'], database):
        return redirect(url_for("get_handle", g_id=idToken['sub']))

    user = User.get(idToken["sub"], database)
    login_user(user)

    return redirect("/dashboard")

@app.route("/logout")
def logout():
    logout_user()
    return redirect("/")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html"), 404


if __name__ == '__main__':
    app.run()