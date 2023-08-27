
import asyncio
from env_canada import ECWeather, ECAirQuality

# initialize the class
coordinates=(45.54160128500828, -73.62824930000188)

ec_fr = ECWeather(coordinates=coordinates, language="french")

ec_fr_aq = ECAirQuality(coordinates=coordinates, language="EN")

# fetch weather data
asyncio.run(ec_fr.update())
asyncio.run(ec_fr_aq.update())

# daily forecast
weather_output = ec_fr.conditions
air_quality_curr = ec_fr_aq.current
air_quality_next = ec_fr_aq.forecasts

# air quality

current_period = {
    "temp" : weather_output["temperature"]["value"],
    "humidex" : weather_output["humidex"]["value"],
    "humidity" : weather_output["humidity"]["value"],
    "uv_index" : weather_output["uv_index"]["value"],
    "aqi_tomorrow" : air_quality_next["daily"]["Tomorrow"],


}

print(air_quality_next)
print(current_period)