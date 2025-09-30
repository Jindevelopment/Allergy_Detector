from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import sys
import base64
from werkzeug.utils import secure_filename
from PIL import Image
import io

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.ocr_utils import extract_text_from_image

# Backend services (with fallback for missing database)
try:
    from services.auth_service import register_user, check_login, get_user
    from services.profile_service import list_allergies, add_allergy, remove_allergy
    from services.report_service import save_report, get_recent_reports
    from services.risk_service import analyze_text
    from services.db_client import init_firestore
    BACKEND_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Backend services not available: {e}")
    BACKEND_AVAILABLE = False

app = Flask(__name__, 
           template_folder=os.path.join(os.path.dirname(__file__), "..", "..", "templates"),
           static_folder=os.path.join(os.path.dirname(__file__), "..", "..", "static"))
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = 'your-secret-key-here'  # 세션을 위한 시크릿 키

# 업로드 폴더 생성
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Firestore (only if backend is available)
if BACKEND_AVAILABLE:
    try:
        # Try to initialize with service account key if available
        key_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "firestore-loader", "serviceAccountKey.json")
        if os.path.exists(key_path):
            init_firestore(key_path)
        else:
            # Fallback to environment variable
            init_firestore()
        print("✅ Firestore initialized successfully")
    except Exception as e:
        print(f"⚠️ Firestore initialization failed: {e}")
        print("Continuing without database connection...")
        BACKEND_AVAILABLE = False
else:
    print("⚠️ Running in demo mode without database connection")

# 허용된 파일 확장자
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_risk_description(risk_level):
    """위험도에 따른 상세 설명 반환"""
    descriptions = {
        'very_low': '매우 낮음 - 알레르기 성분이 감지되지 않았습니다. 안전하게 섭취할 수 있습니다.',
        'low': '낮음 - 일부 알레르기 성분이 있지만 위험도가 낮습니다. 소량으로 테스트해보세요.',
        'medium': '보통 - 알레르기 성분이 감지되었습니다. 주의가 필요합니다.',
        'high': '높음 - 주요 알레르기 성분이 감지되었습니다. 섭취를 피하세요.',
        'very_high': '매우 높음 - 다수의 주요 알레르기 성분이 감지되었습니다. 절대 섭취하지 마세요.'
    }
    return descriptions.get(risk_level, '알 수 없음')

def get_recommendations(risk_level, detected_allergens, risk_factors=None):
    """위험도와 감지된 알레르겐에 따른 상세 권장사항 반환"""
    recommendations = []
    
    if risk_level in ['high', 'very_high']:
        recommendations.append("🚨 이 제품은 섭취하지 마세요!")
        recommendations.append("의사와 상담하여 알레르기 반응 대비책을 준비하세요.")
        recommendations.append("응급 처치용 약물을 준비해두세요.")
    elif risk_level == 'medium':
        recommendations.append("⚠️ 주의해서 섭취하세요.")
        recommendations.append("알레르기 반응이 있다면 즉시 섭취를 중단하세요.")
        recommendations.append("처음 섭취하는 경우 소량으로 테스트해보세요.")
    elif risk_level == 'low':
        recommendations.append("💡 소량으로 테스트해보세요.")
        recommendations.append("알레르기 반응을 주의 깊게 관찰하세요.")
        recommendations.append("불편한 증상이 있다면 즉시 중단하세요.")
    else:
        recommendations.append("✅ 안전하게 섭취할 수 있습니다.")
        recommendations.append("하지만 알레르기 반응에 항상 주의하세요.")
    
    if detected_allergens:
        recommendations.append(f"감지된 알레르기 성분: {', '.join(detected_allergens)}")
    
    if risk_factors:
        recommendations.append(f"위험 요인: {', '.join(risk_factors)}")
    
    return recommendations

@app.route('/')
def home():
    # 로그인 상태 확인
    is_logged_in = 'user_id' in session
    user_name = session.get('user_name', '')
    return render_template('index.html', is_logged_in=is_logged_in, user_name=user_name)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        return render_template('login.html', error='이메일과 비밀번호를 입력해주세요.')
    
    if BACKEND_AVAILABLE:
        try:
            # Use backend auth service
            user_info = check_login(email, password)
            
            # 세션에 사용자 정보 저장
            session['user_id'] = user_info['user_id']
            session['user_name'] = user_info['nickname']
            session['user_email'] = email
            
            # 로그인 성공 시 메인 페이지로 리다이렉트
            return redirect(url_for('home'))
        except ValueError as e:
            # 로그인 실패 시 에러 메시지와 함께 로그인 페이지로
            return render_template('login.html', error=str(e))
        except Exception as e:
            print(f"Login error: {e}")
            return render_template('login.html', error='로그인 중 오류가 발생했습니다.')
    else:
        # 백엔드 서비스가 사용 불가능한 경우
        return render_template('login.html', error='백엔드 서비스가 사용 불가능합니다. 관리자에게 문의하세요.')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup_post():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    terms_agreed = request.form.get('terms_agreed')
    
    # 간단한 회원가입 검증
    if not all([name, email, password, confirm_password]):
        return render_template('signup.html', error='모든 필드를 입력해주세요.')
    
    if password != confirm_password:
        return render_template('signup.html', error='비밀번호가 일치하지 않습니다.')
    
    if len(password) < 8:
        return render_template('signup.html', error='비밀번호는 8자 이상이어야 합니다.')
    
    if not terms_agreed:
        return render_template('signup.html', error='이용약관에 동의해주세요.')
    
    if BACKEND_AVAILABLE:
        try:
            # Use backend auth service
            user_info = register_user(email, password, name)
            
            # 회원가입 성공 시 로그인 페이지로 리다이렉트
            return redirect(url_for('login', success='회원가입이 완료되었습니다. 로그인해주세요.'))
        except ValueError as e:
            return render_template('signup.html', error=str(e))
        except Exception as e:
            print(f"Signup error: {e}")
            return render_template('signup.html', error='회원가입 중 오류가 발생했습니다.')
    else:
        # 백엔드 서비스가 사용 불가능한 경우
        return redirect(url_for('login', success='백엔드 서비스가 사용 불가능합니다. 관리자에게 문의하세요.'))

@app.route('/logout')
def logout():
    # 세션에서 사용자 정보 제거
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    return redirect(url_for('home'))

@app.route('/mypage')
def mypage():
    # 로그인 상태 확인
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    user_name = session.get('user_name', '')
    user_email = session.get('user_email', '')
    
    if BACKEND_AVAILABLE:
        try:
            # Get user info including created_at
            user_info = get_user(user_id)
            user_created_at = user_info.get('created_at') if user_info else None
            
            # Format created_at for display
            if user_created_at:
                if hasattr(user_created_at, 'strftime'):
                    # datetime 객체인 경우
                    formatted_date = user_created_at.strftime('%Y년 %m월 %d일')
                else:
                    # 문자열인 경우
                    formatted_date = str(user_created_at)
            else:
                formatted_date = '가입일 정보 없음'
            
            # Get user allergies
            allergies = list_allergies(user_id)
            allergy_names = [allergy['allergen_name'] for allergy in allergies] if allergies else []
            
            # Get recent reports
            recent_reports = get_recent_reports(user_id, limit=5)
            
            return render_template('mypage.html', 
                                 user_name=user_name, 
                                 user_email=user_email,
                                 user_created_at=formatted_date,
                                 allergies=allergies,
                                 allergy_names=allergy_names,
                                 recent_reports=recent_reports)
        except Exception as e:
            print(f"Error loading mypage: {e}")
            return render_template('mypage.html', 
                                 user_name=user_name, 
                                 user_email=user_email,
                                 user_created_at='가입일 정보 없음',
                                 allergies=[],
                                 allergy_names=[],
                                 recent_reports=[])
    else:
        # 백엔드 서비스가 사용 불가능한 경우
        return render_template('mypage.html', 
                             user_name=user_name, 
                             user_email=user_email,
                             user_created_at='가입일 정보 없음',
                             allergies=[],
                             recent_reports=[],
                             error='백엔드 서비스가 사용 불가능합니다.')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 이미지를 base64로 인코딩하여 프론트엔드로 전송
        with open(filepath, 'rb') as img_file:
            img_data = base64.b64encode(img_file.read()).decode()
        
        return jsonify({
            'success': True,
            'filename': filename,
            'image_data': img_data
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/analyze', methods=['POST'])
def analyze_image():
    data = request.get_json()
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'error': 'No filename provided'}), 400
    
    try:
        # 파일 경로 생성
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # OCR 실행 (ocr_test.py 기반 고성능 모드)
        print(f"OCR 분석 시작: {filepath}")
        try:
            # 고성능 모드로 실행 (fast_mode=False)
            ocr_result = extract_text_from_image(filepath, use_easyocr=True, fast_mode=False)
            if ocr_result['success']:
                extracted_text = ocr_result['text']
                processing_time = ocr_result.get('processing_time')
                engine = ocr_result.get('engine')
                print(f"OCR 완료 - 엔진: {engine}, 처리시간: {processing_time}초")
                print(f"추출된 텍스트 길이: {len(extracted_text)} 문자")
                
                # OCR 텍스트 추출 완료 (성분 추출은 analyze_text에서 처리)
                print(f"OCR 텍스트 추출 완료: {len(extracted_text)} 문자")
                
            else:
                print(f"OCR 오류: {ocr_result.get('error', '알 수 없는 오류')}")
                # 백업으로 간단한 OCR 시도
                try:
                    from core.ocr_utils import ocr_image_with_opencv
                    extracted_text = ocr_image_with_opencv(filepath, "kor+eng", fast_mode=False)
                    print(f"백업 OCR로 텍스트 추출: {extracted_text}")
                except Exception as backup_error:
                    print(f"백업 OCR도 실패: {backup_error}")
                    extracted_text = "OCR 처리 실패 - 이미지를 다시 확인해주세요"
                    detected_ingredients = []
        except Exception as e:
            print(f"OCR 실행 중 오류: {str(e)}")
            extracted_text = "OCR 처리 실패 - 이미지를 다시 확인해주세요"
        
        # 사용자 알레르기 정보 수집
        user_id = session.get('user_id')
        user_allergies = []
        
        # 프론트엔드에서 전달받은 사용자 알레르기 우선 사용
        request_data = request.get_json() or {}
        frontend_user_allergies = request_data.get('user_allergies', [])
        
        if frontend_user_allergies:
            user_allergies = frontend_user_allergies
            print(f"프론트엔드에서 전달받은 사용자 알레르기: {user_allergies}")
        elif BACKEND_AVAILABLE and user_id:
            # 프론트엔드에서 알레르기가 없으면 DB에서 가져오기
            try:
                allergies = list_allergies(user_id)
                user_allergies = [allergy['allergen_name'] for allergy in allergies]
                print(f"DB에서 가져온 사용자 알레르기 프로필: {user_allergies}")
            except Exception as e:
                print(f"사용자 알레르기 프로필 로드 오류: {e}")
                user_allergies = []
        
        # 위험도 분석 실행 (analyze_text가 모든 처리를 담당)
        detected_allergens = []
        user_specific_allergens = []
        risk_score = None
        risk_level = None
        risk_factors = []
        report_id = None
        
        if extracted_text and extracted_text != "OCR 처리 실패 - 이미지를 다시 확인해주세요":
            try:
                print(f"=== 교집합 계산 디버깅 ===")
                print(f"OCR 추출 텍스트 길이: {len(extracted_text)}")
                print(f"사용자 알레르기 목록: {user_allergies}")
                print(f"사용자 알레르기 개수: {len(user_allergies) if user_allergies else 0}")
                
                # 위험도 분석 실행 (analyze_text가 모든 알레르기 감지와 사용자별 매칭을 처리)
                symptoms = ['호흡기', '피부', '소화기']  # 기본 증상
                options = {'fast_onset': True, 'free_label': False}  # 기본 옵션
                
                risk_analysis = analyze_text(
                    text=extracted_text,
                    user_allergies=user_allergies,
                    symptoms=symptoms,
                    options=options
                )
                
                print(f"=== 분석 결과 ===")
                print(f"risk_analysis 전체: {risk_analysis}")
                
                # 분석 결과 추출
                detected_allergens = risk_analysis.get('detected_allergens')  # 모든 감지된 알레르기
                user_specific_allergens = risk_analysis.get('user_specific_allergens')  # 사용자 알레르기와 매칭된 것
                risk_score = risk_analysis.get('score')
                risk_level = risk_analysis.get('level')
                risk_factors = risk_analysis.get('risk_factors')
                
                print(f"전체 감지된 알레르기: {detected_allergens}")
                print(f"사용자 알레르기와 매칭된 것: {user_specific_allergens}")
                print(f"매칭된 개수: {len(user_specific_allergens) if user_specific_allergens else 0}")
                print(f"위험도: {risk_level} (점수: {risk_score})")
                
                # 교집합 계산 테스트
                print(f"=== 교집합 테스트 ===")
                if detected_allergens and user_allergies:
                    intersection = list(set(detected_allergens) & set(user_allergies))
                    print(f"직접 교집합 계산: {intersection}")
                    print(f"직접 교집합 개수: {len(intersection)}")
                else:
                    print("교집합 계산 불가: detected_allergens 또는 user_allergies가 비어있음")
                
            except Exception as e:
                print(f"위험도 분석 오류: {e}")
                # 폴백: 간단한 알레르기 감지
                from core.ocr_utils import extract_ingredients_from_text
                detected_allergens = extract_ingredients_from_text(extracted_text)
                user_specific_allergens = []
                risk_factors = ["위험도 분석 서비스 오류로 기본 계산 사용"]
                
                # 간단한 위험도 계산
                if detected_allergens:
                    high_risk_allergens = ['대두', '밀', '우유', '계란', '밀가루', '탈지분유', '전지분유']
                    high_risk_count = sum(1 for allergen in detected_allergens if allergen in high_risk_allergens)
                    
                    if high_risk_count >= 2:
                        risk_level = 'very_high'
                        risk_score = 10
                        risk_factors.append("고위험 알레르기 성분 2개 이상 감지")
                    elif high_risk_count >= 1:
                        risk_level = 'high'
                        risk_score = 8
                        risk_factors.append("고위험 알레르기 성분 1개 감지")
                    elif len(detected_allergens) >= 3:
                        risk_level = 'medium'
                        risk_score = 6
                        risk_factors.append("알레르기 성분 3개 이상 감지")
                    else:
                        risk_level = 'low'
                        risk_score = 4
                        risk_factors.append("알레르기 성분 소량 감지")
                else:
                    risk_level = 'very_low'
                    risk_score = 0
                    risk_factors.append("알레르기 성분 미감지")
        
        # 보고서 저장 (사용자 알레르기와 매칭된 성분이 있는 경우)
        if user_specific_allergens and BACKEND_AVAILABLE and user_id:
            try:
                report_id = save_report(
                    user_id=user_id,
                    food_name=filename.split('.')[0],
                    detected_allergens=user_specific_allergens,  # 사용자 알레르기와 매칭된 것만 저장
                    symptom_check=['호흡기', '피부', '소화기'],
                    total_score=risk_score,
                    final_risk=risk_level
                )
                print(f"보고서 저장 완료: {report_id}")
            except Exception as e:
                print(f"보고서 저장 오류: {e}")
        
        # 결과 구성
        result = {
            'success': True,
            'extracted_text': extracted_text,
            'analysis': {
                'allergy_risk': risk_level,
                'risk_score': risk_score,
                'confidence': None,
                'detected_allergens': detected_allergens,  # 모든 감지된 알레르기 성분
                'user_specific_allergens': user_specific_allergens,  # 사용자 알레르기와 매칭된 성분 (주의 필요)
                'user_allergies': user_allergies,  # 사용자가 선택한 알레르기 목록
                'total_ingredients_found': len(detected_allergens),  # 전체 감지된 알레르기 성분 수
                'user_matched_count': len(user_specific_allergens),  # 사용자 알레르기와 매칭된 수
                'report_id': report_id,
                'risk_description': get_risk_description(risk_level),
                'recommendations': get_recommendations(risk_level, user_specific_allergens, risk_factors),
                'risk_factors': risk_factors,
                'ocr_engine': engine,
                'processing_time': processing_time
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"OCR 분석 오류: {str(e)}")
        return jsonify({'error': f'OCR analysis failed: {str(e)}'}), 500

@app.route('/api/allergies', methods=['GET'])
def get_user_allergies():
    """Get user's allergies"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if not BACKEND_AVAILABLE:
        return jsonify({'success': True, 'allergies': []})
    
    try:
        user_id = session.get('user_id')
        allergies = list_allergies(user_id)
        return jsonify({'success': True, 'allergies': allergies})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/allergies', methods=['POST'])
def save_user_allergies():
    """Save user's allergies (bulk update)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if not BACKEND_AVAILABLE:
        return jsonify({'success': False, 'message': '백엔드 서비스가 사용 불가능합니다.'})
    
    try:
        data = request.get_json()
        allergies = data.get('allergies', [])
        
        if not allergies:
            return jsonify({'success': False, 'message': '알레르기 정보를 입력해주세요.'})
        
        user_id = session.get('user_id')
        
        # 기존 알레르기 삭제
        existing_allergies = list_allergies(user_id)
        for allergy in existing_allergies:
            remove_allergy(user_id, allergy['id'])
        
        # 새 알레르기 추가
        for allergy_name in allergies:
            add_allergy(user_id, allergy_name, 'medium')
        
        return jsonify({
            'success': True, 
            'message': f'{len(allergies)}개의 알레르기 정보가 저장되었습니다.',
            'allergies': allergies
        })
    except Exception as e:
        print(f"알레르기 저장 오류: {e}")
        return jsonify({'success': False, 'message': f'저장 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/allergies/<allergy_id>', methods=['DELETE'])
def remove_user_allergy(allergy_id):
    """Remove an allergy from the user's profile"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if not BACKEND_AVAILABLE:
        return jsonify({'success': False, 'message': '백엔드 서비스가 사용 불가능합니다.'})
    
    try:
        user_id = session.get('user_id')
        remove_allergy(user_id, allergy_id)
        return jsonify({'success': True, 'message': '알레르기 정보가 삭제되었습니다.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports', methods=['GET'])
def get_user_reports():
    """Get user's recent reports"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if not BACKEND_AVAILABLE:
        return jsonify({'success': True, 'reports': []})
    
    try:
        user_id = session.get('user_id')
        limit = request.args.get('limit', 10, type=int)
        reports = get_recent_reports(user_id, limit)
        return jsonify({'success': True, 'reports': reports})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
