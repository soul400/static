import requests
import json
import time
from datetime import datetime
import pandas as pd

# Base URL for Jaco.live API (hypothetical)
# This would need to be updated if official API becomes available
BASE_URL = "https://api.jaco.live/v1"

def check_api_available():
    """
    Check if the Jaco.live API is available and accessible
    
    Returns:
        bool: True if API is available, False otherwise
    """
    try:
        # Attempt to access a simple endpoint to check availability
        response = requests.get(f"{BASE_URL}/status", timeout=5)
        return response.status_code == 200
    except:
        # Any exception means API is not available
        return False

def fetch_jaco_data(stream_id):
    """
    Fetch stream data from Jaco.live API
    
    Args:
        stream_id (str): The ID of the stream to fetch data for
        
    Returns:
        dict: Stream data or None if failed
    """
    try:
        # Try to get stream data from the API
        response = requests.get(f"{BASE_URL}/streams/{stream_id}/stats", timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            # If API returned an error, log it
            print(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        # Log any exceptions
        print(f"Error fetching data from API: {str(e)}")
        return None

def fetch_historical_data(stream_id, start_time=None, end_time=None):
    """
    Fetch historical data for a stream
    
    Args:
        stream_id (str): The ID of the stream
        start_time (datetime, optional): Start time for data
        end_time (datetime, optional): End time for data
        
    Returns:
        pd.DataFrame: Historical data or empty DataFrame if failed
    """
    try:
        # Set up parameters
        params = {"stream_id": stream_id}
        
        if start_time:
            params["start_time"] = start_time.isoformat()
        
        if end_time:
            params["end_time"] = end_time.isoformat()
        
        # Make API request
        response = requests.get(f"{BASE_URL}/streams/{stream_id}/history", params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and len(data["data"]) > 0:
                return pd.DataFrame(data["data"])
            else:
                return pd.DataFrame()
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching historical data: {str(e)}")
        return pd.DataFrame()
