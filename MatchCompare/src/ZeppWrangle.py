import sqlite3
import pandas as pd
import pytz


# Build your `wrangle` function here
def ZeppWrangle(db_path):
    # Connect to database
    conn = sqlite3.connect(db_path)

    # Construct query
    query = """
    SELECT _id, HAPPENED_TIME, SWING_TYPE, HAND_TYPE,
    SPIN, BALL_SPEED, HEAVINESS,
    POSITION_X,POSITION_Y,
    L_PLAY_SESSION_ID, IS_HIT_FRAME from SWING
    """

    # Read query results into DataFrame
    df = pd.read_sql(query, conn, index_col="_id")
    # Remove HR outliers
    # df = df[df["AVGHR"] > 50]
    # Create duration column from timestamps
    # Convert Unix timestamps to datetime objects

    df['HAPPENED_TIME'] = pd.to_datetime(df['HAPPENED_TIME'], unit='ms')
    az_timezone = pytz.timezone('America/Phoenix')
    df['HAPPENED_TIME'] = df['HAPPENED_TIME'].dt.tz_localize('UTC').dt.tz_convert(az_timezone)
    df['HAPPENED_TIME'] = df['HAPPENED_TIME'].dt.strftime('%m-%d-%Y %I:%M:%S %p')

    
    #Replace type with sport 
    hand_type = {2: "BH", 1: "FH"}
    swing_type = {4: "VOLLEY", 3: "SERVE", 2: "TOPSPIN", 0: "SLICE", 1: "FLAT", 5: "SMASH"}
    df['SWING_TYPE'] = df['SWING_TYPE'].replace(swing_type)
    df['HAND_TYPE'] = df['HAND_TYPE'].replace(hand_type)
    
    conn.close()
    
    return df

