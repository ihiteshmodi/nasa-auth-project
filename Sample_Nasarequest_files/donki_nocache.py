"""
Script: donki.py
Description: Fetches notifications from NASA's DONKI (Space Weather Database Of Notifications, Knowledge, Information) API.
Refresh Frequency: More frequent than daily (multiple updates per day possible)
"""

import os
from dotenv import load_dotenv
import requests


def get_donki_notifications() -> list[dict]:
    """
    Fetches notifications from NASA's DONKI (Space Weather Database Of Notifications, Knowledge, Information) API.

    Returns:
        list[dict]: List of dictionaries, each containing a space weather notification.
    """
    load_dotenv()
    api_key = os.getenv("NASA_API_KEY")
    url = f"https://api.nasa.gov/DONKI/notifications?api_key={api_key}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    from pprint import pprint
    pprint(get_donki_notifications())
