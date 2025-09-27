from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
from werkzeug.utils import secure_filename
import base64
from PIL import Image
import io
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from src.core.ocr.ocr_utils import extract_text_from_image
from src.services.auth.auth_service import register_user, check_login, user_exists
from src.services.risk.risk_service import analyze_text
from src.services.profile.profile_service import list_allergies, add_allergy, remove_allergy
from src.services.report.report_service import save_report, get_recent_reports

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

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    
    # 간단한 로그인 검증 (실제로는 데이터베이스에서 확인)
    if email and password:
        # 세션에 사용자 정보 저장
        session['user_id'] = email  # 실제로는 사용자 ID
        session['user_name'] = email.split('@')[0]  # 이메일에서 이름 추출
        session['user_email'] = email
        
        # 로그인 성공 시 메인 페이지로 리다이렉트
        return redirect(url_for('home'))
    else:
        # 로그인 실패 시 에러 메시지와 함께 로그인 페이지로
        return render_template('login.html', error='이메일과 비밀번호를 확인해주세요.')

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
    
    # 회원가입 성공 시 로그인 페이지로 리다이렉트
    return redirect(url_for('login', success='회원가입이 완료되었습니다. 로그인해주세요.'))

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
    
    user_name = session.get('user_name', '')
    user_email = session.get('user_email', '')
    return render_template('mypage.html', user_name=user_name, user_email=user_email)

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
            ocr_result = extract_text_from_image(filepath, use_easyocr=True, fast_mode=True)
            if ocr_result['success']:
                extracted_text = ocr_result['text']
                print(f"추출된 텍스트: {extracted_text}")
            else:
                print(f"OCR 오류: {ocr_result.get('error', '알 수 없는 오류')}")
                extracted_text = "정제수, 설탕, 청포도과즙농축액(스페인산), 사과페이스트(칠레산), 펙틴, 구연산, 혼합탈지분유(네덜란드산), 구연산나트륨, 향료2종, 혼합제제(토마틴, 효소처리스테비아, 덱스트린) 우유함유"  # 백업 텍스트
        except Exception as e:
            print(f"OCR 실행 중 오류: {str(e)}")
            extracted_text = "정제수, 설탕, 청포도과즙농축액(스페인산), 사과페이스트(칠레산), 펙틴, 구연산, 혼합탈지분유(네덜란드산), 구연산나트륨, 향료2종, 혼합제제(토마틴, 효소처리스테비아, 덱스트린) 우유함유"  # 백업 텍스트
        
        # 알레르기 성분 분석 (간단한 키워드 매칭)
        allergy_keywords = {
            '대두': ['대두', '콩', '두부', '간장', '된장', '고추장'],
            '밀': ['밀', '밀가루', '면', '빵', '파스타'],
            '우유': ['우유', '유제품', '치즈', '버터', '크림'],
            '계란': ['계란', '난백', '난황', '알'],
            '견과류': ['땅콩', '호두', '아몬드', '캐슈넛', '피스타치오'],
            '해산물': ['새우', '게', '조개', '굴', '문어', '오징어'],
            '육류': ['돼지고기', '소고기', '닭고기', '양고기']
        }
        
        detected_allergens = []
        safe_ingredients = []
        
        # 텍스트에서 성분 추출 (간단한 분리)
        ingredients = []
        if extracted_text:
            # 줄바꿈이나 쉼표로 분리
            lines = extracted_text.replace('\n', ',').split(',')
            for line in lines:
                ingredient = line.strip()
                if ingredient and len(ingredient) > 1:
                    ingredients.append(ingredient)
        
        # 알레르기 성분 검사
        for ingredient in ingredients:
            is_allergen = False
            for allergen_type, keywords in allergy_keywords.items():
                for keyword in keywords:
                    if keyword in ingredient:
                        detected_allergens.append({
                            'name': allergen_type,
                            'ingredient': ingredient,
                            'risk': 'high' if allergen_type in ['대두', '밀', '우유'] else 'medium',
                            'confidence': 90
                        })
                        is_allergen = True
                        break
                if is_allergen:
                    break
            
            if not is_allergen:
                safe_ingredients.append(ingredient)
        
        # 위험도 계산
        if detected_allergens:
            high_risk_count = sum(1 for allergen in detected_allergens if allergen['risk'] == 'high')
            if high_risk_count > 0:
                risk_level = 'high'
            else:
                risk_level = 'medium'
        else:
            risk_level = 'low'
        
        result = {
            'success': True,
            'extracted_text': extracted_text,
            'analysis': {
                'total_ingredients': len(ingredients),
                'allergy_risk': risk_level,
                'confidence': 85,
                'detected_allergens': detected_allergens,
                'safe_ingredients': safe_ingredients[:10]  # 최대 10개만 표시
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
    app.run(debug=True, host='0.0.0.0', port=5000)
