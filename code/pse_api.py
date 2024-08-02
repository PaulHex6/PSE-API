# code/pse_api.py
# This file handles API interactions with PSE.
# It includes functions to fetch data from the API with retry logic.

import requests
import chardet
import json
import pandas as pd
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .db import save_data_to_db, fetch_data_from_db

# Function to fetch data from the API for a single day with retry logic and debugging
def fetch_data_for_day(report, date):
    url = f"https://api.raporty.pse.pl/api/{report}"
    params = {
        "$filter": f"business_date eq '{date}'"
    }

    # Set up retry strategy
    retry_strategy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)

    try:
        response = http.get(url, params=params, timeout=15)
        response.raise_for_status()
        data_str = response.content.decode(chardet.detect(response.content)['encoding'])
        data_json = json.loads(data_str)
        if 'value' in data_json:
            df = pd.json_normalize(data_json['value'])
            save_data_to_db(report, date, data_str)
            return df
        else:
            return pd.DataFrame()
    except requests.exceptions.RequestException:
        return pd.DataFrame()

# Function to fetch data from the database or API for a date range
def fetch_data(report, start_date, end_date):
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    all_data = pd.DataFrame()
    current_dt = start_dt

    while current_dt <= end_dt:
        date_str = current_dt.strftime('%Y-%m-%d')
        day_data = fetch_data_from_db(report, date_str)
        if day_data.empty:
            day_data = fetch_data_for_day(report, date_str)
        all_data = pd.concat([all_data, day_data], ignore_index=True)
        current_dt += timedelta(days=1)
    
    return all_data
