#!/usr/bin/env python3
import psycopg2
import matplotlib.pyplot as plt


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
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT event_type, COUNT(*) as count
            FROM customers
            GROUP BY event_type
            ORDER BY count DESC
        """)
        
        results = cursor.fetchall()
        
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
    
    event_types = [row[0] for row in data]
    counts = [row[1] for row in data]
    
    total = sum(counts)
    percentages = [count/total*100 for count in counts]
    
    # 사진과 같은 색상으로 변경: 파란색, 주황색, 초록색, 빨간색
    colors = ['#4472C4', '#E6763A', '#70AD47', '#C5504B']
    
    fig, ax = plt.subplots(figsize=(10, 8), facecolor='white')
    
    # make labels with percentages
    labels_with_percent = [f"{event_type}\n{percentage:.1f}%" for event_type, percentage in zip(event_types, percentages)]
    
    wedges, texts = ax.pie(
        counts,
        labels=labels_with_percent,
        colors=colors,
        startangle=90,
        wedgeprops={'edgecolor': 'white', 'linewidth': 2},
        textprops={'fontsize': 12, 'color': 'black', 'weight': 'bold'},
        labeldistance=1.1,  # move labels outside the pie chart
        pctdistance=0.85    # show percentages
    )
    
    plt.title('Distribution of User Activity Types on the Site', fontsize=18, pad=20, weight='bold')
    
    ax.axis('equal')
    
    plt.tight_layout()
    
    plt.savefig('pie.png', dpi=300, bbox_inches='tight', facecolor='white')
    print("Pie chart saved as 'pie.png'")
    
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