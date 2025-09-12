import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
import pytesseract
from PIL import Image
import io
import re

# 페이지 설정
st.set_page_config(
    page_title="Dangerout Eating - 알레르기 위험 탐지",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f2937;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        background-color: #f8fafc;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #3b82f6;
        margin-bottom: 1rem;
    }
    .danger-high {
        background-color: #fef2f2;
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .danger-medium {
        background-color: #fff7ed;
        border-left: 4px solid #f97316;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .danger-low {
        background-color: #fffbeb;
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .safe {
        background-color: #f0fdf4;
        border-left: 4px solid #22c55e;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .sidebar .sidebar-content {
        background-color: #f8fafc;
    }
</style>
""", unsafe_allow_html=True)

# 데이터베이스 초기화
def init_database():
    conn = sqlite3.connect('allergy_database.db')
    cursor = conn.cursor()
    
    # 사용자 프로필 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            allergy_name TEXT,
            severity TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 분석 이력 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            image_name TEXT,
            ocr_text TEXT,
            detected_allergies TEXT,
            risk_level TEXT,
            analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# 알레르기 데이터베이스 (식약처 고시 23종 + 확장)
ALLERGY_DATABASE = {
    "난류": ["계란", "egg", "eggs", "egg white", "egg yolk", "알부민"],
    "우유": ["milk", "dairy", "lactose", "치즈", "cheese", "버터", "butter", "크림", "cream"],
    "메밀": ["buckwheat", "메밀", "soba"],
    "땅콩": ["peanut", "peanuts", "땅콩", "arachis"],
    "대두": ["soy", "soybean", "대두", "콩", "tofu", "두부", "간장", "된장"],
    "밀": ["wheat", "밀", "flour", "gluten", "글루텐"],
    "고등어": ["mackerel", "고등어", "꽁치"],
    "게": ["crab", "게", "크랩"],
    "새우": ["shrimp", "prawn", "새우", "크릴"],
    "돼지고기": ["pork", "돼지고기", "pork meat"],
    "복숭아": ["peach", "복숭아", "피치"],
    "토마토": ["tomato", "토마토", "토마토 페이스트"],
    "호두": ["walnut", "호두", "월넛"],
    "닭고기": ["chicken", "닭고기", "치킨"],
    "쇠고기": ["beef", "쇠고기", "소고기", "beef meat"],
    "오징어": ["squid", "오징어", "칼라마리"],
    "전복": ["abalone", "전복", "어복"],
    "홍합": ["mussel", "홍합", "뮤셀"],
    "굴": ["oyster", "굴", "오이스터"],
    "잣": ["pine nut", "잣", "파인넛"],
    "아몬드": ["almond", "아몬드", "아몬드밀크"],
    "호박": ["pumpkin", "호박", "펌킨"],
    "쑥": ["mugwort", "쑥", "아르테미시아"]
}

# 위험도 계산 함수
def calculate_risk_level(detected_allergies, user_allergies):
    if not detected_allergies:
        return "안전", "safe"
    
    high_risk_count = 0
    medium_risk_count = 0
    low_risk_count = 0
    
    for allergy in detected_allergies:
        if allergy in user_allergies:
            severity = get_user_allergy_severity(allergy)
            if severity == "심각":
                high_risk_count += 1
            elif severity == "주의":
                medium_risk_count += 1
            else:
                low_risk_count += 1
    
    if high_risk_count > 0:
        return "강", "high"
    elif medium_risk_count > 0:
        return "중", "medium"
    elif low_risk_count > 0:
        return "약", "low"
    else:
        return "안전", "safe"

# 사용자 알레르기 심각도 조회
def get_user_allergy_severity(allergy_name):
    conn = sqlite3.connect('allergy_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT severity FROM user_profiles WHERE allergy_name = ?', (allergy_name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "경미"

# OCR 텍스트 추출
def extract_text_from_image(image):
    try:
        text = pytesseract.image_to_string(image, lang='kor+eng')
        return text.strip()
    except Exception as e:
        st.error(f"OCR 처리 중 오류가 발생했습니다: {str(e)}")
        return ""

# 알레르기 탐지
def detect_allergies(text, user_allergies):
    detected = []
    text_lower = text.lower()
    
    for allergy, variations in ALLERGY_DATABASE.items():
        for variation in variations:
            if variation.lower() in text_lower:
                if allergy in user_allergies and allergy not in detected:
                    detected.append(allergy)
                break
    
    return detected

# 메인 페이지
def main_page():
    st.markdown('<h1 class="main-header">🚨 Dangerout Eating</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #6b7280;">사진 한 장으로 알레르기 위험 확인</p>', unsafe_allow_html=True)
    
    # 핵심 기능 소개
    st.markdown("## 🎯 핵심 기능")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📷 OCR 인식</h3>
            <p>성분표 사진에서 텍스트를 자동으로 추출합니다.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>👤 프로필 매칭</h3>
            <p>등록된 알레르기 정보와 성분을 교차 분석합니다.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>🚦 위험 판별</h3>
            <p>신호등 방식으로 위험도를 직관적으로 표시합니다.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 맞춤 안내</h3>
            <p>개인별 맞춤형 안전 가이드를 제공합니다.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 시작하기 버튼
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔍 성분표 분석 시작하기", key="start_analysis", use_container_width=True):
            st.session_state.current_page = "분석"
            st.rerun()

# 분석 페이지
def analysis_page():
    st.title("🔍 성분표 분석")
    
    # 사용자 알레르기 정보 확인
    user_id = st.session_state.get('user_id', 'default_user')
    conn = sqlite3.connect('allergy_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT allergy_name FROM user_profiles WHERE user_id = ?', (user_id,))
    user_allergies = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    if not user_allergies:
        st.warning("⚠️ 먼저 내 프로필에서 알레르기 정보를 등록해주세요.")
        if st.button("프로필 설정하러 가기"):
            st.session_state.current_page = "내 프로필"
            st.rerun()
        return
    
    # 성분표 업로드
    uploaded_file = st.file_uploader(
        "성분표 이미지를 업로드하세요",
        type=['png', 'jpg', 'jpeg'],
        help="성분표가 선명하게 보이는 사진을 업로드해주세요."
    )
    
    if uploaded_file is not None:
        # 이미지 표시
        image = Image.open(uploaded_file)
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(image, caption="업로드된 성분표", use_column_width=True)
        
        with col2:
            # OCR 처리
            if st.button("🔍 성분 분석하기", key="analyze"):
                with st.spinner("성분을 분석하고 있습니다..."):
                    # OCR 텍스트 추출
                    ocr_text = extract_text_from_image(image)
                    
                    if ocr_text:
                        st.markdown("### 📝 인식된 텍스트")
                        st.text_area("", value=ocr_text, height=200, disabled=True)
                        
                        # 알레르기 탐지
                        detected_allergies = detect_allergies(ocr_text, user_allergies)
                        
                        # 위험도 계산
                        risk_level, risk_class = calculate_risk_level(detected_allergies, user_allergies)
                        
                        # 결과 표시
                        st.markdown("### 🚦 분석 결과")
                        
                        if risk_class == "high":
                            st.markdown(f"""
                            <div class="danger-high">
                                <h3>🔴 강 (고위험)</h3>
                                <p>다수의 알레르기 성분이 감지되었습니다. 섭취를 권하지 않습니다.</p>
                            </div>
                            """, unsafe_allow_html=True)
                        elif risk_class == "medium":
                            st.markdown(f"""
                            <div class="danger-medium">
                                <h3>🟠 중 (중위험)</h3>
                                <p>일부 알레르기 성분이 감지되었습니다. 주의가 필요합니다.</p>
                            </div>
                            """, unsafe_allow_html=True)
                        elif risk_class == "low":
                            st.markdown(f"""
                            <div class="danger-low">
                                <h3>🟡 약 (저위험)</h3>
                                <p>경미한 알레르기 성분이 감지되었습니다. 섭취 전 주의하세요.</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div class="safe">
                                <h3>🟢 안전</h3>
                                <p>등록된 알레르기 성분이 감지되지 않았습니다.</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # 감지된 알레르기 상세 정보
                        if detected_allergies:
                            st.markdown("### ⚠️ 감지된 알레르기 성분")
                            for allergy in detected_allergies:
                                severity = get_user_allergy_severity(allergy)
                                st.markdown(f"- **{allergy}** (심각도: {severity})")
                        
                        # 분석 결과 저장
                        conn = sqlite3.connect('allergy_database.db')
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO analysis_history 
                            (user_id, image_name, ocr_text, detected_allergies, risk_level)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (user_id, uploaded_file.name, ocr_text, 
                              ', '.join(detected_allergies), risk_level))
                        conn.commit()
                        conn.close()
                        
                        st.success("✅ 분석이 완료되었습니다. 이력이 저장되었습니다.")
                    else:
                        st.error("텍스트를 인식할 수 없습니다. 더 선명한 이미지를 업로드해주세요.")

# 프로필 관리 페이지
def profile_page():
    st.title("👤 내 프로필")
    
    user_id = st.session_state.get('user_id', 'default_user')
    
    # 현재 등록된 알레르기
    st.markdown("### 현재 등록된 알레르기")
    conn = sqlite3.connect('allergy_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT allergy_name, severity FROM user_profiles WHERE user_id = ?', (user_id,))
    current_allergies = cursor.fetchall()
    conn.close()
    
    if current_allergies:
        for allergy, severity in current_allergies:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"• {allergy}")
            with col2:
                st.write(f"심각도: {severity}")
            with col3:
                if st.button("삭제", key=f"delete_{allergy}"):
                    conn = sqlite3.connect('allergy_database.db')
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM user_profiles WHERE user_id = ? AND allergy_name = ?', 
                                 (user_id, allergy))
                    conn.commit()
                    conn.close()
                    st.rerun()
    else:
        st.info("등록된 알레르기가 없습니다.")
    
    st.markdown("---")
    
    # 새로운 알레르기 등록
    st.markdown("### 알레르기 추가")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_allergy = st.selectbox(
            "알레르기 선택",
            options=list(ALLERGY_DATABASE.keys()),
            key="new_allergy"
        )
    with col2:
        severity = st.selectbox(
            "심각도",
            options=["심각", "주의", "경미"],
            key="severity"
        )
    
    if st.button("알레르기 추가", key="add_allergy"):
        # 중복 확인
        conn = sqlite3.connect('allergy_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM user_profiles WHERE user_id = ? AND allergy_name = ?', 
                      (user_id, selected_allergy))
        exists = cursor.fetchone()[0] > 0
        
        if not exists:
            cursor.execute('''
                INSERT INTO user_profiles (user_id, allergy_name, severity)
                VALUES (?, ?, ?)
            ''', (user_id, selected_allergy, severity))
            conn.commit()
            st.success(f"✅ {selected_allergy} 알레르기가 등록되었습니다.")
            st.rerun()
        else:
            st.warning("이미 등록된 알레르기입니다.")
        conn.close()

# 이력 페이지
def history_page():
    st.title("📊 분석 이력")
    
    user_id = st.session_state.get('user_id', 'default_user')
    
    conn = sqlite3.connect('allergy_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT image_name, risk_level, analysis_date, detected_allergies
        FROM analysis_history 
        WHERE user_id = ?
        ORDER BY analysis_date DESC
    ''', (user_id,))
    history = cursor.fetchall()
    conn.close()
    
    if history:
        for idx, (image_name, risk_level, analysis_date, detected_allergies) in enumerate(history):
            with st.expander(f"{image_name} - {analysis_date.strftime('%Y-%m-%d %H:%M')}"):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    if risk_level == "강":
                        st.markdown("🔴 **강 (고위험)**")
                    elif risk_level == "중":
                        st.markdown("🟠 **중 (중위험)**")
                    elif risk_level == "약":
                        st.markdown("🟡 **약 (저위험)**")
                    else:
                        st.markdown("🟢 **안전**")
                
                with col2:
                    if detected_allergies:
                        st.write(f"감지된 알레르기: {detected_allergies}")
                    else:
                        st.write("감지된 알레르기 없음")
                
                if st.button("상세 보기", key=f"detail_{idx}"):
                    st.session_state.selected_history = idx
                    st.rerun()
    else:
        st.info("분석 이력이 없습니다.")

# 고객지원 페이지
def support_page():
    st.title("🆘 고객지원")
    
    # FAQ
    st.markdown("## ❓ 자주 묻는 질문")
    
    faq_data = [
        {
            "question": "어떤 이미지 형식을 지원하나요?",
            "answer": "PNG, JPG, JPEG 형식을 지원합니다. 성분표가 선명하게 보이는 사진일수록 정확도가 높아집니다."
        },
        {
            "question": "OCR 인식이 잘 안 될 때는 어떻게 하나요?",
            "answer": "다음과 같은 방법을 시도해보세요:\n- 더 선명한 사진 촬영\n- 성분표 부분만 크롭해서 업로드\n- 충분한 조명에서 촬영\n- 글자가 선명하게 보이도록 각도 조정"
        },
        {
            "question": "알레르기 데이터베이스에 없는 성분은 어떻게 하나요?",
            "answer": "현재 식약처 고시 23종 알레르기 성분을 기준으로 하고 있습니다. 추가 요청이 있으시면 연락주세요."
        },
        {
            "question": "분석 결과가 의학적 진단인가요?",
            "answer": "아니요. 이 서비스는 참고용 도구이며, 의학적 진단을 대체하지 않습니다. 건강에 대한 우려가 있으시면 의사와 상담하시기 바랍니다."
        }
    ]
    
    for faq in faq_data:
        with st.expander(faq["question"]):
            st.write(faq["answer"])
    
    st.markdown("---")
    
    # 연락처
    st.markdown("## 📞 문의 및 연락처")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **이메일:** support@dangerouteating.com  
        **전화:** 02-1234-5678  
        **운영시간:** 평일 09:00-18:00
        """)
    
    with col2:
        st.markdown("""
        **소셜 미디어:**  
        📘 Facebook: @DangeroutEating  
        📷 Instagram: @dangerout_eating  
        🐦 Twitter: @DangeroutEating
        """)
    
    # DB 업데이트 요청
    st.markdown("---")
    st.markdown("## 🔄 알레르기 DB 업데이트 요청")
    
    with st.form("db_update_request"):
        st.text_input("추가를 원하는 알레르기 성분")
        st.text_area("요청 사유 및 상세 정보")
        submitted = st.form_submit_button("요청 보내기")
        
        if submitted:
            st.success("요청이 접수되었습니다. 검토 후 반영하겠습니다.")

# 사이드바 네비게이션
def sidebar_navigation():
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/3b82f6/ffffff?text=Dangerout+Eating", 
                caption="Dangerout Eating")
        
        st.markdown("---")
        
        # 페이지 선택
        pages = {
            "🏠 메인": "메인",
            "🔍 분석": "분석", 
            "👤 내 프로필": "내 프로필",
            "📊 이력": "이력",
            "🆘 고객지원": "고객지원"
        }
        
        selected_page = st.selectbox(
            "페이지 선택",
            options=list(pages.keys()),
            index=list(pages.values()).index(st.session_state.get('current_page', '메인'))
        )
        
        st.session_state.current_page = pages[selected_page]
        
        st.markdown("---")
        
        # 사용자 정보
        st.markdown("### 👤 사용자 정보")
        user_id = st.text_input("사용자 ID", value=st.session_state.get('user_id', 'default_user'))
        st.session_state.user_id = user_id
        
        st.markdown("---")
        
        # 통계 정보
        if st.session_state.get('user_id'):
            conn = sqlite3.connect('allergy_database.db')
            cursor = conn.cursor()
            
            # 등록된 알레르기 수
            cursor.execute('SELECT COUNT(*) FROM user_profiles WHERE user_id = ?', 
                          (st.session_state.user_id,))
            allergy_count = cursor.fetchone()[0]
            
            # 분석 횟수
            cursor.execute('SELECT COUNT(*) FROM analysis_history WHERE user_id = ?', 
                          (st.session_state.user_id,))
            analysis_count = cursor.fetchone()[0]
            
            conn.close()
            
            st.metric("등록된 알레르기", allergy_count)
            st.metric("총 분석 횟수", analysis_count)

# 메인 앱 실행
def main():
    # 데이터베이스 초기화
    init_database()
    
    # 세션 상태 초기화
    if 'current_page' not in st.session_state:
        st.session_state.current_page = '메인'
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 'default_user'
    
    # 사이드바 네비게이션
    sidebar_navigation()
    
    # 페이지 라우팅
    if st.session_state.current_page == '메인':
        main_page()
    elif st.session_state.current_page == '분석':
        analysis_page()
    elif st.session_state.current_page == '내 프로필':
        profile_page()
    elif st.session_state.current_page == '이력':
        history_page()
    elif st.session_state.current_page == '고객지원':
        support_page()

if __name__ == "__main__":
    main()
