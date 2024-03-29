# -*- coding: utf-8 -*-

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dateutil import parser

class GCalConnector:
    """Connector for Google Calendar API to fetch calendar events."""

    def __init__(self, creds, local_timezone_str, calendar_id: str):
        """Initialize the connector with Google credentials."""
        self.creds = creds
        self.service = build('calendar', 'v3', credentials=creds)
        self.calendar_id = calendar_id
        self.now_utc = datetime.now(timezone.utc) # Timezone-aware current time in UTC
        self.local_timezone = ZoneInfo(local_timezone_str) # Get current timezone from string
        self.now_local = self.now_utc.astimezone(self.local_timezone)
        self.today = self.now_local.date()
        self.tomorrow = self.today + timedelta(days=1)
    
    def get_calendars_list(self):
        """Fetch the list of available calendars."""
        try:
            calendar_lists = self.service.calendarList().list().execute()
            print("Calendars list:", calendar_lists)
        except HttpError as error:
            print(f"An error occurred: {error}")

    def get_calendar_events(self, max_results=10):
        
        events = self._fetch_next_events(self.calendar_id, max_results)

        if not events:
            return ["Rien à l'horaire"]
        
        events_by_day = self._assign_events_to_dates(events)
        return self._format_event_list(events_by_day)

    def _fetch_next_events(self, calendar_id : str, max_results : int = 10):
        """Fetch the calendar events for the specified calendar and timezone."""

        # Get time boundaries to retrieve calendar events
        start_of_day, end_of_next_day = self._get_day_boundaries()

        # Retrieve events in the specified range
        events_result = self.service.events().list(
            calendarId=calendar_id,
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_next_day.isoformat(),
            maxResults=max_results, singleEvents=True, orderBy='startTime'
        ).execute()

        return events_result.get('items', [])
    
    def _assign_events_to_dates(self, events):
        # Build dictionary of events with day as key
        events_by_day = {
            self.today: [],
            self.tomorrow: []
        }

        # Cycle through events and assign them to days
        for event in events: 
            event_start_time, event_end_time = self._get_event_start_and_end(event)
            # if the start time is before the end of today, add it to today's events
            # else if the start time is greater than today, add it to tomorrow's events (since we are only retrieving 2 days)
            day = self.today if event_start_time.date() <= self.today else self.tomorrow
            events_by_day[day].append("•\u00A0"+event.get("summary"))
        
        return events_by_day
    
    def _format_event_list(self, events_by_day):
        # Output a list with all day names and events
        event_list = []
        if events_by_day.get(self.today):
            event_list.append("Aujourd'hui:")
            event_list.extend(events_by_day[self.today])
        if events_by_day.get(self.tomorrow):
            event_list.append("Demain:")
            event_list.extend(events_by_day[self.tomorrow])
        return event_list

    
    def _get_event_start_and_end(self, event):
        # Convert string to datetime.datetime objects (https://dateutil.readthedocs.io/en/stable/parser.html)

        if event['start'].get('dateTime'):
            start_time = parser.isoparse(event["start"].get("dateTime", "date"))
            end_time = parser.isoparse(event["end"].get("dateTime", "date")) 

        elif event['start'].get('date'):
            start_time = datetime.strptime(event["start"].get("date"), "%Y-%m-%d")
            end_time = datetime.strptime(event["end"].get("date"), "%Y-%m-%d")

        return start_time, end_time


    def _get_day_boundaries(self):
        start_of_day = self.now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_next_day = (start_of_day + timedelta(days=2))
        return start_of_day, end_of_next_day   
