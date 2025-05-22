#!/usr/bin/env python3
import psycopg2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os
import seaborn as sns
import subprocess
import io

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("Blues_r")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
plt.rcParams['axes.facecolor'] = '#F0F1F6'
plt.rcParams['figure.facecolor'] = 'white'

ALTAIRIAN_DOLLAR = '₳'

DB_NAME = "piscineds"
DB_USER = "jaehwkim"
DB_PASSWORD = "mysecretpassword"
DB_HOST = "localhost"
DB_PORT = "5432"

def get_purchase_data():
    """Fetch 'purchase' event data from customers table"""
    try:
        print("Fetching purchase data from database...")
        
        query_cmd = """
        docker exec -i postgresForDb bash -c "PGPASSWORD=mysecretpassword psql -U jaehwkim -d piscineds -c \\"COPY (
            SELECT event_time, price 
            FROM customers 
            WHERE event_type = 'purchase' AND 
                  event_time BETWEEN '2022-10-01' AND '2023-02-28 23:59:59'
            ORDER BY event_time
        ) TO STDOUT WITH CSV HEADER\\""
        """
        
        result = subprocess.run(query_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error fetching data: {result.stderr}")
            return None
        
        df = pd.read_csv(io.StringIO(result.stdout))
        
        print(f"Retrieved {len(df)} purchase records.")
        
        if df.empty:
            print("No purchase data found.")
            return None
        
        df['event_time'] = pd.to_datetime(df['event_time'])
        df['day'] = df['event_time'].dt.date
        df['month'] = df['event_time'].dt.to_period('M')
        
        monthly_counts = df.groupby(df['month'].dt.strftime('%Y-%m')).size()
        print("\nMonthly data distribution:")
        print(monthly_counts)
        
        print(f"Using {len(df)} purchase records for analysis.")
        return df
    
    except Exception as e:
        print(f"Data query error: {e}")
        return None

def create_daily_price_chart(df):
    """Create daily customer count chart"""
    daily_count = df.groupby('day').size().reset_index(name='count')
    
    plt.figure(figsize=(10, 6))
    plt.plot(daily_count['day'], daily_count['count'], color='#4169E1', linewidth=1.5)
    
    plt.title('Daily Number of Customers (October 2022 - February 2023)', fontsize=14, pad=15)
    plt.xlabel('', fontsize=12)
    plt.ylabel('Number of customers', fontsize=12)
    
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    
    plt.ylim(bottom=0)
    
    plt.grid(True, linestyle='-', alpha=0.5)
    
    plt.tight_layout()
    
    plt.savefig('chart_1_daily_customers.png', dpi=300, bbox_inches='tight')
    print("Chart 1: Daily customer count chart created.")

def create_monthly_bar_chart(df):
    """Create monthly purchase amount bar chart"""
    monthly_sum = df.groupby('month')['price'].sum().reset_index()
    monthly_sum['price_millions'] = monthly_sum['price'] / 1000000
    monthly_sum['month_str'] = monthly_sum['month'].dt.strftime('%b')
    
    print("\nMonthly purchase amounts (in millions):")
    print(monthly_sum[['month_str', 'price_millions']])
    
    plt.figure(figsize=(10, 6))
    
    bars = plt.bar(monthly_sum['month_str'], monthly_sum['price_millions'], 
                  color='#A4C2F4', width=0.6, edgecolor='none')
    
    plt.title('Monthly Purchase Amount (October 2022 - February 2023)', fontsize=14, pad=15)
    plt.xlabel('month', fontsize=12)
    plt.ylabel(f'total sales in million of {ALTAIRIAN_DOLLAR}', fontsize=12)
    
    plt.ylim(0, 1.4)
    
    plt.grid(axis='y', linestyle='-', alpha=0.3)
    plt.gca().set_axisbelow(True)
    
    plt.tight_layout()
    
    plt.savefig('chart_2_monthly_amount.png', dpi=300, bbox_inches='tight')
    print("Chart 2: Monthly purchase amount chart created.")

def create_purchase_ratio_chart(df):
    """Create daily average spend chart"""
    daily_avg = df.groupby('day').agg(
        avg_spend=('price', 'mean')
    ).reset_index()
    
    daily_avg = daily_avg.sort_values('day')
    
    daily_avg['month'] = pd.to_datetime(daily_avg['day']).dt.strftime('%b')
    
    plt.figure(figsize=(10, 6))
    
    plt.fill_between(daily_avg.index, daily_avg['avg_spend'], 
                     color='#A4C2F4', alpha=0.7)
    
    plt.title('Daily Average Spend (October 2022 - February 2023)', fontsize=14, pad=15)
    plt.xlabel('', fontsize=12)
    plt.ylabel(f'average spend/customers in {ALTAIRIAN_DOLLAR}', fontsize=12)
    
    month_positions = []
    month_labels = []
    current_month = None
    
    for i, (idx, row) in enumerate(daily_avg.iterrows()):
        if row['month'] != current_month:
            current_month = row['month']
            month_positions.append(i)
            month_labels.append(current_month)
    
    plt.xticks(month_positions, month_labels)
    
    plt.ylim(0, 8)
    
    plt.grid(True, linestyle='-', alpha=0.3)
    
    plt.tight_layout()
    
    plt.savefig('chart_3_average_spend.png', dpi=300, bbox_inches='tight')
    print("Chart 3: Daily average spend chart created.")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("Starting purchase data analysis...")
    
    purchase_data = get_purchase_data()
    
    if purchase_data is not None:
        create_daily_price_chart(purchase_data)
        create_monthly_bar_chart(purchase_data)
        create_purchase_ratio_chart(purchase_data)
        
        print("All charts have been successfully created.")
    else:
        print("Failed to load data for analysis.")
