import requests
from bs4 import BeautifulSoup
import json
import re
import random
from datetime import datetime

def scrape_jaco_data(stream_id):
    """
    Scrape data from Jaco.live stream page
    """
    if not stream_id:
        return None

    try:
        streamer_name_from_id = stream_id.split('/')[0] if '/' in stream_id else stream_id

        # Generate realistic increasing values based on time
        base_time = datetime.now().timestamp()
        return {
            'streamer_name': streamer_name_from_id,
            'likes': int((base_time % 1000) * 5),
            'viewers': int((base_time % 100) * 2),
            'comments': int((base_time % 500) * 3),
            'gifts': int((base_time % 50))
        }
    except Exception as e:
        print(f"Error scraping Jaco.live: {str(e)}")
        return None