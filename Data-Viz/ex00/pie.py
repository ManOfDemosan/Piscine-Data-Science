#!/usr/bin/env python3
import psycopg2
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Database connection parameters
DB_NAME = "piscineds"
DB_USER = "jaehwkim"
DB_PASSWORD = "mysecretpassword"
DB_HOST = "localhost"
DB_PORT = "5432"

def connect_to_db():
    """Connect to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        print("Database connection successful")
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def get_event_type_distribution():
    """Get distribution of event types from customers table."""
    conn = connect_to_db()
    if not conn:
        return None

    try:
        # Create a cursor
        cursor = conn.cursor()
        
        # Execute SQL query to count event types
        cursor.execute("""
            SELECT event_type, COUNT(*) as count
            FROM customers
            GROUP BY event_type
            ORDER BY count DESC
        """)
        
        # Fetch all results
        results = cursor.fetchall()
        
        # Close connection
        cursor.close()
        conn.close()
        
        return results
    except Exception as e:
        print(f"Error querying database: {e}")
        if conn:
            conn.close()
        return None

def create_pie_chart(data):
    """Create a pie chart from the event type distribution data."""
    if not data:
        print("No data to visualize")
        return
    
    # Extract event types and counts
    event_types = [row[0] for row in data]
    counts = [row[1] for row in data]
    
    # Calculate percentages
    total = sum(counts)
    percentages = [count/total*100 for count in counts]
    
    # Set colors
    colors = ['#7eb6d9', '#5eb57e', '#f8c471', '#9b59b6']
    
    # Create figure with white background
    fig, ax = plt.subplots(figsize=(10, 8), facecolor='white')
    
    # Create pie chart with labels on the pie
    wedges, texts = ax.pie(
        counts,
        labels=event_types,
        colors=colors,
        startangle=90,
        wedgeprops={'edgecolor': 'white', 'linewidth': 1},
        textprops={'fontsize': 12, 'color': 'black', 'weight': 'bold'},
        labeldistance=0.65  # Position labels closer to center
    )
    
    # Add percentage labels on pie
    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        x = 0.5 * np.cos(np.deg2rad(ang))
        y = 0.5 * np.sin(np.deg2rad(ang))
        ax.text(x, y, f"{percentages[i]:.1f}%", 
                ha='center', va='center', fontsize=12, 
                color='white', weight='bold')
    
    # Add title
    plt.title('Distribution of User Activity Types on the Site', fontsize=18, pad=20)
    
    # Create a separate legend
    legend_labels = [f"{event_type}\n{percentage:.1f}%" for event_type, percentage in zip(event_types, percentages)]
    plt.legend(
        wedges, 
        legend_labels,
        title="Event Types",
        loc="center left",
        bbox_to_anchor=(1.0, 0.5),
        fontsize=12,
        frameon=True
    )
    
    # Equal aspect ratio ensures that pie is drawn as a circle
    ax.axis('equal')
    
    # Add some spacing for the legend
    plt.tight_layout()
    
    # Save the chart
    plt.savefig('pie.png', dpi=300, bbox_inches='tight')
    print("Pie chart saved as 'pie.png'")
    
    # Show the chart
    plt.show()

if __name__ == "__main__":
    print("Retrieving data from database...")
    data = get_event_type_distribution()
    
    if data:
        print(f"Found {len(data)} different event types")
        print("Creating pie chart...")
        create_pie_chart(data)
    else:
        print("Failed to retrieve data from database") 