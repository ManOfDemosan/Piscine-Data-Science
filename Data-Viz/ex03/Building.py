#!/usr/bin/env python3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import subprocess
import io
import os

# Set up the plot style to match the images
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("pastel")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3

DB_NAME = "piscineds"
DB_USER = "jaehwkim"
DB_PASSWORD = "mysecretpassword"

ALTAIRIAN_DOLLAR = '₳'

def get_purchase_data():
    """Fetch purchase event data from customers table."""
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

def create_frequency_chart(df):
    """Create bar chart showing the number of orders according to frequency."""
    if df is None or df.empty:
        print("No data available to create charts.")
        return
    
    # Count orders per user
    order_counts = df.groupby('user_id').size().reset_index(name='frequency')
    
    # Create frequency distribution with specific bins like in the image
    freq_bins = [0, 10, 20, 30, 40]
    freq_counts = np.histogram(order_counts['frequency'], bins=freq_bins)[0]
    freq_positions = [0, 10, 20, 30]  # x-positions
    
    # Create the figure with exact dimensions to match the image
    plt.figure(figsize=(6.4, 4.8))
    
    # Plot bars with blue color matching the image
    bars = plt.bar(freq_positions, freq_counts, color='#B3C7E6', width=6)
    
    # Set axis labels and limits
    plt.xlabel('frequency')
    plt.ylabel('customers')
    plt.xlim(-5, 35)
    plt.ylim(0, 70000)
    
    # Set x-ticks
    plt.xticks(freq_positions)
    
    # Format y-axis without scientific notation
    plt.ticklabel_format(style='plain', axis='y')
    
    # Save figure
    plt.tight_layout()
    plt.savefig('Frequency.png', dpi=300, bbox_inches='tight')
    print("Bar chart for order frequency saved as 'Building_1.png'")
    
    plt.close()

def create_spending_chart(df):
    """Create bar chart showing Altairian Dollars spent by customers."""
    if df is None or df.empty:
        return
    
    # Calculate total spending per user
    user_spending = df.groupby('user_id')['price'].sum().reset_index(name='total_spent')
    
    # Create spending distribution with specific bins like in the image
    spend_bins = [0, 50, 100, 150, 200, 250]
    spend_counts = np.histogram(user_spending['total_spent'], bins=spend_bins)[0]
    spend_positions = [0, 50, 100, 150, 200]  # x-positions
    
    # Create the figure with exact dimensions to match the image
    plt.figure(figsize=(6.4, 4.8))
    
    # Plot bars with light blue color
    bars = plt.bar(spend_positions, spend_counts, color='#B3C7E6', width=30)
    
    # Set axis labels and limits
    plt.xlabel(f'monetary value in {ALTAIRIAN_DOLLAR}')
    plt.ylabel('customers')
    plt.xlim(-25, 225)
    plt.ylim(0, 45000)
    
    # Set x-ticks
    plt.xticks(spend_positions)
    
    # Format y-axis without scientific notation
    plt.ticklabel_format(style='plain', axis='y')
    
    # Save figure
    plt.tight_layout()
    plt.savefig('Spending.png', dpi=300, bbox_inches='tight')
    print("Bar chart for spending distribution saved as 'Building_2.png'")
    
    plt.close()

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    purchase_data = get_purchase_data()
    
    if purchase_data is not None:
        create_frequency_chart(purchase_data)
        create_spending_chart(purchase_data)
        print("\nAll charts created successfully.")
    else:
        print("\nFailed to process data.")

if __name__ == "__main__":
    main() 