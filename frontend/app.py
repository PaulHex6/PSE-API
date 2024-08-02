# frontend/app.py
# This file is responsible for the Streamlit frontend.
# It includes the main application logic and UI components.

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import plotly.express as px
import plotly.graph_objects as go

from code.db import init_db, fetch_data_from_db
from code.pse_api import fetch_data_for_day, fetch_data
from code.analysis import rce_pln_analysis
from code.forecast import rce_pln_forecast

# Function to create a line chart for rce-pln analysis
def rce_pln_analysis_chart(data):
    summary_stats, hourly_trends = rce_pln_analysis(data)
    
    if summary_stats:
        st.plotly_chart(px.line(data, x='udtczas', y='rce_pln', title='Market Price of Energy Analysis'), use_container_width=True)
        st.write("### Summary Statistics")
        st.table(pd.DataFrame(list(summary_stats.items()), columns=["Metric", "Value"]))

        if st.checkbox("Show Hourly Trends Heatmap"):
            heatmap_data = hourly_trends
            heatmap = px.imshow(heatmap_data, labels=dict(x="Hour of Day", y="Weekday", color="Average Price [PLN/MWh]"),
                                x=heatmap_data.columns, y=heatmap_data.index, color_continuous_scale=["green", "orange", "red"])
            st.plotly_chart(heatmap, use_container_width=True)
    else:
        st.warning("No data to display on the chart.")

# Function to create a line chart for rce-pln current with live updates
def rce_pln_current_chart(data):
    if not data.empty:
        poland_tz = pytz.timezone('Europe/Warsaw')
        current_time_poland = datetime.now(poland_tz)
        
        data['udtczas'] = pd.to_datetime(data['udtczas']).dt.tz_localize('UTC').dt.tz_convert(poland_tz)
        start_of_day = datetime(current_time_poland.year, current_time_poland.month, current_time_poland.day, 0, 0, 0, tzinfo=poland_tz)
        end_of_day = start_of_day + timedelta(days=1)

        fig = px.line(data, x='udtczas', y='rce_pln', title='Market Price of Energy Today')
        fig.update_layout(xaxis=dict(title='Time', range=[start_of_day, end_of_day], tickformat="%H:%M", nticks=24, showgrid=True, gridwidth=0.5, gridcolor='DarkGrey'),
                          yaxis=dict(title='Price [PLN/MWh]', showgrid=True, gridwidth=0.5, gridcolor='DarkGrey'))
        st.plotly_chart(fig, use_container_width=True)

        next_update = (current_time_poland + timedelta(minutes=15)).replace(minute=(current_time_poland.minute // 15 + 1) * 15 % 60, second=0, microsecond=0)
        time_remaining = (next_update - current_time_poland).total_seconds()

        st.write(f"Current time in Poland: {current_time_poland.strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"Time remaining for next price update: {int(time_remaining // 60)} minutes {int(time_remaining % 60)} seconds")
    else:
        st.warning("No data to display on the chart.")

# Function to create a line chart for rce-pln forecast
def rce_pln_forecast_chart(report, start_date, end_date):
    start_date_1_day_earlier = (datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')

    progress = st.progress(0)
    status_text = st.empty()

    status_text.text("Please wait... Progress: 0%")
    progress.progress(0)
    
    progress.progress(10)
    status_text.text("Please wait... Progress: 10%")
    data = fetch_data(report, start_date_1_day_earlier, end_date)
    
    if not data.empty:
        progress.progress(30)
        status_text.text("Please wait... Progress: 30%")
        data['udtczas'] = pd.to_datetime(data['udtczas'])
        data.set_index('udtczas', inplace=True)

        progress.progress(50)
        status_text.text("Please wait... Progress: 50%")
        forecast_df = rce_pln_forecast(data)
        
        progress.progress(80)
        status_text.text("Please wait... Progress: 80%")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['rce_pln'], mode='lines', name='Actual', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=forecast_df.index, y=forecast_df['forecast'], mode='lines', name='Forecast', line=dict(color='yellow', width=2)))
        fig.update_layout(title='Market Price of Energy Forecast',
                          xaxis=dict(title='Time', tickformat="%H:%M", nticks=48, showgrid=True, gridwidth=0.5, gridcolor='DarkGrey'),
                          yaxis=dict(title='Price [PLN/MWh]', showgrid=True, gridwidth=0.5, gridcolor='DarkGrey'))
        st.plotly_chart(fig, use_container_width=True)
        
        progress.progress(100)
        status_text.text("Processing complete!")
    else:
        st.warning("No data to display on the chart.")
        progress.progress(100)
        status_text.text("Processing complete!")

def main():
    st.set_page_config(layout="wide")
    st.title("Market Price of Energy")

    with st.sidebar:
        st.title("Available Reports")
        report = st.radio("Select report", ["rce-pln analysis", "rce-pln current", "rce-pln forecast"])

    if report == "rce-pln analysis":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Select start date", value=pd.to_datetime("2024-07-01"), key="start_date")
        with col2:
            end_date = st.date_input("Select end date", value=pd.to_datetime("2024-07-03"), key="end_date")

        if start_date > end_date:
            st.error("Error: End date must fall after start date.")
            return

        data = fetch_data("rce-pln", start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        rce_pln_analysis_chart(data)
    elif report == "rce-pln current":
        poland_tz = pytz.timezone('Europe/Warsaw')
        today = datetime.now(poland_tz).strftime('%Y-%m-%d')
        data = fetch_data_for_day("rce-pln", today)
        rce_pln_current_chart(data)
    elif report == "rce-pln forecast":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Select start date", value=pd.to_datetime("2024-07-01"), key="start_date")
        with col2:
            end_date = st.date_input("Select end date", value=pd.to_datetime("2024-07-03"), key="end_date")

        if start_date > end_date:
            st.error("Error: End date must fall after start date.")
            return

        data = fetch_data("rce-pln", start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        rce_pln_forecast_chart("rce-pln", start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))

if __name__ == "__main__":
    init_db()
    main()
