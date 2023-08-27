
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from io import BytesIO

from gmail_connector import Gmail_connector
from eink_image import Image_transform

import os
import datetime
import pytz
from astral.sun import sun
from astral import LocationInfo



def generate_credentials(token_file, scopes):
  #if there are stored credentials, retrieve them
  credentials = Credentials.from_authorized_user_file(token_file, scopes)
  
  #if credentials are expired, refresh
  if not credentials.valid:
    credentials.refresh(Request())
    print("Credentials refreshed!")
        
    #Save credentials to file if they were refreshed 
    with open(token_file, 'w') as token:
      token.write(credentials.to_json())
      print("Credentials saved to file!")

  return credentials
  
def pull_and_display_image(creds):
  #import image from the gmail API

  # initialize connector
  gmail_inbox =  Gmail_connector(creds=creds)

  # pull attachments (num_emails looks at the X most recent emails to be sure we intercept an attachment)
  gmail_inbox.pull_attachments(userID='me', num_emails=3)

  # get the image to send
  image_to_send, output_text = gmail_inbox.grab_first_image(userID = 'me')
 
  #transform image into a low res format for the eink screen
  transformed_image = Image_transform(imported_image=image_to_send, fit="crop", message=output_text)
  transformed_image = transformed_image.render()
  output = BytesIO()
  transformed_image.save(output, "PNG")
    
  # display the image (don't cache it)
  # output.seek resets the pointer to the beginning of the file 
  output.seek(0)
  return output


# taken from https://github.com/mendhak/waveshare-epaper-display/blob/83af28b25a892325fe36c2a028534c6cba798d43/utility.py#L51
import codecs
import logging
import os
import time
from http.client import HTTPConnection
import requests
import datetime
import pytz
import json
import xml.etree.ElementTree as ET
from astral import LocationInfo
from astral.sun import sun
import humanize
import locale
from babel.dates import format_time


from lxml import etree
import textwrap

from itertools import islice

def take_from_dict(n, iterable):
    """Return the first n items of the iterable as a list."""
    return list(islice(iterable, n))


def update_svg(template_svg_filename, output_svg_filename, output_dict):
    # Parse the SVG XML
    tree = etree.parse(template_svg_filename)
    root = tree.getroot()

    # Identify the SVG namespace
    ns = {'svg': 'http://www.w3.org/2000/svg'}

    # For each key-value pair in the dictionary
    for key, value in output_dict.items():
        # Find the text element with the matching id
        text_element = find_text(root, key, ns)

        if text_element is not None:
            if key in ("period_1_forecast", "period_2_forecast"):
                max_width = 38
                font_size = 12
                adjust_text_width_in_svg(root, text_element, value, max_width, font_size, max_lines=5)
            
            if key in ("aqi_next_period_1_value", "aqi_next_period_2_value"):
                value = int(value)
                if value <=3 : 
                    added_text = "(Risque faible)"
                elif value <=6 :
                    added_text = "(Risque modéré)"
                elif value <=10 :
                    added_text = "(Risque élevé)"
                elif value >10 :
                    added_text = "(Risque très élevé)"
                value = str(value)+" " + added_text
                text_element.text = str(value)

            else:
                # Replace the text with the new value
                text_element.text = str(value)

        if "_temp_type" in key and value == "high":
            period = key.split("_temp_type")[0]  # This extracts "period_1" or "period_2" from keys like "period_1_temp_type"
            print(f"{period}_arrow")
            polygon_id = f"{period}_arrow"
            polygon = find_shape(root, id=polygon_id, namespaces=ns)
            print(polygon)
            if polygon is not None:
                new_points = output_up_arrow(period)
                polygon.set('points', new_points)

    # Write the modified SVG to the output file
    tree.write(output_svg_filename, encoding='utf-8', pretty_print=True)

def find_text(root, key, namespaces):
    text_element = root.find(".//svg:text[@id='{}']".format(key), namespaces=namespaces)
    return text_element

def find_shape(root, id, namespaces):
    polygon = root.find(".//svg:polygon[@id='{}']".format(id), namespaces=namespaces)
    return polygon

def output_up_arrow(period_name):
    if period_name=="period_2":
        points="518.1,440.7074 518.1,449.5074 515.6,449.5074 515.6,440.7074 511.8,440.7074 516.9,434.4074 521.9,440.7074"

    else:
        points="517,322 511.5,328.8 515.6,328.8 515.6,338.4 518.3,338.4 518.3,328.8 522.4,328.8 "
    return points

def adjust_text_width_in_svg(root, text_element, new_text, max_width, font_size, max_lines=5):
    # Split the new text into lines based on max_width
    splits = format_text_length(new_text, max_width, max_lines = max_lines)
    
    # Extract the transform attribute values
    matrix_values = text_element.attrib['transform'].split(' ')
    original_x = float(matrix_values[-2])
    start_y = float(matrix_values[-1].replace(')', ''))
    
    # Font size (you may need to adjust this or get it from the text element's style)
    font_size = font_size  # This is a default value; you might want to extract it from the SVG or set it explicitly.
    line_height = font_size + 2
    
    # Create new text elements for each line of text
    for index, line in enumerate(splits):
        new_text_element = etree.SubElement(root, "{http://www.w3.org/2000/svg}text")
        new_text_element.text = line
        new_y = start_y + (line_height * index)
        new_text_element.set('transform', "matrix(1 0 0 1 {} {})".format(original_x, new_y))
        for attr, val in text_element.attrib.items():
            if attr != 'transform':
                new_text_element.set(attr, val)
    
    # Remove the original text element from the SVG after creating the new ones
    text_element.getparent().remove(text_element)


# Updated format_text_length
def format_text_length(weather_description, max_width, max_lines):
    return textwrap.fill(text=weather_description, width=max_width, break_long_words=False, max_lines=max_lines, placeholder='...').split('\n')

def get_formatted_time(dt):
    try:
        formatted_time = format_time(dt, format='short', locale=locale.getlocale()[0])
    except Exception:
        logging.debug("Locale not found for Babel library.")
        formatted_time = dt.strftime("%-I:%M %p")
    return formatted_time


def get_formatted_date(dt, include_time=True):
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)
    next_week = today + datetime.timedelta(days=7)
    formatter_day = "%a %b %-d"

    # Display the time in the locale format, if possible
    if include_time:
        formatted_time = get_formatted_time(dt)
    else:
        formatted_time = " "

    try:
        short_locale = locale.getlocale()[0]  # en_GB
        short_locale = short_locale.split("_")[0]  # en
        if not short_locale == "en":
            humanize.activate(short_locale)
        has_locale = True
    except Exception:
        logging.debug("Locale not found for humanize")
        has_locale = False

    if (has_locale and
            (dt.date() == today.date()
             or dt.date() == tomorrow.date()
             or dt.date() == yesterday.date())):
        # Show today/tomorrow/yesterday if available
        formatter_day = humanize.naturalday(dt.date(), "%A").title()
    elif dt.date() < next_week.date():
        # Just show the day name if it's in the next few days
        formatter_day = "%A"
    return dt.strftime(formatter_day + " " + formatted_time)


def get_sun_times(coordinates = (float, float)):
    """
    Return the sunrise and sunset times for the provided location in local time.
    """
    location_lat = os.getenv("WEATHER_LATITUDE", coordinates[0])
    location_long = os.getenv("WEATHER_LONGITUDE", coordinates[1])
    
    dt = datetime.datetime.now(pytz.utc)
    city = LocationInfo(location_lat, location_long)
    s = sun(city.observer, date=dt)

    # Convert from UTC to local time
    local_timezone = pytz.timezone(city.timezone)
    sunrise_local = s['sunrise'].astimezone(local_timezone)
    sunset_local = s['sunset'].astimezone(local_timezone)
    
    return sunrise_local, sunset_local