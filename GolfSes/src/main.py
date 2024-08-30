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
from scipy.signal import find_peaks

# Path for all three sensors
Apple_path = "/home/blueaz/Downloads/SensorDownload/May2024/AppleWatch/Golfses/WristMotion.csv"
# Bab_path = "~/Python/Bab/BabWrangle/src/BabPopExt.db"
UZepp_path = "/home/blueaz/Downloads/SensorDownload/May2024/AppleWatch/Golfses/Golf3.db"

dfa = WatchWrangle.WatchWrangle(Apple_path) 
# dfb = BabWrangle.BabWrangle(Bab_path) 
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
# normalize_column(dfb, dfu, 'EffectScore', 'ball_spin', 'ZIQspin')
# normalize_column(dfb, dfu, 'SpeedScore', 'racket_speed', 'ZIQspeed')
# Penalty function for center contact. Using Absolute value

# Zepp U sensor sensor signals
fields = ['UPSWING_CLUB_POSTURE', 'UP_DOWN_SWING__GOF', 'TWIST_ROTATION_RATE',
       'IMPACT_SPEED', 'CLUB_FACE_GESTURE__GOF', 'ENDSWING_CLUB_POSTURE',
       'UPSWING__A_TIME', 'UPSWING__B_TIME', 'TWIST_TIME',
       'DOWNSWING_IMPACT_TIME', 'ENDSWING_TIME', 
       'FIRST_HALF_ANIMATION_SAMPLE_POINT_NUMBER',
       'SECOND_HALF_ANIMATION_START_FRAME', 'SECOND_HALF_ANIMATION_END_FRAME',
       'SECOND_HALF_ANIMATION_SAMPLE_POINT_NUMBER', 'BACK_SWING_TEMPO_SLOW',
       'TRANSITION_TEMPO_FAST', 'HAND_SPEED', 'IMPACT_DETECT', 'HAND_FIT',
       'CLUB_PLANE', 'HAND_PLANE', '_ID', 'time', 'S_ID', 'USER_ID',
       'CLIENT_CREATED', 'SWING_TYPE', 'CLUB_TYPE_1', 'CLUB_TYPE_2',
       'CLUB_LENGTH', 'CLUB_POSTURE', 'CLUB_POSITION', 'HAND', 'USER_HEIGHT',
       'YEAR', 'MONTH', 'DAY', 'FACE_ANGLE', 'SCORE', 'MODEL_ID',
       'CLIENT_HOUR', 'timestamp' ]

# Estimated by inspection
tolerance = pd.Timedelta('5s')
shift = -1 

# Ensure the timestamps are in the same format
dfa['timestamp'] = pd.to_datetime(dfa['timestamp'])
dfu['timestamp'] = pd.to_datetime(dfu['timestamp'])
dfa['timestamp'] = dfa['timestamp'] - pd.Timedelta(seconds=shift) 

df_merged = pd.merge_asof(dfa, dfu,
                          left_on='timestamp',
                          right_on='timestamp',
                          tolerance=tolerance,
                          direction='nearest')


# Extract the signal and timestamps for peak detector
signal = df_merged['SCORE']
timestamps = df_merged['timestamp']

# Detect peaks
min_distance = 25
peaks, _ = find_peaks(signal, threshold=20, distance=min_distance)
# Create the plot
fig = go.Figure()
fig.add_trace(go.Scatter(x=timestamps[peaks], y=signal[peaks], mode='markers', marker=dict(color='blue', size=10), name='Peaks'))
fig.add_trace(go.Scatter(x=timestamps, y=signal, line=dict(color='orange'),
                         mode='lines', name='Signal'))
fig.show()

print(len(peaks))



print('complete')
