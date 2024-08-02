# forecast.py
# This file handles forecasting for rce-pln data.
# It includes functions to generate forecasts using SARIMAX models.

import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

# Function to generate forecast for rce-pln data
def rce_pln_forecast(data):
    if not data.empty:
        data['udtczas'] = pd.to_datetime(data['udtczas'])
        data.set_index('udtczas', inplace=True)
        model = SARIMAX(data['rce_pln'], order=(1, 1, 1), seasonal_order=(1, 1, 1, 96))
        model_fit = model.fit(disp=False)
        future_steps = 96
        forecast = model_fit.get_forecast(steps=future_steps)
        forecast_df = forecast.conf_int()
        forecast_df['forecast'] = model_fit.predict(start=forecast_df.index[0], end=forecast_df.index[-1])
        forecast_df.index = pd.date_range(start=data.index[-1], periods=future_steps+1, freq='15min')[1:]
        
        return forecast_df
    else:
        return pd.DataFrame()
