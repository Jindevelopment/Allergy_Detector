"""
바코드 서비스 모듈
바코드 번호를 통해 제품 정보를 조회하고 알레르기 성분을 분석합니다.
"""

import requests
import json
import os
from typing import Dict, List, Optional

class BarcodeService:
    """바코드 정보 조회 및 분석 서비스"""
    
    def __init__(self):
        # 실제 바코드 API 키 (환경변수에서 가져오거나 기본값 사용)
        self.api_key = os.getenv('BARCODE_API_KEY', 'demo_key')
        self.base_url = "https://api.upcitemdb.com/prod/trial/lookup"
        
        # 샘플 바코드 데이터 로드 (외부 JSON 파일에서)
        self.sample_products = self._load_sample_products()
    
    def _load_sample_products(self) -> Dict:
        """JSON 파일에서 샘플 제품 데이터 로드"""
        try:
            # 프로젝트 루트 기준으로 data 폴더 경로 설정
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_file = os.path.join(current_dir, "..", "..", "data", "sample_products.json")
            
            with open(data_file, 'r', encoding='utf-8') as f:
                sample_products = json.load(f)
                print(f"✅ 샘플 제품 데이터 로드 완료: {len(sample_products)}개 제품")
                return sample_products
        except FileNotFoundError:
            print("⚠️ 샘플 제품 데이터 파일을 찾을 수 없습니다. 빈 딕셔너리를 사용합니다.")
            return {}
        except json.JSONDecodeError as e:
            print(f"⚠️ 샘플 제품 데이터 JSON 파싱 오류: {e}")
            return {}
        except Exception as e:
            print(f"⚠️ 샘플 제품 데이터 로드 오류: {e}")
            return {}
    
    def add_sample_product(self, barcode: str, product_info: Dict) -> bool:
        """샘플 제품 데이터에 새 제품 추가"""
        try:
            # 메모리 데이터에 추가
            self.sample_products[barcode] = product_info
            
            # JSON 파일에 저장
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_file = os.path.join(current_dir, "..", "..", "data", "sample_products.json")
            
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(self.sample_products, f, ensure_ascii=False, indent=4)
            
            print(f"✅ 새 제품 추가 완료: {product_info.get('product_name', 'Unknown')} ({barcode})")
            return True
        except Exception as e:
            print(f"⚠️ 제품 추가 오류: {e}")
            return False
    
    def get_product_info(self, barcode: str) -> Dict:
        """
        바코드 번호로 제품 정보 조회
        
        Args:
            barcode (str): 바코드 번호
            
        Returns:
            Dict: 제품 정보 (제품명, 성분, 알레르기 성분 등)
        """
        try:
            # 먼저 샘플 데이터에서 확인
            if barcode in self.sample_products:
                return self.sample_products[barcode]
            
            # 실제 API 호출 (API 키가 있는 경우)
            if self.api_key != 'demo_key':
                return self._fetch_from_api(barcode)
            
            # API가 없으면 기본 응답
            return self._get_default_product_info(barcode)
            
        except Exception as e:
            print(f"바코드 정보 조회 오류: {e}")
            return self._get_default_product_info(barcode)
    
    def _fetch_from_api(self, barcode: str) -> Dict:
        """실제 바코드 API에서 정보 조회"""
        try:
            response = requests.get(
                f"{self.base_url}?upc={barcode}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    item = data['items'][0]
                    return {
                        "product_name": item.get('title', '제품명 정보 없음'),
                        "ingredients": self._extract_ingredients_from_description(item.get('description', '')),
                        "allergens": self._extract_allergens_from_description(item.get('description', '')),
                        "brand": item.get('brand', '브랜드 정보 없음'),
                        "category": item.get('category', '카테고리 정보 없음')
                    }
            
            return self._get_default_product_info(barcode)
            
        except Exception as e:
            print(f"API 호출 오류: {e}")
            return self._get_default_product_info(barcode)
    
    def _extract_ingredients_from_description(self, description: str) -> List[str]:
        """설명에서 성분 추출"""
        # 간단한 성분 추출 로직
        common_ingredients = [
            "면", "소고기", "돼지고기", "닭고기", "참치", "연어", "새우", "게",
            "밀가루", "대두", "우유", "계란", "MSG", "향신료", "식용유", 
            "마늘", "파", "고추", "소금", "설탕", "코코아", "레시틴", "바닐라"
        ]
        
        found_ingredients = []
        description_lower = description.lower()
        
        for ingredient in common_ingredients:
            if ingredient in description_lower:
                found_ingredients.append(ingredient)
        
        return found_ingredients if found_ingredients else ["성분 정보 없음"]
    
    def _extract_allergens_from_description(self, description: str) -> List[str]:
        """설명에서 알레르기 성분 추출"""
        allergen_keywords = [
            "밀가루", "밀", "대두", "콩", "우유", "계란", "난류", "땅콩", "메밀",
            "고등어", "게", "새우", "돼지고기", "복숭아", "토마토"
        ]
        
        found_allergens = []
        description_lower = description.lower()
        
        for allergen in allergen_keywords:
            if allergen in description_lower:
                found_allergens.append(allergen)
        
        return found_allergens
    
    def _get_default_product_info(self, barcode: str) -> Dict:
        """기본 제품 정보 반환 (바코드 정보를 찾을 수 없을 때)"""
        return {
            "product_name": f"바코드 {barcode} 제품",
            "ingredients": ["성분 정보 없음"],
            "allergens": [],
            "brand": "브랜드 정보 없음",
            "category": "카테고리 정보 없음",
            "note": "바코드 정보를 찾을 수 없습니다. 수동으로 성분을 확인해주세요."
        }
    
    def analyze_barcode_allergies(self, barcode: str, user_allergies: List[str]) -> Dict:
        """
        바코드 제품의 알레르기 분석
        
        Args:
            barcode (str): 바코드 번호
            user_allergies (List[str]): 사용자 알레르기 목록
            
        Returns:
            Dict: 알레르기 분석 결과
        """
        # 제품 정보 조회
        product_info = self.get_product_info(barcode)
        
        # 알레르기 분석
        detected_allergens = product_info.get('allergens', [])
        ingredients = product_info.get('ingredients', [])
        
        # 사용자 알레르기와 매칭
        user_specific_allergens = []
        if user_allergies and detected_allergens:
            user_specific_allergens = list(set(detected_allergens) & set(user_allergies))
        
        # 위험도 계산
        risk_score = self._calculate_risk_score(detected_allergens, user_specific_allergens)
        risk_level = self._get_risk_level(risk_score)
        
        # 안전한 성분 (알레르기 성분이 아닌 것들)
        safe_ingredients = [ing for ing in ingredients if ing not in detected_allergens]
        
        return {
            "barcode_info": product_info,
            "analysis": {
                "detected_allergens": detected_allergens,
                "user_specific_allergens": user_specific_allergens,
                "safe_ingredients": safe_ingredients,
                "total_ingredients_found": len(ingredients),
                "user_matched_count": len(user_specific_allergens),
                "risk_score": risk_score,
                "allergy_risk": risk_level,
                "risk_description": self._get_risk_description(risk_level),
                "recommendations": self._get_recommendations(risk_level, user_specific_allergens)
            }
        }
    
    def _calculate_risk_score(self, detected_allergens: List[str], user_specific_allergens: List[str]) -> int:
        """위험도 점수 계산"""
        base_score = len(detected_allergens) * 2  # 기본 점수
        
        # 사용자 알레르기와 매칭되면 추가 점수
        user_match_score = len(user_specific_allergens) * 5
        
        # 고위험 알레르기 성분 확인
        high_risk_allergens = ['대두', '밀', '우유', '계란', '땅콩']
        high_risk_count = sum(1 for allergen in detected_allergens if allergen in high_risk_allergens)
        high_risk_score = high_risk_count * 3
        
        total_score = base_score + user_match_score + high_risk_score
        return min(total_score, 10)  # 최대 10점
    
    def _get_risk_level(self, risk_score: int) -> str:
        """위험도 레벨 결정"""
        if risk_score >= 8:
            return 'very_high'
        elif risk_score >= 6:
            return 'high'
        elif risk_score >= 4:
            return 'medium'
        elif risk_score >= 2:
            return 'low'
        else:
            return 'very_low'
    
    def _get_risk_description(self, risk_level: str) -> str:
        """위험도 설명"""
        descriptions = {
            'very_low': '매우 낮음 - 알레르기 성분이 감지되지 않았습니다.',
            'low': '낮음 - 일부 알레르기 성분이 있지만 위험도가 낮습니다.',
            'medium': '보통 - 알레르기 성분이 감지되었습니다.',
            'high': '높음 - 주요 알레르기 성분이 감지되었습니다.',
            'very_high': '매우 높음 - 다수의 주요 알레르기 성분이 감지되었습니다.'
        }
        return descriptions.get(risk_level, '알 수 없음')
    
    def _get_recommendations(self, risk_level: str, user_specific_allergens: List[str]) -> List[str]:
        """권장사항 생성"""
        recommendations = []
        
        if risk_level in ['high', 'very_high']:
            recommendations.append("🚨 이 제품은 섭취하지 마세요!")
            recommendations.append("의사와 상담하여 알레르기 반응 대비책을 준비하세요.")
        elif risk_level == 'medium':
            recommendations.append("⚠️ 주의해서 섭취하세요.")
            recommendations.append("알레르기 반응이 있다면 즉시 섭취를 중단하세요.")
        elif risk_level == 'low':
            recommendations.append("💡 소량으로 테스트해보세요.")
            recommendations.append("알레르기 반응을 주의 깊게 관찰하세요.")
        else:
            recommendations.append("✅ 안전하게 섭취할 수 있습니다.")
        
        if user_specific_allergens:
            recommendations.append(f"감지된 사용자 알레르기 성분: {', '.join(user_specific_allergens)}")
        
        return recommendations

# 전역 인스턴스
barcode_service = BarcodeService()
