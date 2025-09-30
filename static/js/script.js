// 전역 변수
let selectedAllergies = [];
let uploadedImageData = null;
let uploadedFilename = null;

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    
    // 로그인된 사용자의 경우 저장된 알레르기 정보 로드
    loadUserAllergiesOnPageLoad();
});

// 이벤트 리스너 초기화
function initializeEventListeners() {
    // 파일 입력 이벤트
    document.getElementById('file-input').addEventListener('change', handleFileUpload);
    
    // 드래그 앤 드롭 이벤트
    const uploadArea = document.getElementById('upload-area');
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
}

// 파일 업로드 처리
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        processFile(file);
    }
}

// 드래그 오버 처리
function handleDragOver(event) {
    event.preventDefault();
    event.currentTarget.style.borderColor = '#1890ff';
    event.currentTarget.style.background = '#f6ffed';
}

// 드래그 리브 처리
function handleDragLeave(event) {
    event.preventDefault();
    event.currentTarget.style.borderColor = '#d9d9d9';
    event.currentTarget.style.background = 'white';
}

// 드롭 처리
function handleDrop(event) {
    event.preventDefault();
    event.currentTarget.style.borderColor = '#d9d9d9';
    event.currentTarget.style.background = 'white';
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

// 파일 처리
function processFile(file) {
    if (!file.type.startsWith('image/')) {
        showNotification('이미지 파일만 업로드 가능합니다.', 'error');
        return;
    }
    
    // 로딩 표시
    showLoadingOverlay();
    
    // FormData 생성하여 서버에 업로드
    const formData = new FormData();
    formData.append('file', file);
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('Upload response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Upload response data:', data);
        hideLoadingOverlay();
        if (data.success === true) {
            uploadedImageData = `data:image/jpeg;base64,${data.image_data}`;
            uploadedFilename = data.filename;
            displayUploadedImage(uploadedImageData);
            showNotification('파일이 성공적으로 업로드되었습니다!', 'success');
        } else {
            console.error('Upload failed:', data);
            showNotification('파일 업로드 중 오류가 발생했습니다: ' + (data.error || '알 수 없는 오류'), 'error');
        }
    })
    .catch(error => {
        hideLoadingOverlay();
        console.error('Upload error:', error);
        showNotification('파일 업로드 중 오류가 발생했습니다.', 'error');
    });
}

// 업로드된 이미지 표시
function displayUploadedImage(imageData) {
    const previewImage = document.getElementById('preview-image');
    const uploadedImageDiv = document.getElementById('uploaded-image');
    
    previewImage.src = imageData;
    uploadedImageDiv.style.display = 'block';
    
    // 업로드 영역과 버튼들 완전히 숨기기
    document.getElementById('upload-area').style.display = 'none';
    document.getElementById('upload-buttons').style.display = 'none';
}

// 재업로드 함수
function resetUpload() {
    // 전역 변수 초기화
    uploadedImageData = null;
    uploadedFilename = null;
    
    // 업로드된 이미지 영역 숨기기
    document.getElementById('uploaded-image').style.display = 'none';
    
    // 업로드 영역과 버튼들 다시 표시
    document.getElementById('upload-area').style.display = 'block';
    document.getElementById('upload-buttons').style.display = 'flex';
    
    // 분석 결과 숨기기 (있다면)
    const analysisResult = document.getElementById('analysis-result');
    if (analysisResult) {
        analysisResult.style.display = 'none';
    }
    
    // 파일 입력 초기화
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.value = '';
    }
    
    showNotification('업로드를 다시 시작할 수 있습니다.', 'info');
}

// 이미지 분석
function analyzeImage() {
    if (!uploadedImageData || !uploadedFilename) {
        showNotification('먼저 이미지를 업로드해주세요.', 'error');
        return;
    }
    
    // 로딩 오버레이 표시
    showLoadingOverlay();
    
    // 서버로 이미지 전송 및 분석 요청
    fetch('/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            filename: uploadedFilename,
            user_allergies: getUserSelectedAllergies()
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoadingOverlay();
        if (data.success) {
            displayAnalysisResult(data);
        } else {
            showNotification('분석 중 오류가 발생했습니다: ' + (data.error || '알 수 없는 오류'), 'error');
        }
    })
    .catch(error => {
        hideLoadingOverlay();
        console.error('Error:', error);
        showNotification('분석 중 오류가 발생했습니다.', 'error');
    });
}

// 알레르기 프로필과 분석 결과 매칭 함수
// 사용자가 선택한 알레르기 가져오기
function getUserSelectedAllergies() {
    const selectedAllergies = [];
    
    // 선택된 알레르기 버튼들 찾기
    const allergyButtons = document.querySelectorAll('.allergy-button.selected');
    allergyButtons.forEach(button => {
        // 이모지와 줄바꿈 제거하고 깔끔하게 추출
        let allergyName = button.textContent.trim();
        allergyName = allergyName.replace(/[\n\r]/g, '').replace(/^\s+|\s+$/g, '');
        allergyName = allergyName.replace(/^[^\w가-힣]+/, ''); // 이모지 제거
        
        if (allergyName && !selectedAllergies.includes(allergyName)) {
            selectedAllergies.push(allergyName);
        }
    });
    
    // 직접 입력된 알레르기들도 추가
    const directInputs = document.querySelectorAll('.allergy-item');
    directInputs.forEach(item => {
        let allergyName = item.textContent.trim();
        allergyName = allergyName.replace(/[\n\r]/g, '').replace(/^\s+|\s+$/g, '');
        allergyName = allergyName.replace(/^[^\w가-힣]+/, ''); // 이모지 제거
        
        if (allergyName && !selectedAllergies.includes(allergyName)) {
            selectedAllergies.push(allergyName);
        }
    });
    
    console.log('정리된 사용자 알레르기:', selectedAllergies);
    return selectedAllergies;
}

function matchUserAllergies(extractedText, detectedAllergens) {
    if (selectedAllergies.length === 0) {
        return [];
    }
    
    const matchedAllergens = [];
    const text = extractedText.toLowerCase();
    
    // 사용자가 선택한 알레르기와 매칭되는지 확인
    selectedAllergies.forEach(userAllergy => {
        const allergyKeywords = getAllergyKeywords(userAllergy);
        
        // 각 알레르기 키워드가 텍스트에 포함되어 있는지 확인
        allergyKeywords.forEach(keyword => {
            if (text.includes(keyword.toLowerCase())) {
                // 이미 추가되지 않은 경우만 추가
                if (!matchedAllergens.find(item => item.name === userAllergy)) {
                    matchedAllergens.push({
                        name: userAllergy,
                        keyword: keyword,
                        confidence: 90 // 부분 일치 시 높은 신뢰도
                    });
                }
            }
        });
    });
    
    return matchedAllergens;
}

// 알레르기별 키워드 매핑
function getAllergyKeywords(allergyName) {
    const keywordMap = {
        '난류': ['난류', '계란', '달걀', '전란액', '난황액', '난백분', '난황분말', '난백분말'],
        '우유': ['우유', '전지분유', '탈지분유', '유크림', '가공유크림', '유당', '유청단백분말', '혼합분유', '연유', '버터', '마가린', '치즈', '요거트'],
        '메밀': ['메밀', '메밀가루', '메밀면'],
        '땅콩': ['땅콩', '피넛', '땅콩버터', '땅콩오일', '땅콩분말'],
        '대두': ['대두', '콩', '두부', '된장', '간장', '고추장', '콩기름', '대두단백질', '대두분말', '대두유', '식물성단백가수분해물'],
        '밀': ['밀', '밀가루', '밀글루텐', '밀전분', '밀효소', '밀단백질'],
        '고등어': ['고등어'],
        '게': ['게', '게분말'],
        '새우': ['새우', '새우분말'],
        '돼지고기': ['돼지고기', '돼지'],
        '복숭아': ['복숭아', '복숭아즙', '복숭아향료'],
        '토마토': ['토마토', '토마토페이스트', '토마토소스', '토마토추출물']
    };
    
    return keywordMap[allergyName] || [allergyName];
}

// 분석 결과 표시
function displayAnalysisResult(data) {
    const resultDiv = document.getElementById('analysis-result');
    
    // 1. 감지된 알레르기 성분 섹션 (모든 감지된 알레르기)
    const detectedAllergens = data.analysis.detected_allergens || [];
    const allergyDetectedSection = document.getElementById('allergy-detected-section');
    
    if (detectedAllergens.length > 0) {
        const allergyDetectedList = document.getElementById('allergy-detected-list');
        allergyDetectedList.innerHTML = '';
        
        detectedAllergens.forEach(allergen => {
            const allergyItem = document.createElement('div');
            allergyItem.className = 'allergy-item';
            allergyItem.innerHTML = `${allergen}`;
            allergyDetectedList.appendChild(allergyItem);
        });
        
        allergyDetectedSection.style.display = 'block';
    } else {
        const allergyDetectedList = document.getElementById('allergy-detected-list');
        allergyDetectedList.innerHTML = '<div class="no-allergy-message">✅ 감지된 알레르기 성분이 없습니다</div>';
        allergyDetectedSection.style.display = 'block';
    }
    
    // 2. 사용자 알레르기 성분 섹션 (사용자 선택 알레르기와 감지된 알레르기의 교집합)
    const userSpecificAllergens = data.analysis.user_specific_allergens || [];
    const userAllergyWarningSection = document.getElementById('user-allergy-warning-section');
    
    if (userSpecificAllergens.length > 0) {
        const userAllergyList = document.getElementById('user-allergy-list');
        userAllergyList.innerHTML = '';
        
        userSpecificAllergens.forEach(allergen => {
            const allergyItem = document.createElement('div');
            allergyItem.className = 'allergy-item high-risk-item';
            allergyItem.innerHTML = `🚨 ${allergen}`;
            userAllergyList.appendChild(allergyItem);
        });
        
        userAllergyWarningSection.style.display = 'block';
    } else {
        const userAllergyList = document.getElementById('user-allergy-list');
        userAllergyList.innerHTML = '<div class="no-allergy-message">✅ 사용자 알레르기 성분이 감지되지 않았습니다</div>';
        userAllergyWarningSection.style.display = 'block';
    }
    
    // 안전한 성분 표시
    const safeIngredientsDiv = document.getElementById('safe-ingredients');
    const safeIngredientsSection = document.getElementById('safe-ingredients-section');
    
    if (data.analysis.safe_ingredients && data.analysis.safe_ingredients.length > 0) {
        safeIngredientsDiv.innerHTML = '';
        data.analysis.safe_ingredients.forEach(ingredient => {
            const safeItem = document.createElement('span');
            safeItem.className = 'safe-ingredient';
            safeItem.textContent = ingredient;
            safeIngredientsDiv.appendChild(safeItem);
        });
        safeIngredientsSection.style.display = 'block';
    } else {
        safeIngredientsSection.style.display = 'none';
    }
    
    // 메트릭 업데이트 (risk_service.py 결과 기반)
    const totalIngredients = data.analysis.total_ingredients_found || 0;
    document.getElementById('total-ingredients').textContent = totalIngredients + '개';
    
    // 위험도 점수 표시 및 색상 설정
    const riskScore = data.analysis.risk_score || 0;
    const riskScoreElement = document.getElementById('risk-score');
    riskScoreElement.textContent = riskScore;
    
    // 점수에 따른 색상 설정
    if (riskScore >= 7) {
        riskScoreElement.className = 'metric-value high-risk';
    } else if (riskScore >= 5) {
        riskScoreElement.className = 'metric-value medium-risk';
    } else if (riskScore >= 3) {
        riskScoreElement.className = 'metric-value low-risk';
    } else {
        riskScoreElement.className = 'metric-value';
    }
    
    // 위험도 레벨 표시 및 색상 설정 (risk_service.py level 기반)
    const riskValue = document.getElementById('allergy-risk');
    const riskLevel = data.analysis.allergy_risk || 'very_low';
    
    // 위험도 레벨을 한국어로 변환
    const riskLevelMap = {
        'very_low': { text: '🟢 매우 낮음', class: 'metric-value low-risk' },
        'low': { text: '🟡 낮음', class: 'metric-value low-risk' },
        'medium': { text: '🟠 보통', class: 'metric-value medium-risk' },
        'high': { text: '🔴 높음', class: 'metric-value high-risk' },
        'very_high': { text: '🚨 매우 높음', class: 'metric-value high-risk' }
    };
    
    const riskInfo = riskLevelMap[riskLevel] || riskLevelMap['very_low'];
    riskValue.textContent = riskInfo.text;
    riskValue.className = riskInfo.class;
    
    // 결과 표시
    resultDiv.style.display = 'block';
    
    // 결과로 스크롤
    resultDiv.scrollIntoView({ behavior: 'smooth' });
    
    // 성공 알림
    showNotification('성분표 분석이 완료되었습니다!', 'success');
}

// 섹션으로 스크롤
function scrollToSection(sectionId) {
    const element = document.getElementById(sectionId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

// 사용법 모달 표시
function showUsageModal() {
    const modal = document.getElementById('usage-modal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // 배경 스크롤 방지
    }
}

// 사용법 모달 닫기
function closeUsageModal() {
    const modal = document.getElementById('usage-modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto'; // 배경 스크롤 복원
    }
}

// 로딩 오버레이 표시
function showLoadingOverlay() {
    document.getElementById('loading-overlay').style.display = 'flex';
}

// 로딩 오버레이 숨기기
function hideLoadingOverlay() {
    document.getElementById('loading-overlay').style.display = 'none';
}

// 알림 표시
function showNotification(message, type = 'info') {
    // 기존 알림 제거
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // 새 알림 생성
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // 스타일 적용
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 6px;
        color: white;
        font-weight: bold;
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    // 타입별 색상 설정
    if (type === 'success') {
        notification.style.background = '#52c41a';
    } else if (type === 'error') {
        notification.style.background = '#ff4d4f';
    } else {
        notification.style.background = '#1890ff';
    }
    
    // DOM에 추가
    document.body.appendChild(notification);
    
    // 3초 후 자동 제거
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// CSS 애니메이션 추가
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// 알레르기 정보 저장 (메인페이지용)
function saveAllergies() {
    if (selectedAllergies.length === 0) {
        showNotification('알레르기 정보를 선택해주세요.', 'error');
        return;
    }
    
    // 로그인 상태 확인
    fetch('/api/allergies', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            allergies: selectedAllergies
        })
    })
    .then(response => {
        if (response.status === 401) {
            showNotification('로그인이 필요합니다. 로그인 후 다시 시도해주세요.', 'warning');
            return;
        }
        return response.json();
    })
    .then(data => {
        if (data && data.success) {
            showNotification(data.message || '알레르기 정보가 저장되었습니다!', 'success');
        } else {
            showNotification('저장 중 오류가 발생했습니다: ' + (data.message || '알 수 없는 오류'), 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('저장 중 오류가 발생했습니다.', 'error');
    });
}

// 모달 이벤트 리스너
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('usage-modal');
    if (modal) {
        // 모달 외부 클릭 시 닫기
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeUsageModal();
            }
        });
    }
    
    // 알레르기 설정 모달 이벤트 리스너
    const allergyModal = document.getElementById('allergy-settings-modal');
    if (allergyModal) {
        // 모달 외부 클릭 시 닫기
        allergyModal.addEventListener('click', function(e) {
            if (e.target === allergyModal) {
                closeAllergySettings();
            }
        });
        
        // 알레르기 아이템 클릭 이벤트는 모달이 열릴 때 등록
    }
    
    // ESC 키로 모달 닫기
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeUsageModal();
            closeAllergySettings();
        }
    });
    
    // 커스텀 알레르기 입력 엔터키 처리
    const customInput = document.getElementById('custom-allergy-input');
    if (customInput) {
        customInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                addCustomAllergy();
            }
        });
    }
});

// 알레르기 설정 모달 열기
function openAllergySettings() {
    const modal = document.getElementById('allergy-settings-modal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        // 선택 상태 초기화
        selectedAllergies = [];
        updateSelectedAllergiesDisplay();
        
        // 기존 선택된 알레르기 로드
        loadUserAllergies();
    }
}

// 알레르기 설정 모달 닫기
function closeAllergySettings() {
    const modal = document.getElementById('allergy-settings-modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        
        // 변경사항 초기화
        resetAllergySelection();
    }
}

// 알레르기 선택 토글 (모달용)
function toggleAllergySelection(element) {
    const allergyName = element.dataset.allergy;
    console.log('=== 알레르기 토글 시작 ===');
    console.log('알레르기 이름:', allergyName);
    console.log('현재 선택된 알레르기:', selectedAllergies);
    console.log('요소 클래스:', element.className);
    
    if (!allergyName) {
        console.error('알레르기 이름이 없습니다!');
        return;
    }
    
    if (element.classList.contains('selected')) {
        // 선택 해제
        element.classList.remove('selected');
        removeFromSelectedAllergies(allergyName);
        console.log('알레르기 제거됨:', allergyName);
    } else {
        // 선택 추가
        element.classList.add('selected');
        addToSelectedAllergies(allergyName);
        console.log('알레르기 추가됨:', allergyName);
    }
    
    console.log('업데이트 후 선택된 알레르기:', selectedAllergies);
    updateSelectedAllergiesDisplay();
    console.log('=== 알레르기 토글 완료 ===');
}

// 선택된 알레르기에 추가
function addToSelectedAllergies(allergyName) {
    console.log('addToSelectedAllergies 호출:', allergyName);
    console.log('현재 배열:', selectedAllergies);
    
    if (!selectedAllergies.includes(allergyName)) {
        selectedAllergies.push(allergyName);
        console.log('추가 완료. 새로운 배열:', selectedAllergies);
    } else {
        console.log('이미 존재하는 알레르기:', allergyName);
    }
}

// 선택된 알레르기에서 제거
function removeFromSelectedAllergies(allergyName) {
    console.log('removeFromSelectedAllergies 호출:', allergyName);
    console.log('현재 배열:', selectedAllergies);
    
    const oldLength = selectedAllergies.length;
    selectedAllergies = selectedAllergies.filter(item => item !== allergyName);
    
    console.log('제거 완료. 이전 길이:', oldLength, '새로운 길이:', selectedAllergies.length);
    console.log('새로운 배열:', selectedAllergies);
}

// 커스텀 알레르기 추가
function addCustomAllergy() {
    const input = document.getElementById('custom-allergy-input');
    const allergyName = input.value.trim();
    
    if (allergyName && !selectedAllergies.includes(allergyName)) {
        selectedAllergies.push(allergyName);
        updateSelectedAllergiesDisplay();
        input.value = '';
        
        // 커스텀 알레르기 목록에 추가
        addToCustomAllergiesList(allergyName);
        
        showNotification('알레르기가 추가되었습니다!', 'success');
    } else if (allergyName) {
        showNotification('이미 추가된 알레르기입니다.', 'warning');
    }
}

// 커스텀 알레르기 목록에 추가
function addToCustomAllergiesList(allergyName) {
    const customList = document.getElementById('custom-allergies-list');
    const tag = document.createElement('div');
    tag.className = 'custom-allergy-tag';
    tag.innerHTML = `
        <span>${allergyName}</span>
        <button class="remove-btn" onclick="removeCustomAllergy('${allergyName}')">&times;</button>
    `;
    customList.appendChild(tag);
}

// 커스텀 알레르기 제거
function removeCustomAllergy(allergyName) {
    selectedAllergies = selectedAllergies.filter(item => item !== allergyName);
    updateSelectedAllergiesDisplay();
    
    // 커스텀 알레르기 목록에서 제거
    const customTags = document.querySelectorAll('.custom-allergy-tag');
    customTags.forEach(tag => {
        if (tag.textContent.includes(allergyName)) {
            tag.remove();
        }
    });
}

// 선택된 알레르기 표시 업데이트 (모달용)
function updateSelectedAllergiesDisplay() {
    console.log('updateSelectedAllergiesDisplay 호출됨');
    
    // 메인페이지와 마이페이지 모달 모두 처리
    const selectedListMain = document.getElementById('selected-list');
    const selectedListModal = document.getElementById('selected-allergies-display');
    
    const selectedList = selectedListModal || selectedListMain;
    console.log('selectedList 요소:', selectedList);
    
    if (!selectedList) {
        console.error('선택된 알레르기 표시 영역을 찾을 수 없습니다!');
        return;
    }
    
    selectedList.innerHTML = '';
    
    if (selectedAllergies.length === 0) {
        selectedList.innerHTML = '<div style="color: #999; font-style: italic;">선택된 알레르기가 없습니다</div>';
        console.log('선택된 알레르기가 없음');
        return;
    }
    
    console.log('선택된 알레르기 개수:', selectedAllergies.length);
    selectedAllergies.forEach(allergy => {
        const item = document.createElement('div');
        item.className = 'selected-item';
        
        if (selectedListModal) {
            // 마이페이지 모달용 (제거 버튼 포함)
            item.innerHTML = `
                <span>${allergy}</span>
                <button class="remove-btn" onclick="removeFromSelectedAllergies('${allergy}'); updateSelectedAllergiesDisplay(); updateAllergyItemSelection('${allergy}');">&times;</button>
            `;
        } else {
            // 메인페이지용 (단순 텍스트)
            item.textContent = allergy;
        }
        
        selectedList.appendChild(item);
        console.log('알레르기 아이템 추가:', allergy);
    });
}

// 알레르기 아이템 선택 상태 업데이트
function updateAllergyItemSelection(allergyName) {
    const allergyItems = document.querySelectorAll('.allergy-item');
    allergyItems.forEach(item => {
        if (item.dataset.allergy === allergyName) {
            item.classList.remove('selected');
        }
    });
}

// 페이지 로드 시 사용자 알레르기 정보 로드 (메인페이지용)
function loadUserAllergiesOnPageLoad() {
    console.log('페이지 로드 시 사용자 알레르기 정보 로드 시작');
    
    // 로그인 상태 확인 (세션이 있는지 확인)
    fetch('/api/allergies')
        .then(response => {
            if (response.status === 401) {
                console.log('로그인되지 않은 사용자 - 알레르기 정보 로드 건너뜀');
                return;
            }
            return response.json();
        })
        .then(data => {
            if (data && data.success && data.allergies) {
                selectedAllergies = data.allergies.map(allergy => allergy.allergen_name || allergy);
                console.log('페이지 로드 시 로드된 알레르기:', selectedAllergies);
                updateSelectedAllergiesDisplay();
                updateAllergyItemsSelection();
                
                // 사용자에게 알림 표시
                if (selectedAllergies.length > 0) {
                    showNotification(`저장된 알레르기 정보 ${selectedAllergies.length}개가 자동으로 설정되었습니다.`, 'success');
                }
            } else {
                console.log('저장된 알레르기 정보 없음');
                selectedAllergies = [];
                updateSelectedAllergiesDisplay();
            }
        })
        .catch(error => {
            console.error('페이지 로드 시 알레르기 로드 오류:', error);
            selectedAllergies = [];
            updateSelectedAllergiesDisplay();
        });
}

// 사용자 알레르기 로드 (모달용)
function loadUserAllergies() {
    console.log('loadUserAllergies 호출됨');
    fetch('/api/allergies')
        .then(response => response.json())
        .then(data => {
            console.log('API 응답:', data);
            if (data.success && data.allergies) {
                selectedAllergies = data.allergies.map(allergy => allergy.allergen_name || allergy);
                console.log('로드된 알레르기:', selectedAllergies);
                updateSelectedAllergiesDisplay();
                updateAllergyItemsSelection();
            } else {
                console.log('저장된 알레르기가 없음');
                selectedAllergies = [];
                updateSelectedAllergiesDisplay();
            }
        })
        .catch(error => {
            console.error('알레르기 로드 오류:', error);
            selectedAllergies = [];
            updateSelectedAllergiesDisplay();
        });
}

// 알레르기 아이템들 선택 상태 업데이트
function updateAllergyItemsSelection() {
    const allergyItems = document.querySelectorAll('.allergy-item');
    allergyItems.forEach(item => {
        const allergyName = item.dataset.allergy;
        if (selectedAllergies.includes(allergyName)) {
            item.classList.add('selected');
        } else {
            item.classList.remove('selected');
        }
    });
}

// 알레르기 설정 저장
function saveAllergySettings() {
    if (selectedAllergies.length === 0) {
        showNotification('최소 하나의 알레르기를 선택해주세요.', 'warning');
        return;
    }
    
    fetch('/api/allergies', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            allergies: selectedAllergies
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('알레르기 설정이 저장되었습니다!', 'success');
            closeAllergySettings();
            
            // 페이지 새로고침하여 업데이트된 정보 표시
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            showNotification('저장 중 오류가 발생했습니다: ' + (data.message || '알 수 없는 오류'), 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('저장 중 오류가 발생했습니다.', 'error');
    });
}

// 알레르기 선택 초기화
function resetAllergySelection() {
    selectedAllergies = [];
    updateSelectedAllergiesDisplay();
    
    // 알레르기 아이템 선택 해제
    const allergyItems = document.querySelectorAll('.allergy-item');
    allergyItems.forEach(item => {
        item.classList.remove('selected');
    });
    
    // 커스텀 알레르기 목록 초기화
    const customList = document.getElementById('custom-allergies-list');
    if (customList) {
        customList.innerHTML = '';
    }
    
    // 입력 필드 초기화
    const customInput = document.getElementById('custom-allergy-input');
    if (customInput) {
        customInput.value = '';
    }
}

// 카메라 촬영 기능
function openCamera() {
    // 모바일 환경에서 카메라 접근
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        // 카메라 접근 요청
        navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: 'environment' // 후면 카메라 사용
            } 
        })
        .then(function(stream) {
            // 카메라 스트림을 받았을 때의 처리
            showCameraModal(stream);
        })
        .catch(function(error) {
            console.error('카메라 접근 오류:', error);
            showNotification('카메라에 접근할 수 없습니다. 파일 선택을 사용해주세요.', 'error');
        });
    } else {
        // 카메라를 지원하지 않는 경우 파일 입력으로 대체
        showNotification('카메라를 지원하지 않는 브라우저입니다. 파일 선택을 사용해주세요.', 'warning');
        document.getElementById('file-input').click();
    }
}

// 카메라 모달 표시
function showCameraModal(stream) {
    // 카메라 모달 HTML 생성
    const modalHTML = `
        <div id="camera-modal" class="camera-modal-overlay">
            <div class="camera-modal-content">
                <div class="camera-header">
                    <h3>성분표 촬영</h3>
                    <button class="camera-close" onclick="closeCameraModal()">&times;</button>
                </div>
                <div class="camera-body">
                    <video id="camera-video" autoplay playsinline></video>
                    <div class="camera-controls">
                        <button class="btn-capture" onclick="capturePhoto()">📷 촬영</button>
                        <button class="btn-cancel" onclick="closeCameraModal()">취소</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 모달을 body에 추가
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // 비디오 요소에 스트림 연결
    const video = document.getElementById('camera-video');
    video.srcObject = stream;
    
    // 카메라 모달 스타일 추가
    addCameraModalStyles();
}

// 카메라 모달 스타일 추가
function addCameraModalStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .camera-modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .camera-modal-content {
            background: white;
            border-radius: 15px;
            width: 90%;
            max-width: 500px;
            overflow: hidden;
        }
        
        .camera-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            border-bottom: 1px solid #eee;
        }
        
        .camera-header h3 {
            margin: 0;
            color: #333;
        }
        
        .camera-close {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #999;
        }
        
        .camera-body {
            padding: 20px;
            text-align: center;
        }
        
        #camera-video {
            width: 100%;
            max-width: 400px;
            height: 300px;
            object-fit: cover;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .camera-controls {
            display: flex;
            gap: 15px;
            justify-content: center;
        }
        
        .btn-capture,
        .btn-cancel {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-capture {
            background: #4CAF50;
            color: white;
        }
        
        .btn-capture:hover {
            background: #45a049;
            transform: translateY(-2px);
        }
        
        .btn-cancel {
            background: #f44336;
            color: white;
        }
        
        .btn-cancel:hover {
            background: #da190b;
            transform: translateY(-2px);
        }
        
        @media (max-width: 480px) {
            .camera-modal-content {
                width: 95%;
                margin: 10px;
            }
            
            #camera-video {
                height: 250px;
            }
            
            .camera-controls {
                flex-direction: column;
            }
            
            .btn-capture,
            .btn-cancel {
                width: 100%;
            }
        }
    `;
    document.head.appendChild(style);
}

// 사진 촬영
function capturePhoto() {
    const video = document.getElementById('camera-video');
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    
    // 캔버스 크기를 비디오 크기에 맞춤
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // 비디오 프레임을 캔버스에 그리기
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // 캔버스를 Blob으로 변환
    canvas.toBlob(function(blob) {
        // Blob을 File 객체로 변환
        const file = new File([blob], 'camera-photo.jpg', { type: 'image/jpeg' });
        
        // 파일 업로드 처리
        handleFileUpload({ target: { files: [file] } });
        
        // 카메라 모달 닫기
        closeCameraModal();
        
        showNotification('사진이 촬영되었습니다!', 'success');
    }, 'image/jpeg', 0.8);
}

// 카메라 모달 닫기
function closeCameraModal() {
    const modal = document.getElementById('camera-modal');
    if (modal) {
        // 비디오 스트림 정지
        const video = document.getElementById('camera-video');
        if (video && video.srcObject) {
            const tracks = video.srcObject.getTracks();
            tracks.forEach(track => track.stop());
        }
        
        // 모달 제거
        modal.remove();
    }
}
