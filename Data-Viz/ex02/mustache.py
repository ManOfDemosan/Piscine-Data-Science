#!/usr/bin/env python3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import subprocess
import io
import os

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("pastel") 
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
plt.rcParams['figure.facecolor'] = 'white'

DB_NAME = "piscineds"
DB_USER = "jaehwkim"
DB_PASSWORD = "mysecretpassword"

def get_purchase_data():
    """Fetch 'purchase' event data from customers table."""
    try:
        print("Fetching purchase data from database...")
        
        query_cmd = """
        docker exec -i postgresForDb bash -c "PGPASSWORD=mysecretpassword psql -U jaehwkim -d piscineds -c \\"COPY (
            SELECT user_id, event_time, price 
            FROM customers 
            WHERE event_type = 'purchase' AND 
                  event_time BETWEEN '2022-10-01' AND '2023-02-28 23:59:59'
        ) TO STDOUT WITH CSV HEADER\\""
        """
        
        result = subprocess.run(query_cmd, shell=True, capture_output=True, text=True, check=True)
        
        df = pd.read_csv(io.StringIO(result.stdout))
        
        print(f"Retrieved {len(df)} purchase records.")
        
        if df.empty:
            print("No purchase data found.")
            return None
        
        df['event_time'] = pd.to_datetime(df['event_time'])
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df.dropna(subset=['price'], inplace=True) 
        
        return df
    
    except subprocess.CalledProcessError as e:
        print(f"Error fetching data: {e.stderr}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def print_price_statistics(df):
    """Print mean, median, min, max, and quartiles for item prices."""
    if df is None or df.empty:
        print("No data available to calculate statistics.")
        return
        
    print("\nPrice Statistics for Purchased Items:")
    desc = df['price'].describe(percentiles=[.25, .5, .75])
    print(f"Mean: {desc['mean']:.6f}")
    print(f"Median (50%): {desc['50%']:.6f}")
    print(f"Min: {desc['min']:.6f}")
    print(f"Max: {desc['max']:.6f}")
    print(f"1st Quartile (25%): {desc['25%']:.6f}")
    print(f"2nd Quartile (50%): {desc['50%']:.6f}") 
    print(f"3rd Quartile (75%): {desc['75%']:.6f}")
    
    print("\n--- Expected Output Format ---")
    print(f"count {desc['count']:10.6f}")
    print(f"mean  {desc['mean']:10.6f}")
    print(f"std   {desc['std']:10.6f}")
    print(f"min   {desc['min']:10.6f}")
    print(f"25%   {desc['25%']:10.6f}")
    print(f"50%   {desc['50%']:10.6f}")
    print(f"75%   {desc['75%']:10.6f}")
    print(f"max   {desc['max']:10.6f}")
    print("----------------------------")


def create_box_plots(df):
    """Create and save box plots for item prices and average basket price."""
    if df is None or df.empty:
        print("No data available to create box plots.")
        return

    # Box Plot 1: All item prices
    plt.figure(figsize=(8, 4)) 
    sns.boxplot(x=df['price'], color="#BDC3C7") 
    plt.title('Distribution of Item Prices') 
    plt.xlabel('Price') 
    plt.savefig('boxplot_all_prices.png', dpi=300)
    print("\nBox plot for all item prices saved as 'boxplot_all_prices.png'")
    plt.close()

    # Box Plot 2: Zoomed-in item prices
    plt.figure(figsize=(8, 4))
    sns.boxplot(x=df['price'], color="#A9DFBF") 
    plt.title('Distribution of Item Prices (Zoomed In)')
    plt.xlabel('Price') 
    plt.xlim(-1, 13) 
    plt.savefig('boxplot_zoomed_prices.png', dpi=300)
    print("Box plot for zoomed-in item prices saved as 'boxplot_zoomed_prices.png'")
    plt.close()
    
    # Box Plot 3: Average basket price per user
    if 'user_id' in df.columns:
        average_basket_price = df.groupby('user_id')['price'].mean().reset_index()
        
        plt.figure(figsize=(8, 4))
        sns.boxplot(x=average_basket_price['price'], color="#AED6F1", fliersize=5, 
                    flierprops=dict(marker='D', markerfacecolor='gray')) 
        plt.title('Average Basket Price per User') 
        plt.xlabel('Average Basket Price') 
        
        plt.xlim(0, 42)

        plt.savefig('boxplot_average_basket_price.png', dpi=300)
        print("Box plot for average purchase price per user saved as 'boxplot_average_basket_price.png'")
        plt.close()
    else:
        print("Column 'user_id' not found, cannot create average basket price plot.")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    purchase_data = get_purchase_data()
    
    if purchase_data is not None:
        print_price_statistics(purchase_data)
        create_box_plots(purchase_data)
        print("\nAll tasks completed.")
    else:
        print("\nFailed to process data.") 