"""
Script: eonet_events.py
Description: Fetches natural event data from NASA's Earth Observatory Natural Event Tracker (EONET) API.
Refresh Frequency: Daily or more frequent (events updated as they occur)
"""

import os
from dotenv import load_dotenv
import requests


def get_eonet_events() -> dict:
    """
    Fetches natural event data from NASA's EONET API.

    Returns:
        dict: JSON response containing a list of current natural events tracked by NASA.
    """
    load_dotenv()
    api_key = os.getenv("NASA_API_KEY")
    url = f"https://eonet.gsfc.nasa.gov/api/v3/events?api_key={api_key}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    from pprint import pprint
    pprint(get_eonet_events())
