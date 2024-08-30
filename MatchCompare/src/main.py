import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import pytz
import UZeppWrangle
import ZeppWrangle
import BabWrangle
import plotly.graph_objects as go
import subprocess
from IPython.display import display

Zepp2_path = "/home/blueaz/Downloads/SensorDownload/Sep14/ZeppTennis.db"
Bab_path = "/home/blueaz/Python/Sensors/Bab/BabWrangle/src/BabPopExt.db"
UZepp_path = "/home/blueaz/Downloads/SensorDownload/May2024/ztennis.db"

df = ZeppWrangle.ZeppWrangle(Zepp2_path) 
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 300)

mask = df['HAPPENED_TIME'] > '05-11-23'
df = df[mask]
mask = df['HAPPENED_TIME'] < '05-13-23'
df = df[mask]
df["HAPPENED_TIME"] = pd.to_datetime(df["HAPPENED_TIME"])
dfz = df

df = BabWrangle.BabWrangle(Bab_path) 
mask = df['time'] > '05-24-23'
df = df[mask]
mask = df['time'] < '05-25-23'
df = df[mask]
df["time"] = pd.to_datetime(df["time"])
df = df.iloc[2:] # First two rows considered outliers by inspection
dfb = df

df = UZeppWrangle.UZeppWrangle(UZepp_path) 
df.rename(columns = {'l_id' : 'time'}, inplace=True)
mask = df['time'] > '2024-05-25'
df = df[mask]
mask = df['time'] < '2024-05-26'
df = df[mask]
dfu = df

# General normalization function - written by GPT-4o
def normalize_column(dfa, dfb, ref_col, norm_col, new_col_name):
    min_A = dfa[ref_col].min()
    max_A = dfa[ref_col].max()
    min_B = dfb[norm_col].min()
    max_B = dfb[norm_col].max()
    def normalize(x, min_B, max_B, min_A, max_A):
        return ((x - min_B) * (max_A - min_A) / (max_B - min_B)) + min_A
    dfb[new_col_name] = dfb[norm_col].apply(normalize,
                                            args=(min_B, max_B, min_A, max_A))

# Normalize different columns with different new column names
# A is ref column, B normalized. 
normalize_column(dfb, dfz, 'EffectScore', 'SPIN', 'ZIQspin')
normalize_column(dfb, dfz, 'SpeedScore', 'BALL_SPEED', 'ZIQspeed')
normalize_column(dfb, dfz, 'StyleScore', 'HEAVINESS', 'ZIQheav')
dfz['ZIQ'] = dfz['ZIQspeed'] + dfz['ZIQspin'] + dfz['ZIQheav']
shift = 2 #Estimated by inspection
dfz['HAPPENED_TIME'] = dfz['HAPPENED_TIME'] - pd.Timedelta(seconds=shift) 

normalize_column(dfb, dfu, 'EffectScore', 'ball_spin', 'ZIQspin')
normalize_column(dfb, dfu, 'SpeedScore', 'racket_speed', 'ZIQspeed')
absx = 0 - dfu['impact_position_x'].abs()
absy = 0 - dfu['impact_position_y'].abs()
dfu['abs_imp'] = 0 + (absx + absy)
normalize_column(dfb, dfu, 'StyleScore', 'abs_imp', 'ZIQpos')
#Normalize data based on inspection
dfu.loc[dfu['stroke'] != 'SERVEFH', 'ZIQspin'] = dfu['ZIQspin'] * 2
dfu.loc[dfu['stroke'] != 'SERVEFH', 'ZIQspeed'] = dfu['ZIQspeed'] * 1.6 
dfu['ZIQ'] = dfu['ZIQspeed'] + dfu['ZIQspin'] + dfu['ZIQpos']
dfu.loc[dfu['stroke'] == 'SERVEFH', 'ZIQ'] = dfu['ZIQ'] * .9 
# Remove outliers
dfu = dfu[dfu["ZIQ"] < 10000]

# Set tolerance level - found by repitition
tolerance = pd.Timedelta('7s')

# Fuzzy join for dfu
# Shift (value chosen by inspection)
shift = 2 #Estimated by inspection
dfb['time'] = dfb['time'] - pd.Timedelta(seconds=shift) 

merged_df = pd.merge_asof(dfu, dfb,
                          left_on='time',
                          right_on='time',
                          tolerance=tolerance,
                          direction='nearest')

# merged_df.loc[merged_df['stroke'] == 'SERVEFH'] = df['ZIQ']/2
# fig = px.histogram(merged_df, x="abs_imp", color='hand_type')

# Create the first line plot
fig = px.line(merged_df, x="time",
              y="ZIQ", title="Line Plot of ZIQ and PIQ over Time")
# Add the second line plot
fig.add_trace(
    go.Scatter(x=merged_df["time"],
               y=merged_df["PIQ"], mode="lines", name="PIQ Line")
)

fig.show()

print("completed")
