from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.skill import Skill
from models.role import Role
from models.user_skill import UserSkill
from models.user_role import UserRole
from models.experience import Experience
from models.personality import (
    Question as QuestionModel, 
    Option as OptionModel, 
    UserTraitProfile as UserTraitProfileModel, 
    ProfileRule as ProfileRuleModel
)
from schemas.registration import (
    RegistrationStep1, RegistrationStep2, RegistrationStep3, RegistrationStep4,
    CompleteRegistration, RegistrationStatus, StepResponse
)
from schemas.user import (
    EmailVerificationRequest, EmailVerificationResponse, EmailVerificationCode,
    UserIdCheckRequest, UserIdCheckResponse, UserCreateWithVerification
)
from utils.auth import get_password_hash, create_access_token
from utils.email_auth import send_verification_email, verify_email_code, mark_email_as_verified
from datetime import datetime, timedelta
from typing import List
from config import settings

router = APIRouter(prefix="/registration", tags=["registration"])

# 메모리 기반 회원가입 진행 상태 저장 
registration_sessions = {}

def find_matching_profile(traits: dict, db: Session) -> ProfileRuleModel:
    """사용자 답변과 ProfileRule을 매칭하여 최적의 성향 찾기"""
    # 모든 ProfileRule 조회
    profile_rules = db.query(ProfileRuleModel).all()
    
    best_match = None
    best_score = -1
    
    for rule in profile_rules:
        required_tags = rule.required_tags_json
        
        # 정확히 일치하는 태그 개수 계산
        match_count = 0
        for tag in required_tags:
            if tag in traits.values():
                match_count += 1
        
        # 모든 태그가 일치하는 경우만 고려
        if match_count == len(required_tags):
            # priority가 낮을수록 우선순위가 높음
            score = 1000 - rule.priority + match_count
            
            if score > best_score:
                best_score = score
                best_match = rule
    
    return best_match

# ===== 회원가입 관련 엔드포인트 =====

@router.post("/send-verification", response_model=EmailVerificationResponse)
def send_email_verification(request: EmailVerificationRequest):
    """이메일 인증번호 발송"""
    try:
        # 이메일 인증번호 발송
        if send_verification_email(request.email):
            return EmailVerificationResponse(
                message=f"인증번호가 {request.email}로 발송되었습니다."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/verify-email", response_model=dict)
def verify_email(request: EmailVerificationCode):
    """이메일 인증번호 검증"""
    try:
        if verify_email_code(request.email, request.verification_code):
            return {"message": "이메일 인증이 완료되었습니다."}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/check-userid", response_model=UserIdCheckResponse)
def check_user_id_availability(request: UserIdCheckRequest, db: Session = Depends(get_db)):
    """사용자 ID 중복 검사"""
    try:
        db_user = db.query(User).filter(User.user_id == request.user_id).first()
        if db_user:
            return UserIdCheckResponse(
                available=False,
                message=f"사용자 ID '{request.user_id}'는 이미 사용 중입니다."
            )
        else:
            return UserIdCheckResponse(
                available=True,
                message=f"사용자 ID '{request.user_id}'는 사용 가능합니다."
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/register", response_model=dict)
def register(user: UserCreateWithVerification, db: Session = Depends(get_db)):
    """회원가입 (이메일 인증 필요)"""
    try:
        # 중복 사용자 확인
        db_user = db.query(User).filter(User.user_id == user.user_id).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID already registered"
            )
        
        # 중복 이메일 확인
        db_email = db.query(User).filter(User.email == user.email).first()
        if db_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # 이메일 인증번호 검증
        if not verify_email_code(user.email, user.verification_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code"
            )
        
        # 비밀번호 해싱
        hashed_password = get_password_hash(user.password)
        
        # 사용자 생성
        db_user = User(
            user_id=user.user_id,
            name=user.name,
            email=user.email,
            password_hash=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # 이메일을 인증 완료 상태로 표시
        mark_email_as_verified(user.email)
        
        # 액세스 토큰 생성
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.user_id}, expires_delta=access_token_expires
        )
        
        return {
            "message": "회원가입이 완료되었습니다!",
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# ===== 다단계 회원가입 엔드포인트 =====

@router.get("/skills", response_model=List[dict])
def get_available_skills(db: Session = Depends(get_db)):
    """사용 가능한 스킬 목록 조회"""
    try:
        skills = db.query(Skill).filter(Skill.is_custom == False).all()
        return [
            {
                "skill_id": skill.skill_id,
                "name": skill.name,
                "is_custom": skill.is_custom
            }
            for skill in skills
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/roles", response_model=List[dict])
def get_available_roles(db: Session = Depends(get_db)):
    """사용 가능한 역할 목록 조회"""
    try:
        roles = db.query(Role).filter(Role.is_custom == False).all()
        return [
            {
                "role_id": role.role_id,
                "name": role.name,
                "is_custom": role.is_custom
            }
            for role in roles
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/step1", response_model=StepResponse)
def complete_step1(step1: RegistrationStep1, db: Session = Depends(get_db)):
    """1단계: 기본 정보 + 이메일 인증 완료"""
    try:
        # 중복 사용자 확인
        existing_user = db.query(User).filter(User.user_id == step1.user_id).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID already registered"
            )
        
        existing_email = db.query(User).filter(User.email == step1.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # 이메일 인증번호 검증
        if not verify_email_code(step1.email, step1.verification_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code"
            )
        
        # 회원가입 세션에 1단계 정보 저장
        registration_sessions[step1.user_id] = {
            "step1": step1.dict(),
            "current_step": 1,
            "completed_steps": [1],
            "created_at": datetime.now()
        }
        
        return StepResponse(
            success=True,
            message="1단계가 완료되었습니다. 스킬과 역할을 선택해주세요.",
            current_step=1,
            next_step=2,
            is_completed=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/step2", response_model=StepResponse)
def complete_step2(step2: RegistrationStep2, db: Session = Depends(get_db)):
    """2단계: 스킬 + 역할 선택 완료"""
    try:
        # 1단계 완료 여부 확인
        if not registration_sessions.get(step2.user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please complete step 1 first"
            )
        
        # 스킬 검증: 기존 선택 또는 사용자 정의 중 최소 1개 이상
        total_skills = len(step2.skill_ids) + len([s for s in step2.custom_skills if s.strip()])
        if total_skills == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="스킬을 최소 1개 이상 선택하거나 입력해주세요."
            )
        
        # 역할 검증: 기존 선택 또는 사용자 정의 중 최소 1개 이상
        total_roles = len(step2.role_ids) + len([r for r in step2.custom_roles if r.strip()])
        if total_roles == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="역할을 최소 1개 이상 선택하거나 입력해주세요."
            )
        
        # 기존 스킬 ID 유효성 검사
        for skill_id in step2.skill_ids:
            skill = db.query(Skill).filter(Skill.skill_id == skill_id).first()
            if not skill:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid skill ID: {skill_id}"
                )
        
        # 기존 역할 ID 유효성 검사
        for role_id in step2.role_ids:
            role = db.query(Role).filter(Role.role_id == role_id).first()
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role ID: {role_id}"
                )
        
        # 사용자 정의 스킬 유효성 검사 (중복 확인)
        custom_skills_data = []
        for custom_skill_name in step2.custom_skills:
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
        
        # 사용자 정의 역할 유효성 검사 (중복 확인)
        custom_roles_data = []
        for custom_role_name in step2.custom_roles:
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
        
        # 최종 검증: 실제로 유효한 스킬/역할이 있는지 확인
        if len(step2.skill_ids) + len(custom_skills_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효한 스킬을 최소 1개 이상 선택하거나 입력해주세요."
            )
        
        if len(step2.role_ids) + len(custom_roles_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효한 역할을 최소 1개 이상 선택하거나 입력해주세요."
            )
        
        # 2단계 정보 저장 (사용자 정의 스킬/역할 포함)
        step2_data = step2.dict()
        step2_data["custom_skills"] = custom_skills_data
        step2_data["custom_roles"] = custom_roles_data
        
        registration_sessions[step2.user_id]["step2"] = step2_data
        registration_sessions[step2.user_id]["current_step"] = 2
        registration_sessions[step2.user_id]["completed_steps"].append(2)
        
        return StepResponse(
            success=True,
            message="2단계가 완료되었습니다. 공모전 수상 경험을 입력해주세요.",
            current_step=2,
            next_step=3,
            is_completed=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/step3", response_model=StepResponse)
def complete_step3(step3: RegistrationStep3, db: Session = Depends(get_db)):
    """3단계: 공모전 수상 경험 입력 완료"""
    try:
        # 1, 2단계 완료 여부 확인
        session = registration_sessions.get(step3.user_id)
        if not session or session["current_step"] < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please complete previous steps first"
            )
        
        # 3단계 정보 저장
        session["step3"] = step3.dict()
        session["current_step"] = 3
        session["completed_steps"].append(3)
        
        return StepResponse(
            success=True,
            message="3단계가 완료되었습니다. 성향테스트를 진행해주세요.",
            current_step=3,
            next_step=4,
            is_completed=False,
            can_skip_personality=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/step4", response_model=StepResponse)
def complete_step4(step4: RegistrationStep4, db: Session = Depends(get_db)):
    """4단계: 성향테스트 (필수) 완료"""
    try:
        # 1, 2, 3단계 완료 여부 확인
        session = registration_sessions.get(step4.user_id)
        if not session or session["current_step"] < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please complete previous steps first"
            )
        
        # 성향테스트 답변 검증
        if len(step4.answers) != 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="성향테스트는 4개 질문에 모두 답변해야 합니다."
            )
        
        # 4단계 정보 저장
        session["step4"] = step4.dict()
        session["current_step"] = 4
        session["completed_steps"].append(4)
        
        return StepResponse(
            success=True,
            message="성향테스트가 완료되었습니다. 회원가입을 완료하시겠습니까?",
            current_step=4,
            next_step=None,
            is_completed=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/complete", response_model=StepResponse)
def complete_registration(user_id: str, db: Session = Depends(get_db)):
    """전체 회원가입 완료"""
    try:
        # 모든 단계 완료 여부 확인 (이제 4단계까지 필수)
        session = registration_sessions.get(user_id)
        if not session or session["current_step"] < 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please complete all 4 steps including personality test"
            )
        
        # 1단계: 사용자 기본 정보 생성
        step1_data = session["step1"]
        hashed_password = get_password_hash(step1_data["password"])
        
        new_user = User(
            user_id=step1_data["user_id"],
            name=step1_data["name"],
            email=step1_data["email"],
            password_hash=hashed_password
        )
        db.add(new_user)
        db.flush()  # user_id 생성
        
        # 2단계: 스킬과 역할 처리
        step2_data = session["step2"]
        
        # 사용자 정의 스킬 생성 및 연결
        for custom_skill_name in step2_data["custom_skills"]:
            new_skill = Skill(
                name=custom_skill_name,
                is_custom=True
            )
            db.add(new_skill)
            db.flush()  # skill_id 생성
            
            # UserSkill 연결
            user_skill = UserSkill(
                user_id=user_id,
                skill_id=new_skill.skill_id
            )
            db.add(user_skill)
        
        # 기존 스킬 연결
        for skill_id in step2_data["skill_ids"]:
            user_skill = UserSkill(
                user_id=user_id,
                skill_id=skill_id
            )
            db.add(user_skill)
        
        # 사용자 정의 역할 생성 및 연결
        for custom_role_name in step2_data["custom_roles"]:
            new_role = Role(
                name=custom_role_name,
                is_custom=True
            )
            db.add(new_role)
            db.flush()  # role_id 생성
            
            # UserRole 연결
            user_role = UserRole(
                user_id=user_id,
                role_id=new_role.role_id
            )
            db.add(user_role)
        
        # 기존 역할 연결
        for role_id in step2_data["role_ids"]:
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id
            )
            db.add(user_role)
        
        # 3단계: 공모전 수상 경험 저장
        step3_data = session["step3"]
        for exp_data in step3_data["experiences"]:
            experience = Experience(
                user_id=user_id,
                contest_name=exp_data["contest_name"],
                award_date=exp_data["award_date"],
                host_organization=exp_data["host_organization"],
                award_name=exp_data["award_name"],
                description=exp_data["description"]
            )
            db.add(experience)
        
        # 4단계: 성향테스트 결과 저장
        step4_data = session["step4"]
        if step4_data and "answers" in step4_data:
            # 답변에서 trait_tag 추출
            traits = {}
            for answer in step4_data["answers"]:
                option = db.query(OptionModel).filter(OptionModel.id == answer["option_id"]).first()
                if not option:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid option_id: {answer['option_id']}"
                    )
                
                question = db.query(QuestionModel).filter(QuestionModel.id == answer["question_id"]).first()
                if not question:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid question_id: {answer['question_id']}"
                    )
                
                traits[question.key_name] = option.trait_tag
            
            # ProfileRule과 매칭하여 성향 결정
            profile_rule = find_matching_profile(traits, db)
            if not profile_rule:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No matching personality profile found"
                )
            
            # UserTraitProfile 저장
            trait_profile = UserTraitProfileModel(
                user_id=user_id,
                profile_code=profile_rule.profile_code,
                traits_json=traits
            )
            db.add(trait_profile)
        
        # 이메일을 인증 완료 상태로 표시
        mark_email_as_verified(step1_data["email"])
        
        # 커밋
        db.commit()
        
        # 세션 정리
        del registration_sessions[user_id]
        
        return StepResponse(
            success=True,
            message="회원가입이 완료되었습니다!",
            current_step=4,
            next_step=None,
            is_completed=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/status/{user_id}", response_model=RegistrationStatus)
def get_registration_status(user_id: str):
    """회원가입 진행 상태 확인"""
    session = registration_sessions.get(user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration session not found"
        )
    
    return RegistrationStatus(
        user_id=user_id,
        current_step=session["current_step"],
        is_completed=session["current_step"] >= 4,  # 4단계까지 완료해야 함
        completed_steps=session["completed_steps"]
    )
