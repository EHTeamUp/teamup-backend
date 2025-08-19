from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.personality import (
    Question as QuestionModel, 
    Option as OptionModel, 
    UserTraitProfile as UserTraitProfileModel, 
    ProfileRule as ProfileRuleModel
)
from schemas.personality import (
    QuestionListResponse, 
    SubmitTestRequest, 
    TestResultResponse, 
    TraitProfile
)
from typing import List
import json

router = APIRouter(prefix="/personality", tags=["personality"])

@router.get("/questions", response_model=QuestionListResponse)
def get_questions(db: Session = Depends(get_db)):
    """모든 질문과 보기 조회"""
    try:
        questions = db.query(QuestionModel)\
            .order_by(QuestionModel.order_no)\
            .all()
        
        print(f"DEBUG: Found {len(questions)} questions")
        
        # 각 질문에 보기 추가
        for question in questions:
            print(f"DEBUG: Question {question.id} ({question.key_name}): {question.text}")
            
            options = db.query(OptionModel)\
                .filter(OptionModel.question_id == question.id)\
                .order_by(OptionModel.order_no)\
                .all()
            
            print(f"DEBUG: Found {len(options)} options for question {question.id}")
            
            question.options = options
        
        return QuestionListResponse(
            questions=questions,
            total_count=len(questions)
        )
    except Exception as e:
        print(f"DEBUG: Error in get_questions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/test", response_model=TestResultResponse)
def submit_personality_test(request: SubmitTestRequest, db: Session = Depends(get_db)):
    """성향 테스트 제출 및 결과 계산"""
    try:
        # 답변에서 trait_tag 추출
        traits = {}
        for answer in request.answers:
            option = db.query(OptionModel).filter(OptionModel.id == answer.option_id).first()
            if not option:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid option_id: {answer.option_id}"
                )
            
            question = db.query(QuestionModel).filter(QuestionModel.id == answer.question_id).first()
            if not question:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid question_id: {answer.question_id}"
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
            user_id=request.user_id,
            profile_code=profile_rule.profile_code,
            traits_json=traits
        )
        
        db.add(trait_profile)
        db.commit()
        db.refresh(trait_profile)
        
        # 결과 응답
        return TestResultResponse(
            profile_code=profile_rule.profile_code,
            display_name=profile_rule.display_name,
            description=profile_rule.description,
            traits=traits,
            completed_at=trait_profile.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

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

@router.get("/user-profile/{user_id}", response_model=TraitProfile)
def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    """사용자 성향 프로필 조회 (최신 결과)"""
    try:
        profile = db.query(UserTraitProfileModel)\
            .filter(UserTraitProfileModel.user_id == user_id)\
            .order_by(UserTraitProfileModel.created_at.desc())\
            .first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
