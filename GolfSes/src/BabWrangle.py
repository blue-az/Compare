import sqlite3
import pandas as pd
import pytz

# Build your `wrangle` function here
def BabWrangle(db_path):
    # Connect to database
    conn = sqlite3.connect(db_path)

    # Construct query
    query = """
    SELECT time, type, spin, 
    StyleScore, StyleValue, 
    EffectScore, EffectValue,
    SpeedScore, SpeedValue,
    stroke_counter 
    FROM motions
    """

    # Read query results into DataFrame
    # df = pd.read_sql(query, conn, index_col="time")
    df = pd.read_sql(query, conn)
    # Remove HR outliers
    # df = df[df["AVGHR"] > 50]
    # Create duration column from timestamps
    # Convert Unix timestamps to datetime objects

#    df.drop(["session_counter"])
    df = df.sort_index()  
    df = df.drop_duplicates()
    df['time'] = pd.to_datetime(df['time']/10000, unit='s')
    az_timezone = pytz.timezone('America/Phoenix')
    df['time'] = df['time'].dt.tz_localize('UTC').dt.tz_convert(az_timezone)
    df['time'] = df['time'].dt.strftime('%m-%d-%Y %I:%M:%S %p')
    #Add PIQ column
    df['PIQ'] = df['SpeedScore'] + df['StyleScore'] + df['EffectScore']
    df = df.sort_values("time")

    # Select calibration session 6/13
    mask = df['time'] > '06-12-24'
    df = df[mask]
    mask = df['time'] < '06-14-24'
    df = df[mask]
    df["time"] = pd.to_datetime(df["time"])
    dfb = df
    
    conn.close()
    
    return df
