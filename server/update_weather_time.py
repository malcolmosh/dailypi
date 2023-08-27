#!/usr/bin/python

import datetime
import sys
import os
import logging
#from alert_providers import metofficerssfeed, weathergovalerts
#from alert_providers import meteireann as meteireannalertprovider
from helper_functions import get_formatted_time, update_svg
import textwrap
import html
from helper_functions import take_from_dict

def format_weather_description(weather_description, max_width):
    if len(weather_description) < max_width:
        return {1: weather_description, 2: ''}

    splits = textwrap.fill(text = weather_description, width = max_width, break_long_words=False,
                           max_lines=8, placeholder='...').split('\n')
    
    # return all splits
    return splits

import asyncio
from env_canada import ECWeather, ECAirQuality

def capitalize_first_letter(string):
    new_text_element = string[0].upper() + string[1:]
    return new_text_element

def get_can_weather(coordinates : (float, float)):

    # initialize the class
    ec_fr = ECWeather(coordinates=coordinates, language='french')
    ec_fr_aq = ECAirQuality(coordinates=coordinates, language="FR")

    # fetch weather data
    asyncio.run(ec_fr.update())
    asyncio.run(ec_fr_aq.update())

    # weather conditions
    curr_conditions = ec_fr.conditions
    forecast = ec_fr.daily_forecasts
    #air_quality_curr = ec_fr_aq.current
    air_quality_next = ec_fr_aq.forecasts
    air_quality_two_first_items = take_from_dict(2, air_quality_next["daily"].items())

    current_period = {
        "temp" : str(curr_conditions["temperature"]["value"]),
        "humidex" : str(curr_conditions["humidex"]["value"]),
        "humidity" : str(curr_conditions["humidity"]["value"]),
        "uv_index" : str(curr_conditions["uv_index"]["value"]),
    }

    future_period_1 = {
        "title" : capitalize_first_letter(forecast[0]["period"]),
        "description" : forecast[0]["text_summary"],
        "temp" : str(forecast[0]["temperature"]),
        "temp_class" : forecast[0]["temperature_class"],
        "icon_url" : f"https://meteo.gc.ca/weathericons/{forecast[0]['icon_code']}.gif",
        "precip" : str(forecast[0]["precip_probability"]),
        "aqi_next_period_1_title" : air_quality_two_first_items[0][0],
        "aqi_next_period_1" : str(air_quality_two_first_items[0][1]),
    }

    future_period_2 = {
        "title" : capitalize_first_letter(forecast[1]["period"]),
        "description" : forecast[1]["text_summary"],
        "temp" : str(forecast[1]["temperature"]),
        "temp_class" : forecast[1]["temperature_class"],
        "icon_url" : f"https://meteo.gc.ca/weathericons/{forecast[1]['icon_code']}.gif",
        "precip" : str(forecast[1]["precip_probability"]),
        "aqi_next_period_2_title" : air_quality_two_first_items[1][0],
        "aqi_next_period_2" : str(air_quality_two_first_items[1][1])
    }

    return current_period, future_period_1, future_period_2
