from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.personality import (
    Question, Option, UserTestSession, UserAnswer, UserTraitProfile
)
from schemas.personality import *
from typing import List

router = APIRouter(prefix="/personality", tags=["personality"])

@router.get("/questions", response_model=QuestionListResponse)
def get_questions(db: Session = Depends(get_db)):
    """모든 질문과 보기 조회"""
    try:
        questions = db.query(Question)\
            .order_by(Question.order_no)\
            .all()
        
        # 각 질문에 보기 추가
        for question in questions:
            question.options = db.query(Option)\
                .filter(Option.question_id == question.id)\
                .order_by(Option.order_no)\
                .all()
        
        return QuestionListResponse(
            questions=questions,
            total_count=len(questions)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/start-test", response_model=TestSession)
def start_personality_test(request: StartTestRequest, db: Session = Depends(get_db)):
    """성향 테스트 시작"""
    try:
        # 테스트 세션 생성 (user_id는 인증에서 가져와야 함)
        # TODO: 실제 구현 시 current_user에서 user_id 가져오기
        test_session = UserTestSession(
            user_id="temp_user"  # 임시 값
        )
        
        db.add(test_session)
        db.commit()
        db.refresh(test_session)
        
        return test_session
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/submit-test", response_model=TestResultResponse)
def submit_personality_test(request: SubmitTestRequest, db: Session = Depends(get_db)):
    """성향 테스트 제출 및 결과 계산"""
    try:
        # 세션 확인
        session = db.query(UserTestSession)\
            .filter(UserTestSession.id == request.session_id)\
            .first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test session not found"
            )
        
        if session.finished_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Test session already completed"
            )
        
        # 답변 저장
        for answer_data in request.answers:
            answer = UserAnswer(
                session_id=request.session_id,
                question_id=answer_data.question_id,
                option_id=answer_data.option_id
            )
            db.add(answer)
        
        # 세션 완료 처리
        session.finished_at = func.now()
        
        # 성향 프로필 계산 및 저장
        profile = calculate_trait_profile(request.session_id, db)
        
        db.commit()
        
        # 결과 응답
        return TestResultResponse(
            session_id=request.session_id,
            profile_code=profile.profile_code,
            traits=profile.traits_json,
            completed_at=session.finished_at,
            total_questions=len(request.answers),
            answered_questions=len(request.answers)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

def calculate_trait_profile(session_id: int, db: Session) -> UserTraitProfile:
    """성향 프로필 계산"""
    # 사용자 답변 조회
    answers = db.query(UserAnswer)\
        .filter(UserAnswer.session_id == session_id)\
        .all()
    
    # 성향 특성 계산
    traits = {}
    for answer in answers:
        option = db.query(Option).filter(Option.id == answer.option_id).first()
        if option:
            traits[option.question.key_name] = option.trait_tag
    
    # 프로필 코드 생성
    profile_code = generate_profile_code(traits)
    
    # 프로필 저장
    profile = UserTraitProfile(
        session_id=session_id,
        user_id=answers[0].session.user_id if answers else "unknown",
        profile_code=profile_code,
        traits_json=traits
    )
    
    db.add(profile)
    return profile

def generate_profile_code(traits: dict) -> str:
    """성향 특성을 기반으로 프로필 코드 생성"""
    if not traits:
        return "UNKNOWN"
    
    # 예시: LEADER + MORNING = "MORNING_LEADER"
    role = traits.get('role', 'UNKNOWN')
    time = traits.get('time', 'UNKNOWN')
    
    if role != 'UNKNOWN' and time != 'UNKNOWN':
        return f"{time}_{role}"
    elif role != 'UNKNOWN':
        return role
    else:
        return "UNKNOWN"

@router.get("/results/{session_id}", response_model=TraitProfile)
def get_test_result(session_id: int, db: Session = Depends(get_db)):
    """테스트 결과 조회"""
    try:
        profile = db.query(UserTraitProfile)\
            .filter(UserTraitProfile.session_id == session_id)\
            .first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test result not found"
            )
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
