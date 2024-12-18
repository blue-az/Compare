Tennis Sensors Analysis Dashboard
A Streamlit-based dashboard for analyzing and comparing data from Babolat and Zepp U tennis sensors.
Features

Multi-sensor Analysis: Simultaneously analyze data from Babolat and Zepp U tennis sensors
Date Range Selection: Filter data by custom date ranges
Three Analysis Tabs:

Babolat Signals: Visualize Babolat sensor metrics
Zepp U Signals: Visualize Zepp U sensor metrics
Merged Analysis: Cross-compare metrics between sensors


Stroke Filtering: Filter data by specific tennis strokes:

Serve
Backhand Slice
Forehand Slice
Forehand Topspin
Backhand Topspin
Backhand Flat
Forehand Flat


Visualization Options:

Separate or combine stroke types
Color-code by stroke type
Temporal sequence visualization
Interactive plots with hover information



Requirements

Python 3.x
Streamlit
Pandas
Plotly
NumPy
BabWrangle (custom module)
UZeppWrangle (custom module)

Usage

Run the dashboard:

bashCopystreamlit run dashboard.py

Configure in sidebar:

Set paths to Babolat and Zepp U sensor databases
Select date range
Click "Load Data"


Interact with tabs:

Select signals to visualize
Choose stroke types
Toggle visualization options
View summary statistics



Data Processing

Automatically handles time synchronization between sensors
Normalizes data for comparison
Calculates additional metrics (ZIQ scores)
Removes outliers
Merges datasets with configurable time tolerance

Notes

Maximum recommended date range: 30 days
Database paths must be valid and accessible
Requires both sensor databases to function properly
