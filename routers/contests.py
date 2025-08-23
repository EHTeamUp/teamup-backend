from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.contest import Contest, Tag, ContestTag, Filter, ContestFilter
from schemas.contest import ContestListResponse, Contest as ContestSchema
from typing import List

router = APIRouter(prefix="/contests", tags=["contests"])

@router.get("/filters", response_model=List[dict])
def get_available_filters(db: Session = Depends(get_db)):
    """필터 목록 조회"""
    try:
        filters = db.query(Filter).order_by(Filter.filter_id.asc()).all()
        return [
            {
                "filter_id": filter.filter_id,
                "name": filter.name
            }
            for filter in filters
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/", response_model=ContestListResponse)
def get_contests(db: Session = Depends(get_db)):
    """공모전 목록 조회"""
    try:
        # 전체 공모전 수 조회
        total_count = db.query(func.count(Contest.contest_id)).scalar()
        
        # 공모전 목록 조회 (마감일 기준 오름차순) - 태그 정보 포함
        contests = db.query(Contest)\
            .outerjoin(ContestTag, Contest.contest_id == ContestTag.contest_id)\
            .outerjoin(Tag, ContestTag.tag_id == Tag.tag_id)\
            .order_by(Contest.due_date.asc())\
            .all()
        
        # 각 공모전에 태그 정보 추가
        for contest in contests:
            contest.tags = []
            contest_tags = db.query(ContestTag, Tag)\
                .join(Tag, ContestTag.tag_id == Tag.tag_id)\
                .filter(ContestTag.contest_id == contest.contest_id)\
                .all()
            
            for contest_tag, tag in contest_tags:
                contest.tags.append(tag)
        
        return ContestListResponse(
            contests=contests,
            total_count=total_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/filter/{filter_id}", response_model=ContestListResponse)
def get_contests_by_filter(filter_id: int, db: Session = Depends(get_db)):
    """필터 ID에 따른 공모전 목록 조회"""
    try:
        # 필터 존재 여부 확인
        filter_exists = db.query(Filter).filter(Filter.filter_id == filter_id).first()
        if not filter_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Filter with ID {filter_id} not found"
            )
        
        # 해당 필터의 공모전 수 조회
        total_count = db.query(func.count(Contest.contest_id))\
            .join(ContestFilter, Contest.contest_id == ContestFilter.contest_id)\
            .filter(ContestFilter.filter_id == filter_id)\
            .scalar()
        
        # 해당 필터의 공모전 목록 조회 (마감일 기준 오름차순)
        contests = db.query(Contest)\
            .join(ContestFilter, Contest.contest_id == ContestFilter.contest_id)\
            .filter(ContestFilter.filter_id == filter_id)\
            .order_by(Contest.due_date.asc())\
            .all()
        
        # 각 공모전에 태그 정보 추가
        for contest in contests:
            contest.tags = []
            contest_tags = db.query(ContestTag, Tag)\
                .join(Tag, ContestTag.tag_id == Tag.tag_id)\
                .filter(ContestTag.contest_id == contest.contest_id)\
                .all()
            
            for contest_tag, tag in contest_tags:
                contest.tags.append(tag)
        
        return ContestListResponse(
            contests=contests,
            total_count=total_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )



@router.get("/latest", response_model=List[ContestSchema])
def get_latest_contests(db: Session = Depends(get_db)):
    """D-day 기준 공모전 3개 조회 (마감일이 가장 가까운 순)"""
    try:
        # D-day 기준 공모전 3개 조회 (마감일 기준 오름차순)
        latest_contests = db.query(Contest)\
            .order_by(Contest.due_date.asc())\
            .limit(3)\
            .all()
        
        # 각 공모전에 태그 정보 추가
        for contest in latest_contests:
            contest.tags = []
            contest_tags = db.query(ContestTag, Tag)\
                .join(Tag, ContestTag.tag_id == Tag.tag_id)\
                .filter(ContestTag.contest_id == contest.contest_id)\
                .all()
            
            for contest_tag, tag in contest_tags:
                contest.tags.append(tag)
        
        return latest_contests
        
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
