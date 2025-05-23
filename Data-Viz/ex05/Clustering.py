#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import subprocess
import io
import os
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import warnings

# 경고 메시지 숨기기
warnings.filterwarnings('ignore')

# 그래프 스타일 설정
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3

# 데이터베이스 연결 정보
DB_NAME = "piscineds"
DB_USER = "jaehwkim"
DB_PASSWORD = "mysecretpassword"

def get_customer_data():
    """데이터베이스에서 고객 행동 데이터 가져오기"""
    try:
        print("고객 데이터를 가져오는 중...")
        
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
        
        print(f"{len(df)}명의 고객 데이터를 가져왔습니다.")
        
        if df.empty:
            print("고객 데이터가 없습니다.")
            return None
        
        # 데이터 전처리
        df = df.dropna()
        df = df.replace([np.inf, -np.inf], 0)
        
        # 날짜/시간 데이터 처리
        for col in ['last_visit', 'first_visit']:
            df[col] = pd.to_datetime(df[col])
        
        # recency를 일 단위로 변환
        df['recency_days'] = df['recency'].apply(lambda x: int(x.split(' ')[0]) if isinstance(x, str) else 0)
        
        # 구매 빈도(frequency)와 총 지출(monetary) 계산
        df['frequency'] = df['purchase_count']
        df['monetary'] = df['total_spent']
        
        return df
    
    except subprocess.CalledProcessError as e:
        print(f"데이터 가져오기 오류: {e.stderr}")
        return None
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")
        return None

def prepare_rfm_data(df):
    """RFM (Recency, Frequency, Monetary) 데이터 준비"""
    print("RFM 데이터 준비 중...")
    
    # RFM 특성 선택
    rfm_df = df[['user_id', 'recency_days', 'frequency', 'monetary']].copy()
    
    # 데이터 스케일링
    scaler = StandardScaler()
    rfm_features = ['recency_days', 'frequency', 'monetary']
    rfm_scaled = scaler.fit_transform(rfm_df[rfm_features])
    
    # 스케일링된 데이터를 데이터프레임에 추가
    for i, feature in enumerate(rfm_features):
        rfm_df[f'{feature}_scaled'] = rfm_scaled[:, i]
    
    return rfm_df, rfm_features

def apply_kmeans_clustering(df, features, n_clusters=4):
    """KMeans 클러스터링 적용"""
    print(f"{n_clusters}개의 클러스터로 KMeans 클러스터링 적용 중...")
    
    # 클러스터링을 위한 특성 선택
    X = df[[f'{feature}_scaled' for feature in features]].values
    
    # KMeans 클러스터링 수행
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(X)
    
    # 클러스터 중심점
    cluster_centers = kmeans.cluster_centers_
    
    # 고객 유형 라벨 생성
    # 중심점 기반으로 클러스터 특성 분석
    labels = analyze_clusters(df, features, cluster_centers)
    
    return df, kmeans, cluster_centers, labels

def analyze_clusters(df, features, centers):
    """클러스터 분석하여 의미 있는 라벨 부여"""
    n_clusters = centers.shape[0]
    
    # 각 클러스터에 대한 평균값 계산
    cluster_stats = df.groupby('cluster')[features].mean()
    
    # 클러스터 특성 분석
    loyalty_score = cluster_stats['monetary'] * cluster_stats['frequency'] / (cluster_stats['recency_days'] + 1)
    
    # 충성도 점수에 따라 클러스터 정렬
    sorted_clusters = loyalty_score.sort_values().index
    
    # 클러스터 라벨 할당
    if n_clusters >= 3:
        labels = {
            sorted_clusters[0]: 'Inactive',            # 낮은 지출, 낮은 빈도, 높은 최근성
            sorted_clusters[-1]: 'Loyal customers',     # 높은 지출, 높은 빈도, 낮은 최근성
            sorted_clusters[1]: 'New customers'         # 중간 지출, 낮은 빈도, 낮은 최근성
        }
        
        # 4개 이상의 클러스터가 있는 경우 추가 세분화
        if n_clusters >= 4:
            labels[sorted_clusters[2]] = 'Regular'
            
        if n_clusters >= 5:
            labels[sorted_clusters[3]] = 'Potential loyal'
    else:
        # 클러스터가 3개 미만인 경우 기본 라벨
        labels = {i: f'Cluster {i+1}' for i in range(n_clusters)}
    
    return labels

def create_bar_chart(df, labels, output_file='customer_segments_bar.png'):
    """고객 세그먼트별 수를 보여주는 바차트 생성"""
    print("고객 세그먼트 바차트 생성 중...")
    
    # 클러스터별 고객 수 계산
    cluster_counts = df['cluster'].value_counts().sort_index()
    
    # 라벨 적용
    cluster_names = [labels.get(i, f'Cluster {i+1}') for i in cluster_counts.index]
    
    # 색상 설정 (참조 이미지와 유사하게)
    colors = {
        'Inactive': '#A9DFBF',        # 밝은 초록
        'New customers': '#F5CBA7',    # 베이지/피치
        'Loyal customers': '#F5CBA7',  # 베이지/피치
        'Regular': '#AED6F1',          # 밝은 파랑
        'Potential loyal': '#D2B4DE'   # 연한 보라
    }
    
    color_list = [colors.get(name, '#A9DFBF') for name in cluster_names]
    
    # 바차트 생성
    plt.figure(figsize=(12, 6))
    ax = plt.subplot(111)
    
    # 격자무늬 설정
    ax.grid(True, axis='x', alpha=0.3)
    ax.grid(False, axis='y')
    
    # 수평 바차트 그리기
    bars = ax.barh(cluster_names, cluster_counts, color=color_list, height=0.6, edgecolor='white')
    
    # 바 끝에 숫자 표시
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.01 * width, bar.get_y() + bar.get_height()/2, 
                f'{int(width):,}', ha='left', va='center', fontsize=10)
    
    # 축 레이블 및 타이틀 설정
    ax.set_xlabel('number of customers', fontsize=11)
    ax.set_xlim(right=max(cluster_counts) * 1.1)  # 오른쪽 여백 추가
    
    # 불필요한 테두리 제거
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # x축 레이블 설정
    plt.xticks(fontsize=9)
    plt.yticks(fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"바차트가 {output_file}에 저장되었습니다.")

def create_bubble_chart(df, features, labels, output_file='customer_segments_bubble.png'):
    """고객 세그먼트를 보여주는 버블차트 생성"""
    print("고객 세그먼트 버블차트 생성 중...")
    
    # 클러스터별 중앙값 계산 (평균보다 중앙값이 이상치에 덜 민감)
    cluster_stats = df.groupby('cluster')[['frequency', 'recency_days', 'monetary']].median()
    
    # 라벨 적용
    cluster_stats['label'] = [labels.get(i, f'Cluster {i+1}') for i in cluster_stats.index]
    
    # 색상 매핑 (참조 이미지와 유사하게)
    colors = {
        'Loyal customers': '#F5CBA7',    # 베이지/피치 
        'New customers': '#AED6F1',      # 밝은 파랑
        'Inactive': '#A9DFBF',           # 밝은 초록
        'Regular': '#D2B4DE',            # 연한 보라
        'Potential loyal': '#F9E79F'     # 연한 노랑
    }
    
    # 버블 크기 계산 (monetary 값 기준)
    max_monetary = cluster_stats['monetary'].max()
    # 참조 이미지와 비슷하게 보이도록 버블 크기 조정
    sizes = (cluster_stats['monetary'] / max_monetary) * 800  
    
    # 버블차트 생성
    plt.figure(figsize=(10, 8))
    ax = plt.subplot(111)
    
    # 배경 그리드 설정
    ax.grid(True, alpha=0.3)
    
    # 각 클러스터에 대한 버블 그리기
    for i, (idx, row) in enumerate(cluster_stats.iterrows()):
        label = row['label']
        color = colors.get(label, '#CCCCCC')
        
        # 버블 크기를 monetary에 비례하게 설정, 참조 이미지처럼 크게 만들기
        bubble_size = sizes[idx]
        
        # 버블 그리기
        ax.scatter(row['recency_days']/30, row['frequency'], 
                  s=bubble_size, color=color, alpha=0.7, edgecolor='white')
        
        # 버블 내부에 텍스트 표시
        ax.text(row['recency_days']/30, row['frequency'], 
               f'Average "{label}": {int(row["monetary"])}₳', 
               ha='center', va='center', fontsize=10, fontweight='bold')
    
    # 축 레이블 및 타이틀 설정
    ax.set_xlabel('Median Recency (month)', fontsize=12)
    ax.set_ylabel('Median Frequency', fontsize=12)
    ax.set_title('Customer Segments', fontsize=14)
    
    # 축 범위 설정 (참조 이미지와 유사하게)
    x_padding = 2  # 추가 여백
    y_padding = 10  # 추가 여백
    x_min = min(cluster_stats['recency_days']/30) - x_padding
    x_max = max(cluster_stats['recency_days']/30) + x_padding
    y_min = 0  # 빈도는 항상 0부터 시작
    y_max = max(cluster_stats['frequency']) + y_padding
    
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"버블차트가 {output_file}에 저장되었습니다.")

def create_scatter_plot(df, kmeans, output_file='customer_segments_scatter.png'):
    """클러스터링 결과를 보여주는 산점도 생성"""
    print("클러스터링 산점도 생성 중...")
    
    # PCA를 사용하여 차원 축소
    pca = PCA(n_components=2)
    X_scaled = df[['recency_days_scaled', 'frequency_scaled', 'monetary_scaled']].values
    X_pca = pca.fit_transform(X_scaled)
    
    # 클러스터 중심점도 변환
    centers_pca = pca.transform(kmeans.cluster_centers_)
    
    # 산점도 생성
    plt.figure(figsize=(12, 8))
    ax = plt.subplot(111)
    
    # 클러스터별 색상 및 마커 설정 (참조 이미지와 유사하게)
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#C25283']  # 밝고 선명한 색상
    markers = ['o', 's', '^', 'D', '*']  # 다양한 마커
    
    # 범례 항목
    legend_elements = []
    
    # 각 클러스터별 데이터 포인트 그리기
    for i in range(kmeans.n_clusters):
        cluster_points = X_pca[df['cluster'] == i]
        ax.scatter(cluster_points[:, 0], cluster_points[:, 1], 
                  c=colors[i % len(colors)], marker=markers[i % len(markers)], 
                  s=30, alpha=0.7, label=f'Cluster {i+1}')
        
        # 범례 항목 추가
        legend_elements.append(plt.Line2D([0], [0], marker=markers[i % len(markers)], 
                              color='w', markerfacecolor=colors[i % len(colors)], 
                              markersize=10, label=f'Cluster {i+1}'))
    
    # 클러스터 중심점 그리기 (더 눈에 띄게)
    ax.scatter(centers_pca[:, 0], centers_pca[:, 1], c='yellow', s=300, 
              alpha=0.9, label='Centroids', edgecolors='black', zorder=10)
    
    # 중심점 범례 항목 추가
    legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                          markerfacecolor='yellow', markersize=15, 
                          markeredgecolor='black', label='Centroids'))
    
    # 제목 및 축 레이블 설정
    ax.set_title('Clusters of customers', fontsize=16)
    ax.set_xlabel('PCA Component 1 (Monetary & Frequency)', fontsize=12)  # PCA 해석 추가
    ax.set_ylabel('PCA Component 2 (Recency)', fontsize=12)  # PCA 해석 추가
    
    # 그리드 및 범례 설정
    ax.grid(True, alpha=0.3)
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"산점도가 {output_file}에 저장되었습니다.")

def create_decision_boundary(df, kmeans, output_file='customer_segments_boundary.png'):
    """클러스터 경계를 시각화하는 결정 경계 플롯 생성"""
    print("클러스터 경계 시각화 생성 중...")
    
    # PCA를 사용하여 차원 축소
    pca = PCA(n_components=2)
    X_scaled = df[['recency_days_scaled', 'frequency_scaled', 'monetary_scaled']].values
    X_pca = pca.fit_transform(X_scaled)
    
    # 메쉬 그리드 생성
    h = 0.1  # 그리드 스텝 사이즈
    x_min, x_max = X_pca[:, 0].min() - 1, X_pca[:, 0].max() + 1
    y_min, y_max = X_pca[:, 1].min() - 1, X_pca[:, 1].max() + 1
    xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                         np.arange(y_min, y_max, h))
    
    # PCA 공간에서의 KMeans 분류기 생성
    classifier = KMeans(n_clusters=kmeans.n_clusters, init=pca.transform(kmeans.cluster_centers_), n_init=1)
    classifier.fit(X_pca)
    
    # 그리드 포인트 예측
    Z = classifier.predict(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)
    
    # 결정 경계 플롯 생성
    plt.figure(figsize=(12, 8))
    ax = plt.subplot(111)
    
    # 색상 설정 (참조 이미지와 유사하게)
    custom_cmap = plt.cm.get_cmap('Spectral', kmeans.n_clusters)
    
    # 경계 시각화 (더 선명하고 뚜렷하게)
    im = ax.contourf(xx, yy, Z, alpha=0.8, cmap=custom_cmap)
    
    # 각 클러스터별 데이터 포인트 그리기 (반투명하게)
    for i in range(kmeans.n_clusters):
        cluster_points = X_pca[df['cluster'] == i]
        if len(cluster_points) > 0:  # 빈 클러스터 방지
            ax.scatter(cluster_points[:, 0], cluster_points[:, 1], 
                      c='white', edgecolors=custom_cmap(i/kmeans.n_clusters), s=10, alpha=0.2)
    
    # 클러스터 중심점 그리기
    centers_pca = pca.transform(kmeans.cluster_centers_)
    ax.scatter(centers_pca[:, 0], centers_pca[:, 1], c='yellow', s=300, 
              alpha=0.9, label='Centroids', edgecolors='black', zorder=10)
    
    # 범례 항목 생성
    legend_elements = [plt.Line2D([0], [0], marker='o', color='w',
                     markerfacecolor=custom_cmap(i/kmeans.n_clusters), markersize=10, 
                     label=f'Cluster {i+1}')
                     for i in range(kmeans.n_clusters)]
    legend_elements.append(plt.Line2D([0], [0], marker='o', color='w',
                     markerfacecolor='yellow', markersize=15, 
                     markeredgecolor='black', label='Centroids'))
    
    # 제목 및 축 레이블 설정
    ax.set_title('Clusters of customers', fontsize=16)
    ax.set_xlabel('PCA Component 1 (Monetary & Frequency)', fontsize=12)
    ax.set_ylabel('PCA Component 2 (Recency)', fontsize=12)
    
    # 범례 및 그리드 설정
    ax.legend(handles=legend_elements, loc='lower right', fontsize=10)
    ax.grid(False)  # 경계 시각화에서는 그리드 제거
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"클러스터 경계 시각화가 {output_file}에 저장되었습니다.")

def main():
    try:
        # 스크립트 디렉토리로 이동
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # 데이터 가져오기
        customer_data = get_customer_data()
        
        if customer_data is None:
            print("데이터를 가져오지 못했습니다. 종료합니다.")
            return
        
        # RFM 데이터 준비
        rfm_data, rfm_features = prepare_rfm_data(customer_data)
        
        # KMeans 클러스터링 적용 (5개 클러스터)
        clustered_data, kmeans_model, centers, cluster_labels = apply_kmeans_clustering(
            rfm_data, rfm_features, n_clusters=5)
        
        print("클러스터 라벨:", cluster_labels)
        
        # 시각화 1: 바 차트
        create_bar_chart(clustered_data, cluster_labels)
        
        # 시각화 2: 버블 차트
        create_bubble_chart(clustered_data, rfm_features, cluster_labels)
        
        # 시각화 3: 산점도
        create_scatter_plot(clustered_data, kmeans_model)
        
        # 시각화 4: 결정 경계
        create_decision_boundary(clustered_data, kmeans_model)
        
        print("모든 작업이 완료되었습니다.")
    
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 