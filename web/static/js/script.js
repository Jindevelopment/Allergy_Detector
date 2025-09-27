// 전역 변수
let selectedAllergies = [];
let uploadedImageData = null;
let uploadedFilename = null;

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    
    // 프로필 페이지인 경우 알레르기 목록과 분석 기록 로드
    if (window.location.pathname === '/mypage') {
        loadUserAllergies();
        loadAnalysisHistory();
    }
});

// 이벤트 리스너 초기화
function initializeEventListeners() {
    // 알레르기 아이템 클릭 이벤트
    document.querySelectorAll('.allergy-item').forEach(item => {
        item.addEventListener('click', function() {
            toggleAllergySelection(this);
        });
    });
    
    // 파일 입력 이벤트
    document.getElementById('file-input').addEventListener('change', handleFileUpload);
    
    // 드래그 앤 드롭 이벤트
    const uploadArea = document.getElementById('upload-area');
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
}

// 알레르기 선택 토글
function toggleAllergySelection(element) {
    const allergyName = element.dataset.allergy;
    
    if (element.classList.contains('selected')) {
        element.classList.remove('selected');
        selectedAllergies = selectedAllergies.filter(item => item !== allergyName);
    } else {
        element.classList.add('selected');
        selectedAllergies.push(allergyName);
    }
    
    updateSelectedAllergiesDisplay();
}

// 선택된 알레르기 표시 업데이트
function updateSelectedAllergiesDisplay() {
    const selectedList = document.getElementById('selected-list');
    selectedList.innerHTML = '';
    
    selectedAllergies.forEach(allergy => {
        const item = document.createElement('div');
        item.className = 'selected-item';
        item.textContent = allergy;
        selectedList.appendChild(item);
    });
}

// 커스텀 알레르기 추가
function addCustomAllergy() {
    const input = document.getElementById('custom-allergy-input');
    const allergyName = input.value.trim();
    
    if (allergyName && !selectedAllergies.includes(allergyName)) {
        selectedAllergies.push(allergyName);
        updateSelectedAllergiesDisplay();
        input.value = '';
        
        // 성공 메시지 표시
        showNotification('알레르기가 추가되었습니다!', 'success');
    }
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
    .then(response => response.json())
    .then(data => {
        hideLoadingOverlay();
        if (data.success) {
            uploadedImageData = `data:image/jpeg;base64,${data.image_data}`;
            uploadedFilename = data.filename;
            displayUploadedImage(uploadedImageData);
            showNotification('파일이 성공적으로 업로드되었습니다!', 'success');
        } else {
            showNotification('파일 업로드 중 오류가 발생했습니다.', 'error');
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
            filename: uploadedFilename
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
    
    // 추출된 텍스트 표시
    const extractedTextDiv = document.getElementById('extracted-text');
    extractedTextDiv.textContent = data.extracted_text || '텍스트를 추출할 수 없었습니다.';
    
    // 알레르기 성분 표시 (새로운 데이터 구조 사용)
    const allergyListDiv = document.getElementById('allergy-list');
    const allergyWarningSection = document.getElementById('allergy-warning-section');
    
    allergyListDiv.innerHTML = ''; // 기존 내용 제거
    
    // 서버에서 전달된 알레르기 정보 사용
    const userRiskAllergens = data.analysis?.user_risk_allergens || [];
    const generalDetectedAllergens = data.analysis?.general_detected_allergens || [];
    const userAllergies = data.analysis?.user_allergies || [];
    
    if (userRiskAllergens.length > 0) {
        // 사용자에게 위험한 알레르기 성분
        userRiskAllergens.forEach(allergen => {
            const allergyItem = document.createElement('div');
            allergyItem.className = 'allergy-item high-risk';
            allergyItem.innerHTML = `
                <span class="allergy-name">${allergen.name}</span>
                <span class="risk-badge">위험!</span>
            `;
            allergyListDiv.appendChild(allergyItem);
        });
        allergyWarningSection.style.display = 'block';
    } else if (generalDetectedAllergens.length > 0) {
        // 일반적으로 감지된 알레르기 성분
        generalDetectedAllergens.forEach(allergen => {
            const allergyItem = document.createElement('div');
            allergyItem.className = 'allergy-item general-risk';
            allergyItem.innerHTML = `
                <span class="allergy-name">${allergen.name}</span>
                <span class="info-badge">주의</span>
            `;
            allergyListDiv.appendChild(allergyItem);
        });
        allergyWarningSection.style.display = 'block';
    } else if (userAllergies.length === 0 && isLoggedIn) {
        // 로그인했지만 알레르기 프로필이 설정되지 않은 경우
        allergyListDiv.innerHTML = `
            <div class="profile-message">
                <i class="fas fa-exclamation-triangle"></i>
                알레르기 프로필을 먼저 설정해주세요
            </div>
        `;
        allergyWarningSection.style.display = 'block';
    } else {
        allergyWarningSection.style.display = 'none';
    }
    
    // 안전한 성분 표시
    const safeIngredientsDiv = document.getElementById('safe-ingredients');
    const safeIngredientsSection = document.getElementById('safe-ingredients-section');
    
    safeIngredientsDiv.innerHTML = ''; // 기존 내용 제거
    
    if (data.analysis?.safe_ingredients && data.analysis.safe_ingredients.length > 0) {
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
    
    // 메트릭 업데이트 (새로운 데이터 구조 기반)
    document.getElementById('total-ingredients').textContent = (data.analysis?.total_ingredients || 0) + '개';
    document.getElementById('confidence').textContent = (data.analysis?.confidence || 0) + '%';
    
    // 위험도 표시 및 색상 설정 (새로운 데이터 구조 기반)
    const riskValue = document.getElementById('allergy-risk');
    
    if (userRiskAllergens.length > 0) {
        // 사용자에게 위험한 알레르기가 발견된 경우
        riskValue.textContent = '🔴 주의 필요';
        riskValue.className = 'metric-value high-risk';
    } else if (generalDetectedAllergens.length > 0) {
        // 일반적으로 감지된 알레르기가 있는 경우
        riskValue.textContent = '🟡 주의';
        riskValue.className = 'metric-value medium-risk';
    } else if (userAllergies.length === 0 && isLoggedIn) {
        // 알레르기 프로필이 설정되지 않은 경우
        riskValue.textContent = '❓ 프로필 미설정';
        riskValue.className = 'metric-value medium-risk';
    } else {
        // 사용자에게 안전한 경우
        riskValue.textContent = '🟢 안전';
        riskValue.className = 'metric-value low-risk';
    }
    
    // 결과 표시
    resultDiv.style.display = 'block';
    
    // 결과로 스크롤
    resultDiv.scrollIntoView({ behavior: 'smooth' });
    
    // 분석 기록 저장
    saveAnalysisResult(data);
    
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

// 알레르기 정보 저장
function saveAllergies() {
    if (selectedAllergies.length === 0) {
        showNotification('알레르기 정보를 선택해주세요.', 'error');
        return;
    }
    
    fetch('/save_allergies', {
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
            showNotification(data.message, 'success');
        } else {
            showNotification('저장 중 오류가 발생했습니다.', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('저장 중 오류가 발생했습니다.', 'error');
    });
}

// 프로필 페이지 관련 함수들
// 페이지 로드 시 알레르기 목록 로드
function loadUserAllergies() {
    fetch('/get_allergies', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayUserAllergies(data.allergies);
        } else {
            console.error('알레르기 로딩 실패:', data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// 사용자 알레르기 목록 표시
function displayUserAllergies(allergies) {
    const allergyList = document.getElementById('user-allergy-list');
    if (!allergyList) return;
    
    allergyList.innerHTML = '';
    
    if (allergies.length === 0) {
        allergyList.innerHTML = '<div class="no-allergies">등록된 알레르기 정보가 없습니다.</div>';
        return;
    }
    
    allergies.forEach(allergy => {
        const allergyItem = document.createElement('div');
        allergyItem.className = 'allergy-item';
        allergyItem.innerHTML = `
            <div class="allergy-info">
                <span class="allergy-name">${allergy.allergen_name}</span>
                <span class="allergy-severity severity-${allergy.severity}">${allergy.severity}</span>
            </div>
            <button class="btn-delete" onclick="removeAllergy('${allergy.id}')">삭제</button>
        `;
        allergyList.appendChild(allergyItem);
    });
}

// 알레르기 추가
function addAllergy() {
    const allergenSelect = document.getElementById('allergen-select');
    const severitySelect = document.getElementById('severity-select');
    
    const allergenName = allergenSelect.value;
    const severity = severitySelect.value;
    
    if (!allergenName) {
        showNotification('알레르기를 선택해주세요.', 'error');
        return;
    }
    
    fetch('/add_allergy', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            allergen_name: allergenName,
            severity: severity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            loadUserAllergies(); // 목록 새로고침
            // 선택박스 초기화
            allergenSelect.value = '';
            severitySelect.value = '주의';
        } else {
            showNotification(data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('알레르기 추가 중 오류가 발생했습니다.', 'error');
    });
}

// 알레르기 삭제
function removeAllergy(allergyId) {
    if (!confirm('정말로 이 알레르기를 삭제하시겠습니까?')) {
        return;
    }
    
    fetch('/remove_allergy', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            allergy_id: allergyId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            loadUserAllergies(); // 목록 새로고침
        } else {
            showNotification(data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('알레르기 삭제 중 오류가 발생했습니다.', 'error');
    });
}

// 분석 기록 로드
function loadAnalysisHistory() {
    fetch('/get_analysis_history', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayAnalysisHistory(data.analysis_history);
        } else {
            console.error('분석 기록 로딩 실패:', data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// 분석 기록 표시
function displayAnalysisHistory(history) {
    const historyContainer = document.getElementById('analysis-history');
    const noAnalysisMessage = document.getElementById('no-analysis-message');
    
    if (!historyContainer) return;
    
    historyContainer.innerHTML = '';
    
    if (history.length === 0) {
        historyContainer.style.display = 'none';
        noAnalysisMessage.style.display = 'block';
        return;
    }
    
    historyContainer.style.display = 'block';
    noAnalysisMessage.style.display = 'none';
    
    history.forEach(analysis => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        
        // 날짜 포맷팅
        const date = new Date(analysis.created_at);
        const formattedDate = date.toLocaleString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        // 결과 상태 클래스
        const resultClass = analysis.is_safe ? 'safe' : 'danger';
        const resultText = analysis.is_safe ? '안전' : '위험';
        
        historyItem.innerHTML = `
            <div class="history-info">
                <span class="history-date">${formattedDate}</span>
                <span class="history-product">${analysis.product_name}</span>
            </div>
            <div class="history-result ${resultClass}">${resultText}</div>
        `;
        
        historyContainer.appendChild(historyItem);
    });
}

// 분석 결과 저장
function saveAnalysisResult(data) {
    // 로그인된 사용자만 저장
    if (!document.querySelector('.user-menu')) {
        return; // 로그인하지 않은 사용자는 저장하지 않음
    }
    
    const productName = uploadedFilename ? uploadedFilename.replace(/\.(jpg|jpeg|png|gif)$/i, '') : '성분표';
    const analysisResult = {
        matched_allergens: data.analysis?.detected_allergens || [],
        total_ingredients: data.analysis?.total_ingredients || 0,
        confidence: data.analysis?.confidence || 0,
        safe_ingredients: data.analysis?.safe_ingredients || []
    };
    
    fetch('/save_analysis', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_name: productName,
            analysis_result: analysisResult,
            extracted_text: data.extracted_text || ''
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            console.log('분석 기록이 저장되었습니다:', result.message);
        } else {
            console.error('분석 기록 저장 실패:', result.error);
        }
    })
    .catch(error => {
        console.error('분석 기록 저장 중 오류:', error);
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
    
    // ESC 키로 모달 닫기
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeUsageModal();
        }
    });
});

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
