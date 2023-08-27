# -*- Code created August 2023. Olivier Simard-Hanley. -*-
# this is the main file for the a working eink dashboard, adapted from DispatchPi.


# Fix font size in text replacement
# Add precip probability for two forecasts 

import os
import flask
from flask import send_file
import requests
import json
import datetime

#google libraries
import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

#local functions

from helper_functions import generate_credentials, pull_and_display_image, update_svg, get_sun_times
from update_weather_time import *
from google_tasks import Gtasks_connector

##SECRETS  - change the file paths as needed

#Path to your API credentials file
CLIENT_SECRETS_FILE_GMAIL = "secrets/client_secret_gmail.json"
CLIENT_SECRETS_FILE_GTASKS = "secrets/client_secret_gtasks.json"
#Path to your API Access token file
TOKEN_FILE_GMAIL = 'secrets/token_gmail.json'
TOKEN_FILE_GTASKS = 'secrets/token_gtasks.json'

#Path to your Flask app key
FLASK_KEY='secrets/flask_key.json'

##AUTH

# This OAuth 2.0 access scope allows to read emails
SCOPES_GMAIL = ['https://www.googleapis.com/auth/gmail.readonly']
SCOPES_GTASKS = ['https://www.googleapis.com/auth/tasks.readonly']
#API_SERVICE_NAME = 'gmail'
#API_VERSION = 'v3'

##FLASK APP
app = flask.Flask(__name__)
   
# Flask app key (so that session parameters work)
with open(FLASK_KEY) as secrets_file:
    key_file = json.load(secrets_file)
    app.secret_key = key_file['SECRET_KEY']
  
# !!!!!! APP STARTS HERE !!!!
# draw the index
@app.route('/')
def index():

  return ('<table>' + 
          "<tr><td><a href='/display_gmail_image''>See the image pulled from Gmail</a></td>" +
          "<tr><td><a href='/display_grocery_list''>See the Google Tasks grocery list</a></td>" +
          "<tr><td><a href='/dashboard_homepage''>See dashboard homepage</a></td>" +    
          "<tr><td><a href='/weather_output''>See weather output</a></td>" +                
          '<tr><td><a href="/authorize">Test the auth flow directly (gmail by default). You will be sent back to the index</a></td>' +
          '<tr><td><a href="/revoke">Revoke current credentials</a></td>' +
          '</td></tr></table>')

# display grocery list fetched from Google Keep
@app.route('/display_grocery_list')
def api_route_grocery_list():
     #update refresh token if we have a token file
  if os.path.exists(TOKEN_FILE_GTASKS):
    credentials = generate_credentials(token_file=TOKEN_FILE_GTASKS, scopes=SCOPES_GTASKS)
  
  #if there are no credentials, redirect to the authorization flow 
  else:
    # keep the current token file and scopes in session memory
    flask.session['token_file'] = TOKEN_FILE_GTASKS
    flask.session['scopes'] = SCOPES_GTASKS
    flask.session["client_secret_file"] = CLIENT_SECRETS_FILE_GTASKS
    return flask.redirect('authorize')

  # pull and display grocery list
  # initialize connector
  Google_tasks =  Gtasks_connector(creds=credentials)

  # print the current lists
  #Google_tasks.display_lists()

  # show tasks
  to_buy = Google_tasks.list_tasks(tasklist_id = "QURQdHRPV1RhVkRKWUhWcQ") 
  
  return to_buy


# display weather output
@app.route('/weather_output')
def weather_output():

  weather_output = get_can_weather(coordinates=(45.54160128500828, -73.62824930000188))

  pretty_output = format_weather_description(
     weather_description = weather_output[1]["description"],
     max_width = 50)
  
  return(f'{weather_output}')
  return(f'{pretty_output}')

# display dashboard homepage
@app.route('/dashboard_homepage')
def display_homepage():


  # get sunrise/sunset
  sunrise_local, sunset_local = get_sun_times(coordinates=(45.54160128500828, -73.62824930000188))

  current_period, future_period_1, future_period_2 = ({'temp': '23.3', 'humidex': '28', 'humidity': '67', 'uv_index': '7'}, {'title': 'Ce soir et cette nuit', 'description': "Devenant nuageux ce soir. 60 pour cent de probabilité d'averses au cours de la nuit. Vents du sud-ouest de 20 km/h avec rafales à 40 devenant légers ce soir. Minimum 18.", 'temp': '18', 'temp_class': 'low', 'icon_url': 'https://meteo.gc.ca/weathericons/36.gif', 'precip': '60', 'aqi_next_period_1_title': 'Ce soir et cette nuit', 'aqi_next_period_1': '3'}, {'title': 'Lundi', 'description': 'Dégagement le matin. Maximum 24. Humidex 26. Indice UV de 7 ou élevé.', 'temp': '24', 'temp_class': 'high', 'icon_url': 'https://meteo.gc.ca/weathericons/05.gif', 'precip': '0', 'aqi_next_period_2_title': 'Demain', 'aqi_next_period_2': '2'})

  output_svg_filename = 'svg_output.svg'
  
  output_dict = {
    "current_temp" : current_period["temp"]+" °C",
    "current_humidex" : current_period["humidex"]+ " °C",
    "current_humidity" : current_period["humidity"]+ "%",
    "current_uv_index" : current_period["uv_index"],
    "aqi_next_period_1_title" : "IQA " + future_period_1["aqi_next_period_1_title"].lower(),
    "aqi_next_period_1_value" : future_period_1["aqi_next_period_1"],
    "aqi_next_period_2_title" : "IQA " + future_period_2["aqi_next_period_2_title"].lower(),
    "aqi_next_period_2_value" : future_period_2["aqi_next_period_2"],
    "period_1_title" : future_period_1["title"],
    "period_1_forecast" : future_period_1["description"],
    "period_1_precip" : future_period_1["precip"]+ "%",
    "period_1_temp" : future_period_1["temp"]+ " °C",
    "period_1_temp_type" : future_period_1["temp_class"],
    "period_2_title" : future_period_2["title"],
    "period_2_forecast" : future_period_2["description"],
    "period_2_precip" : future_period_2["precip"]+ "%",
    "period_2_temp" : future_period_2["temp"]+ " °C",
    "period_2_temp_type" : future_period_2["temp_class"], 
    "sunrise" : sunrise_local.strftime('%H:%M'), #display HH:MM
    "sunset" : sunset_local.strftime('%H:%M'), #display HH:MM 
  }

  update_svg(template_svg_filename = "svg_final.svg", output_svg_filename = output_svg_filename, output_dict = output_dict)

  # Read the SVG file and send it as a response
  with open(output_svg_filename, 'r') as f:
      svg = f.read()
  return flask.Response(svg, mimetype="image/svg+xml")

# display image pulled from gmail
@app.route('/display_gmail_image')
def api_route_gmail_image():
  
  #update refresh token if we have a token file
  if os.path.exists(TOKEN_FILE_GMAIL):
    credentials = generate_credentials(token_file=TOKEN_FILE_GMAIL, scopes=SCOPES_GMAIL)
  
  #if there are no credentials, redirect to the authorization flow 
  else:
    # keep the current token file and scopes in session memory
    flask.session['token_file'] = TOKEN_FILE_GMAIL
    flask.session['scopes'] = SCOPES_GMAIL
    flask.session["client_secret_file"] = CLIENT_SECRETS_FILE_GMAIL
    return flask.redirect('authorize')

  #pull and display image
  output = pull_and_display_image(creds = credentials)
  return send_file(output, mimetype="image/png")


# build the authorization flow
@app.route('/authorize')
def authorize():

  # if no token file stored in session, assume we are testing gmail
  if 'token_file' not in flask.session:
    flask.session['token_file'] = TOKEN_FILE_GMAIL
    flask.session['scopes'] = SCOPES_GMAIL
    flask.session["client_secret_file"] = CLIENT_SECRETS_FILE_GMAIL
    
  #if we are just testing the auth flow and the credentials are expired, simply refresh them
  if os.path.exists(flask.session['token_file']):
      credentials = Credentials.from_authorized_user_file(flask.session['token_file'], flask.session['scopes'])
      if not credentials.valid:
          credentials.refresh(Request())

          #Save credentials to file if they were refreshed
          with open(flask.session['token_file'], 'w') as token:
              token.write(credentials.to_json())

      return flask.redirect(flask.url_for('index'))
    
  #otherwise fetch the full creds
  else: 
      # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
      flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
          flask.session["client_secret_file"], scopes=flask.session["scopes"])

      # The URI created here must exactly match one of the authorized redirect URIs
      # for the OAuth 2.0 client, which you configured in the API Console. If this
      # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
      # error.
      flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
    
      authorization_url, state = flow.authorization_url(
          # Enable offline access so that you can refresh an access token without
          # re-prompting the user for permission. Recommended for web server apps.
          access_type='offline',
          # Enable incremental authorization. Recommended as a best practice.
          include_granted_scopes='false')
    
      # Store the state so the callback can verify the auth server response.
      flask.session['state'] = state

      return flask.redirect(authorization_url)

# define the callback
@app.route('/oauth2callback')
def oauth2callback():
  # Specify the state when creating the flow in the callback so that it can
  # verified in the authorization server response.
  state = flask.session['state']

  flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      flask.session["client_secret_file"], scopes=flask.session["scopes"], state=state)
  flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

  # Use the authorization server's response to fetch the OAuth 2.0 tokens.
  authorization_response = flask.request.url
  flow.fetch_token(authorization_response=authorization_response)

  # Store credentials in the session.
  credentials = flow.credentials
 
  #save the credentials to file
  with open(flask.session['token_file'], 'w') as token:
      token.write(credentials.to_json())

  return flask.redirect(flask.url_for('index'))

#revoke the credentials : remove the app from authorized apps
#this will reset the refresh token, you'll have to erase the token file to start over
@app.route('/revoke')
def revoke():

  credentials = Credentials.from_authorized_user_file(flask.session['token_file'], flask.session['scopes'])

  revoke = requests.post('https://oauth2.googleapis.com/revoke',
      params={'token': credentials.token},
      headers = {'content-type': 'application/x-www-form-urlencoded'})

  status_code = getattr(revoke, 'status_code')
  if status_code == 200:
    return('Credentials successfully revoked.' + index())
    
  else:
    return('An error occurred.' + index())

if __name__ == '__main__':
  #   When running locally, disable OAuthlib's HTTPs verification.
  #   When running in production *do not* leave this option enabled.
  os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

   #Specify a hostname and port that are set as a valid redirect URI
   #for your API project in the Google API Console.
   #set debug to true when testing locally
  app.run('localhost', 8080, debug=True)

else:
  # When running online, use HTTPS for URLs
  # The lines below should be disabled if you are testing the code locally
  # This is handled by the if name == main block above
  class ReverseProxied(object):
      def __init__(self, app):
          self.app = app

      def __call__(self, environ, start_response):
          scheme = environ.get('HTTP_X_FORWARDED_PROTO')
          if scheme:
              environ['wsgi.url_scheme'] = scheme
          return self.app(environ, start_response)
          
  app.wsgi_app = ReverseProxied(app.wsgi_app)

