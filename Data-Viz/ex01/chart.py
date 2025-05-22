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

# 시각화 스타일 설정
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("Blues_r")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
plt.rcParams['axes.facecolor'] = '#F0F1F6'  # 배경색 변경
plt.rcParams['figure.facecolor'] = 'white'  # 그림 배경색

# 알타리안 달러 기호
ALTAIRIAN_DOLLAR = '₳'

# 데이터베이스 연결 설정
DB_NAME = "piscineds"
DB_USER = "jaehwkim"
DB_PASSWORD = "mysecretpassword"
DB_HOST = "localhost"
DB_PORT = "5432"

def get_purchase_data():
    """customers 테이블에서 'purchase' 이벤트 데이터 가져오기"""
    try:
        # 1. 데이터베이스에서 직접 쿼리 실행하여 결과 가져오기
        print("데이터베이스에서 구매 데이터 가져오는 중...")
        
        # 직접 SQL 쿼리 실행
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
            print(f"데이터 가져오기 오류: {result.stderr}")
            return None
        
        # CSV 형식의 결과를 DataFrame으로 변환
        df = pd.read_csv(io.StringIO(result.stdout))
        
        print(f"총 {len(df)}개의 구매 데이터를 가져왔습니다.")
        
        # 결과 확인
        if df.empty:
            print("구매 데이터가 없습니다.")
            return None
        
        # 추가 정보 계산
        df['event_time'] = pd.to_datetime(df['event_time'])
        df['day'] = df['event_time'].dt.date
        df['month'] = df['event_time'].dt.to_period('M')
        
        # 월별 데이터 분포 출력
        monthly_counts = df.groupby(df['month'].dt.strftime('%Y-%m')).size()
        print("\n월별 데이터 건수:")
        print(monthly_counts)
        
        print(f"총 {len(df)} 개의 구매 데이터를 사용합니다.")
        return df
    
    except Exception as e:
        print(f"데이터 조회 오류: {e}")
        return None

def create_daily_price_chart(df):
    """일별 구매 금액 추이 차트 생성"""
    # 일별 고객 수 계산
    daily_count = df.groupby('day').size().reset_index(name='count')
    
    # 그래프 생성
    plt.figure(figsize=(10, 6))
    plt.plot(daily_count['day'], daily_count['count'], color='#4169E1', linewidth=1.5)
    
    # 차트 타이틀 및 라벨 설정
    plt.title('Daily Number of Customers (October 2022 - February 2023)', fontsize=14, pad=15)
    plt.xlabel('', fontsize=12)  # x축 라벨 없음
    plt.ylabel('Number of customers', fontsize=12)
    
    # x축 날짜 포맷 설정
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    
    # y축 범위 설정
    plt.ylim(bottom=0)  # 0부터 시작
    
    # 그리드 설정
    plt.grid(True, linestyle='-', alpha=0.5)
    
    # 여백 조정
    plt.tight_layout()
    
    # 저장
    plt.savefig('chart_1_daily_customers.png', dpi=300, bbox_inches='tight')
    print("차트 1: 일별 고객 수 차트가 생성되었습니다.")

def create_monthly_bar_chart(df):
    """월별 총 구매 금액 바 차트 생성"""
    # 월별 총 구매 금액 계산 (백만 단위)
    monthly_sum = df.groupby('month')['price'].sum().reset_index()
    monthly_sum['price_millions'] = monthly_sum['price'] / 1000000  # 백만 단위로 변환
    monthly_sum['month_str'] = monthly_sum['month'].dt.strftime('%b')  # 월 이름으로 변환
    
    print("\n월별 총 구매 금액 (백만 단위):")
    print(monthly_sum[['month_str', 'price_millions']])
    
    plt.figure(figsize=(10, 6))
    
    # 바 차트 생성
    bars = plt.bar(monthly_sum['month_str'], monthly_sum['price_millions'], 
                  color='#A4C2F4', width=0.6, edgecolor='none')
    
    # 차트 타이틀 및 라벨 설정
    plt.title('Monthly Purchase Amount (October 2022 - February 2023)', fontsize=14, pad=15)
    plt.xlabel('month', fontsize=12)
    plt.ylabel(f'total sales in million of {ALTAIRIAN_DOLLAR}', fontsize=12)
    
    # y축 범위 설정
    plt.ylim(0, 1.4)  # 0부터 1.4까지
    
    # 그리드 설정 (y축만)
    plt.grid(axis='y', linestyle='-', alpha=0.3)
    plt.gca().set_axisbelow(True)  # 그리드를 막대 뒤로 보내기
    
    # 여백 조정
    plt.tight_layout()
    
    # 저장
    plt.savefig('chart_2_monthly_amount.png', dpi=300, bbox_inches='tight')
    print("차트 2: 월별 구매 금액 차트가 생성되었습니다.")

def create_purchase_ratio_chart(df):
    """일별 평균 지출액 차트 생성"""
    # 일별 평균 지출액 계산
    daily_avg = df.groupby('day').agg(
        avg_spend=('price', 'mean')
    ).reset_index()
    
    # 날짜별로 정렬
    daily_avg = daily_avg.sort_values('day')
    
    # 월 정보 추가
    daily_avg['month'] = pd.to_datetime(daily_avg['day']).dt.strftime('%b')
    
    plt.figure(figsize=(10, 6))
    
    # 영역 채우기 차트 생성
    plt.fill_between(daily_avg.index, daily_avg['avg_spend'], 
                     color='#A4C2F4', alpha=0.7)
    
    # 차트 타이틀 및 라벨 설정
    plt.title('Daily Average Spend (October 2022 - February 2023)', fontsize=14, pad=15)
    plt.xlabel('', fontsize=12)  # x축 라벨 없음
    plt.ylabel(f'average spend/customers in {ALTAIRIAN_DOLLAR}', fontsize=12)
    
    # x축 설정 (월별 구분)
    month_positions = []
    month_labels = []
    current_month = None
    
    for i, (idx, row) in enumerate(daily_avg.iterrows()):
        if row['month'] != current_month:
            current_month = row['month']
            month_positions.append(i)
            month_labels.append(current_month)
    
    plt.xticks(month_positions, month_labels)
    
    # y축 범위 설정 - 실제 데이터에 맞게 조정
    plt.ylim(0, 8)  # 0부터 8까지 (데이터 범위 4-6에 여유 추가)
    
    # 그리드 설정
    plt.grid(True, linestyle='-', alpha=0.3)
    
    # 여백 조정
    plt.tight_layout()
    
    # 저장
    plt.savefig('chart_3_average_spend.png', dpi=300, bbox_inches='tight')
    print("차트 3: 일별 평균 지출액 차트가 생성되었습니다.")

if __name__ == "__main__":
    # 현재 디렉토리를 스크립트 위치로 변경
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("구매 데이터 분석 시작...")
    
    # 데이터 가져오기
    purchase_data = get_purchase_data()
    
    if purchase_data is not None:
        # 차트 생성
        create_daily_price_chart(purchase_data)
        create_monthly_bar_chart(purchase_data)
        create_purchase_ratio_chart(purchase_data)
        
        print("모든 차트 생성이 완료되었습니다.")
    else:
        print("데이터를 불러오는 데 실패했습니다.")
