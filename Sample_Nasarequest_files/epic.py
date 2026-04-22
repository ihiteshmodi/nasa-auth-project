"""
Script: epic.py
Description: Fetches images from NASA's EPIC (Earth Polychromatic Imaging Camera) API.
Refresh Frequency: Daily (new images every day)
"""

import os
from dotenv import load_dotenv
import requests


def get_epic_images() -> list[dict]:
    """
    Fetches images from NASA's EPIC (Earth Polychromatic Imaging Camera) API.

    Returns:
        list[dict]: List of dictionaries, each containing metadata for an EPIC image.
    """
    load_dotenv()
    api_key = os.getenv("NASA_API_KEY")
    url = f"https://api.nasa.gov/EPIC/api/natural?api_key={api_key}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    from pprint import pprint
    pprint(get_epic_images())
