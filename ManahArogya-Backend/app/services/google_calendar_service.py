import os
import json
import datetime
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build
from app.core.logging import logger

def get_calendar_service():
    """Builds and returns the Google Calendar service."""
    creds_str = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
    if not creds_str:
        logger.warning("GOOGLE_CALENDAR_CREDENTIALS environment variable is not set. Calendar sync will be disabled.")
        return None

    try:
        # Check if it's a JSON string representing a service account
        creds_dict = json.loads(creds_str)
        creds = ServiceAccountCredentials.from_service_account_info(
            creds_dict, scopes=['https://www.googleapis.com/auth/calendar']
        )
        return build('calendar', 'v3', credentials=creds)
    except Exception as e:
        logger.error(f"Failed to initialize Google Calendar client: {e}")
        return None


def fetch_free_busy(therapist_email: str, time_min: datetime.datetime, time_max: datetime.datetime):
    """Fetch free/busy info for a specific therapist's calendar email."""
    service = get_calendar_service()
    if not service:
        return []

    try:
        body = {
            "timeMin": time_min.isoformat() + 'Z',
            "timeMax": time_max.isoformat() + 'Z',
            "timeZone": "UTC",
            "items": [{"id": therapist_email}]
        }
        eventsResult = service.freebusy().query(body=body).execute()
        calendars = eventsResult.get('calendars', {})
        calendar = calendars.get(therapist_email, {})
        busy_slots = calendar.get('busy', [])
        return busy_slots
    except Exception as e:
        logger.error(f"Error fetching free/busy for {therapist_email}: {e}")
        return []


def create_calendar_event(therapist_email: str, user_email: str, start_time: str, end_time: str, summary: str, description: str):
    """Creates a new calendar event for the booking."""
    service = get_calendar_service()
    if not service:
        # Return a fake ID for testing if calendar is disabled
        return f"fake_event_{datetime.datetime.now().timestamp()}"

    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time,
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'UTC',
        },
        'attendees': [
            {'email': user_email},
            {'email': therapist_email},
        ],
        'reminders': {
            'useDefault': True,
        },
    }

    try:
        # Insert event into the primary (service account) calendar or the therapist's calendar
        # We assume the service account has domain-wide delegation or the calendar is shared
        created_event = service.events().insert(calendarId=therapist_email, body=event, sendUpdates='all').execute()
        return created_event.get('id')
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        return None


def delete_calendar_event(therapist_email: str, event_id: str):
    """Deletes an event from the calendar."""
    service = get_calendar_service()
    if not service:
        return
        
    try:
        service.events().delete(calendarId=therapist_email, eventId=event_id).execute()
    except Exception as e:
        logger.error(f"Error deleting event {event_id}: {e}")
