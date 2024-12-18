import sqlite3
import pandas as pd
import pytz
from icecream import ic

# Build your `wrangle` function here
def BabWrangle(db_path, start_date, end_date):
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
    df["time"] = pd.to_datetime(df["time"])

    # Select calibration session 6/13
    df = df[(df['time'] >= start_date) & (df['time'] <= end_date)]
    
    # Create consistent stroke field for Babolat data
    def map_bab_stroke(row):
        stroke_type = row['type'].upper() if 'type' in row else ''
        spin = row['spin'].upper() if 'spin' in row else ''
        
        if stroke_type == 'SERVE':
            return 'SERVEFH'
        elif stroke_type == 'FOREHAND':
            if spin == 'LIFTED':
                return 'TOPSPINFH'
            elif spin == 'SLICED':
                return 'SLICEFH'
            elif spin == 'FLAT':
                return 'FLATFH'
            else:  # UNSPECIFIED
                return 'FLATFH'
        elif stroke_type == 'BACKHAND':
            if spin == 'LIFTED':
                return 'TOPSPINBH'
            elif spin == 'SLICED':
                return 'SLICEBH'
            elif spin == 'FLAT':
                return 'FLATBH'
            else:  # UNSPECIFIED
                return 'FLATBH'
        else:
            return 'FLATFH'  # Default case
    
    # Add stroke field to Babolat data
    if 'type' in df.columns:
        df['stroke'] = df.apply(map_bab_stroke, axis=1)
    
    conn.close()
    
    return df
