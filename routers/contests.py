from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.contest import Contest, Tag, ContestTag
from schemas.contest import ContestListResponse
from typing import List

router = APIRouter(prefix="/contests", tags=["contests"])

@router.get("/", response_model=ContestListResponse)
def get_contests(db: Session = Depends(get_db)):
    """공모전 목록 조회"""
    try:
        # 전체 공모전 수 조회
        total_count = db.query(func.count(Contest.contest_id)).scalar()
        
        # 공모전 목록 조회 (마감일 기준 오름차순)
        contests = db.query(Contest)\
            .order_by(Contest.due_date.asc())\
            .all()
        
        return ContestListResponse(
            contests=contests,
            total_count=total_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/{contest_id}")
def get_contest_detail(contest_id: int, db: Session = Depends(get_db)):
    """공모전 상세 정보 조회"""
    try:
        contest = db.query(Contest).filter(Contest.contest_id == contest_id).first()
        if not contest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contest not found"
            )
        
        return contest
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
