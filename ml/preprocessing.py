import pandas as pd
import numpy as np
from scipy.stats import entropy

class TeamFeatureGenerator:
    """
    팀 데이터를 기반으로 머신러닝 모델 학습에 사용할
    팀 벡터(feature vector)를 생성하는 전처리 클래스입니다.
    """
    def __init__(self, role_skill_matrix_path, skill_contest_matrix_path, role_contest_matrix_path):
        """클래스 초기화 시점에 모든 매트릭스 파일을 한 번만 로드합니다."""
        self.role_skill_matrix = self._load_matrix(role_skill_matrix_path)
        self.skill_contest_matrix = self._load_matrix(skill_contest_matrix_path)
        self.role_contest_matrix = self._load_matrix(role_contest_matrix_path)
        self.contest_map = {
            1: '웹/앱', 2: 'AI/데이터 사이언스', 3: '아이디어/기획',
            4: 'IoT/임베디드', 5: '게임', 6: '정보보안/블록체인'
        }

    def _load_matrix(self, filepath):
        """CSV 파일을 로드하고 첫 번째 열을 인덱스로 설정합니다."""
        try:
            return pd.read_csv(filepath, index_col=0)
        except FileNotFoundError:
            print(f"Error: Matrix file not found at {filepath}.")
            return None
    
            
    def create_team_vector(self, team_df, contest_id):
        """하나의 팀 데이터에 대해 6가지 기준의 피처 벡터를 생성합니다."""
        if any(matrix is None for matrix in [self.role_skill_matrix, self.skill_contest_matrix, self.role_contest_matrix]):
            raise ValueError("매트릭스 파일이 제대로 로드되지 않았습니다.")

        contest_name = self.contest_map.get(contest_id)
        if not contest_name:
            raise ValueError(f"유효하지 않은 공모전 ID입니다: {contest_id}")

        vector = {
            'role_skill_match_score': self._calculate_role_skill_match(team_df),
            'contest_skill_relevance_score': self._calculate_contest_skill_relevance(team_df, contest_name),
            'contest_role_relevance_score': self._calculate_contest_role_relevance(team_df, contest_name),
            'experience_relevance_score': self._calculate_experience_relevance(team_df, contest_id),
            'tendency_alignment_score': self._calculate_tendency_alignment(team_df),
            'leadership_distribution_score': self._calculate_leadership_distribution(team_df),
            'style_diversity_score': self._calculate_style_diversity_score(team_df),
            'team_size_factor': self._get_small_team_penalty_factor(len(team_df))
        }
        return {k: round(v, 2) for k, v in vector.items()}
    
    def _get_small_team_penalty_factor(self, team_size):
        """팀 규모가 작을 경우 페널티 팩터를 반환하는 함수"""
        if team_size == 1:
            return 0.2  # 1명 팀은 페널티 완화 (40% 반영)
        elif team_size == 2:
            return 0.35  # 2명 팀은 페널티 완화 (60% 반영)
        elif team_size == 3:
            return 0.4 # 3명 팀은 약한 페널티 (75% 반영)
        elif team_size == 4:
            return 0.85 # 4명 팀은 매우 약한 페널티 (85% 반영)
        else: # 5명 이상
            return 1.0  # 페널티 없음
    
    # --- 각 피처 계산 메서드 ---
    def _calculate_role_skill_match(self, team_df):
        """팀원이 맡은 여러 역할과 보유 스킬의 적합도를 평가"""
        member_scores = []
        for _, member in team_df.iterrows():
            # 역할과 스킬을 쉼표(,) 기준으로 분리하여 리스트로 만듭니다.
            roles = [r.strip() for r in str(member.get('role', '')).split(',')]
            skills = [s.strip() for s in str(member.get('skill', '')).split(',')]
            
            if not roles or not skills:
                member_scores.append(0)
                continue
                
            # 한 사람이 가진 여러 역할에 대한 점수를 저장할 리스트
            individual_role_scores = []
            for role in roles:
                # 현재 역할이 평가 기준표에 없으면 건너뜁니다.
                if role not in self.role_skill_matrix.index:
                    individual_role_scores.append(0)
                    continue
                
                # 현재 역할과 스킬들의 적합도 점수를 계산합니다.
                skill_scores = [self.role_skill_matrix.loc[role].get(skill, 0) for skill in skills]
                avg_skill_score_for_role = np.mean(skill_scores) if skill_scores else 0
                individual_role_scores.append(avg_skill_score_for_role)
            
            # 한 사람의 최종 점수는 각 역할 점수들의 평균입니다.
            final_member_score = np.mean(individual_role_scores) if individual_role_scores else 0
            member_scores.append(final_member_score)
            
        # 팀 전체의 최종 점수는 모든 팀원 점수들의 평균입니다.
        base_score = (np.mean(member_scores) * 100) if member_scores else 0
        
        # 팀 크기 페널티 적용
        penalty_factor = self._get_small_team_penalty_factor(len(team_df))
        return base_score * penalty_factor

    def _calculate_contest_skill_relevance(self, team_df, contest_name):
        """팀원들의 스킬이 해당 공모전 분야와 얼마나 관련있는지 평가"""
        if contest_name not in self.skill_contest_matrix.columns:
            return 0
            
        member_scores = []
        for _, member in team_df.iterrows():
            skills = [s.strip() for s in str(member.get('skill', '')).split(',')]
            
            if not skills:
                member_scores.append(0)
                continue
                
            # 각 스킬의 공모전 관련성 점수를 계산합니다.
            skill_scores = []
            for skill in skills:
                if skill in self.skill_contest_matrix.index:
                    score = self.skill_contest_matrix.loc[skill, contest_name]
                    skill_scores.append(score)
            
            # 한 사람의 최종 점수는 모든 스킬 점수들의 평균입니다.
            member_score = np.mean(skill_scores) if skill_scores else 0
            member_scores.append(member_score)
            
        # 팀 전체의 최종 점수는 모든 팀원 점수들의 평균입니다.
        base_score = (np.mean(member_scores) * 100) if member_scores else 0
        
        # 팀 크기 페널티 적용
        penalty_factor = self._get_small_team_penalty_factor(len(team_df))
        return base_score * penalty_factor

    def _calculate_contest_role_relevance(self, team_df, contest_name):
        """팀원들의 역할이 해당 공모전 분야와 얼마나 관련있는지 평가"""
        if contest_name not in self.role_contest_matrix.columns:
            return 0
            
        member_scores = []
        for _, member in team_df.iterrows():
            roles = [r.strip() for r in str(member.get('role', '')).split(',')]
            
            if not roles:
                member_scores.append(0)
                continue
                
            # 각 역할의 공모전 관련성 점수를 계산합니다.
            role_scores = []
            for role in roles:
                if role in self.role_contest_matrix.index:
                    score = self.role_contest_matrix.loc[role, contest_name]
                    role_scores.append(score)
            
            # 한 사람의 최종 점수는 모든 역할 점수들의 평균입니다.
            member_score = np.mean(role_scores) if role_scores else 0
            member_scores.append(member_score)
            
        # 팀 전체의 최종 점수는 모든 팀원 점수들의 평균입니다.
        base_score = (np.mean(member_scores) * 100) if member_scores else 0
        
        # 팀 크기 페널티 적용
        penalty_factor = self._get_small_team_penalty_factor(len(team_df))
        return base_score * penalty_factor

    def _calculate_experience_relevance(self, team_df, contest_id):
        """팀원들의 경험이 해당 공모전 분야와 얼마나 관련있는지 평가"""
        member_scores = []
        for _, member in team_df.iterrows():
            experience_str = str(member.get('experience', ''))
            
            if not experience_str:
                member_scores.append(0)
                continue
                
            # 경험 데이터 파싱: "filter_id:award_status" 형태
            experiences = []
            for exp in experience_str.split(','):
                exp = exp.strip()
                if ':' in exp:
                    try:
                        filter_id, award_status = exp.split(':')
                        filter_id = int(filter_id.strip())
                        award_status = int(award_status.strip())
                        
                        # 같은 분야의 공모전 경험이 있는지 확인
                        if filter_id == contest_id:
                            # 수상 여부에 따라 점수 차등 부여
                            if award_status == 1:  # 수상
                                experiences.append(100)
                            else:  # 참가
                                experiences.append(50)
                    except ValueError:
                        continue
            
            # 한 사람의 최종 점수는 모든 경험 점수들의 평균입니다.
            member_score = np.mean(experiences) if experiences else 0
            member_scores.append(member_score)
            
        # 팀 전체의 최종 점수는 모든 팀원 점수들의 평균입니다.
        base_score = np.mean(member_scores) if member_scores else 0
        
        # 팀 크기 페널티 적용
        penalty_factor = self._get_small_team_penalty_factor(len(team_df))
        return base_score * penalty_factor

    def _calculate_tendency_alignment(self, team_df):
        """팀원들의 성향이 서로 잘 맞는지 평가"""
        tendency_types = []
        goals = []
        times = []
        problems = []
        
        for _, member in team_df.iterrows():
            tendency_types.append(member.get('tendency_type', ''))
            goals.append(member.get('goal', ''))
            times.append(member.get('time', ''))
            problems.append(member.get('problem', ''))
        
        # 각 성향 차원별로 다양성 점수 계산
        tendency_diversity = self._calculate_diversity_score(tendency_types)
        goal_diversity = self._calculate_diversity_score(goals)
        time_diversity = self._calculate_diversity_score(times)
        problem_diversity = self._calculate_diversity_score(problems)
        
        # 전체 성향 정렬 점수 (다양성이 적절할수록 높은 점수)
        alignment_score = (tendency_diversity + goal_diversity + time_diversity + problem_diversity) / 4
        
        # 팀 크기 페널티 적용
        penalty_factor = self._get_small_team_penalty_factor(len(team_df))
        return alignment_score * penalty_factor

    def _calculate_leadership_distribution(self, team_df):
        """리더십 분포가 적절한지 평가"""
        leader_count = 0
        total_members = len(team_df)
        
        for _, member in team_df.iterrows():
            if member.get('tendency_type') == 'LEADER':
                leader_count += 1
        
        # 리더 비율 계산
        leader_ratio = leader_count / total_members if total_members > 0 else 0
        
        # 적절한 리더 비율 (20-40%)일 때 높은 점수
        if 0.2 <= leader_ratio <= 0.4:
            distribution_score = 100
        elif 0.1 <= leader_ratio <= 0.5:
            distribution_score = 80
        elif 0.05 <= leader_ratio <= 0.6:
            distribution_score = 60
        else:
            distribution_score = 30
        
        # 팀 크기 페널티 적용
        penalty_factor = self._get_small_team_penalty_factor(len(team_df))
        return distribution_score * penalty_factor

    def _calculate_style_diversity_score(self, team_df):
        """팀의 스타일 다양성을 평가"""
        styles = []
        for _, member in team_df.iterrows():
            # 각 팀원의 스타일을 조합하여 고유한 스타일 생성
            style = f"{member.get('goal', '')}_{member.get('problem', '')}"
            styles.append(style)
        
        diversity_score = self._calculate_diversity_score(styles)
        
        # 팀 크기 페널티 적용
        penalty_factor = self._get_small_team_penalty_factor(len(team_df))
        return diversity_score * penalty_factor

    def _calculate_diversity_score(self, values):
        """값들의 다양성을 계산하는 헬퍼 함수"""
        if not values:
            return 0
        
        # 고유한 값들의 개수
        unique_count = len(set(values))
        total_count = len(values)
        
        # 다양성 점수 계산 (고유한 값이 많을수록 높은 점수, 단 너무 극단적이면 감점)
        if total_count == 1:
            return 30  # 1명 팀은 낮은 점수
        elif unique_count == 1:
            return 40  # 모두 같은 스타일
        elif unique_count == total_count:
            return 70  # 모두 다른 스타일
        else:
            # 중간 정도의 다양성 (가장 높은 점수)
            return 90
