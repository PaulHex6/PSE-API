# forecast.py
# This file handles forecasting for rce-pln data.
# It includes functions to generate forecasts using different models.

import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import streamlit as st

# Function to generate forecast using SARIMAX model with progress bar
def forecast_sarimax(data, p, d, q, sp, sd, sq, seasonal_period):
    if not data.empty:
        data['udtczas'] = pd.to_datetime(data['udtczas'])
        data.set_index('udtczas', inplace=True)
        progress_bar = st.progress(0)
        progress_bar.progress(10)
        model = SARIMAX(data['rce_pln'], order=(p, d, q), seasonal_order=(sp, sd, sq, seasonal_period))
        model_fit = model.fit()
        progress_bar.progress(80)
        forecast_df = generate_forecast(model_fit, data)
        progress_bar.progress(100)
        return forecast_df
    else:
        return pd.DataFrame()

# Function to generate forecast using ARIMA model with progress bar
def forecast_arima(data, p, d, q):
    if not data.empty:
        data['udtczas'] = pd.to_datetime(data['udtczas'])
        data.set_index('udtczas', inplace=True)
        progress_bar = st.progress(0)
        progress_bar.progress(10)
        model = ARIMA(data['rce_pln'], order=(p, d, q))
        model_fit = model.fit()
        progress_bar.progress(80)
        forecast_df = generate_forecast(model_fit, data)
        progress_bar.progress(100)
        return forecast_df
    else:
        return pd.DataFrame()

# Function to generate forecast using Holt-Winters model with progress bar
def forecast_holt_winters(data, seasonal_period, trend):
    if not data.empty:
        data['udtczas'] = pd.to_datetime(data['udtczas'])
        data.set_index('udtczas', inplace=True)
        progress_bar = st.progress(0)
        progress_bar.progress(10)
        model = ExponentialSmoothing(data['rce_pln'], seasonal_periods=seasonal_period, trend=trend, seasonal='add')
        model_fit = model.fit()
        progress_bar.progress(80)
        future_steps = 96
        forecast_df = pd.DataFrame(index=pd.date_range(start=data.index[-1], periods=future_steps + 1, freq='15min')[1:])
        forecast_df['forecast'] = model_fit.forecast(steps=future_steps)
        progress_bar.progress(100)
        return forecast_df
    else:
        return pd.DataFrame()

# Common function to generate and format forecast results for SARIMAX and ARIMA
def generate_forecast(model_fit, data):
    future_steps = 96  # Assuming forecast for next 24 hours with 15-minute intervals
    forecast = model_fit.get_forecast(steps=future_steps)
    forecast_df = forecast.conf_int()
    forecast_df['forecast'] = model_fit.predict(start=forecast_df.index[0], end=forecast_df.index[-1])
    forecast_df.index = pd.date_range(start=data.index[-1], periods=future_steps + 1, freq='15min')[1:]
    return forecast_df
