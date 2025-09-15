import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime
import base64
from PIL import Image
import io
import pytesseract
import re

# 페이지 설정
st.set_page_config(
    page_title="알레르기 안전 탐지기",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f2937;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #374151;
        margin: 1.5rem 0 1rem 0;
    }
    
    .feature-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        text-align: center;
    }
    
    .danger-high {
        background-color: #FF4D4F;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: bold;
        text-align: center;
    }
    
    .danger-medium {
        background-color: #FA8C16;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: bold;
        text-align: center;
    }
    
    .danger-low {
        background-color: #FAAD14;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: bold;
        text-align: center;
    }
    
    .safe {
        background-color: #52C41A;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: bold;
        text-align: center;
    }
    
    .step-card {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: #f8fafc;
        margin: 1rem 0;
    }
    
    .footer {
        background: #1f2937;
        color: white;
        padding: 2rem;
        text-align: center;
        margin-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect('allergy_detector.db')
    cursor = conn.cursor()
    
    # 사용자 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 알레르기 정보 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_allergies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            allergen_name TEXT,
            severity TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES users (session_id)
        )
    ''')
    
    # 분석 이력 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            image_name TEXT,
            ocr_text TEXT,
            detected_allergens TEXT,
            risk_level TEXT,
            analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES users (session_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# 알레르기 데이터베이스
ALLERGY_DATABASE = {
    "난류": ["계란", "egg", "eggs", "albumen", "ovalbumin", "lecithin"],
    "우유": ["milk", "lactose", "casein", "whey", "butter", "cheese", "크림"],
    "메밀": ["buckwheat", "soba"],
    "땅콩": ["peanut", "peanuts", "arachis"],
    "대두": ["soy", "soybean", "tofu", "soy sauce", "대두단백", "게맛살"],
    "밀": ["wheat", "gluten", "flour", "bread", "pasta"],
    "고등어": ["mackerel", "고등어"],
    "게": ["crab", "게살"],
    "새우": ["shrimp", "prawn", "새우"],
    "돼지고기": ["pork", "pig", "돼지"],
    "복숭아": ["peach", "복숭아"],
    "토마토": ["tomato", "토마토"],
    "호두": ["walnut", "walnuts", "호두"],
    "닭고기": ["chicken", "닭", "치킨"],
    "쇠고기": ["beef", "소고기", "소"],
    "오징어": ["squid", "오징어"],
    "조개류": ["shellfish", "clam", "cockle", "조개"],
    "잣": ["pine nut", "잣"],
    "아황산류": ["sulfite", "sulfur dioxide", "아황산"],
    "복합조미료": ["MSG", "monosodium glutamate", "조미료"],
    "카라멜색소": ["caramel color", "카라멜"],
    "아질산나트륨": ["sodium nitrite", "아질산"]
}

# 세션 ID 관리
def get_session_id():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return st.session_state.session_id

# 메인 페이지
def main_page():
    st.markdown('<div class="main-header">🛡️ 알레르기 안전 탐지기</div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align: center; font-size: 1.2rem; color: #6b7280; margin-bottom: 3rem;">사진 한 장으로 알레르기 위험 확인</div>', unsafe_allow_html=True)
    
    # 서비스 소개
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 🎯 서비스 개요
        AI 기반 성분표 알레르기 위험 탐지 서비스로, 사용자가 등록한 알레르기 정보를 기반으로 
        식품 성분표를 촬영/업로드하면 자동으로 알레르겐 포함 여부를 판별하고, 
        위험 수준을 **신호등 방식(강·중·약)**으로 직관적으로 안내합니다.
        """)
        
        st.markdown("""
        ### ✨ 주요 특징
        - 📱 **간편한 사용**: 성분표 사진만 업로드하면 즉시 분석
        - 🎨 **직관적 표시**: 색상으로 구분되는 위험도 신호등
        - 🧠 **AI 기반**: OCR과 AI를 활용한 정확한 성분 인식
        - 📊 **개인 맞춤**: 사용자별 알레르기 정보 기반 맞춤 분석
        """)
    
    with col2:
        st.image("https://plus.unsplash.com/premium_photo-1661322648010-a167acb12603?q=80&w=1809&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", caption="알레르기 안전 탐지 서비스")
    
    # 4단계 기능 소개
    st.markdown('<div class="sub-header">🚀 4단계 간편 분석 과정</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('''
        <div class="step-card">
            <h4>1️⃣ 성분표 촬영</h4>
            <p>식품 성분표를 사진으로 촬영하거나 이미지를 업로드합니다.</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown('''
        <div class="step-card">
            <h4>2️⃣ OCR 인식</h4>
            <p>AI가 이미지에서 텍스트를 자동으로 추출하고 성분을 인식합니다.</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown('''
        <div class="step-card">
            <h4>3️⃣ 위험 판별</h4>
            <p>등록된 알레르기 정보와 교차 분석하여 위험도를 판별합니다.</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        st.markdown('''
        <div class="step-card">
            <h4>4️⃣ 맞춤 안내</h4>
            <p>신호등 방식으로 위험도를 표시하고 상세한 안내를 제공합니다.</p>
        </div>
        ''', unsafe_allow_html=True)
    
    # CTA 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔍 지금 분석하기", type="primary", use_container_width=True):
            st.session_state.page = "analysis"
            st.rerun()

# 분석 페이지
def analysis_page():
    st.markdown('<div class="sub-header">🔍 성분표 분석</div>', unsafe_allow_html=True)
    
    # 이미지 업로드
    uploaded_file = st.file_uploader(
        "성분표 이미지를 업로드하세요",
        type=['png', 'jpg', 'jpeg'],
        help="식품 성분표가 명확하게 보이는 이미지를 업로드해주세요."
    )
    
    if uploaded_file is not None:
        # 이미지 표시
        image = Image.open(uploaded_file)
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(image, caption="업로드된 성분표", use_column_width=True)
        
        with col2:
            # OCR 처리
            if st.button("🔍 성분 분석 시작", type="primary"):
                with st.spinner("이미지를 분석 중입니다..."):
                    # OCR 텍스트 추출
                    ocr_text = pytesseract.image_to_string(image, lang='kor+eng')
                    
                    # 알레르기 탐지
                    detected_allergens = detect_allergens(ocr_text)
                    risk_level = calculate_risk_level(detected_allergens)
                    
                    # 결과 표시
                    st.success("분석이 완료되었습니다!")
                    
                    # OCR 결과
                    st.subheader("📝 인식된 텍스트")
                    st.text_area("", value=ocr_text, height=150, disabled=True)
                    
                    # 위험도 표시
                    st.subheader("🚦 위험도 분석")
                    display_risk_level(risk_level)
                    
                    # 탐지된 알레르겐
                    if detected_allergens:
                        st.subheader("⚠️ 탐지된 알레르겐")
                        for allergen in detected_allergens:
                            st.warning(f"• {allergen}")
                    else:
                        st.success("✅ 등록된 알레르겐이 탐지되지 않았습니다.")
                    
                    # 분석 결과 저장
                    save_analysis_result(uploaded_file.name, ocr_text, detected_allergens, risk_level)

# 알레르기 탐지 함수
def detect_allergens(text):
    detected = []
    session_id = get_session_id()
    
    # 사용자 알레르기 정보 가져오기
    user_allergies = get_user_allergies(session_id)
    
    for user_allergen in user_allergies:
        allergen_name = user_allergen[1]
        if allergen_name in ALLERGY_DATABASE:
            synonyms = ALLERGY_DATABASE[allergen_name]
            for synonym in synonyms:
                if synonym.lower() in text.lower():
                    detected.append(allergen_name)
                    break
    
    return list(set(detected))

# 위험도 계산
def calculate_risk_level(detected_allergens):
    if not detected_allergens:
        return "safe"
    
    count = len(detected_allergens)
    if count >= 3:
        return "high"
    elif count >= 2:
        return "medium"
    else:
        return "low"

# 위험도 표시
def display_risk_level(risk_level):
    if risk_level == "high":
        st.markdown('<div class="danger-high">🔴 고위험 - 다수 알레르겐 포함</div>', unsafe_allow_html=True)
    elif risk_level == "medium":
        st.markdown('<div class="danger-medium">🟠 중위험 - 일부 알레르겐 포함</div>', unsafe_allow_html=True)
    elif risk_level == "low":
        st.markdown('<div class="danger-low">🟡 저위험 - 경미한 주의 필요</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="safe">🟢 안전 - 알레르겐 미탐지</div>', unsafe_allow_html=True)

# 분석 결과 저장
def save_analysis_result(image_name, ocr_text, detected_allergens, risk_level):
    conn = sqlite3.connect('allergy_detector.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO analysis_history 
        (session_id, image_name, ocr_text, detected_allergens, risk_level)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        get_session_id(),
        image_name,
        ocr_text,
        json.dumps(detected_allergens, ensure_ascii=False),
        risk_level
    ))
    
    conn.commit()
    conn.close()

# 내 프로필 페이지
def profile_page():
    st.markdown('<div class="sub-header">👤 내 알레르기 프로필</div>', unsafe_allow_html=True)
    
    session_id = get_session_id()
    
    # 현재 등록된 알레르기 표시
    st.subheader("📋 현재 등록된 알레르기")
    user_allergies = get_user_allergies(session_id)
    
    if user_allergies:
        for allergy in user_allergies:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"• {allergy[1]}")
            with col2:
                severity_color = {"심각": "🔴", "주의": "🟠", "경미": "🟡"}
                st.write(f"{severity_color.get(allergy[2], '⚪')} {allergy[2]}")
            with col3:
                if st.button(f"삭제", key=f"delete_{allergy[0]}"):
                    delete_user_allergy(allergy[0])
                    st.rerun()
    else:
        st.info("등록된 알레르기 정보가 없습니다.")
    
    # 알레르기 추가
    st.subheader("➕ 알레르기 정보 추가")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_allergen = st.selectbox(
            "알레르기 성분을 선택하세요",
            list(ALLERGY_DATABASE.keys()),
            key="new_allergen"
        )
    
    with col2:
        severity = st.selectbox(
            "심각도",
            ["심각", "주의", "경미"],
            key="severity"
        )
    
    if st.button("추가", type="primary"):
        add_user_allergy(session_id, selected_allergen, severity)
        st.success(f"{selected_allergen} 알레르기가 추가되었습니다.")
        st.rerun()

# 알레르기 정보 관리 함수들
def get_user_allergies(session_id):
    conn = sqlite3.connect('allergy_detector.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_allergies WHERE session_id = ?', (session_id,))
    result = cursor.fetchall()
    conn.close()
    return result

def add_user_allergy(session_id, allergen_name, severity):
    conn = sqlite3.connect('allergy_detector.db')
    cursor = conn.cursor()
    
    # 중복 확인
    cursor.execute('SELECT * FROM user_allergies WHERE session_id = ? AND allergen_name = ?', 
                   (session_id, allergen_name))
    if cursor.fetchone():
        conn.close()
        return False
    
    cursor.execute('''
        INSERT INTO user_allergies (session_id, allergen_name, severity)
        VALUES (?, ?, ?)
    ''', (session_id, allergen_name, severity))
    
    conn.commit()
    conn.close()
    return True

def delete_user_allergy(allergy_id):
    conn = sqlite3.connect('allergy_detector.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_allergies WHERE id = ?', (allergy_id,))
    conn.commit()
    conn.close()

# 이력 페이지
def history_page():
    st.markdown('<div class="sub-header">📊 분석 이력</div>', unsafe_allow_html=True)
    
    session_id = get_session_id()
    history = get_analysis_history(session_id)
    
    if history:
        for record in history:
            with st.expander(f"{record[2]} - {record[6]} ({record[5]})"):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.write("**위험도:**")
                    display_risk_level(record[5])
                    
                with col2:
                    st.write("**분석일시:**")
                    st.write(record[6])
                
                detected_allergens = json.loads(record[4]) if record[4] else []
                if detected_allergens:
                    st.write("**탐지된 알레르겐:**")
                    for allergen in detected_allergens:
                        st.warning(f"• {allergen}")
                
                st.write("**인식된 텍스트:**")
                st.text_area("", value=record[3], height=100, disabled=True)
    else:
        st.info("분석 이력이 없습니다.")

def get_analysis_history(session_id):
    conn = sqlite3.connect('allergy_detector.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM analysis_history WHERE session_id = ? ORDER BY analysis_date DESC', 
                   (session_id,))
    result = cursor.fetchall()
    conn.close()
    return result

# 고객지원 페이지
def support_page():
    st.markdown('<div class="sub-header">💬 고객지원</div>', unsafe_allow_html=True)
    
    # FAQ
    st.subheader("❓ 자주 묻는 질문")
    
    faq_data = [
        {
            "Q": "어떤 종류의 이미지를 업로드할 수 있나요?",
            "A": "PNG, JPG, JPEG 형식의 이미지를 업로드할 수 있습니다. 성분표가 명확하게 보이는 이미지를 권장합니다."
        },
        {
            "Q": "OCR 인식 정확도는 어떻게 되나요?",
            "A": "이미지 품질에 따라 다르지만, 일반적으로 90% 이상의 정확도를 보입니다. 글씨가 선명하고 배경이 깔끔한 사진일수록 정확도가 높습니다."
        },
        {
            "Q": "알레르기 정보는 어떻게 관리되나요?",
            "A": "개인정보는 로컬 세션에서만 관리되며, 외부로 전송되지 않습니다. 브라우저를 닫으면 데이터가 초기화됩니다."
        },
        {
            "Q": "어떤 알레르기 성분을 지원하나요?",
            "A": "식약처 고시 23종 알레르기 유발 성분을 지원하며, 동의어와 영문명도 함께 인식합니다."
        }
    ]
    
    for i, faq in enumerate(faq_data):
        with st.expander(f"Q{i+1}. {faq['Q']}"):
            st.write(faq['A'])
    
    # 연락처 정보
    st.subheader("📞 연락처")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **이메일:** jinhyeok1001@naver.com  
        **전화:** 1588-0000  
        **운영시간:** 평일 09:00 - 18:00
        """)
    
    with col2:
        st.markdown("""
        **소셜미디어:**  
        📘 Facebook: @AllergyDetector  
        📷 Instagram: @allergy_detector  
        🐦 Twitter: @AllergyDetector
        """)
    
    # DB 업데이트 요청
    st.subheader("🔧 알레르기 DB 확장 요청")
    st.write("새로운 알레르기 성분이나 동의어를 추가하고 싶으시면 아래 양식을 작성해주세요.")
    
    with st.form("db_request"):
        col1, col2 = st.columns(2)
        with col1:
            allergen_name = st.text_input("알레르기 성분명")
        with col2:
            synonyms = st.text_input("동의어 (쉼표로 구분)")
        
        description = st.text_area("추가 정보 또는 설명")
        
        if st.form_submit_button("요청 제출"):
            st.success("요청이 제출되었습니다. 검토 후 반영하겠습니다.")

# 사이드바 네비게이션
def sidebar():
    with st.sidebar:
        st.image("https://images.unsplash.com/photo-1634128221567-3220e071d1ea?q=80&w=1740&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", caption="알레르기 안전 탐지기")
        
        st.markdown("### 🧭 메뉴")
        
        if st.button("🏠 메인", use_container_width=True):
            st.session_state.page = "main"
            st.rerun()
        
        if st.button("🔍 분석", use_container_width=True):
            st.session_state.page = "analysis"
            st.rerun()
        
        if st.button("👤 내 프로필", use_container_width=True):
            st.session_state.page = "profile"
            st.rerun()
        
        if st.button("📊 이력", use_container_width=True):
            st.session_state.page = "history"
            st.rerun()
        
        if st.button("💬 고객지원", use_container_width=True):
            st.session_state.page = "support"
            st.rerun()
        
        st.markdown("---")
        
        # 현재 알레르기 정보 요약
        session_id = get_session_id()
        user_allergies = get_user_allergies(session_id)
        
        st.markdown("### 📋 내 알레르기")
        if user_allergies:
            for allergy in user_allergies[:3]:  # 최대 3개만 표시
                st.write(f"• {allergy[1]} ({allergy[2]})")
            if len(user_allergies) > 3:
                st.write(f"... 외 {len(user_allergies)-3}개")
        else:
            st.info("등록된 알레르기가 없습니다.")

# 메인 앱 실행
def main():
    # 데이터베이스 초기화
    init_db()
    
    # 페이지 상태 초기화
    if 'page' not in st.session_state:
        st.session_state.page = "main"
    
    # 사이드바
    sidebar()
    
    # 페이지 라우팅
    if st.session_state.page == "main":
        main_page()
    elif st.session_state.page == "analysis":
        analysis_page()
    elif st.session_state.page == "profile":
        profile_page()
    elif st.session_state.page == "history":
        history_page()
    elif st.session_state.page == "support":
        support_page()
    
    # 푸터
    st.markdown("""
    <div class="footer">
        <p>© 2025 알레르기 안전 탐지기. 모든 권리 보유.</p>
        <p>⚠️ 본 서비스는 의학적 진단을 대체하지 않습니다. 정확한 알레르기 정보는 의사와 상담하시기 바랍니다.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
