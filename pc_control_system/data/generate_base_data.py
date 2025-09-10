#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
베이스 통계 데이터 생성 스크립트
2023년 10월 ~ 2025년 8월까지의 월별 로그인 수 데이터를 바탕으로
통계용 베이스 로그인 기록을 생성합니다.
"""

import json
import random
from datetime import datetime, timedelta
import pytz

# 월별 로그인 수 데이터
monthly_data = [w
    # 2023년
    ("2023", "10", 11),
    ("2023", "11", 4),
    ("2023", "12", 9),
    
    # 2024년
    ("2024", "01", 10),
    ("2024", "02", 5),
    ("2024", "03", 4),
    ("2024", "04", 1),
    ("2024", "05", 4),
    ("2024", "06", 12),
    ("2024", "07", 25),
    ("2024", "08", 8),
    ("2024", "09", 4),
    ("2024", "10", 6),
    ("2024", "11", 5),
    ("2024", "12", 4),
    
    # 2025년
    ("2025", "01", 8),
    ("2025", "02", 35),
    ("2025", "03", 31),
    ("2025", "04", 19),
    ("2025", "05", 18),
    ("2025", "06", 15),
    ("2025", "07", 11),
    ("2025", "08", 28),
]

def get_month_days(year, month):
    """해당 월의 일수를 반환"""
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return 31
    elif month in [4, 6, 9, 11]:
        return 30
    else:  # 2월
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            return 29
        else:
            return 28

def generate_base_timestamp(year, month):
    """베이스 데이터용 간단한 타임스탬프 생성 (월 정보만 포함)"""
    # 해당 월의 첫째 날 00:00:00으로 설정 (통계용)
    korea_tz = pytz.timezone('Asia/Seoul')
    dt = datetime(int(year), int(month), 1, 0, 0, 0)
    dt = korea_tz.localize(dt)
    return dt.isoformat()

def generate_base_login_history():
    """베이스 로그인 히스토리 생성"""
    login_history = []
    
    print("🔄 베이스 통계 데이터 생성 중...")
    
    for year, month, count in monthly_data:
        print(f"  📅 {year}년 {month}월: {count}개 기록 생성")
        
        for i in range(count):
            # 베이스 데이터 생성 (모든 필드를 최소한으로)
            record = {
                "timestamp": generate_base_timestamp(year, month),
                "name": "베이스데이터",
                "affiliation": "베이스데이터", 
                "contact": "",
                "email": "",
                "pc_number": ""  # 빈 문자열
            }
            login_history.append(record)
    
    # 시간순으로 정렬
    login_history.sort(key=lambda x: x["timestamp"])
    
    return login_history

def save_to_file(login_history, filename="backend/login_history.json"):
    """생성된 데이터를 JSON 파일로 저장"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(login_history, f, ensure_ascii=False, indent=2)
        print(f"✅ 베이스 데이터가 {filename}에 저장되었습니다.")
        print(f"📊 총 {len(login_history)}개의 로그인 기록 생성")
        
        # 월별 통계 출력
        monthly_stats = {}
        for record in login_history:
            month_key = record["timestamp"][:7]  # YYYY-MM
            monthly_stats[month_key] = monthly_stats.get(month_key, 0) + 1
        
        print("\n📈 월별 생성 현황:")
        for month, count in sorted(monthly_stats.items()):
            print(f"  {month}: {count}개")
            
    except Exception as e:
        print(f"❌ 파일 저장 실패: {e}")

if __name__ == "__main__":
    print("🎯 PC 제어시스템 베이스 데이터 생성기")
    print("=" * 50)
    
    # 베이스 데이터 생성
    base_data = generate_base_login_history()
    
    # 파일 저장
    save_to_file(base_data)
    
    print("\n✨ 베이스 데이터 생성 완료!")
    print("📌 9월부터는 실제 사용자 데이터가 이 파일에 추가됩니다.")
