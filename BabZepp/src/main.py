import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import BabWrangle
import UZeppWrangle
from icecream import ic

st.set_page_config(layout="wide")
pd.set_option("display.max_columns", None)
# Data loading and processing function
@st.cache_data
def load_and_process_data(bab_path, uzepp_path, start_date, end_date):
    try:
        # Convert all inputs to datetime64[ns] format
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        elif isinstance(start_date, datetime):
            start_date = pd.to_datetime(start_date)
        else:  # Assuming it's a date object
            start_date = pd.to_datetime(start_date)

        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)
        elif isinstance(end_date, datetime):
            end_date = pd.to_datetime(end_date)
        else:  # Assuming it's a date object
            end_date = pd.to_datetime(end_date)
            
        # Validate dates
        if start_date > end_date:
            raise ValueError("Start date must be before end date")
        
        # Optional: Add maximum date range validation
        if (end_date - start_date).total_seconds() / (24 * 3600) > 30:
            st.warning("Processing a large date range. This might take longer.")
            
        # Convert to string format for the API calls
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        # Load data
        dfb = BabWrangle.BabWrangle(bab_path, start_date, end_date)
        dfu = UZeppWrangle.UZeppWrangle(uzepp_path, start_date, end_date)
        
        # Check if DataFrames are empty
        if dfb.empty:
            raise ValueError("No Babolat data available for the selected date range")
        if dfu.empty:
            raise ValueError("No Zepp data available for the selected date range")
        
        def normalize_column(dfa, dfb, ref_col, norm_col, new_col_name):
            min_A = dfa[ref_col].min()
            max_A = dfa[ref_col].max()
            min_B = dfb[norm_col].min()
            max_B = dfb[norm_col].max()
            
            # Check for division by zero
            if max_B == min_B:
                dfb[new_col_name] = 0
            else:
                def normalize(x, min_B, max_B, min_A, max_A):
                    return ((x - min_B) * (max_A - min_A) / (max_B - min_B)) + min_A
                dfb[new_col_name] = dfb[norm_col].apply(normalize, args=(min_B, max_B, min_A, max_A))

        # Add ZIQ calculations
        normalize_column(dfb, dfu, 'EffectScore', 'ball_spin', 'ZIQspin')
        normalize_column(dfb, dfu, 'SpeedScore', 'racket_speed', 'ZIQspeed')
        
        # Calculate impact position scores
        absx = 0 - dfu['impact_position_x'].abs()
        absy = 0 - dfu['impact_position_y'].abs()
        dfu['abs_imp'] = 0 + (absx + absy)
        normalize_column(dfb, dfu, 'StyleScore', 'abs_imp', 'ZIQpos')
        
        # Normalize data
        dfu.loc[dfu['stroke'] != 'SERVEFH', 'ZIQspin'] = dfu['ZIQspin'] * 2
        dfu.loc[dfu['stroke'] != 'SERVEFH', 'ZIQspeed'] = dfu['ZIQspeed'] * 1.6
        dfu['ZIQ'] = dfu['ZIQspeed'] + dfu['ZIQspin'] + dfu['ZIQpos']
        dfu.loc[dfu['stroke'] == 'SERVEFH', 'ZIQ'] = dfu['ZIQ'] * 0.9
        
        # Remove outliers
        dfu = dfu[dfu["dbg_acc_1"] < 10000]
        dfu = dfu[dfu["dbg_acc_3"] < 10000]
        dfu = dfu[dfu["ZIQ"] < 10000]
        
        # Ensure time columns are properly sorted
        dfu = dfu.sort_values('time')
        dfb = dfb.sort_values('time')
        
        # Updated Zepp U sensor fields
        zepp_sensor = [col for col in dfu.columns if col not in ['time', 'stroke']]
        
        # Updated Babolat sensor fields - include all numeric columns
        bab_sensor = [col for col in dfb.columns if col not in ['time', 'stroke'] and 
                     pd.api.types.is_numeric_dtype(dfb[col])]
        
        # Updated calculated fields
        calc = ['backswing_time', 'power', 'ball_spin', 'impact_position_x',
                'impact_position_y', 'racket_speed', 'impact_region', 'ZIQ',
                'ZIQspin', 'ZIQspeed', 'ZIQpos']
        
        # Merge datasets
        dfb['time'] = dfb['time'] - pd.Timedelta(seconds=5)
        
        # Handle stroke columns before merge
        if 'stroke' in dfu.columns:
            dfu = dfu.rename(columns={'stroke': 'stroke_zepp'})
        if 'stroke' in dfb.columns:
            dfb = dfb.rename(columns={'stroke': 'stroke_bab'})
        
        # Perform merge
        dfu_dfb_merge = pd.merge_asof(dfu, dfb,
                                   left_on='time',
                                   right_on='time',
                                   tolerance=pd.Timedelta('5s'),
                                   direction='nearest')
        
        # Handle stroke column in merged dataset
        if 'stroke_zepp' in dfu_dfb_merge.columns and 'stroke_bab' in dfu_dfb_merge.columns:
            dfu_dfb_merge['stroke'] = dfu_dfb_merge['stroke_zepp'].fillna(dfu_dfb_merge['stroke_bab'])
            dfu_dfb_merge = dfu_dfb_merge.drop(['stroke_zepp', 'stroke_bab'], axis=1)
        elif 'stroke_zepp' in dfu_dfb_merge.columns:
            dfu_dfb_merge = dfu_dfb_merge.rename(columns={'stroke_zepp': 'stroke'})
        elif 'stroke_bab' in dfu_dfb_merge.columns:
            dfu_dfb_merge = dfu_dfb_merge.rename(columns={'stroke_bab': 'stroke'})
        
        # Verify which columns actually exist in the merged DataFrame
        zepp_sensor = [col for col in zepp_sensor if col in dfu_dfb_merge.columns]
        bab_sensor = [col for col in bab_sensor if col in dfu_dfb_merge.columns]
        calc = [col for col in calc if col in dfu_dfb_merge.columns]
        
        return dfu_dfb_merge, zepp_sensor, bab_sensor, calc
        
    except Exception as e:
        raise Exception(f"Error processing data: {str(e)}")

def create_stroke_selection(tab_prefix):
    """
    Create a unified stroke selection interface
    
    Parameters:
    tab_prefix (str): Prefix for the checkbox keys to avoid duplicates across tabs
    """
    all_strokes = {
        'SERVEFH': 'Serve',
        'SLICEBH': 'Backhand Slice',
        'SLICEFH': 'Forehand Slice',
        'TOPSPINFH': 'Forehand Topspin',
        'TOPSPINBH': 'Backhand Topspin',
        'FLATBH': 'Backhand Flat',
        'FLATFH': 'Forehand Flat'
    }
    
    selected_strokes = []
    cols = st.columns(4)  # Adjust number of columns as needed
    for i, (stroke_key, stroke_name) in enumerate(all_strokes.items()):
        if cols[i % 4].checkbox(stroke_name, value=True, key=f"{tab_prefix}_stroke_{stroke_key}"):
            selected_strokes.append(stroke_key)
    
    return selected_strokes

def create_scatter_plot(df, signals, separate_strokes, color_by_stroke, selected_strokes, title):
    """
    Create a scatter plot for signal visualization with consistent stroke separation
    and connected lines
    """
    fig = go.Figure()
    
    # Sort DataFrame by time to ensure proper line connections
    df = df.sort_values('time')
    
    # Define shapes and colors for different strokes
    shape_map = {
        'SERVEFH': 'star',
        'SLICEBH': 'diamond',
        'SLICEFH': 'diamond-open',
        'TOPSPINFH': 'pentagon',
        'TOPSPINBH': 'pentagon-open',
        'FLATBH': 'square',
        'FLATFH': 'square-open'
    }
    
    colors = {
        'SERVEFH': '#FF1F5B',    # bright red
        'SLICEBH': '#009ADE',    # bright blue
        'SLICEFH': '#F28522',    # orange
        'TOPSPINFH': '#85D4E3',  # light blue
        'TOPSPINBH': '#B4DC7F',  # light green
        'FLATBH': '#9B7EDE',     # purple
        'FLATFH': '#EFB435'      # yellow
    }
    
    if separate_strokes:
        # Original behavior: separate lines for each stroke
        for stroke in selected_strokes:
            stroke_df = df[df['stroke'] == stroke].copy()
            
            for signal in signals:
                trace_name = f"{signal} - {stroke}"
                
                fig.add_trace(
                    go.Scatter(
                        x=stroke_df['time'],
                        y=stroke_df[signal],
                        name=trace_name,
                        mode='lines+markers',
                        marker=dict(
                            symbol=shape_map.get(stroke, 'circle'),
                            size=8,
                            color=colors.get(stroke, '#000000'),
                            line=dict(width=1, color='white')
                        ),
                        line=dict(
                            color=colors.get(stroke, '#000000'),
                            width=2
                        ),
                        connectgaps=False
                    )
                )
    else:
        # Combined lines with optional color by stroke
        for signal in signals:
            if color_by_stroke:
                # One line but colored points by stroke
                for stroke in selected_strokes:
                    stroke_df = df[df['stroke'] == stroke].copy()
                    
                    fig.add_trace(
                        go.Scatter(
                            x=stroke_df['time'],
                            y=stroke_df[signal],
                            name=f"{signal} - {stroke}",
                            mode='markers',
                            marker=dict(
                                symbol=shape_map.get(stroke, 'circle'),
                                size=8,
                                color=colors.get(stroke, '#000000'),
                                line=dict(width=1, color='white')
                            ),
                            showlegend=True
                        )
                    )
                
                # Add a single connecting line
                fig.add_trace(
                    go.Scatter(
                        x=df['time'],
                        y=df[signal],
                        name=signal,
                        mode='lines',
                        line=dict(
                            color='gray',
                            width=1,
                            dash='dot'
                        ),
                        showlegend=False
                    )
                )
            else:
                # Single color line with markers
                fig.add_trace(
                    go.Scatter(
                        x=df['time'],
                        y=df[signal],
                        name=signal,
                        mode='lines+markers',
                        marker=dict(
                            symbol='circle',
                            size=8,
                            color=list(colors.values())[0],
                            line=dict(width=1, color='white')
                        ),
                        line=dict(
                            color=list(colors.values())[0],
                            width=2
                        ),
                        connectgaps=False
                    )
                )
    
    fig.update_layout(
        title=title,
        xaxis_title="Time",
        yaxis_title="Value",
        showlegend=True,
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            type='date'
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray'
        ),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.02
        )
    )
    
    return fig

def create_correlation_plot(df, x_signal, y_signal, separate_strokes):
    """
    Create a correlation scatter plot that maintains temporal sequence
    while distinguishing strokes by color/shape
    """
    fig = go.Figure()
    
    # Sort DataFrame by time for proper temporal sequence
    df = df.sort_values('time')
    
    # Define shapes and colors for different strokes
    shape_map = {
        'SERVEFH': 'star',
        'SLICEBH': 'diamond',
        'SLICEFH': 'diamond-open',
        'TOPSPINFH': 'pentagon',
        'TOPSPINBH': 'pentagon-open',
        'FLATBH': 'square',
        'FLATFH': 'square-open'
    }
    
    colors = {
        'SERVEFH': '#FF1F5B',    # bright red
        'SLICEBH': '#009ADE',    # bright blue
        'SLICEFH': '#F28522',    # orange
        'TOPSPINFH': '#85D4E3',  # light blue
        'TOPSPINBH': '#B4DC7F',  # light green
        'FLATBH': '#9B7EDE',     # purple
        'FLATFH': '#EFB435'      # yellow
    }
    
    if separate_strokes:
        # Create a single trace for the connecting line (temporal sequence)
        fig.add_trace(
            go.Scatter(
                x=df[x_signal],
                y=df[y_signal],
                mode='lines',
                line=dict(
                    color='lightgray',
                    width=1,
                    dash='dot'
                ),
                name='Temporal Sequence',
                hoverinfo='skip'
            )
        )
        
        # Add scatter points for each stroke type
        for stroke in df['stroke'].unique():
            stroke_df = df[df['stroke'] == stroke].copy()
            
            fig.add_trace(
                go.Scatter(
                    x=stroke_df[x_signal],
                    y=stroke_df[y_signal],
                    name=stroke,
                    mode='markers',
                    marker=dict(
                        symbol=shape_map.get(stroke, 'circle'),
                        size=10,
                        color=colors.get(stroke, '#000000'),
                        line=dict(width=1, color='white')
                    ),
                    customdata=stroke_df[['time', 'stroke']].values,
                    hovertemplate=(
                        f"{x_signal}: %{{x}}<br>" +
                        f"{y_signal}: %{{y}}<br>" +
                        "Time: %{customdata[0]}<br>" +
                        "Stroke: %{customdata[1]}<br>" +
                        "<extra></extra>"
                    )
                )
            )
    else:
        fig.add_trace(
            go.Scatter(
                x=df[x_signal],
                y=df[y_signal],
                mode='lines+markers',
                marker=dict(
                    size=10,
                    color=list(colors.values())[0],
                    line=dict(width=1, color='white')
                ),
                line=dict(
                    color=list(colors.values())[0],
                    width=2
                ),
                name='All strokes',
                customdata=df[['time', 'stroke']].values,
                hovertemplate=(
                    f"{x_signal}: %{{x}}<br>" +
                    f"{y_signal}: %{{y}}<br>" +
                    "Time: %{customdata[0]}<br>" +
                    "Stroke: %{customdata[1]}<br>" +
                    "<extra></extra>"
                )
            )
        )
    
    fig.update_layout(
        title=f"{y_signal} vs {x_signal}",
        xaxis_title=x_signal,
        yaxis_title=y_signal,
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray'
        ),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.02
        )
    )
    
    return fig

# Main dashboard
st.title("Tennis Sensors Data Analysis Dashboard")

# Sidebar controls
st.sidebar.header("Data Loading")
bab_path = st.sidebar.text_input("Babolat Sensor Path", "/home/blueaz/Python/Sensors/Bab/BabWrangle/src/BabPopExt.db")
uzepp_path = st.sidebar.text_input("Zepp U Sensor Path", "/home/blueaz/Downloads/SensorDownload/Compare/ztennis2.db")

start_date = st.sidebar.date_input("Start Date", datetime(2024, 6, 12))
end_date = st.sidebar.date_input("End Date", datetime(2024, 6, 14))

# Add date validation before the load button
if start_date > end_date:
    st.sidebar.error("⚠️ Start date must be before end date")
elif (end_date - start_date).days > 30:  # Optional: Add a maximum date range
    st.sidebar.warning("⚠️ Date range exceeds 30 days. This might take longer to process.")

# Only show the load button if dates are valid
if start_date <= end_date:
    if st.sidebar.button("Load Data"):
        try:
            df, zepp_sensor_cols, bab_sensor_cols, calc_cols = load_and_process_data(
                bab_path, uzepp_path, 
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            # Store the data in session state
            st.session_state['df'] = df
            st.session_state['zepp_sensor_cols'] = zepp_sensor_cols
            st.session_state['bab_sensor_cols'] = bab_sensor_cols
            st.session_state['calc_cols'] = calc_cols
            st.success("Data loaded successfully!")
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            st.info("Try selecting a different date range or check if the data files exist")

if 'df' in st.session_state:
    df = st.session_state['df']
    zepp_sensor_cols = st.session_state['zepp_sensor_cols']
    bab_sensor_cols = st.session_state['bab_sensor_cols']
    calc_cols = st.session_state['calc_cols']
    
    # Create tabs for different visualizations
    tab1, tab2, tab3 = st.tabs(["Babolat Signals", "Zepp U Signals", "Merged Analysis"])
    
    with tab1:
        st.header("Babolat Sensor Signals")
        
        # Visualization controls
        col1, col2 = st.columns(2)
        with col1:
            separate_strokes_bab = st.checkbox("Separate by stroke type", key="bab_separate", value=False)
        with col2:
            color_by_stroke_bab = st.checkbox("Color by stroke type", key="bab_color", value=True, disabled=separate_strokes_bab)
        
        # Stroke selection
        st.subheader("Select Strokes to Display")
        selected_strokes_bab = create_stroke_selection("bab")

        available_bab_cols = [col for col in bab_sensor_cols if col != 'time']
        if available_bab_cols:
            selected_bab_signals = st.multiselect(
                "Select Babolat Signals",
                available_bab_cols,
                default=[available_bab_cols[0]] if available_bab_cols else None
            )
            
            if selected_bab_signals:
                fig_bab = create_scatter_plot(
                    df, 
                    selected_bab_signals, 
                    separate_strokes_bab,
                    color_by_stroke_bab,
                    selected_strokes_bab,
                    "Babolat Signals"
                )
                st.plotly_chart(fig_bab, use_container_width=True)              
                # Summary stats for Babolat signals
                st.header("Babolat Summary Statistics")
                bab_stats = df[available_bab_cols].describe()
                st.dataframe(bab_stats)
            else:
                st.warning("No Babolat signals available in the data")
        
    with tab2:
        st.header("Zepp U Sensor Signals")
        
        # Visualization controls
        col1, col2 = st.columns(2)
        with col1:
            separate_strokes_zepp = st.checkbox("Separate by stroke type", key="zepp_separate", value=False)
        with col2:
            color_by_stroke_zepp = st.checkbox("Color by stroke type", key="zepp_color", value=True, disabled=separate_strokes_zepp)
        
        # Stroke selection
        st.subheader("Select Strokes to Display")
        selected_strokes_zepp = create_stroke_selection("zepp")
        
        available_zepp_cols = [col for col in zepp_sensor_cols if col != 'time']
        if available_zepp_cols:
            selected_zepp_signals = st.multiselect(
                "Select Zepp U Signals",
                available_zepp_cols,
                default=[available_zepp_cols[0]] if available_zepp_cols else None
            )
            
            if selected_zepp_signals:
                fig_zepp = create_scatter_plot(
                    df, 
                    selected_zepp_signals,
                    separate_strokes_zepp,
                    color_by_stroke_zepp,
                    selected_strokes_zepp,
                    "Zepp U Signals"
                )
                st.plotly_chart(fig_zepp, use_container_width=True)
            
            # Summary stats for Zepp U signals
            st.header("Zepp U Summary Statistics")
            zepp_stats = df[available_zepp_cols].describe()
            st.dataframe(zepp_stats)
        else:
            st.warning("No Zepp U signals available in the data")
    
 # Then update the tab3 section to only pass the required arguments:
# [Previous code remains the same until tab3 section]

    with tab3:
        st.header("Merged Sensors Analysis")
        
        # Visualization controls
        separate_strokes_merged = st.checkbox("Separate by stroke type", key="merged_separate", value=False)
        
        # Add stroke selection for tab3
        st.subheader("Select Strokes to Display")
        selected_strokes_merged = create_stroke_selection("merged")
        
        all_metrics = (
            [col for col in zepp_sensor_cols if col != 'time'] +
            [col for col in bab_sensor_cols if col != 'time'] +
            calc_cols
        )
        
        if all_metrics:
            col1, col2 = st.columns(2)
            with col1:
                x_signals = st.multiselect(
                    "X-axis Metrics",
                    all_metrics,
                    default=[all_metrics[0]] if all_metrics else None,
                    key='merged_x'
                )
            with col2:
                y_signals = st.multiselect(
                    "Y-axis Metrics",
                    all_metrics,
                    default=[all_metrics[1]] if len(all_metrics) > 1 else None,
                    key='merged_y'
                )
            
            if x_signals and y_signals:
                # Filter DataFrame based on selected strokes
                df_filtered = df[df['stroke'].isin(selected_strokes_merged)]
                
                if df_filtered.empty:
                    st.warning("No data available for the selected strokes")
                else:
                    for x_signal in x_signals:
                        for y_signal in y_signals:
                            fig_merged = create_correlation_plot(
                                df_filtered,  # Use filtered DataFrame
                                x_signal,
                                y_signal,
                                separate_strokes_merged
                            )
                            st.plotly_chart(fig_merged, use_container_width=True)           
            
            # Summary statistics for calculated fields
            if calc_cols:
                st.header("Calculated Metrics Summary Statistics")
                # Update summary stats to use filtered DataFrame
                summary_stats = df_filtered[calc_cols].describe()
                st.dataframe(summary_stats)
        else:
            st.warning("No metrics available for analysis")
else:
    st.info("Please load the data using the sidebar controls.")
