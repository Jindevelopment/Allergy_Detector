#!/usr/bin/env python3
"""
Firebase DB 데이터 확인 스크립트
"""
import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.append('/Users/sunoo/Desktop/code/Allergy_Detector')

from src.database.clients.db_client import get_db

def check_users():
    """사용자 데이터 확인"""
    try:
        db = get_db()
        
        print("🔍 Firebase DB 연결 확인 중...")
        
        # users 컬렉션 확인
        users_ref = db.collection('users')
        users = users_ref.stream()
        
        print("\n📊 저장된 사용자 목록:")
        user_count = 0
        for user in users:
            user_count += 1
            user_data = user.to_dict()
            print(f"  {user_count}. ID: {user.id}")
            print(f"     - 닉네임: {user_data.get('nickname', 'N/A')}")
            print(f"     - 생성일: {user_data.get('created_at', 'N/A')}")
            print(f"     - 마지막 로그인: {user_data.get('last_login', 'N/A')}")
            print()
        
        if user_count == 0:
            print("  ❌ 저장된 사용자가 없습니다.")
        else:
            print(f"  ✅ 총 {user_count}명의 사용자가 저장되어 있습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def check_allergies():
    """알레르기 데이터 확인"""
    try:
        db = get_db()
        
        # allergies 컬렉션 확인
        allergies_ref = db.collection('allergies')
        allergies = allergies_ref.stream()
        
        print("\n⚠️ 저장된 알레르기 목록:")
        allergy_count = 0
        for allergy in allergies:
            allergy_count += 1
            allergy_data = allergy.to_dict()
            print(f"  {allergy_count}. ID: {allergy.id}")
            print(f"     - 사용자: {allergy_data.get('user_id', 'N/A')}")
            print(f"     - 알레르기: {allergy_data.get('allergen_name', 'N/A')}")
            print(f"     - 심각도: {allergy_data.get('severity', 'N/A')}")
            print(f"     - 생성일: {allergy_data.get('created_at', 'N/A')}")
            print()
        
        if allergy_count == 0:
            print("  ❌ 저장된 알레르기가 없습니다.")
        else:
            print(f"  ✅ 총 {allergy_count}개의 알레르기가 저장되어 있습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    print("🚀 Firebase DB 데이터 확인 시작!")
    print("=" * 50)
    
    # 환경변수 설정
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/sunoo/Desktop/code/Allergy_Detector/serviceAccountKey.json'
    
    check_users()
    check_allergies()
    
    print("\n" + "=" * 50)
    print("✅ DB 확인 완료!")
