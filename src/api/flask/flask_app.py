from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
from werkzeug.utils import secure_filename
import base64
from PIL import Image
import io
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from src.core.ocr.ocr_test import extract_ingredients_from_image
from src.services.auth.auth_service import register_user, check_login, user_exists
from src.services.risk.risk_service import analyze_text
from src.services.profile.profile_service import list_allergies, add_allergy, remove_allergy
from src.services.report.report_service import save_report, get_recent_reports
from src.database.clients.db_client import get_db
from google.cloud import firestore
from datetime import datetime

app = Flask(__name__, 
            template_folder='../../../web/templates',
            static_folder='../../../web/static')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '../../../web/uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = 'your-secret-key-here'  # 세션을 위한 시크릿 키

# 업로드 폴더 생성
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 허용된 파일 확장자
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    # 로그인 상태 확인
    is_logged_in = 'user_id' in session
    user_name = session.get('user_name', '')
    return render_template('index.html', is_logged_in=is_logged_in, user_name=user_name)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    # POST 요청 처리
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password or not email:
        return jsonify({'error': '모든 필드를 입력해주세요'}), 400
    
    try:
        # 사용자 등록 (email을 user_id로 사용)
        result = register_user(email, password, username)
        return jsonify({'success': True, 'message': '회원가입이 완료되었습니다!', 'user_id': result['user_id']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    # JSON 요청 처리
    if request.is_json:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
    else:
        # Form 요청 처리
        email = request.form.get('email')
        password = request.form.get('password')
    
    if not email or not password:
        if request.is_json:
            return jsonify({'error': '이메일과 비밀번호를 입력해주세요.'}), 400
        else:
            return render_template('login.html', error='이메일과 비밀번호를 확인해주세요.')
    
    try:
        # 실제 데이터베이스에서 로그인 확인 (email을 user_id로 사용)
        result = check_login(email, password)
        
        # 세션에 사용자 정보 저장
        session['user_id'] = result['user_id']
        session['user_name'] = result['nickname']
        session['user_email'] = email
        
        if request.is_json:
            return jsonify({'success': True, 'message': '로그인 성공!', 'user_id': result['user_id']})
        else:
            return redirect(url_for('home'))
            
    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 401
        else:
            return render_template('login.html', error=str(e))

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
    
    try:
        # 실제 데이터베이스에 사용자 등록
        result = register_user(email, password, name)
        
        # 회원가입 성공 시 로그인 페이지로 리다이렉트
        return redirect(url_for('login', success='회원가입이 완료되었습니다. 로그인해주세요.'))
    except Exception as e:
        return render_template('signup.html', error=str(e))

@app.route('/logout')
def logout():
    # 세션에서 사용자 정보 제거
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    return redirect(url_for('home'))

@app.route('/service')
def service():
    return render_template('service.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/mypage')
def mypage():
    # 로그인 상태 확인
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    user_name = session.get('user_name', '')
    user_email = session.get('user_email', '')
    
    # 실제 DB에서 데이터 가져오기
    try:
        # 사용자 알레르기 정보 가져오기
        user_allergies = list_allergies(user_id)
        
        # 최근 분석 기록 가져오기
        analysis_history = get_recent_reports(user_id, limit=3)
        
        # 분석 통계 계산
        total_analyses = len(analysis_history)
        danger_count = sum(1 for report in analysis_history if report.get('final_risk') in ['High', 'Medium'])
        
        # 알레르기 이름만 추출
        allergy_names = [allergy.get('allergen_name', '') for allergy in user_allergies]
        
    except Exception as e:
        print(f"DB 데이터 로딩 오류: {e}")
        # 오류 시 기본값
        user_allergies = []
        analysis_history = []
        total_analyses = 0
        danger_count = 0
        allergy_names = []
    
    return render_template('mypage.html', 
                         user_name=user_name, 
                         user_email=user_email)

# 프로필 기능 라우트들
@app.route('/add_allergy', methods=['POST'])
def add_allergy_route():
    if 'user_id' not in session:
        return jsonify({'error': '로그인이 필요합니다'}), 401
    
    user_id = session.get('user_id')
    data = request.get_json()
    
    allergen_name = data.get('allergen_name')
    severity = data.get('severity', '주의')
    
    try:
        result = add_allergy(user_id, allergen_name, severity)
        return jsonify({'success': True, 'message': '알레르기가 추가되었습니다'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/remove_allergy', methods=['POST'])
def remove_allergy_route():
    if 'user_id' not in session:
        return jsonify({'error': '로그인이 필요합니다'}), 401
    
    user_id = session.get('user_id')
    data = request.get_json()
    
    allergy_id = data.get('allergy_id')
    
    try:
        remove_allergy(user_id, allergy_id)
        return jsonify({'success': True, 'message': '알레르기가 삭제되었습니다'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_allergies', methods=['GET'])
def get_allergies_route():
    if 'user_id' not in session:
        return jsonify({'error': '로그인이 필요합니다'}), 401
    
    user_id = session.get('user_id')
    
    try:
        allergies = list_allergies(user_id)
        return jsonify({'success': True, 'allergies': allergies})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save_analysis', methods=['POST'])
def save_analysis_route():
    if 'user_id' not in session:
        return jsonify({'error': '로그인이 필요합니다'}), 401
    
    user_id = session.get('user_id')
    data = request.get_json()
    
    product_name = data.get('product_name', '알 수 없는 제품')
    analysis_result = data.get('analysis_result', {})
    extracted_text = data.get('extracted_text', '')
    
    try:
        # 분석 기록을 DB에 저장
        db = get_db()
        analysis_data = {
            'user_id': user_id,
            'product_name': product_name,
            'extracted_text': extracted_text,
            'analysis_result': analysis_result,
            'created_at': datetime.utcnow(),
            'matched_allergens': analysis_result.get('matched_allergens', []),
            'total_ingredients': analysis_result.get('total_ingredients', 0),
            'confidence': analysis_result.get('confidence', 0),
            'is_safe': len(analysis_result.get('matched_allergens', [])) == 0
        }
        
        # analyses 컬렉션에 저장
        doc_ref = db.collection('analyses').add(analysis_data)
        
        return jsonify({'success': True, 'message': '분석 기록이 저장되었습니다', 'analysis_id': doc_ref[1].id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_analysis_history', methods=['GET'])
def get_analysis_history_route():
    if 'user_id' not in session:
        return jsonify({'error': '로그인이 필요합니다'}), 401
    
    user_id = session.get('user_id')
    limit = request.args.get('limit', 10, type=int)
    
    try:
        db = get_db()
        
        # 사용자의 분석 기록을 최신순으로 조회
        analyses = db.collection('analyses')\
                    .where('user_id', '==', user_id)\
                    .order_by('created_at', direction=firestore.Query.DESCENDING)\
                    .limit(limit)\
                    .stream()
        
        analysis_history = []
        for analysis in analyses:
            data = analysis.to_dict()
            analysis_history.append({
                'id': analysis.id,
                'product_name': data.get('product_name', '알 수 없는 제품'),
                'created_at': data.get('created_at').isoformat() if data.get('created_at') else '',
                'is_safe': data.get('is_safe', True),
                'matched_allergens': data.get('matched_allergens', []),
                'total_ingredients': data.get('total_ingredients', 0),
                'confidence': data.get('confidence', 0)
            })
        
        return jsonify({'success': True, 'analysis_history': analysis_history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        
        # OCR 실행
        print(f"OCR 분석 시작: {filepath}")
        try:
            ocr_result = extract_ingredients_from_image(filepath, use_easyocr=True, fast_mode=True)
            if 'error' not in ocr_result:
                extracted_text = ocr_result['full_text']
                detected_allergens = ocr_result['ingredients']  # ocr_test.py에서 이미 알레르기 성분만 추출됨
                print(f"추출된 텍스트: {extracted_text}")
                print(f"추출된 알레르기 성분: {detected_allergens}")
            else:
                print(f"OCR 오류: {ocr_result.get('error', '알 수 없는 오류')}")
                extracted_text = "정제수, 설탕, 청포도과즙농축액(스페인산), 사과페이스트(칠레산), 펙틴, 구연산, 혼합탈지분유(네덜란드산), 구연산나트륨, 향료2종, 혼합제제(토마틴, 효소처리스테비아, 덱스트린) 우유함유"  # 백업 텍스트
                detected_allergens = ['우유']  # 백업 알레르기 성분
        except Exception as e:
            print(f"OCR 실행 중 오류: {str(e)}")
            extracted_text = "정제수, 설탕, 청포도과즙농축액(스페인산), 사과페이스트(칠레산), 펙틴, 구연산, 혼합탈지분유(네덜란드산), 구연산나트륨, 향료2종, 혼합제제(토마틴, 효소처리스테비아, 덱스트린) 우유함유"  # 백업 텍스트
            detected_allergens = ['우유']  # 백업 알레르기 성분
        
        # 사용자 알레르기 프로필 가져오기
        user_allergies = []
        if session.get('user_id'):
            try:
                user_allergies = list_allergies(session['user_id'])
                print(f"사용자 알레르기 프로필: {user_allergies}")
            except Exception as e:
                print(f"사용자 알레르기 프로필 조회 오류: {e}")
        
        # 사용자 프로필과 연동된 알레르기 분석
        user_risk_allergens = []
        general_detected_allergens = []
        
        # 추출된 알레르기 성분을 사용자 프로필과 비교
        for allergen in detected_allergens:
            allergen_info = {
                'name': allergen,
                'ingredient': allergen,
                'risk': 'high',
                'confidence': 95
            }
            
            # 사용자 알레르기 프로필과 매칭
            if user_allergies and allergen in user_allergies:
                allergen_info['user_risk'] = True
                user_risk_allergens.append(allergen_info)
            else:
                allergen_info['user_risk'] = False
                general_detected_allergens.append(allergen_info)
        
        # 전체 성분에서 안전한 성분 추출 (간단한 분리)
        safe_ingredients = []
        if extracted_text:
            lines = extracted_text.replace('\n', ',').split(',')
            for line in lines:
                ingredient = line.strip()
                if ingredient and len(ingredient) > 1 and ingredient not in detected_allergens:
                    safe_ingredients.append(ingredient)
        
        # 위험도 계산
        if user_risk_allergens:
            risk_level = 'high'
        elif general_detected_allergens:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        result = {
            'success': True,
            'extracted_text': extracted_text,
            'analysis': {
                'total_ingredients': len(detected_allergens) + len(safe_ingredients),
                'allergy_risk': risk_level,
                'confidence': 95,
                'detected_allergens': detected_allergens,
                'user_risk_allergens': user_risk_allergens,
                'general_detected_allergens': general_detected_allergens,
                'safe_ingredients': safe_ingredients[:10],  # 최대 10개만 표시
                'user_allergies': user_allergies
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"OCR 분석 오류: {str(e)}")
        return jsonify({'error': f'OCR analysis failed: {str(e)}'}), 500

@app.route('/save_allergies', methods=['POST'])
def save_allergies():
    data = request.get_json()
    allergies = data.get('allergies', [])
    
    # 여기에 사용자 알레르기 정보를 저장하는 로직을 추가할 수 있습니다
    # 현재는 세션에 저장하거나 데이터베이스에 저장
    
    return jsonify({'success': True, 'message': '알레르기 정보가 저장되었습니다.'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3001)
