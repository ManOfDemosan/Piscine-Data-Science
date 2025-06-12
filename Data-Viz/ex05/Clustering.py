import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import subprocess
import io
import os
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings

warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3

DB_NAME = "piscineds"
DB_USER = "jaehwkim"
DB_PASSWORD = "mysecretpassword"

def get_customer_data():
    try:
        print("Fetching customer data...")
        
        query_cmd = """
        docker exec -i postgresForDb bash -c "PGPASSWORD=mysecretpassword psql -U jaehwkim -d piscineds -c \\"COPY (
            WITH customer_metrics AS (
                SELECT 
                    user_id,
                    COUNT(*) AS visit_count,
                    COUNT(DISTINCT TO_CHAR(event_time, 'YYYY-MM-DD')) AS days_active,
                    MAX(event_time) - MIN(event_time) AS time_span,
                    MAX(event_time) AS last_visit,
                    MIN(event_time) AS first_visit,
                    CURRENT_TIMESTAMP - MAX(event_time) AS recency,
                    SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchase_count,
                    SUM(CASE WHEN event_type = 'purchase' THEN price ELSE 0 END) AS total_spent,
                    COUNT(DISTINCT TO_CHAR(event_time, 'YYYY-MM')) AS active_months
                FROM customers
                GROUP BY user_id
            )
            SELECT 
                user_id,
                visit_count,
                days_active,
                time_span,
                last_visit,
                first_visit,
                recency,
                purchase_count,
                total_spent,
                active_months,
                CASE WHEN days_active > 0 THEN visit_count::float / days_active ELSE 0 END AS avg_daily_visits,
                CASE WHEN purchase_count > 0 THEN total_spent / purchase_count ELSE 0 END AS avg_purchase_value,
                CASE WHEN purchase_count > 0 THEN visit_count::float / purchase_count ELSE 0 END AS visits_per_purchase
            FROM customer_metrics
            WHERE visit_count > 0
        ) TO STDOUT WITH CSV HEADER\\""
        """
        
        result = subprocess.run(query_cmd, shell=True, capture_output=True, text=True, check=True)
        df = pd.read_csv(io.StringIO(result.stdout))
        
        print(f"Retrieved data for {len(df)} customers.")
        
        if df.empty:
            print("No customer data found.")
            return None
        
        df = df.dropna()
        df = df.replace([np.inf, -np.inf], 0)
        
        for col in ['last_visit', 'first_visit']:
            df[col] = pd.to_datetime(df[col])
        
        df['recency_days'] = df['recency'].apply(lambda x: int(x.split(' ')[0]) if isinstance(x, str) else 0)
        df['frequency'] = df['purchase_count']
        df['monetary'] = df['total_spent']
        
        return df
    
    except subprocess.CalledProcessError as e:
        print(f"Data retrieval error: {e.stderr}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def prepare_and_cluster_data(df):
    print("Preparing RFM data and applying clustering...")
    
    rfm_features = ['recency_days', 'frequency', 'monetary']
    
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df[rfm_features])
    
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(scaled_features)
    
    cluster_stats = df.groupby('cluster')[rfm_features].mean()
    loyalty_score = cluster_stats['monetary'] * cluster_stats['frequency'] / (cluster_stats['recency_days'] + 1)
    sorted_clusters = loyalty_score.sort_values(ascending=False).index
    
    labels = {
        sorted_clusters[0]: 'Gold customers',
        sorted_clusters[1]: 'Silver customers',
        sorted_clusters[2]: 'New customers',
        sorted_clusters[3]: 'Inactive customers'
    }
    
    return df, labels

def create_bar_chart(df, labels):
    print("Creating customer segments bar chart...")
    
    cluster_counts = df['cluster'].value_counts().sort_index()
    cluster_names = [labels.get(i, f'Cluster {i+1}') for i in cluster_counts.index]
    
    colors = {
        'Gold customers': '#FFA500',
        'Silver customers': '#C0C0C0',
        'New customers': '#98FB98',
        'Inactive customers': '#F0E68C'
    }
    
    color_list = [colors[name] for name in cluster_names]
    
    plt.figure(figsize=(12, 6))
    ax = plt.subplot(111)
    
    ax.grid(True, axis='x', alpha=0.3)
    ax.grid(False, axis='y')
    
    bars = ax.barh(cluster_names, cluster_counts, color=color_list, height=0.6, edgecolor='white')
    
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.01 * width, bar.get_y() + bar.get_height()/2, 
                f'{int(width):,}', ha='left', va='center', fontsize=10)

    ax.set_xlabel('Number of customers', fontsize=11)
    ax.set_title('Customer Segments Distribution', fontsize=14, fontweight='bold', pad=20)
    ax.set_xlim(right=max(cluster_counts) * 1.1)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    plt.xticks(fontsize=9)
    plt.yticks(fontsize=10)
    
    plt.tight_layout()
    plt.savefig('customer_segments_bar.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Bar chart saved to customer_segments_bar.png")

def create_bubble_chart(df, labels):
    print("Creating customer segments bubble chart...")
    
    cluster_stats = df.groupby('cluster')[['frequency', 'recency_days', 'monetary']].median()
    cluster_stats['label'] = [labels.get(i, f'Cluster {i+1}') for i in cluster_stats.index]
    
    colors = {
        'Gold customers': '#FFA500',
        'Silver customers': '#C0C0C0',
        'New customers': '#98FB98',
        'Inactive customers': '#F0E68C'
    }
    
    max_monetary = cluster_stats['monetary'].max()
    sizes = (cluster_stats['monetary'] / max_monetary) * 2000 + 500
    
    plt.figure(figsize=(10, 8))
    ax = plt.subplot(111)
    
    ax.grid(True, alpha=0.3)
    
    for i, (idx, row) in enumerate(cluster_stats.iterrows()):
        label = row['label']
        color = colors[label]
        bubble_size = sizes[idx]
        
        ax.scatter(row['recency_days']/30, row['frequency'], 
                  s=bubble_size, color=color, alpha=0.7, edgecolor='white', linewidth=2)
        
        ax.text(row['recency_days']/30, row['frequency'], 
               f'Average "{label}":\n{int(row["monetary"])}₳', 
               ha='center', va='center', fontsize=9, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    ax.set_xlabel('Median Recency (months)', fontsize=12)
    ax.set_ylabel('Median Frequency', fontsize=12)
    ax.set_title('Customer Segments by RFM Analysis', fontsize=14, fontweight='bold', pad=20)
    
    x_padding = 1
    y_padding = 5
    x_min = max(0, min(cluster_stats['recency_days']/30) - x_padding)
    x_max = max(cluster_stats['recency_days']/30) + x_padding
    y_min = 0
    y_max = max(cluster_stats['frequency']) + y_padding
    
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    
    plt.tight_layout()
    plt.savefig('customer_segments_bubble.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Bubble chart saved to customer_segments_bubble.png")

def main():
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        customer_data = get_customer_data()
        
        if customer_data is None:
            print("Failed to retrieve data. Exiting.")
            return
        
        clustered_data, cluster_labels = prepare_and_cluster_data(customer_data)
        
        print("Cluster labels:", cluster_labels)
        
        create_bar_chart(clustered_data, cluster_labels)
        create_bubble_chart(clustered_data, cluster_labels)
        
        print("All visualization tasks completed successfully.")
    
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 