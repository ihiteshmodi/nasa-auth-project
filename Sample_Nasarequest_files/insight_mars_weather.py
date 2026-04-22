"""
Script: insight_mars_weather.py
Description: Fetches daily Mars weather data from NASA's InSight Mars Weather Service API.
Refresh Frequency: Daily (new weather data every day)
"""

import os
from dotenv import load_dotenv
import requests


def get_mars_weather() -> dict:
    """
    Fetches daily Mars weather data from NASA's InSight Mars Weather Service API.

    Returns:
        dict: JSON response containing Mars weather data for the latest sol(s).
    """
    load_dotenv()
    api_key = os.getenv("NASA_API_KEY")
    url = f"https://api.nasa.gov/insight_weather/?api_key={api_key}&feedtype=json&ver=1.0"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    from pprint import pprint
    pprint(get_mars_weather())
