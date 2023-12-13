import asyncio
import datetime
from typing import List, Dict, Tuple
from env_canada import ECWeather, ECAirQuality
import os
import pytz
import locale
from itertools import islice
from timezonefinder import TimezoneFinder

TEMP_SUFFIX = "°C"
PRECIP_SUFFIX = "%"

class GetEnviroCanWeather:

    def __init__(self, coordinates: Tuple[float, float], language='french', aq_language='FR'):
        self.coordinates = coordinates
        self.ec_weather = ECWeather(coordinates=coordinates, language=language)
        self.ec_air_quality = ECAirQuality(coordinates=coordinates, language=aq_language)
        locale.setlocale(locale.LC_TIME, 'fr_CA.UTF-8')

    async def _update_data(self):
        await self.ec_weather.update()
        await self.ec_air_quality.update()

    def _capitalize(self, string: str) -> str:
        return string[0].upper() + string[1:]

    def _format_number(self, number: str, suffix: str) -> str:
        return f"{number}{suffix}"

    def get_curr_weather_and_two_next_periods(self) -> (Dict, Dict, Dict):
        asyncio.run(self._update_data())

        # Pull weather data from Environment Canada Weather website
        curr_conditions, forecast, curr_aqi, air_quality_next, alerts = self.ec_weather.conditions, self.ec_weather.daily_forecasts, self.ec_air_quality.current, self.ec_air_quality.forecasts, self.ec_weather.alerts
        
        # Get AQI only for next 2 periosd (first 2 items in dict)
        aqi_forecast_next_2_periods = list(islice(air_quality_next["daily"].items(), 2))
    
        # Format weather data
        current, period_1, period_2, alerts = self._format_current_period(curr_conditions, curr_aqi), self._format_future_period(forecast[0], aqi_forecast_next_2_periods[0], dict_num=1), self._format_future_period(forecast[1], aqi_forecast_next_2_periods[1], dict_num=2), self._format_alerts(alerts)

        # Combine dictionaries to be returned
        return (
            {**current, 
            "current_date": self.get_local_time().strftime('%A %d %B %Y, %H:%M').capitalize(),
            "sunrise": self.utc_to_local(self.get_sunrise()),
            "sunset": self.utc_to_local(self.get_sunset())
            },
            period_1,
            period_2,
            alerts

        )

    def _format_alerts(self, alerts : Dict) -> List:
        list_of_notices = []
        for value in alerts.values():
            if len(value["value"])>0:
                notice = value["label"] + ": "  + value["value"][0]["title"]
                list_of_notices.append(notice)
        return list_of_notices

    def _format_current_period(self, conditions: Dict, aqi: str) -> Dict:
        return {
            "current_temp": self._format_number(int(round(conditions["temperature"]["value"], 0)), TEMP_SUFFIX),
            "current_humidex": self._format_number(conditions["humidex"]["value"], TEMP_SUFFIX),
            "current_humidity": self._format_number(conditions["humidity"]["value"], PRECIP_SUFFIX),
            "current_uv_index": conditions["uv_index"]["value"],
            "current_icon_code": int(conditions["icon_code"]["value"]),
            "current_aqi": aqi or "0"
        }

    def _format_future_period(self, forecast: Dict, aqi_forecast_item: Tuple, dict_num: int) -> Dict:
        title, aqi_value = aqi_forecast_item
        return {
            f"period{dict_num}_title": self._capitalize(forecast["period"]),
            f"period{dict_num}_forecast": forecast["text_summary"],
            f"period{dict_num}_temp": self._format_number(forecast["temperature"], TEMP_SUFFIX),
            f"period{dict_num}_temp_type": forecast["temperature_class"],
            f"period{dict_num}_icon_code": int(forecast['icon_code']),
            f"period{dict_num}_precip": self._format_number(forecast["precip_probability"], PRECIP_SUFFIX),
            "aqi_next_period": str(aqi_value),
        }
   
    def get_timezone(self):
        tf = TimezoneFinder()

        # Use timezonefinder to get the timezone
        timezone_str = tf.timezone_at(lat=self.coordinates[0], lng=self.coordinates[1])
        if timezone_str is None:
            raise ValueError("Could not determine the timezone from the provided coordinates.")
        return timezone_str

    def get_local_time(self):
        # Get the current time
        local_timezone = pytz.timezone(self.get_timezone())
        local_time = datetime.datetime.now(local_timezone)  # you get the local time (not UTC) directly
        return local_time
    
    def get_sunrise(self):
        sunrise = self.ec_weather.conditions['sunrise']['value']
        return sunrise
        
    def get_sunset(self):
        sunset = self.ec_weather.conditions['sunset']['value']
        return sunset
    
    def utc_to_local(self, utc_dt):
        # Check if utc_dt is a valid datetime object
        if utc_dt is None or not isinstance(utc_dt, datetime.datetime):
            raise ValueError("Invalid utc_dt: utc_dt must be a valid datetime object.")

        # Get the timezone string from coordinates
        local_tz_str = self.get_timezone()
        
        # Create a timezone object from the string
        local_tz = pytz.timezone(local_tz_str)
        
        # Convert the UTC datetime object to the local timezone
        local_dt = utc_dt.astimezone(local_tz)  # since utc_dt now has pytz.utc, we don't need to replace it again
        
        # Return the local datetime
        return local_dt.strftime('%H:%M')