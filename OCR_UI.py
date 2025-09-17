# 성분표 분석 페이지 
#UI
#이미지 업로드와 카메라 촬영
from PIL import Image
import streamlit as st
from ocr_utils import ocr_image_with_opencv   



def analysis_page(detect_allergens, calculate_risk_level, display_risk_level, save_analysis_result):
    st.markdown('<div class="sub-header">🔍 성분표 분석</div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["이미지 업로드", "카메라 촬영"])
    image = None

    # ---------------------------
    # 업로드 탭
    # ---------------------------
    with tab1:
        uploaded_file = st.file_uploader(
            "성분표 이미지를 업로드하세요",
            type=['png', 'jpg', 'jpeg'],
            help="식품 성분표가 명확하게 보이는 이미지를 업로드해주세요."
        )
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="성분표 이미지", use_column_width=True)
            analyze_btn = st.button("🔍 성분 분석 시작", key="analyze_upload")
            if analyze_btn:
                with st.spinner("이미지를 분석 중입니다..."):
                    ocr_text = ocr_image_with_opencv(image, lang='kor+eng')
                    detected_allergens = detect_allergens(ocr_text)
                    risk_level = calculate_risk_level(detected_allergens)
                    
                    # 결과 표시
                    st.success("분석이 완료되었습니다!")
                    st.subheader("📝 인식된 텍스트")
                    st.text_area("", value=ocr_text, height=250, disabled=True)
                    st.subheader("🚦 위험도 분석")
                    display_risk_level(risk_level)
                    if detected_allergens:
                        st.subheader("⚠️ 탐지된 알레르겐")
                        for allergen in detected_allergens:
                            st.warning(f"• {allergen}")
                    else:
                        st.success("✅ 등록된 알레르겐이 탐지되지 않았습니다.")

                    # 결과 저장
                    image_name = uploaded_file.name
                    save_analysis_result(image_name, ocr_text, detected_allergens, risk_level)

    # ---------------------------
    # 카메라 탭
    # ---------------------------
    with tab2:
        camera_image = st.camera_input("카메라로 촬영하기")
        if camera_image is not None:
            image = Image.open(camera_image)
            st.image(image, caption="성분표 이미지", use_column_width=True)
            analyze_btn = st.button("🔍 성분 분석 시작", key="analyze_camera")
            if analyze_btn:
                with st.spinner("이미지를 분석 중입니다..."):
                    ocr_text = ocr_image_with_opencv(image, lang='kor+eng')
                    detected_allergens = detect_allergens(ocr_text)
                    risk_level = calculate_risk_level(detected_allergens)
                    
                    # 결과 표시
                    st.success("분석이 완료되었습니다!")
                    st.subheader("📝 인식된 텍스트")
                    st.text_area("", value=ocr_text, height=150, disabled=True)
                    st.subheader("🚦 위험도 분석")
                    display_risk_level(risk_level)
                    if detected_allergens:
                        st.subheader("⚠️ 탐지된 알레르겐")
                        for allergen in detected_allergens:
                            st.warning(f"• {allergen}")
                    else:
                        st.success("✅ 등록된 알레르겐이 탐지되지 않았습니다.")

                    # 결과 저장
                    image_name = "촬영이미지"
                    save_analysis_result(image_name, ocr_text, detected_allergens, risk_level)
