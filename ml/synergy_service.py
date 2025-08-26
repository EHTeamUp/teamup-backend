import os
from typing import Optional
from .predict import SynergyPredictor
from .message_generator import SynergyMessageGenerator

class SynergyService:
    """
    시너지 예측 서비스 - 싱글톤 패턴으로 모델과 CSV를 한 번만 로드
    """
    _instance: Optional['SynergyService'] = None
    _predictor: Optional[SynergyPredictor] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SynergyService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._load_predictor()
    
    def _load_predictor(self):
        """모델과 CSV 파일들을 한 번만 로드"""
        try:
            # 모델 파일 경로
            model_path = os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'predictor.joblib')
            
            print("🔄 시너지 예측 모델 로딩 중...")
            self._predictor = SynergyPredictor(model_path)
            print("✅ 시너지 예측 모델 로딩 완료!")
            
        except Exception as e:
            print(f"❌ 시너지 예측 모델 로딩 실패: {e}")
            self._predictor = None
    
    @property
    def predictor(self) -> Optional[SynergyPredictor]:
        """예측기 인스턴스 반환"""
        return self._predictor
    
    def is_ready(self) -> bool:
        """모델이 준비되었는지 확인"""
        return self._predictor is not None
    
    def predict_synergy(self, team_data_list, filtering_id):
        """시너지 예측 실행"""
        if not self.is_ready():
            raise RuntimeError("시너지 예측 모델이 로드되지 않았습니다.")
        
        return self._predictor.predict_and_explain(team_data_list, filtering_id)

# 전역 인스턴스
synergy_service = SynergyService()
