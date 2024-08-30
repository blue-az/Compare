import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import pytz
import UZeppWrangle
import WatchWrangle
import BabWrangle
import plotly.graph_objects as go
import subprocess
from IPython.display import display

# Path for all three sensors
Apple_path = "/home/blueaz/Downloads/SensorDownload/Compare/WristMotion.csv"
Bab_path = "/home/blueaz/Python/Sensors/Bab/BabWrangle/src/BabPopExt.db"
UZepp_path = "/home/blueaz/Downloads/SensorDownload/Compare/ztennis.db"

dfa = WatchWrangle.WatchWrangle(Apple_path) 
dfb = BabWrangle.BabWrangle(Bab_path) 
dfu = UZeppWrangle.UZeppWrangle(UZepp_path) 
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 300)

# General normalization function - written by GPT-4o
# Normalizes a column based on limits from another dataframe
def normalize_column(dfa, dfb, ref_col, norm_col, new_col_name):
    min_A = dfa[ref_col].min()
    max_A = dfa[ref_col].max()
    min_B = dfb[norm_col].min()
    max_B = dfb[norm_col].max()
    def normalize(x, min_B, max_B, min_A, max_A):
        return ((x - min_B) * (max_A - min_A) / (max_B - min_B)) + min_A
    dfb[new_col_name] = dfb[norm_col].apply(normalize,
                                            args=(min_B, max_B, min_A, max_A))

# Add ZIQ value to Zepp U sensor
# ZIQ is based on PIQ & roughly grades a tennis shot on power, spin, and sweet spot
normalize_column(dfb, dfu, 'EffectScore', 'ball_spin', 'ZIQspin')
normalize_column(dfb, dfu, 'SpeedScore', 'racket_speed', 'ZIQspeed')
# Penalty function for center contact. Using Absolute value
absx = 0 - dfu['impact_position_x'].abs()
absy = 0 - dfu['impact_position_y'].abs()
dfu['abs_imp'] = 0 + (absx + absy)
normalize_column(dfb, dfu, 'StyleScore', 'abs_imp', 'ZIQpos')
#Normalize data based on inspection values chosen previously
dfu.loc[dfu['stroke'] != 'SERVEFH', 'ZIQspin'] = dfu['ZIQspin'] * 2
dfu.loc[dfu['stroke'] != 'SERVEFH', 'ZIQspeed'] = dfu['ZIQspeed'] * 1.6 
dfu['ZIQ'] = dfu['ZIQspeed'] + dfu['ZIQspin'] + dfu['ZIQpos']
dfu.loc[dfu['stroke'] == 'SERVEFH', 'ZIQ'] = dfu['ZIQ'] * .9 
# Remove outliers found during data visualization
dfu = dfu[dfu["dbg_acc_1"] < 10000]
dfu = dfu[dfu["dbg_acc_3"] < 10000]
dfu = dfu[dfu["ZIQ"] < 10000]

# Zepp U sensor has raw sensor signals and calculated fields
# create session and calc dataframes
sensor = ['time', 'dbg_acc_1', 'dbg_acc_2', 'dbg_acc_3', 'dbg_gyro_1',
       'dbg_gyro_2', 'dbg_var_1', 'dbg_var_2', 'dbg_var_3', 'dbg_var_4',
       'dbg_sum_gx', 'dbg_sum_gy', 'dbg_sv_ax', 'dbg_sv_ay', 'dbg_max_ax',
       'dbg_max_ay', 'dbg_min_az', 'dbg_max_az', 'timestamp']
calc = [ 'backswing_time', 'power', 'ball_spin',
        'impact_position_x', 'impact_position_y',
       'racket_speed', 'impact_region', 'ZIQ']
df_sensor = dfu[sensor]
df_calc = dfu[calc]

# Estimated by inspection to properly line up clocks
tolerance = pd.Timedelta('5s')
shift = 5 
dfb['time'] = dfb['time'] - pd.Timedelta(seconds=shift) 

dfu_dba_merge = pd.merge_asof(dfu, dfb,
                          left_on='time',
                          right_on='time',
                          tolerance=tolerance,
                          direction='nearest')

# Estimated by inspection
tolerance = pd.Timedelta('5s')
shift = -1 

# Ensure the timestamps are in the same format
dfa['timestamp'] = pd.to_datetime(dfa['timestamp'])
df_sensor['timestamp'] = pd.to_datetime(df_sensor['timestamp'])
dfa['timestamp'] = dfa['timestamp'] - pd.Timedelta(seconds=shift) 

df_merged = pd.merge_asof(dfa, df_sensor,
                          left_on='timestamp',
                          right_on='timestamp',
                          tolerance=tolerance,
                          direction='nearest')

# normalize_column(df_sensor, df_merged, 'dbg_acc_1', 'rotationRateX', 'RRXNorm1')
# normalize_column(df_sensor, df_merged, 'dbg_acc_2', 'rotationRateY', 'RRXNorm2')
# normalize_column(df_sensor, df_merged, 'dbg_acc_3', 'rotationRateZ', 'RRXNorm3')
normalize_column(df_sensor, df_merged, 'dbg_acc_1', 'accelerationX', 'AccXNorm1')
# normalize_column(df_sensor, df_merged, 'dbg_acc_2', 'accelerationY', 'AccXNorm2')
# normalize_column(df_sensor, df_merged, 'dbg_acc_3', 'accelerationZ', 'AccXNorm3')
# normalize_column(df_sensor, df_merged, 'dbg_max_ax', 'accelerationX', 'AccMax1')
# normalize_column(df_sensor, df_merged, 'dbg_max_ay', 'accelerationY', 'AccMax2')
# normalize_column(df_sensor, df_merged, 'dbg_max_az', 'accelerationZ', 'AccMax3')
# normalize_column(df_sensor, df_merged, 'dbg_acc_1', 'gravityX', 'GravXNorm1')
# normalize_column(df_sensor, df_merged, 'dbg_acc_2', 'gravityY', 'GravXNorm2')
# normalize_column(df_sensor, df_merged, 'dbg_acc_3', 'gravityZ', 'GravXNorm3')
normalize_column(df_sensor, df_merged, 'dbg_gyro_1', 'accelerationX', 'Gyro1Norm1')
# normalize_column(df_sensor, df_merged, 'dbg_gyro_2', 'accelerationX', 'Gyro2Norm2')
# normalize_column(df_sensor, df_merged, 'dbg_sum_gy', 'accelerationX', 'gyNorm')

# Create the first line plot
fig = px.line(df_merged, x="timestamp", 
              y="AccXNorm1", title="Apple Watch Accelerometer")
# Add the second line plot
fig.add_trace(
    go.Scatter(x=df_merged["timestamp"],
               y=df_merged["Gyro1Norm1"],
               mode="lines", name="Apple Watch Gyro")
)
fig.add_trace(
    go.Scatter(x=df_sensor["timestamp"],
               y=df_sensor["dbg_acc_1"],
               mode="lines+markers",  # Set mode to "lines + markers" for circles
               marker=dict(size=10, symbol='circle'),  # Specify the marker symbol
               name="Zepp Acc signal Line")
)

fig.show()

print('complete')
