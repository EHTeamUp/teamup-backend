from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models.user import User
from models.user_skill import UserSkill as UserSkillModel
from models.user_role import UserRole as UserRoleModel
from models.experience import Experience
from models.personality import UserTraitProfile, ProfileRule
from models.skill import Skill
from models.role import Role
from schemas.synergy import (
    SynergyRequest, SynergyResponse, SynergyUser, UserSkill, UserRole, 
    UserTrait, SynergyAnalysisRequest, SynergyAnalysisResponse,
    ApplicantData
)
from ml.synergy_service import synergy_service
from ml.message_generator import SynergyMessageGenerator

from typing import List
import json

router = APIRouter(prefix="/synergy", tags=["synergy"])

# 머신러닝 예측 함수
def predict_synergy(data: SynergyAnalysisRequest) -> SynergyAnalysisResponse:
    """
    실제 머신러닝 모델을 사용한 시너지 예측 함수 (최적화된 버전)
    """
    try:
        # 팀 데이터를 딕셔너리 리스트로 변환
        team_data_list = []
        for applicant in data.applicants:
            team_data_list.append({
                'role': applicant.role,
                'skill': applicant.skill,
                'experience': applicant.experience,
                'tendency_type': applicant.tendency_type,
                'goal': applicant.goal,
                'time': applicant.time,
                'problem': applicant.problem
            })
        
        # 싱글톤 서비스를 통한 머신러닝 예측 실행
        result = synergy_service.predict_synergy(team_data_list, data.filtering_id)
        
        # 메시지 생성
        message_generator = SynergyMessageGenerator()
        description_message = message_generator.generate_messages(result['explanation'])
        
        # explanation에 메시지 추가
        explanation_with_messages = result['explanation'].copy()
        
        # 소수점을 일의자리까지 표시 
        explanation_with_messages['baseline'] = float(f"{explanation_with_messages['baseline']:.1f}")
        
        # good_points에 메시지 추가
        for i, point in enumerate(explanation_with_messages['good_points']):
            feature = point['feature']
            if feature in description_message['detailed_analysis']:
                explanation_with_messages['good_points'][i]['message'] = description_message['detailed_analysis'][feature]['message']
            # 소수점 조정 
            explanation_with_messages['good_points'][i]['value'] = float(f"{point['value']:.1f}")
            explanation_with_messages['good_points'][i]['contribution'] = float(f"{point['contribution']:.1f}")
        
        # bad_points에 메시지 추가
        for i, point in enumerate(explanation_with_messages['bad_points']):
            feature = point['feature']
            if feature in description_message['detailed_analysis']:
                explanation_with_messages['bad_points'][i]['message'] = description_message['detailed_analysis'][feature]['message']
            # 소수점 조정 
            explanation_with_messages['bad_points'][i]['value'] = float(f"{point['value']:.1f}")
            explanation_with_messages['bad_points'][i]['contribution'] = float(f"{point['contribution']:.1f}")
        
        # SynergyAnalysisResponse로 변환
        return SynergyAnalysisResponse(
            synergy_score=float(f"{result['synergy_score']:.1f}"),
            explanation=explanation_with_messages
        )
        
    except Exception as e:
        print(f"머신러닝 예측 중 오류 발생: {e}")
        # 오류 발생 시 기본 응답 반환
        return SynergyAnalysisResponse(
            synergy_score=50.0,
            explanation={
                "baseline": 0.5,
                "good_points": [],
                "bad_points": []
            }
        )

# Synergy용 함수들
def get_user_skills_detailed(db: Session, user_id: str) -> List[UserSkill]:
    """사용자의 스킬 정보를 상세하게 가져옵니다."""
    user_skills = db.query(UserSkillModel).join(Skill).filter(
        UserSkillModel.user_id == user_id
    ).all()
    
    return [
        UserSkill(
            skill_name=user_skill.skill.name
        ) for user_skill in user_skills
    ]

def get_user_roles_detailed(db: Session, user_id: str) -> List[UserRole]:
    """사용자의 역할 정보를 상세하게 가져옵니다."""
    user_roles = db.query(UserRoleModel).join(Role).filter(
        UserRoleModel.user_id == user_id
    ).all()
    
    return [
        UserRole(
            role_name=user_role.role.name
        ) for user_role in user_roles
    ]



def get_user_traits_detailed(db: Session, user_id: str) -> UserTrait:
    """사용자의 성향 정보를 상세하게 가져옵니다."""
    trait_profile = db.query(UserTraitProfile).filter(
        UserTraitProfile.user_id == user_id
    ).first()
    
    if trait_profile and trait_profile.profile_code:
        # profile_rules 테이블에서 display_name 조회
        profile_rule = db.query(ProfileRule).filter(
            ProfileRule.profile_code == trait_profile.profile_code
        ).first()
        
        if profile_rule:
            return UserTrait(
                profile_code=trait_profile.profile_code,
                display_name=profile_rule.display_name
            )
        else:
            return UserTrait(
                profile_code=trait_profile.profile_code,
                display_name=trait_profile.profile_code
            )
    return None

def create_synergy_user(db: Session, user_id: str) -> SynergyUser:
    """사용자 정보와 상세 정보를 포함한 SynergyUser 생성"""
    return SynergyUser(
        user_id=user_id,
        skills=get_user_skills_detailed(db, user_id),
        roles=get_user_roles_detailed(db, user_id),
        traits=get_user_traits_detailed(db, user_id)
    )

def get_user_experience_string(db: Session, user_id: str) -> str:
    """사용자의 경험을 문자열 형태로 변환 (filter_id:award_status 형식)"""
    experiences = db.query(Experience).filter(
        Experience.user_id == user_id
    ).all()
    
    if not experiences:
        return ""
    
    experience_parts = []
    for exp in experiences:
        experience_parts.append(f"{exp.filter_id}:{exp.award_status}")
    
    return ", ".join(experience_parts)

def get_user_roles_string(db: Session, user_id: str) -> str:
    """사용자의 역할을 문자열로 변환"""
    user_roles = db.query(UserRoleModel).join(Role).filter(
        UserRoleModel.user_id == user_id
    ).all()
    
    roles = [user_role.role.name for user_role in user_roles]
    return ", ".join(roles) if roles else ""

def get_user_skills_string(db: Session, user_id: str) -> str:
    """사용자의 스킬을 문자열로 변환"""
    user_skills = db.query(UserSkillModel).join(Skill).filter(
        UserSkillModel.user_id == user_id
    ).all()
    
    skills = [user_skill.skill.name for user_skill in user_skills]
    return ", ".join(skills) if skills else ""

def map_tags_to_fields(required_tags: List[str]) -> dict:
    """required_tags_json을 tendency_type, goal, time, problem으로 매핑"""
    mapping = {
        'tendency_type': None,
        'goal': None,
        'time': None,
        'problem': None
    }
    
    for tag in required_tags:
        if tag in ['LEADER', 'SUPPORTER']:
            mapping['tendency_type'] = tag
        elif tag in ['QUALITY', 'SCHEDULE']:
            mapping['goal'] = tag
        elif tag in ['MORNING', 'NIGHT']:
            mapping['time'] = tag
        elif tag in ['ANALYTIC', 'ADHOC']:
            mapping['problem'] = tag
    
    return mapping

@router.post("/analyze", response_model=SynergyResponse)
def analyze_synergy(
    request: SynergyRequest,
    db: Session = Depends(get_db)
):
    """
    사용자 리스트를 받아서 시너지 분석을 위한 사용자 정보를 반환합니다.
    """
    try:
        # 요청된 사용자들 조회
        users = db.query(User).filter(
            User.user_id.in_(request.user_ids),
            User.is_deleted == False
        ).all()
        
        # 모든 사용자를 SynergyUser 형태로 변환
        all_users = [
            create_synergy_user(db, user.user_id)
            for user in users
        ]
        
        # 머신러닝 예측을 위한 데이터 준비
        applicants = []
        for user in users:
            # 사용자 정보 가져오기
            traits = get_user_traits_detailed(db, user.user_id)
            roles_str = get_user_roles_string(db, user.user_id)
            skills_str = get_user_skills_string(db, user.user_id)
            experience_str = get_user_experience_string(db, user.user_id)
            
            # 태그 매핑
            if traits:
                # profile_rules에서 required_tags_json 가져오기
                profile_rule = db.query(ProfileRule).filter(
                    ProfileRule.profile_code == traits.profile_code
                ).first()
                required_tags = profile_rule.required_tags_json if profile_rule else []
            else:
                required_tags = []
            
            tag_mapping = map_tags_to_fields(required_tags)
            
            applicant = ApplicantData(
                role=roles_str,
                skill=skills_str,
                experience=experience_str,
                tendency_type=tag_mapping['tendency_type'] or "UNKNOWN",
                goal=tag_mapping['goal'] or "UNKNOWN",
                time=tag_mapping['time'] or "UNKNOWN",
                problem=tag_mapping['problem'] or "UNKNOWN"
            )
            applicants.append(applicant)
        
        # 머신러닝 예측 요청 데이터 생성
        analysis_request = SynergyAnalysisRequest(
            filtering_id=request.filter_id,
            applicants=applicants
        )
        
        # 머신러닝 예측 실행
        synergy_result = predict_synergy(analysis_request)
        
        return SynergyResponse(
            users=all_users,
            synergy_result=synergy_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시너지 분석 중 오류가 발생했습니다: {str(e)}"
        )
