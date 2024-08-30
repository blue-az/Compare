import sqlite3
import pandas as pd
import pytz

# Build your `wrangle` function here
def UZeppWrangle(db_path):
    # Connect to database
    conn = sqlite3.connect(db_path)

    # Construct query
    query = """
    SELECT * 
    FROM swings
    """
    # Read query results into DataFrame
    # df = pd.read_sql(query, conn, index_col="time")
    df = pd.read_sql(query, conn)
    df = df.sort_index()  
    # df = df.drop_duplicates()
    
    df['l_id'] = pd.to_datetime(df['l_id'], unit='ms')
    az_timezone = pytz.timezone('America/Phoenix')
    df['l_id'] = df['l_id'].dt.tz_localize('UTC').dt.tz_convert(az_timezone)
    df['l_id'] = df['l_id'].dt.strftime('%m-%d-%Y %I:%M:%S %p')
    df["l_id"] = pd.to_datetime(df["l_id"])

    df.dropna(inplace=True)
    df = df.sort_values("l_id")
    # df.set_index('l_id', inplace=True)
    # Replace # with descriptions
    hand_type = {1: "BH", 0: "FH"}
    swing_type = {4: "VOLLEY", 3: "SERVE",
                  2: "TOPSPIN", 0: "SLICE",
                  1: "FLAT", 5: "SMASH"}
    df['swing_type'] = df['swing_type'].replace(swing_type)
    df['hand_type'] = df['swing_side'].replace(hand_type)
    df['stroke'] = df['swing_type'] + df['hand_type']

    # add new impact column
    df['diffxy'] = 0.5 * df['impact_position_x'] - df['impact_position_y']

    # add to select comparison match on 6/13
    df.rename(columns = {'l_id' : 'time'}, inplace=True)
    mask = df['time'] > '2024-06-12'
    df = df[mask]
    mask = df['time'] < '2024-06-14'
    df = df[mask]

    # Format with fractional seconds to match Apple Watch
    df['timestamp'] = df['time'].dt.strftime('%m-%d-%Y %I:%M:%S.%f %p')

    conn.close()
    
    return df
