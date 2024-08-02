# analysis.py
# This file handles data analysis for rce-pln reports.
# It includes functions to perform data analysis and return summary statistics and trends.

import pandas as pd

# Function to perform analysis on rce-pln data
def rce_pln_analysis(data):
    if not data.empty:
        data['udtczas'] = pd.to_datetime(data['udtczas'])

        # Additional analysis
        min_price = data['rce_pln'].min()
        max_price = data['rce_pln'].max()
        avg_price = data['rce_pln'].mean()
        min_price_time = data.loc[data['rce_pln'].idxmin()]['udtczas']
        max_price_time = data.loc[data['rce_pln'].idxmax()]['udtczas']
        cumulative_sum = data['rce_pln'].sum()

        data['weekday'] = data['udtczas'].dt.weekday
        weekday_avg = data[data['weekday'] < 5]['rce_pln'].mean()
        weekend_avg = data[data['weekday'] >= 5]['rce_pln'].mean()

        summary_stats = {
            "Minimum Price": f"{min_price:.2f} PLN/MWh at {min_price_time}",
            "Maximum Price": f"{max_price:.2f} PLN/MWh at {max_price_time}",
            "Average Price": f"{avg_price:.2f} PLN/MWh",
            "Cumulative Sum": f"{cumulative_sum:,.2f} PLN",
            "Weekday Average Price": f"{weekday_avg:.2f} PLN/MWh",
            "Weekend Average Price": f"{weekend_avg:.2f} PLN/MWh"
        }

        hourly_trends = data.groupby([data['udtczas'].dt.day_name(), data['udtczas'].dt.hour])['rce_pln'].mean().unstack()
        return summary_stats, hourly_trends
    else:
        return None, None
