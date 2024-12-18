import sqlite3
import pandas as pd
import pytz
from icecream import ic

# Build your `wrangle` function here
def UZeppWrangle(db_path, start_date, end_date):
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
    # Define available signals
    zepp_sensor_signals = [
        'dbg_acc_1', 'dbg_acc_2', 'dbg_acc_3', 'dbg_gyro_1', 
        'dbg_gyro_2', 'dbg_var_1', 'dbg_var_2', 'dbg_var_3', 
        'dbg_var_4', 'dbg_sum_gx', 'dbg_sum_gy', 'dbg_sv_ax', 
        'dbg_sv_ay', 'dbg_max_ax', 'dbg_max_ay', 'dbg_min_az', 
        'dbg_max_az'
    ]
    zepp_calc_signals = [
        'backswing_time', 'power', 'ball_spin', 'impact_position_x', 
        'impact_position_y', 'racket_speed', 'impact_region',
        'swing_type', 'swing_side', 'l_id'
    ]
    
    # Combine sensor signals and calculation signals
    all_signals = zepp_sensor_signals + zepp_calc_signals
    df = df[all_signals]
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
    # Filter the DataFrame based on the date range
    df = df[(df['time'] >= start_date) & (df['time'] <= end_date)]
    # Format with fractional seconds to match Apple Watch
    df['timestamp'] = df['time'].dt.strftime('%m-%d-%Y %I:%M:%S.%f %p')
    df['timestamp'].sort_values()
    conn.close()
    
    return df
