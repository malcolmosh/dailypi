# -*- Code created 2023-2024. Olivier Simard-Hanley. -*-

# A simple dashboard for an e-paper screen powered by a Raspberry Pi. 
# This is a flask app that fetches data from Google services (Gmail, Calendar, Tasks) and other libraries to display on an e-paper screen.
# It produces a simple PNG image that can be displayed on the e-paper screen.

import os
import flask
from flask import send_file
import requests
import json
from io import BytesIO
from itertools import islice
from dotenv import load_dotenv
import ast

#google libraries
import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

#local functions

from gmail_connector import GmailConnector
from google_calendar import GCalConnector
from eink_image import Image_transform
from svg_updater import SVGFile
from get_weather import GetEnviroCanWeather
from google_tasks import GtasksConnector

# Get the absolute path of the directory of the current script
dir_path = os.path.dirname(os.path.realpath(__file__))

# Load environment variables in .env file
load_dotenv()

# Fetch env variables
CLIENT_SECRETS_FILE = os.getenv("CLIENT_SECRETS_FILE")
FLASK_KEY = os.getenv("FLASK_KEY")
WEATHER_COORDINATES = ast.literal_eval(os.getenv("WEATHER_COORDINATES"))
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
GOOGLE_TASKS_LIST_ID = os.getenv("GOOGLE_TASKS_LIST_ID")

# Fetch tokens for Google services from .env file
TOKEN_GMAIL = os.getenv("TOKEN_GMAIL")
TOKEN_GTASKS = os.getenv("TOKEN_GTASKS")
TOKEN_GCALENDAR = os.getenv("TOKEN_GCALENDAR")

# Fetch scopes (transform string into list)
SCOPES_GMAIL = os.getenv('SCOPES_GMAIL').split(',')
SCOPES_GTASKS = os.getenv('SCOPES_GTASKS').split(',')
SCOPES_GCALENDAR = os.getenv('SCOPES_GCALENDAR').split(',')

## FLASK APP
app = flask.Flask(__name__)
app.secret_key= FLASK_KEY

## FUNCTIONS

def refresh_token(token_name : str, from_session : bool):

  if from_session:
    credentials = Credentials.from_authorized_user_info(
    json.loads(flask.session[token_name])
  )
    
  elif from_session==False:
    credentials = Credentials.from_authorized_user_info(
    json.loads(os.getenv(token_name))
  )

  if not credentials.valid:
    print(f"{flask.session['service_name']} credentials not valid, refreshing")

    credentials.refresh(Request())

    # Save credentials to flask session
    flask.session[token_name] = credentials.to_json()

  return credentials

def auth_flow():

  token_name = flask.session['service_name']+'_TOKEN'
  token_from_env = os.getenv(flask.session['service_name']+'_TOKEN')

  # first check if we have a credential stored in the flask session
  if token_name in flask.session:
    print(f"{token_name} found in session")
    credentials = refresh_token(token_name = token_name, from_session = True)
    return credentials

  # otherwise check if we have anything in the env file
  elif token_from_env:
    print(f"{token_name} found in env")

    credentials = refresh_token(token_name=token_name, from_session = False)
    return credentials

   # otherwise generate credentials from scratch
  else:
    print(f"{token_name} not found, generating new credentials")
    return None
  
def revoke_flow():
   
  token_from_env = os.getenv(flask.session['service_name']+'_TOKEN')

  credentials = Credentials.from_authorized_user_info(json.loads(token_from_env), flask.session['scopes'])

  revoke = requests.post('https://oauth2.googleapis.com/revoke',
      params={'token': credentials.token},
      headers = {'content-type': 'application/x-www-form-urlencoded'})

  status_code = getattr(revoke, 'status_code')

  if status_code == 200:
    return('Credentials successfully revoked.' + index())
    
  else:
    return('An error occurred.' + index())

   
def fetch_grocery_list():
    flask.session['service_name'] = 'GTASKS'
    flask.session['scopes'] = SCOPES_GTASKS
    
    credentials = auth_flow()

    # If credentials are None, we need to generated them
    if not credentials:
      return flask.redirect('authorize')
    
    else:   
      Google_tasks = GtasksConnector(creds=credentials) # Connect to service 
      # Google_tasks.get_lists() # Run to see the available task lists in your account
      grocery_items = Google_tasks.get_tasks(tasklist_id=GOOGLE_TASKS_LIST_ID) # Fetch a specific task list
      
      return grocery_items

def fetch_image_from_gmail():
  flask.session['service_name'] = 'GMAIL'
  flask.session['scopes'] = SCOPES_GMAIL
  
  credentials = auth_flow()
  
  # If credentials are None, we need to generated them
  if not credentials:
    return flask.redirect('authorize')
  
  else:   
    # initialize Gmail connector
    gmail_inbox =  GmailConnector(creds=credentials)

    # pull attachments (num_emails looks at the X most recent emails to be sure we intercept an attachment)
    gmail_inbox.pull_attachments(userID='me', num_emails=3)

    # get the image to send
    image_to_send, output_text = gmail_inbox.grab_first_image(userID = 'me')
  
    # prepare bytes stream
    output_stream = BytesIO()
    #transform image into a low res format for the eink screen
    transformed_image = Image_transform(path_or_image=image_to_send)
    transformed_image.save(output_path_or_stream = output_stream)
      
    # display the image (don't cache it)
    # output.seek resets the pointer to the beginning of the file 
    output_stream.seek(0)
    
    return send_file(output_stream, mimetype="image/png")

def fetch_weather():
  weather_service = GetEnviroCanWeather(WEATHER_COORDINATES)
  return weather_service.get_weather_data()

def fetch_calendar_events():
  flask.session['service_name'] = 'GCALENDAR'
  flask.session['scopes'] = SCOPES_GCALENDAR
  
  credentials = auth_flow()
  
  # If credentials are None, we need to generated them
  if not credentials:
    return flask.redirect('authorize')

  else:   
    weather_service = GetEnviroCanWeather(WEATHER_COORDINATES)   # Get local timezone from weather service
    local_timezone_str = weather_service._timezone 

    google_calendar = GCalConnector(creds = credentials, local_timezone_str= local_timezone_str, calendar_id=GOOGLE_CALENDAR_ID)
    #google_calendar.get_calendars_list() # Run to print the available calendars in your account

    return google_calendar.get_calendar_events()

def take_from_dict(n, iterable):
    """Return the first n items of the iterable as a list."""
    return list(islice(iterable, n))

  
## APP STARTS HERE

# draw the index
@app.route('/')
def index():

  return ('<table>' + 
    "<tr><td><a href='/display_gmail_image'>Test Gmail</a></td></tr>" +
    "<tr><td><a href='/display_calendar_events'>Test Google Calendar</a></td></tr>" +
    "<tr><td><a href='/display_grocery_list'>Test Google Tasks</a></td></tr>" +
    "<tr><td><a href='/weather_output'>Test the weather output (no API required)</a></td></tr>" +                
    "<tr><td colspan='2'><hr></td></tr>" +
    "<tr><td><b><a href='/dashboard_homepage'>See dashboard homepage</a></b></td></tr>" +    
    "<tr><td colspan='2'><hr></td></tr>" +
    "<tr><td><a href='/authorize'>Test the auth flow (Gmail by default). You will be sent back to the index</a></td></tr>" +
    "<tr><td><a href='/revoke_gmail'>Revoke the credentials for Gmail</a></td></tr>" +
    "<tr><td><a href='/revoke_gtasks'>Revoke the credentials for Google Tasks</a></td></tr>" +
    "<tr><td><a href='/revoke_gcalendar'>Revoke the credentials for Google Calendar</a></td></tr>" +
    '</table>')
# display grocery list fetched from Google Tasks
@app.route('/display_grocery_list')
def api_route_grocery_list():
  return fetch_grocery_list()

# display grocery list fetched from Google Calendar
@app.route('/display_calendar_events')
def api_route_calendar_events():
  return fetch_calendar_events()

# display weather output fetched from Weather Canada
@app.route('/weather_output')
def weather_output():
    weather_data = fetch_weather()
    return f'{weather_data}'

# display dashboard homepage
@app.route('/dashboard_homepage')
def draw_homepage():
    # Get weather data as a dictionary
    weather_data = fetch_weather()
    current_weather_dict = weather_data["current"]
    forecast_1_period_dict = weather_data["period_1"]
    forecast_period_2_dict = weather_data["period_2"]
    alerts = weather_data["alerts"]

    # Get grocery list
    grocery_items = {"grocery_list": fetch_grocery_list()}

    # Get calendar items
    calendar_items = {"calendar_events": fetch_calendar_events()}

    final_svg = SVGFile(template_svg_filepath=os.path.join(dir_path, "svg_template.svg"), 
                       output_filename=os.path.join(dir_path, "svg_output.svg"))
    
    final_svg.update_svg(current_weather_dict=current_weather_dict, 
                        forecast_1_period_dict=forecast_1_period_dict, 
                        forecast_period_2_dict=forecast_period_2_dict, 
                        grocery_dict=grocery_items, 
                        calendar_dict=calendar_items)
    output = final_svg.send_to_pi()
    
    return send_file(output, mimetype="image/png")


# display image pulled from gmail
@app.route('/display_gmail_image')
def api_route_gmail_image():

  return fetch_image_from_gmail()


# build the authorization flow
@app.route('/authorize')
def authorize():

  # if no service name is stored in session, assume we are testing gmail
  if 'service_name' not in flask.session:
    flask.session['service_name'] = 'GMAIL'
    flask.session['scopes'] = SCOPES_GMAIL
    
  # first try to get credentials in the flask session or in our env file
  try: 
    credentials = auth_flow()
  except RefreshError:
      return (f"The crendentials could not be refreshed... try removing them from the env file and restarting the auth flow again.<br><br>"
      "<a href='/'><button>Return to Index</button></a>")

  if credentials:    
      return flask.redirect(flask.url_for('index'))
       
  elif not credentials: 
      # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.

      # First, parse the OAuth 2.0 credential string stored in our env file - this is generated from your project in GCP
      client_config = json.loads(CLIENT_SECRETS_FILE)

      flow = google_auth_oauthlib.flow.Flow.from_client_config(
          client_config, scopes=flask.session["scopes"])

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

  config_file = json.loads(CLIENT_SECRETS_FILE)

  flow = google_auth_oauthlib.flow.Flow.from_client_config(
     config_file, scopes=flask.session["scopes"], state=state)
  flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

  # Use the authorization server's response to fetch the OAuth 2.0 tokens.
  authorization_response = flask.request.url
  flow.fetch_token(authorization_response=authorization_response)

  # Store credentials in the session.
  credentials = flow.credentials

  token_name = flask.session['service_name']+'_TOKEN'

  # Credentials as json
  credentials_as_json = credentials.to_json()

  # Save credentials to flask session
  flask.session[token_name] = credentials_as_json

  return (f"Copy this token to your .env file under the {token_name} variable: <br><br>{credentials_as_json} <br><br>"
    "<a href='/'><button>Return to Index</button></a>")


# revoke the credentials : remove the app from authorized apps
# only works if the token is stored in the env vars
# this will reset the refresh token, you'll have to remove your current token and start a new auth flow to get one
@app.route('/revoke_gmail')
def revoke_gmail():

  flask.session['service_name'] = 'GMAIL'
  return revoke_flow()

@app.route('/revoke_gtasks')
def revoke_gtasks():

  flask.session['service_name'] = 'GTASKS'
  return revoke_flow()

@app.route('/revoke_gcalendar')
def revoke_gcal():

  flask.session['service_name'] = 'GCALENDAR'
  return revoke_flow()

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
  class ReverseProxied(object):
      def __init__(self, app):
          self.app = app

      def __call__(self, environ, start_response):
          scheme = environ.get('HTTP_X_FORWARDED_PROTO')
          if scheme:
              environ['wsgi.url_scheme'] = scheme
          return self.app(environ, start_response)
          
  app.wsgi_app = ReverseProxied(app.wsgi_app)


