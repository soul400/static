import pandas as pd
from datetime import datetime
import numpy as np

def process_stream_data(raw_data, stream_id):
    """
    Process raw stream data from API or scraper into a standardized format
    
    Args:
        raw_data (dict): Raw data from API or scraper
        stream_id (str): Stream ID
        
    Returns:
        pd.DataFrame: Processed data in standardized format
    """
    try:
        # Initialize empty dataframe with required columns
        processed_data = pd.DataFrame({
            'timestamp': [datetime.now()],
            'stream_id': [stream_id],
            'streamer_name': [''],
            'likes': [0],
            'viewers': [0],
            'comments': [0],
            'gifts': [0]
        })
        
        # Extract data from raw_data, handling different formats
        if isinstance(raw_data, dict):
            # If raw_data is from API, extract fields based on expected API structure
            if 'broadcaster' in raw_data and 'name' in raw_data['broadcaster']:
                processed_data['streamer_name'] = raw_data['broadcaster']['name']
            elif 'streamer_name' in raw_data:
                processed_data['streamer_name'] = raw_data['streamer_name']
            
            # Extract metrics
            if 'stats' in raw_data:
                stats = raw_data['stats']
                processed_data['likes'] = stats.get('likes', 0)
                processed_data['viewers'] = stats.get('viewers', 0)
                processed_data['comments'] = stats.get('comments', 0)
                processed_data['gifts'] = stats.get('gifts', 0)
            else:
                processed_data['likes'] = raw_data.get('likes', 0)
                processed_data['viewers'] = raw_data.get('viewers', 0)
                processed_data['comments'] = raw_data.get('comments', 0)
                processed_data['gifts'] = raw_data.get('gifts', 0)
        
        return processed_data
    
    except Exception as e:
        print(f"Error processing stream data: {str(e)}")
        # Return empty dataframe with correct structure
        return pd.DataFrame({
            'timestamp': [datetime.now()],
            'stream_id': [stream_id],
            'streamer_name': ['Unknown'],
            'likes': [0],
            'viewers': [0],
            'comments': [0],
            'gifts': [0]
        })

def aggregate_data(data, interval='minute'):
    """
    Aggregate data for visualization based on specified time interval
    
    Args:
        data (pd.DataFrame): Raw data points
        interval (str): Time interval for aggregation ('minute', 'hour', 'day')
        
    Returns:
        pd.DataFrame: Aggregated data
    """
    if data.empty:
        return data
    
    # Ensure timestamp is datetime
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    
    # Create time group based on interval
    if interval == 'minute':
        data['time_group'] = data['timestamp'].dt.floor('Min')
    elif interval == 'hour':
        data['time_group'] = data['timestamp'].dt.floor('H')
    elif interval == 'day':
        data['time_group'] = data['timestamp'].dt.floor('D')
    else:
        data['time_group'] = data['timestamp'].dt.floor('Min')
    
    # Group by time_group and stream_id, taking max values for each metric
    # This works because metrics like likes, viewers, etc. are cumulative
    aggregated = data.groupby(['time_group', 'stream_id']).agg({
        'streamer_name': 'first',  # Take first streamer name
        'likes': 'max',            # Take maximum likes in the interval
        'viewers': 'max',          # Take maximum viewers
        'comments': 'max',         # Take maximum comments
        'gifts': 'max'             # Take maximum gifts
    }).reset_index()
    
    # Rename time_group back to timestamp for consistency
    aggregated = aggregated.rename(columns={'time_group': 'timestamp'})
    
    return aggregated

def calculate_engagement_rate(data):
    """
    Calculate engagement rate based on likes, comments, and viewers
    
    Args:
        data (pd.DataFrame): Stream data
        
    Returns:
        pd.DataFrame: Data with engagement rate added
    """
    if data.empty or 'viewers' not in data.columns:
        return data
    
    # Avoid division by zero
    data['engagement_rate'] = 0.0
    mask = data['viewers'] > 0
    
    # Calculate engagement as (likes + comments) / viewers
    data.loc[mask, 'engagement_rate'] = (data.loc[mask, 'likes'] + data.loc[mask, 'comments']) / data.loc[mask, 'viewers']
    
    # Convert to percentage
    data['engagement_rate'] = data['engagement_rate'] * 100
    
    return data

def calculate_growth_rates(data):
    """
    Calculate growth rates for key metrics
    
    Args:
        data (pd.DataFrame): Time-ordered stream data
        
    Returns:
        dict: Growth rates for different metrics
    """
    if len(data) < 2:
        return {
            'likes_growth': 0,
            'viewers_growth': 0,
            'comments_growth': 0,
            'gifts_growth': 0
        }
    
    # Sort by timestamp to ensure correct calculation
    data = data.sort_values('timestamp')
    
    # Calculate percentage changes
    first_point = data.iloc[0]
    last_point = data.iloc[-1]
    
    # Time difference in minutes
    time_diff = (last_point['timestamp'] - first_point['timestamp']).total_seconds() / 60
    
    # Avoid division by zero
    if time_diff == 0:
        time_diff = 1
    
    # Calculate rates per minute
    growth_rates = {
        'likes_growth': (last_point['likes'] - first_point['likes']) / time_diff,
        'viewers_growth': (last_point['viewers'] - first_point['viewers']) / time_diff,
        'comments_growth': (last_point['comments'] - first_point['comments']) / time_diff,
        'gifts_growth': (last_point['gifts'] - first_point['gifts']) / time_diff
    }
    
    return growth_rates
