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
from code.forecast import forecast_sarimax, forecast_arima, forecast_holt_winters

# Function to create a line chart for rce-pln analysis
def rce_pln_analysis_chart(data):
    summary_stats, hourly_trends = rce_pln_analysis(data)
        
    if summary_stats:
        #st.plotly_chart(px.line(data, x='udtczas', y='rce_pln', title='Market Price of Energy Analysis'), use_container_width=True)

        # Create the plot
        fig = px.line(data, x='udtczas', y='rce_pln', 
                      title='PSE Electricity Market Price Analysis in Poland',
                      labels={'udtczas': 'Time', 'rce_pln': 'PLN/MWh'})
        
        # Add the source annotation
        fig.add_annotation(
            text="Source: Polskie Sieci Energetyczne",
            xref="paper", yref="paper",
            x=1, y=-0.25,  # Position below the plot
            showarrow=False,
            xanchor="right",
            font=dict(size=11)
        )

        # Display the plot with the source annotation
        st.plotly_chart(fig, use_container_width=True)
        
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

# Function to display forecast configuration options in the UI
def display_forecast_options():
    st.subheader("Forecasting Options")
    forecast_method = st.selectbox("Choose Forecast Method", ["SARIMAX", "ARIMA", "Holt-Winters"])
    
    st.subheader("Method Parameters")
    params = {}

    with st.container():
        if forecast_method == "SARIMAX":
            col1, col2, col3 = st.columns(3)
            with col1:
                params['p'] = st.number_input("p (AR term)", min_value=0, max_value=10, value=1)
                st.caption("p: The number of lag observations included in the model.")
            with col2:
                params['d'] = st.number_input("d (Differencing term)", min_value=0, max_value=2, value=1)
                st.caption("d: The number of times that the raw observations are differenced.")
            with col3:
                params['q'] = st.number_input("q (MA term)", min_value=0, max_value=10, value=1)
                st.caption("q: The size of the moving average window.")
            col4, col5, col6 = st.columns(3)
            with col4:
                params['sp'] = st.number_input("Seasonal p", min_value=0, max_value=10, value=1)
                st.caption("Seasonal p: The number of lag observations in the seasonal component.")
            with col5:
                params['sd'] = st.number_input("Seasonal d", min_value=0, max_value=2, value=1)
                st.caption("Seasonal d: The number of times that the seasonal component is differenced.")
            with col6:
                params['sq'] = st.number_input("Seasonal q", min_value=0, max_value=10, value=1)
                st.caption("Seasonal q: The size of the moving average window in the seasonal component.")
            col7 = st.columns(1)
            with col7[0]:
                params['seasonal_period'] = st.number_input("Seasonal Period", min_value=1, max_value=365, value=96)
                st.caption("Seasonal Period: The number of observations per seasonal cycle.")
        elif forecast_method == "ARIMA":
            col1, col2, col3 = st.columns(3)
            with col1:
                params['p'] = st.number_input("p (AR term)", min_value=0, max_value=10, value=5)
                st.caption("p: The number of lag observations included in the model.")
            with col2:
                params['d'] = st.number_input("d (Differencing term)", min_value=0, max_value=2, value=0)
                st.caption("d: The number of times that the raw observations are differenced.")
            with col3:
                params['q'] = st.number_input("q (MA term)", min_value=0, max_value=10, value=5)
                st.caption("q: The size of the moving average window.")
        elif forecast_method == "Holt-Winters":
            col1, col2 = st.columns(2)
            with col1:
                params['seasonal_period'] = st.number_input("Seasonal Period", min_value=1, max_value=365, value=96)
                st.caption("Seasonal Period: The number of observations per seasonal cycle.")
            with col2:
                params['trend'] = st.selectbox("Trend Type", ["add", "mul", "additive", "multiplicative"])
                st.caption("Trend: The type of trend component in the model.")
    
    return forecast_method, params

# Function to display the forecast chart
def display_forecast_chart(data, forecast_df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['rce_pln'], mode='lines', name='Actual', line=dict(color='light blue')))
    fig.add_trace(go.Scatter(x=forecast_df.index, y=forecast_df['forecast'], mode='lines', name='Forecast', line=dict(color='orange', width=2)))
    fig.update_layout(title='Market Price of Energy Forecast',
                      xaxis=dict(title='Time', tickformat="%H:%M", nticks=48, showgrid=True, gridwidth=0.5, gridcolor='DarkGrey'),
                      yaxis=dict(title='Price [PLN/MWh]', showgrid=True, gridwidth=0.5, gridcolor='DarkGrey'))
    st.plotly_chart(fig, use_container_width=True)

# Function to handle the forecast generation logic with progress bar
def handle_forecasting(forecast_method, params, start_date, end_date):
    data = fetch_data("rce-pln", start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    
    with st.spinner('Calculating forecast...'):
        if forecast_method == "SARIMAX":
            forecast_df = forecast_sarimax(data, **params)
        elif forecast_method == "ARIMA":
            forecast_df = forecast_arima(data, **params)
        elif forecast_method == "Holt-Winters":
            forecast_df = forecast_holt_winters(data, **params)
    
    display_forecast_chart(data, forecast_df)
    
def main():
    st.set_page_config(layout="wide")
    st.title("Electricity Prices in Poland")

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
        forecast_method, params = display_forecast_options()
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Select start date", value=pd.to_datetime("2024-07-01"))
        with col2:
            end_date = st.date_input("Select end date", value=pd.to_datetime("2024-07-03"))

        if st.button("Forecast now"):
            handle_forecasting(forecast_method, params, start_date, end_date)


if __name__ == "__main__":
    init_db()
    main()
