import asyncio
import datetime
from typing import List, Dict, Tuple, Optional
from env_canada import ECWeather, ECAirQuality
import pytz
import locale
from timezonefinder import TimezoneFinder

class GetEnviroCanWeather:   
    def __init__(self, coordinates: Tuple[float, float], language='french', aq_language='FR'):
        self.coordinates = coordinates
        self.ec_weather = ECWeather(coordinates=coordinates, language=language)
        self.ec_air_quality = ECAirQuality(coordinates=coordinates, language=aq_language)
        locale.setlocale(locale.LC_TIME, 'fr_CA.UTF-8')
        
        # Cache timezone
        self._timezone = self._get_timezone()

    async def _fetch_weather_data(self):
        await self.ec_weather.update()
        await self.ec_air_quality.update()

    def get_weather_data(self) -> Dict:
        # Fetch fresh data
        asyncio.run(self._fetch_weather_data())
        
        # Extract and format data
        current_weather = self._format_current_weather()
        next_periods = self._format_forecast_periods()
        weather_alerts = self._format_alerts()
        
        return {
            "current": current_weather,
            "period_1": next_periods[0] if next_periods else {},
            "period_2": next_periods[1] if len(next_periods) > 1 else {},
            "alerts": weather_alerts
        }

    def _safe_get(self, data: Dict, key: str, default="N/A"):
        """Safely get value from nested dict structure"""
        try:
            return data[key]['value']
        except (KeyError, TypeError):
            return default

    def _format_current_weather(self) -> Dict:
        conditions = self.ec_weather.conditions
        current_aqi = self.ec_air_quality.current
        
        if not conditions:
            return self._get_empty_current_weather()
        
        # Get humidex value once
        humidex_value = self._safe_get(conditions, 'humidex')
        
        return {
            "temp": f"{int(round(self._safe_get(conditions, 'temperature', 0), 0))}°C",
            "humidex": f"{humidex_value}°C" if humidex_value != "N/A" else "N/A",
            "humidity": f"{self._safe_get(conditions, 'humidity')}% h.r.",
            "uv_index": self._safe_get(conditions, 'uv_index'),
            "weather_icon": int(self._safe_get(conditions, 'icon_code', '0')),
            "aqi": str(current_aqi) if current_aqi else "N/A",
            "current_date": self._get_formatted_date(),
            "sunrise": self._format_time(self._safe_get(conditions, 'sunrise')),
            "sunset": self._format_time(self._safe_get(conditions, 'sunset'))
        }

    def _format_forecast_periods(self) -> List[Dict]:
        forecasts = self.ec_weather.daily_forecasts
        aqi_forecasts = self.ec_air_quality.forecasts
        
        if not forecasts or len(forecasts) < 2:
            return []
            
        # Get AQI values
        aqi_values = list(aqi_forecasts.get("daily", {}).values())[:2] if aqi_forecasts else []
        
        return [
            self._format_single_period(forecasts[i], aqi_values[i] if i < len(aqi_values) else "N/A")
            for i in range(min(2, len(forecasts)))
        ]

    def _format_single_period(self, forecast: Dict, aqi_value) -> Dict:
        return {
            "title": forecast.get("period", "").capitalize(),
            "forecast": forecast.get("text_summary", ""),
            "temp": f"{forecast.get('temperature', 0)}°C",  
            "temp_type": forecast.get("temperature_class", ""), 
            "weather_icon": int(forecast.get('icon_code', '0')),
            "precip": f"{forecast.get('precip_probability', 0)}%",
            "aqi": f"AQI: {aqi_value}"
        }

    def _format_alerts(self) -> List[str]:
        alerts = self.ec_weather.alerts
        if not alerts:
            return []
            
        alert_list = []
        for alert_data in alerts.values():
            if alert_data.get("value"):
                for alert in alert_data["value"]:
                    alert_list.append(f"{alert_data['label']}: {alert['title']}")
                    
        return alert_list

    def _get_empty_current_weather(self) -> Dict:
        return {
            "temp": "N/A",
            "humidex": "N/A", 
            "humidity": "N/A",
            "uv_index": "N/A",
            "weather_icon": 0,
            "aqi": "N/A",
            "current_date": self._get_formatted_date(),
            "sunrise": "N/A",
            "sunset": "N/A"
        }

    def _get_timezone(self) -> str:
        """Get timezone string from coordinates"""
        tf = TimezoneFinder()
        timezone = tf.timezone_at(lat=self.coordinates[0], lng=self.coordinates[1])
        if not timezone:
            raise ValueError("Could not determine timezone from coordinates")
        return timezone

    def _get_formatted_date(self) -> str:
        """Get formatted current date and time"""
        try:
            local_tz = pytz.timezone(self._timezone)
            local_time = datetime.datetime.now(local_tz)
            return local_time.strftime('%A %d %B %Y, %H:%M').capitalize()
        except Exception:
            return "N/A"

    def _format_time(self, utc_datetime) -> str:
        """Convert UTC datetime to local time string"""
        if not utc_datetime or not isinstance(utc_datetime, datetime.datetime):
            return "N/A"
            
        try:
            local_tz = pytz.timezone(self._timezone)
            local_time = utc_datetime.astimezone(local_tz)
            return local_time.strftime('%H:%M')
        except Exception:
            return "N/A"