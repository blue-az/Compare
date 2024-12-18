import sqlite3
import pandas as pd
import pytz

def WatchWrangle(file_path, start_date=None, end_date=None):
    # Read into DataFrame
    df = pd.read_csv(file_path)
    
    # Convert Unix timestamps to datetime objects and localize to Arizona timezone
    az_timezone = pytz.timezone('America/Phoenix')
    df["timestamp"] = pd.to_datetime(df['time'], unit='ns').dt.tz_localize('UTC').dt.tz_convert(az_timezone)
    
    # Ensure the start and end dates are timezone-aware (localized to the correct timezone)
    if start_date:
        start_date = pd.to_datetime(start_date).tz_localize(az_timezone)
    if end_date:
        end_date = pd.to_datetime(end_date).tz_localize(az_timezone)
    
    # Filter the DataFrame based on the date range if provided
    if start_date and end_date:
        df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
    
    # Format timestamp with fractional seconds
    df['timestamp'] = df['timestamp'].dt.strftime('%m-%d-%Y %I:%M:%S.%f %p')
    
    return df
