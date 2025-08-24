from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.skill import Skill
from models.role import Role
from models.user_skill import UserSkill
from models.user_role import UserRole
from models.experience import Experience
from models.contest import Filter
from schemas.user import (
    SkillUpdate, RoleUpdate, ExperienceUpdate, ExperienceCreate
)
from utils.auth import get_current_user
from typing import List

router = APIRouter(prefix="/profile", tags=["profile"])

@router.put("/skills", response_model=dict)
def update_user_skills(
    skill_update: SkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """프로필 - 스킬 수정"""
    try:
        # 스킬 검증: 기존 선택 또는 사용자 정의 중 최소 1개 이상
        total_skills = len(skill_update.skill_ids) + len([s for s in skill_update.custom_skills if s.strip()])
        if total_skills == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="스킬을 최소 1개 이상 선택하거나 입력해주세요."
            )
        
        # 기존 스킬 ID 유효성 검사
        for skill_id in skill_update.skill_ids:
            skill = db.query(Skill).filter(Skill.skill_id == skill_id).first()
            if not skill:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid skill ID: {skill_id}"
                )
        
        # 사용자 정의 스킬 유효성 검사 (중복 확인)
        custom_skills_data = []
        for custom_skill_name in skill_update.custom_skills:
            if not custom_skill_name.strip():
                continue
                
            # 이미 존재하는 스킬인지 확인
            existing_skill = db.query(Skill).filter(Skill.name == custom_skill_name.strip()).first()
            if existing_skill:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"스킬 '{custom_skill_name}'은 이미 존재합니다. 기존 스킬을 선택해주세요."
                )
            
            custom_skills_data.append(custom_skill_name.strip())
        
        # 최종 검증: 실제로 유효한 스킬이 있는지 확인
        if len(skill_update.skill_ids) + len(custom_skills_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효한 스킬을 최소 1개 이상 선택하거나 입력해주세요."
            )
        
        # 기존 사용자 스킬 삭제
        db.query(UserSkill).filter(UserSkill.user_id == current_user.user_id).delete()
        
        # 사용자 정의 스킬 생성 및 연결
        for custom_skill_name in custom_skills_data:
            new_skill = Skill(
                name=custom_skill_name,
                is_custom=True
            )
            db.add(new_skill)
            db.flush()  # skill_id 생성
            
            # UserSkill 연결
            user_skill = UserSkill(
                user_id=current_user.user_id,
                skill_id=new_skill.skill_id
            )
            db.add(user_skill)
        
        # 기존 스킬 연결
        for skill_id in skill_update.skill_ids:
            user_skill = UserSkill(
                user_id=current_user.user_id,
                skill_id=skill_id
            )
            db.add(user_skill)
        
        # 데이터베이스에 저장
        db.commit()
        
        return {
            "message": "스킬이 성공적으로 수정되었습니다.",
            "updated_skills": {
                "skill_ids": skill_update.skill_ids,
                "custom_skills": custom_skills_data
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.put("/roles", response_model=dict)
def update_user_roles(
    role_update: RoleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """프로필 - 역할 수정"""
    try:
        # 역할 검증: 기존 선택 또는 사용자 정의 중 최소 1개 이상
        total_roles = len(role_update.role_ids) + len([r for r in role_update.custom_roles if r.strip()])
        if total_roles == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="역할을 최소 1개 이상 선택하거나 입력해주세요."
            )
        
        # 기존 역할 ID 유효성 검사
        for role_id in role_update.role_ids:
            role = db.query(Role).filter(Role.role_id == role_id).first()
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role ID: {role_id}"
                )
        
        # 사용자 정의 역할 유효성 검사 (중복 확인)
        custom_roles_data = []
        for custom_role_name in role_update.custom_roles:
            if not custom_role_name.strip():
                continue
                
            # 이미 존재하는 역할인지 확인
            existing_role = db.query(Role).filter(Role.name == custom_role_name.strip()).first()
            if existing_role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"역할 '{custom_role_name}'은 이미 존재합니다. 기존 역할을 선택해주세요."
                )
            
            custom_roles_data.append(custom_role_name.strip())
        
        # 최종 검증: 실제로 유효한 역할이 있는지 확인
        if len(role_update.role_ids) + len(custom_roles_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효한 역할을 최소 1개 이상 선택하거나 입력해주세요."
            )
        
        # 기존 사용자 역할 삭제
        db.query(UserRole).filter(UserRole.user_id == current_user.user_id).delete()
        
        # 사용자 정의 역할 생성 및 연결
        for custom_role_name in custom_roles_data:
            new_role = Role(
                name=custom_role_name,
                is_custom=True
            )
            db.add(new_role)
            db.flush()  # role_id 생성
            
            # UserRole 연결
            user_role = UserRole(
                user_id=current_user.user_id,
                role_id=new_role.role_id
            )
            db.add(user_role)
        
        # 기존 역할 연결
        for role_id in role_update.role_ids:
            user_role = UserRole(
                user_id=current_user.user_id,
                role_id=role_id
            )
            db.add(user_role)
        
        # 데이터베이스에 저장
        db.commit()
        
        return {
            "message": "역할이 성공적으로 수정되었습니다.",
            "updated_roles": {
                "role_ids": role_update.role_ids,
                "custom_roles": custom_roles_data
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.put("/experiences", response_model=dict)
def update_user_experiences(
    experience_update: ExperienceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """프로필 - 공모전 수상 경험 수정"""
    try:
        # filter_id 유효성 검사
        for exp_data in experience_update.experiences:
            filter_exists = db.query(Filter).filter(Filter.filter_id == exp_data.filter_id).first()
            if not filter_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid filter_id: {exp_data.filter_id}"
                )
        
        # 기존 사용자 경험 삭제
        db.query(Experience).filter(Experience.user_id == current_user.user_id).delete()
        
        # 새로운 경험 정보 저장
        for exp_data in experience_update.experiences:
            experience = Experience(
                user_id=current_user.user_id,
                contest_name=exp_data.contest_name,
                award_date=exp_data.award_date,
                host_organization=exp_data.host_organization,
                award_status=exp_data.award_status,
                description=exp_data.description,
                filter_id=exp_data.filter_id
            )
            db.add(experience)
        
        # 데이터베이스에 저장
        db.commit()
        
        return {
            "message": "공모전 수상 경험이 성공적으로 수정되었습니다.",
            "updated_experiences_count": len(experience_update.experiences)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/skills", response_model=dict)
def get_user_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """프로필 - 현재 사용자의 스킬 조회"""
    try:
        # 사용자의 스킬 정보 조회
        user_skills = db.query(UserSkill).filter(UserSkill.user_id == current_user.user_id).all()
        
        skill_ids = []
        custom_skills = []
        
        for user_skill in user_skills:
            skill = db.query(Skill).filter(Skill.skill_id == user_skill.skill_id).first()
            if skill:
                if skill.is_custom:
                    custom_skills.append(skill.name)
                else:
                    skill_ids.append(skill.skill_id)
        
        return {
            "skill_ids": skill_ids,
            "custom_skills": custom_skills
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/roles", response_model=dict)
def get_user_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """프로필 - 현재 사용자의 역할 조회"""
    try:
        # 사용자의 역할 정보 조회
        user_roles = db.query(UserRole).filter(UserRole.user_id == current_user.user_id).all()
        
        role_ids = []
        custom_roles = []
        
        for user_role in user_roles:
            role = db.query(Role).filter(Role.role_id == user_role.role_id).first()
            if role:
                if role.is_custom:
                    custom_roles.append(role.name)
                else:
                    role_ids.append(role.role_id)
        
        return {
            "role_ids": role_ids,
            "custom_roles": custom_roles
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/experiences", response_model=List[dict])
def get_user_experiences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """프로필 - 현재 사용자의 공모전 수상 경험 조회"""
    try:
        # 사용자의 경험 정보 조회
        experiences = db.query(Experience).filter(Experience.user_id == current_user.user_id).all()
        
        return [
            {
                "contest_name": exp.contest_name,
                "award_date": exp.award_date,
                "host_organization": exp.host_organization,
                "award_status": exp.award_status,
                "description": exp.description,
                "filter_id": exp.filter_id
            }
            for exp in experiences
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/{user_id}", response_model=dict)
def get_user_mypage(
    user_id: str,
    db: Session = Depends(get_db)
):
    """특정 사용자의 프로필 정보 조회"""
    try:
        # 사용자 조회
        user = db.query(User).filter(User.user_id == user_id, User.is_deleted == False).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        # 사용자의 스킬 정보 조회
        user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
        skill_ids = []
        custom_skills = []
        
        for user_skill in user_skills:
            skill = db.query(Skill).filter(Skill.skill_id == user_skill.skill_id).first()
            if skill:
                if skill.is_custom:
                    custom_skills.append(skill.name)
                else:
                    skill_ids.append(skill.skill_id)
        
        # 사용자의 역할 정보 조회
        user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
        role_ids = []
        custom_roles = []
        
        for user_role in user_roles:
            role = db.query(Role).filter(Role.role_id == user_role.role_id).first()
            if role:
                if role.is_custom:
                    custom_roles.append(role.name)
                else:
                    role_ids.append(role.role_id)
        
        # 사용자의 경험 정보 조회
        experiences = db.query(Experience).filter(Experience.user_id == user_id).all()
        experience_list = [
            {
                "contest_name": exp.contest_name,
                "award_date": exp.award_date,
                "host_organization": exp.host_organization,
                "award_status": exp.award_status,
                "description": exp.description,
                "filter_id": exp.filter_id
            }
            for exp in experiences
        ]
        
        return {
            "user_info": {
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "is_deleted": user.is_deleted
            },
            "skills": {
                "skill_ids": skill_ids,
                "custom_skills": custom_skills
            },
            "roles": {
                "role_ids": role_ids,
                "custom_roles": custom_roles
            },
            "experiences": experience_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
