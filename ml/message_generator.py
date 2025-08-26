import random
from typing import Dict, List, Any

class SynergyMessageGenerator:
    """
    머신러닝 결과를 메시지로 변환
    """
    
    def __init__(self):
        self.messages = {
            'role_skill_match_score': {
                'good': "🎯 역할과 기술이 잘 맞아떨어집니다! 프로젝트 진행이 원활할 것입니다.",
                'bad': "⚠️ 역할에 필요한 기술이 부족합니다. 기술 스택을 조금 더 보완하면 좋겠어요."
            },
            'contest_skill_relevance_score': {
                'good': "🏆 해당 공모전 카테고리에 필요한 기술을 모두 갖추고 있어요! 우승 가능성이 높습니다.",
                'bad': "🚨 해당 공모전 카테고리에 필요한 기술이 부족합니다. 기술 스택을 보완해야 해요."
            },
            'contest_role_relevance_score': {
                'good': "👥 공모전 역할 구성이 적절합니다. 최적의 팀워크를 기대할 수 있습니다.",
                'bad': "⚠️ 공모전에 필요한 역할이 부족합니다. 추가 팀원을 모집하거나 역할을 보완해보세요"
            },
            'experience_relevance_score': {
                'good': "🏅 카테고리와 유사한 공모전 경험이 충분해요. 유사한 공모전 경험이 있어 안정적인 진행이 가능해요.",
                'bad': "💡 공모전 경험이 부족해요. 카테고리와 유사한 프로젝트 경험이 거의 없어 예상치 못한 어려움이 있을 수 있습니다."
            },
            'tendency_alignment_score': {
                'good': "💫 팀원들의 성향이 조화롭게 어우러져요! 서로를 보완하며 좋은 팀워크를 만들어낼 수 있어요.",
                'bad': "⚠️ 팀원들의 성향 차이가 있어요. 정기적인 소통을 통해 서로를 이해해보세요."
            },
            'leadership_distribution_score': {
                'good': "👑 리더십 분배가 적절해요! 역할에 따른 리더십이 잘 분담되어 있어요.",
                'bad': "🚨 리더십 역할을 재정의해야 해요. 각자의 강점을 살린 리더십을 발휘해보세요."
            },
            'style_diversity_score': {
                'good': "🎯 체계적 계획과 유연한 대응이 균형잡혀 있어요! 분석적 사고와 창의적 문제해결이 시너지를 낼 것입니다.",
                'bad': "⚠️ 업무 스타일이 한쪽으로 치우쳐 있어요. 체계적인 분석과 유연한 창의성을 모두 활용해보세요."
            },
            'team_size_limitation': {
                'good': "👥 팀원 수가 적절합니다! 효율적인 의사소통과 협업이 가능할 것입니다.",
                'bad': "⚠️ 팀원 수가 너무 적어요. 적절한 인원으로 재구성하는 것을 고려해보세요."
            },
            'team_size_factor': {
                'good': "👥 팀원 수가 적절합니다! 효율적인 의사소통과 협업이 가능할 것입니다.",
                'bad': "⚠️ 팀원 수가 부족해요. 적절한 인원으로 재구성하는 것을 고려해보세요."
            }
        }
    
    def _get_score_level(self, score: float) -> str:
        """점수에 따른 레벨 반환"""
        if score >= 80:
            return 'high'
        elif score >= 50:
            return 'medium'
        else:
            return 'low'
    
    def _get_contribution_type(self, contribution: float) -> str:
        """기여도에 따른 타입 반환"""
        if contribution > 0:
            return 'good'
        else:
            return 'bad'
    
    def generate_messages(self, explanation_data: Dict[str, Any]) -> Dict[str, Any]:
        """머신러닝 결과를 사용자 친화적인 메시지로 변환"""
        
        result = {
            'summary': {
                'good_points': [],
                'bad_points': []
            },
            'detailed_analysis': {}
        }
        
        # 모든 포인트를 한 번에 처리
        all_points = []
        all_points.extend(explanation_data.get('good_points', []))
        all_points.extend(explanation_data.get('bad_points', []))
        
        # summary와 detailed_analysis 동시 생성
        for point in all_points:
            feature = point['feature']
            if feature not in self.messages:
                continue
                
            is_good_point = point in explanation_data.get('good_points', [])
            contribution_type = 'good' if is_good_point else 'bad'
            message = self.messages[feature][contribution_type]
            
            # summary에 추가
            point_data = {
                'feature': feature,
                'message': message,
                'score': point['value'],
                'contribution': point['contribution']
            }
            
            if is_good_point:
                result['summary']['good_points'].append(point_data)
            else:
                result['summary']['bad_points'].append(point_data)
            
            # detailed_analysis에 추가
            score_level = self._get_score_level(point['value'])
            result['detailed_analysis'][feature] = {
                'score': point['value'],
                'level': score_level,
                'type': contribution_type,
                'message': message
            }
        
        return result
