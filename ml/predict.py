import pandas as pd
import joblib
import shap
from .preprocessing import TeamFeatureGenerator

class SynergyPredictor:
    def __init__(self, model_path):
        try:
            model_data = joblib.load(model_path)
            self.model = model_data['model']
            self.trained_columns = model_data['trained_columns']
            # .get()을 사용하여 'shap_explainer' 키가 없어도 오류 없이 안전하게 로드
            self.shap_explainer = model_data.get('shap_explainer')
            
            print(f"모델 로드 완료: {type(self.model)}")
            print(f"훈련된 컬럼 수: {len(self.trained_columns)}")
            print(f"SHAP Explainer 타입: {type(self.shap_explainer) if self.shap_explainer else 'None'}")
            
            if self.shap_explainer:
                print("모델과 SHAP Explainer를 성공적으로 불러왔습니다.")
            else:
                print("모델을 성공적으로 불러왔습니다. (SHAP Explainer는 포함되지 않음)")

            self.feature_generator = TeamFeatureGenerator(
                role_skill_matrix_path='data/role_skill_matching_matrix.csv',
                skill_contest_matrix_path='data/updated_skill_matrix.csv',
                role_contest_matrix_path='data/updated_role_matrix.csv'
            )
            print("전처리기 초기화 완료.")
        except Exception as e:
            print(f"오류: 초기화 중 문제가 발생했습니다. {e}")
            self.model = None

    def predict_and_explain(self, team_data_list, filtering_id):
        if not self.model:
            raise RuntimeError("모델이 로드되지 않았습니다.")

        # 1. 팀 벡터 생성
        team_df = pd.DataFrame(team_data_list)
        team_size = len(team_df)  # 팀 크기 저장
        team_vector = self.feature_generator.create_team_vector(team_df, filtering_id)
        predict_df = pd.DataFrame([team_vector])[self.trained_columns]
        
        print(f"예측용 데이터 형태: {predict_df.shape}")
        print(f"예측용 데이터 컬럼: {list(predict_df.columns)}")
        print(f"팀 크기: {team_size}명")

        # 2. 시너지 점수(수상 확률) 예측
        prediction_proba = self.model.predict_proba(predict_df)[:, 1]
        
        # 팀 크기를 고려한 확률 보정
        calibrated_prob = self._calibrate_probability(prediction_proba[0], team_size)
        synergy_score = round(calibrated_prob * 100, 2)
        
        print(f"원본 예측 확률: {prediction_proba[0]:.4f}")
        print(f"보정된 확률: {calibrated_prob:.4f}")
        print(f"시너지 점수: {synergy_score}%")

        # 3. SHAP 분석 (Explainer가 있는 경우에만)
        if self.shap_explainer:
            try:
                print("SHAP 분석 시작...")
                shap_values = self.shap_explainer.shap_values(predict_df)
                print(f"SHAP 값 형태: {type(shap_values)}")
                
                if isinstance(shap_values, list):
                    # 이진 분류의 경우 SHAP 값이 리스트로 반환됨
                    shap_values = shap_values[1][0]  # 양성 클래스(1)에 대한 SHAP 값
                else:
                    shap_values = shap_values[0]  # 단일 배열인 경우
                
                print(f"SHAP 값 개수: {len(shap_values)}")
                
                # 4. 피처별 기여도 데이터 생성 및 정렬
                contributions = []
                for feature, shap_val, feature_val in zip(predict_df.columns, shap_values, predict_df.iloc[0]):
                    contributions.append({
                        "feature": feature,
                        "value": round(feature_val, 2),
                        "contribution": round(shap_val, 4)
                    })
                contributions.sort(key=lambda x: x['contribution'], reverse=True)

                # 5. SHAP 분석 결과
                expected_value = self.shap_explainer.expected_value
                if isinstance(expected_value, list):
                    baseline = expected_value[1]  # 양성 클래스의 expected value
                else:
                    baseline = expected_value
                
                # 팀 크기에 따라 bad_points 구성
                good_points = contributions[:2]
                
                if team_size <= 3:
                    # 팀원 수 부족 문제를 가장 큰 문제로 추가
                    team_size_issue = self._create_team_size_issue(team_size)
                    bad_points = [team_size_issue] + contributions[-1:]  # 팀원 수 부족 + 가장 작은 값 하나
                else:
                    bad_points = contributions[-2:]  # 가장 작은 값 두 개
                
                explanation_data = {
                    "baseline": round(baseline, 4),
                    "good_points": good_points,
                    "bad_points": bad_points
                }
                print("SHAP 분석 완료!")
            except Exception as e:
                print(f"SHAP 분석 중 오류 발생: {e}")
                explanation_data = self._create_fallback_explanation(predict_df, team_size)
        else:
            # SHAP Explainer가 없는 경우 fallback
            print("SHAP Explainer가 없어 fallback 설명을 사용합니다.")
            explanation_data = self._create_fallback_explanation(predict_df, team_size)
        
        final_result = {
            "synergy_score": synergy_score,
            "explanation": explanation_data
        }
        return final_result

    def _calibrate_probability(self, raw_prob, team_size=None):
        """예측 확률을 보정하여 더 현실적인 값으로 조정"""
        if team_size == 2:
            # 2명 팀은 강한 보정
            if raw_prob > 0.7:
                calibrated = 0.7 + (raw_prob - 0.7) * 0.3  # 70% 이상은 30%로 압축
            else:
                calibrated = raw_prob * 0.7 # 전체적으로 30% 감소
            calibrated = min(calibrated, 0.4)  # 최대 40%로 제한
            
        elif team_size == 3:
            # 3명 팀은 중간 보정
            if raw_prob > 0.5:
                calibrated = 0.5 + (raw_prob - 0.5) * 0.6  # 50% 이상은 60%로 압축
            else:
                calibrated = raw_prob * 0.8  # 전체적으로 20% 감소
            calibrated = min(calibrated, 0.55)  # 최대 70%로 제한
            
        else:
            # 4명 이상 팀은 기존 보정
            if raw_prob > 0.5:
                calibrated = 0.5 + (raw_prob - 0.5) * 0.7
            else:
                calibrated = raw_prob
            calibrated = min(calibrated, 0.85)
        
        return calibrated

    def _create_team_size_issue(self, team_size):
        """팀원 수 부족 문제를 나타내는 bad_point 생성"""
        if team_size == 1:
            return {
                "feature": "team_size_limitation",
                "value": 1,
                "contribution": -0.5  # 1명 팀은 매우 큰 페널티
            }
        elif team_size == 2:
            return {
                "feature": "team_size_limitation", 
                "value": 2,
                "contribution": -0.5  # 2명 팀은 큰 페널티
            }
        else:  # team_size == 3
            return {
                "feature": "team_size_limitation",
                "value": 3, 
                "contribution": -0.5  # 3명 팀은 중간 페널티
            }

    def _create_fallback_explanation(self, predict_df, team_size):
        """SHAP Explainer가 없을 때 사용하는 fallback 설명"""
        # 피처 값들을 기반으로 간단한 분석 제공
        feature_values = predict_df.iloc[0]
        
        # 값이 높은 순서로 정렬
        sorted_features = sorted(
            [(col, val) for col, val in feature_values.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        good_points = [
            {"feature": col, "value": round(val, 2), "contribution": round(val/100, 4)}
            for col, val in sorted_features[:2]
        ]
        
        # 팀 크기에 따라 bad_points 구성
        if team_size <= 3:
            # 팀원 수 부족 문제를 가장 큰 문제로 추가
            team_size_issue = self._create_team_size_issue(team_size)
            bad_points = [team_size_issue] + [
                {"feature": col, "value": round(val, 2), "contribution": round(val/100, 4)}
                for col, val in sorted_features[-1:]  # 가장 작은 값 하나만
            ]
        else:
            bad_points = [
                {"feature": col, "value": round(val, 2), "contribution": round(val/100, 4)}
                for col, val in sorted_features[-2:]  # 가장 작은 값 두 개
            ]
        
        return {
            "baseline": 0.5,  # 기본값
            "good_points": good_points,
            "bad_points": bad_points
        }
