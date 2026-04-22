"""
Script: asteroids_neows.py
Description: Fetches near-Earth object (asteroid) data from NASA's NeoWs API.
Refresh Frequency: Daily (new asteroid data every day)
"""

import os
from dotenv import load_dotenv
import requests


def get_asteroids_feed() -> dict:
    """
    Fetches near-Earth object (asteroid) data from NASA's NeoWs API.

    Returns:
        dict: JSON response containing asteroid data for the current date range.
    """
    load_dotenv()
    api_key = os.getenv("NASA_API_KEY")
    url = f"https://api.nasa.gov/neo/rest/v1/feed?api_key={api_key}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    from pprint import pprint
    pprint(get_asteroids_feed())
