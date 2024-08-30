import sqlite3
import pandas as pd
import pytz


# Build your `wrangle` function here
def WatchWrangle(file_path):
    # Read into DataFrame
    df = pd.read_csv(file_path)

    # Convert Unix timestamps to datetime objects
    df["timestamp"] = pd.to_datetime(df['time'], unit='ns')# + pd.to_timedelta(df['seconds_elapsed'], unit='s')

    # Convert to desired timezone (America/Phoenix)
    az_timezone = pytz.timezone('America/Phoenix')
    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert(az_timezone)

    # Format timestamp with fractional seconds
    df['timestamp'] = df['timestamp'].dt.strftime('%m-%d-%Y %I:%M:%S.%f %p')

    return df

