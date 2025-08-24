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
from schemas.synergy import SynergyRequest, SynergyResponse, SynergyUser, UserSkill, UserRole, UserExperience, UserTrait

from typing import List



router = APIRouter(prefix="/synergy", tags=["synergy"])

# Synergy용 함수들
def get_user_skills_detailed(db: Session, user_id: str) -> List[UserSkill]:
    """사용자의 스킬 정보를 상세하게 가져옵니다."""
    user_skills = db.query(UserSkillModel).join(Skill).filter(
        UserSkillModel.user_id == user_id
    ).all()
    
    return [
        UserSkill(
            skill_name=user_skill.skill.name,
            is_custom=user_skill.skill.is_custom
        ) for user_skill in user_skills
    ]

def get_user_roles_detailed(db: Session, user_id: str) -> List[UserRole]:
    """사용자의 역할 정보를 상세하게 가져옵니다."""
    user_roles = db.query(UserRoleModel).join(Role).filter(
        UserRoleModel.user_id == user_id
    ).all()
    
    return [
        UserRole(
            role_name=user_role.role.name,
            is_custom=user_role.role.is_custom
        ) for user_role in user_roles
    ]

def get_user_experiences_detailed(db: Session, user_id: str) -> List[UserExperience]:
    """사용자의 경험 정보를 상세하게 가져옵니다."""
    experiences = db.query(Experience).filter(
        Experience.user_id == user_id
    ).all()
    
    return [
        UserExperience(
            contest_name=exp.contest_name,
            award_status=exp.award_status  # 0: 참가, 1: 수상
        ) for exp in experiences
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
        
        display_name = profile_rule.display_name if profile_rule else trait_profile.profile_code
        
        return UserTrait(
            profile_code=trait_profile.profile_code,
            display_name=display_name
        )
    return None

def create_synergy_user(db: Session, user_id: str) -> SynergyUser:
    """사용자 정보와 상세 정보를 포함한 SynergyUser 생성"""
    return SynergyUser(
        user_id=user_id,
        skills=get_user_skills_detailed(db, user_id),
        roles=get_user_roles_detailed(db, user_id),
        experiences=get_user_experiences_detailed(db, user_id),
        traits=get_user_traits_detailed(db, user_id)
    )

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
        
        return SynergyResponse(
            users=all_users
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시너지 분석 중 오류가 발생했습니다: {str(e)}"
        )
