import requests
import json
import os
import base64
from PIL import Image
import io
import time
import ollama
import hashlib
import re
import sys
from datetime import datetime

# 데이터베이스 관련 import를 선택적으로 처리
try:
    from sqlalchemy.orm import Session
    from sqlalchemy import or_
    # 프로젝트 루트(teamup-backend)를 import 경로에 추가
    _CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    _BACKEND_ROOT = os.path.dirname(_CURRENT_DIR)
    if _BACKEND_ROOT not in sys.path:
        sys.path.append(_BACKEND_ROOT)

    from database import SessionLocal
    from models.contest import Contest, Tag, ContestTag, Filter, ContestFilter
    DB_AVAILABLE = True
except ImportError as e:
    print(f"데이터베이스 모듈 import 실패: {e}")
    print("데이터베이스 기능 없이 이미지 분석만 진행합니다.")
    DB_AVAILABLE = False
    SessionLocal = None
    Contest = Tag = ContestTag = Filter = ContestFilter = None

class TagGenerator:
    def __init__(self, ollama_host="http://localhost:11434"):
        """태그 생성기 초기화"""
        self.ollama_host = ollama_host
        self.model_name = "llava:7b"
        os.environ['OLLAMA_HOST'] = ollama_host
        self.image_cache = {}
        # jobs/data 디렉토리 기준
        self.base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        os.makedirs(self.base_dir, exist_ok=True)
        
        # 데이터베이스 연결 테스트
        if DB_AVAILABLE:
            self.db_available = self.test_db_connection()
        else:
            self.db_available = False
    
    def test_db_connection(self):
        """데이터베이스 연결 테스트"""
        if not DB_AVAILABLE:
            return False
        try:
            session = SessionLocal()
            # 간단한 쿼리로 연결 테스트
            contest_count = session.query(Contest).count()
            tag_count = session.query(Tag).count()
            filter_count = session.query(Filter).count()
            print(f"DB 연결 성공 - Contest: {contest_count}개, Tag: {tag_count}개, Filter: {filter_count}개")
            session.close()
            return True
        except Exception as e:
            print(f"DB 연결 실패: {str(e)}")
            print("데이터베이스 연결 없이 이미지 분석만 진행합니다.")
            return False

    def parse_date_maybe(self, date_str):
        if not date_str or date_str == 'N/A':
            return None
        date_formats = ['%Y-%m-%d', '%Y.%m.%d', '%Y/%m/%d', '%Y년 %m월 %d일', '%Y년%m월%d일']
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None

    def save_contests_to_db(self, contests):
        if not contests:
            return 0, 0
        
        # 데이터베이스 연결이 불가능한 경우
        if not self.db_available:
            print("데이터베이스 연결이 불가능하여 DB 저장을 건너뜁니다.")
            return 0, len(contests)
        
        session: Session = SessionLocal()
        inserted = 0
        skipped = 0
        newly_inserted_contests = []  # 새로 추가된 공모전들을 추적
        
        try:
            print(f"DB 저장 시작: {len(contests)}개 공모전")
            
            for i, c in enumerate(contests, 1):
                try:
                    title = (c.get('title') or '').strip()
                    site_url = (c.get('site_url') or '').strip()
                    poster_url = (c.get('poster_url') or '').strip()
                    start_date = self.parse_date_maybe(c.get('start_date') or '')
                    end_date = self.parse_date_maybe(c.get('end_date') or '')

                    # 데이터 검증
                    if not title or not site_url or not poster_url or start_date is None or end_date is None:
                        print(f"  [{i}] 데이터 누락으로 건너뜀: {title}")
                        skipped += 1
                        continue

                    # 중복 확인
                    exists = (
                        session.query(Contest)
                        .filter(or_(Contest.poster_img_url == poster_url, Contest.contest_url == site_url))
                        .first()
                    )
                    if exists:
                        print(f"  [{i}] 중복으로 건너뜀: {title}")
                        skipped += 1
                        continue

                    # Contest 엔티티 생성
                    contest_entity = Contest(
                        name=title,
                        contest_url=site_url,
                        poster_img_url=poster_url,
                        start_date=start_date,
                        due_date=end_date,
                    )
                    session.add(contest_entity)
                    session.flush()  # contest_id를 얻기 위해 flush
                    print(f"  [{i}] Contest 생성 완료: {title} (ID: {contest_entity.contest_id})")

                    # 태그 처리
                    tags_str = c.get('tags', '')
                    if tags_str and tags_str not in ['포스터 없음', '이미지 다운로드 실패']:
                        tag_names = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
                        print(f"  [{i}] 태그 처리: {tag_names}")
                        for tag_name in tag_names:
                            # 태그가 존재하는지 확인하고 없으면 생성
                            tag = session.query(Tag).filter(Tag.name == tag_name).first()
                            if not tag:
                                tag = Tag(name=tag_name)
                                session.add(tag)
                                session.flush()
                                print(f"    - 새 태그 생성: {tag_name} (ID: {tag.tag_id})")
                            else:
                                print(f"    - 기존 태그 사용: {tag_name} (ID: {tag.tag_id})")
                            
                            # ContestTag 관계 생성
                            contest_tag = ContestTag(
                                contest_id=contest_entity.contest_id,
                                tag_id=tag.tag_id
                            )
                            session.add(contest_tag)

                    # 필터 처리
                    filtering_str = c.get('filtering', '')
                    if filtering_str and filtering_str not in ['포스터 없음', '이미지 다운로드 실패']:
                        print(f"  [{i}] 필터 처리: {filtering_str}")
                        # 필터가 존재하는지 확인하고 없으면 생성
                        filter_obj = session.query(Filter).filter(Filter.name == filtering_str).first()
                        if not filter_obj:
                            filter_obj = Filter(name=filtering_str)
                            session.add(filter_obj)
                            session.flush()
                            print(f"    - 새 필터 생성: {filtering_str} (ID: {filter_obj.filter_id})")
                        else:
                            print(f"    - 기존 필터 사용: {filtering_str} (ID: {filter_obj.filter_id})")
                        
                        # ContestFilter 관계 생성
                        contest_filter = ContestFilter(
                            contest_id=contest_entity.contest_id,
                            filter_id=filter_obj.filter_id
                        )
                        session.add(contest_filter)

                    inserted += 1
                    newly_inserted_contests.append(contest_entity)  # 새로 추가된 공모전 추적
                    print(f"  [{i}] 완료: {title}")
                    
                except Exception as e:
                    print(f"  [{i}] 개별 공모전 처리 중 오류 ({title}): {str(e)}")
                    skipped += 1
                    continue

            if inserted > 0:
                session.commit()
                print(f"DB 저장 완료: {inserted}개 추가, {skipped}개 건너뜀")
                
                # 새로 추가된 공모전들에 대해 스킬 매칭 알림 전송
                try:
                    from utils.notification_service import NotificationService
                    for contest in newly_inserted_contests:
                        sent_count = NotificationService.notify_new_contest_with_skill_matching(session, contest)
                        print(f"  - '{contest.name}' 공모전 스킬 매칭 알림: {sent_count}명에게 전송")
                except Exception as e:
                    print(f"  - 스킬 매칭 알림 전송 중 오류: {e}")
            else:
                session.rollback()
                print("저장할 데이터가 없어 롤백")
            
            return inserted, skipped
            
        except Exception as e:
            session.rollback()
            print(f"DB 저장 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return 0, len(contests)  # 오류 발생 시 모든 항목을 건너뜀으로 처리
        finally:
            session.close()
    
    def download_and_encode_image(self, image_url):
        """URL에서 이미지를 다운로드하고 base64로 인코딩"""
        # 캐시 확인
        url_hash = hashlib.md5(image_url.encode()).hexdigest()
        if url_hash in self.image_cache:
            return self.image_cache[url_hash]
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(image_url, timeout=30, headers=headers)
            response.raise_for_status()
            
            image = Image.open(io.BytesIO(response.content))
            
            # 이미지 최적화
            target_size = self.get_optimal_size(image.size)
            if target_size != image.size:
                image = image.resize(target_size, Image.Resampling.LANCZOS)
            
            # RGB 변환
            if image.mode in ('RGBA', 'LA', 'P'):
                if image.mode == 'RGBA':
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1])
                    image = background
                else:
                    image = image.convert('RGB')
            
            # JPEG 변환 및 base64 인코딩
            img_byte_arr = io.BytesIO()
            quality = 85 if image.size[0] * image.size[1] > 400000 else 80
            image.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
            
            image_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
            self.image_cache[url_hash] = image_base64
            
            return image_base64
            
        except Exception as e:
            print(f"이미지 처리 오류: {e}")
            return None
    
    def get_optimal_size(self, original_size):
        """분석 정확도를 위한 최적 이미지 크기 계산"""
        width, height = original_size
        
        # 너무 작은 이미지는 확대
        if width < 400 or height < 400:
            scale = max(400 / width, 400 / height)
            return (int(width * scale), int(height * scale))
        
        # 너무 큰 이미지는 축소
        max_dimension = 1200
        if width > max_dimension or height > max_dimension:
            if width > height:
                return (max_dimension, int(height * (max_dimension / width)))
            else:
                return (int(width * (max_dimension / height)), max_dimension)
        
        return original_size
    
    def analyze_image(self, image_base64, contest_title=None):
        """이미지 분석 및 키워드 추출"""
        title_context = f"공모전 제목: {contest_title}" if contest_title else ""
        
        prompt = f"""
{title_context}

당신은 공모전 포스터 분석 전문가입니다. 이 포스터를 정확히 분석해서 3개의 키워드와 1개의 필터링 키워드를 추출해주세요.

**중요한 규칙:**
1. 공모전 제목을 정확히 읽고 이해하세요
2. 포스터에 실제로 나타나는 내용만 키워드로 추출하세요
3. 추측하지 말고 확실한 내용만 답변하세요
4. 키워드는 정확히 3개만 추출하세요
5. 필터링 키워드는 정확히 1개만 추출하세요

**키워드 추출 기준 (3개):**
- 공모전 제목의 핵심 단어
- 주제 분야 (AI, 데이터, 프로그래밍, 디자인, 해커톤, 논문 등)
- 대상 참가자 (대학생, 청년, 개발자, 연구자 등)
- 주최/주관 기관 (LG, 삼성, 정부기관 등)

**필터링 키워드 추출 기준 (1개):**
다음 6개 중에서 포스터 내용과 가장 관련이 깊은 것 1개만 선택:
- 웹/앱
- AI/데이터분석
- 정보보안/블록체인
- 아이디어/기획
- IOT/임베디드
- 게임

**답변 형식:** 키워드1, 키워드2, 키워드3, 필터링키워드

예시:
- "2025 춘천시 데이터 활용 해커톤" → "춘천시, 데이터, 해커톤, AI/데이터분석"
- "LG 프로그래밍 대회" → "LG, 프로그래밍, 대학생, 웹/앱"
- "AI 아이디어 공모전" → "AI, 아이디어, 청년, AI/데이터분석"

**주의:** 
1. 번호나 설명 없이 키워드만 쉼표로 구분해서 답변해주세요
2. 필터링 키워드는 반드시 마지막에 위치해야 합니다
3. 필터링 키워드는 위의 6개 중에서만 선택하세요
"""
        
        try:
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                images=[image_base64],
                stream=False,
                options={
                    "temperature": 0.05,
                    "top_p": 4096,
                    "repeat_penalty": 1.3,
                    "top_k": 23
                }
            )
            
            if 'response' in response:
                result = response['response'].strip()
                return self.validate_and_fix_keywords(result, contest_title)
            else:
                return "분석 응답 없음"
            
        except Exception as e:
            print(f"이미지 분석 오류: {e}")
            return f"분석 오류: {str(e)}"
    
    def analyze_image_with_retry(self, image_base64, contest_title=None, max_retries=2):
        """재시도 로직이 포함된 이미지 분석"""
        for attempt in range(max_retries + 1):
            try:
                result = self.analyze_image(image_base64, contest_title)
                
                if self.is_valid_result(result):
                    return result
                elif attempt < max_retries:
                    time.sleep(1)
                    continue
                else:
                    return self.generate_fallback_keywords(contest_title)
                    
            except Exception as e:
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                else:
                    return self.generate_fallback_keywords(contest_title)
        
        return "분석 실패"
    
    def is_valid_result(self, result):
        """분석 결과가 유효한지 검증"""
        if not result or result in ["분석 응답 없음", "분석 실패", "분석 오류"]:
            return False
        
        keywords = [k.strip() for k in result.split(',') if k.strip()]
        if len(keywords) != 4:
            return False
        
        valid_filtering_keywords = ['웹/앱', '데이터분석', 'AI', '아이디어', '기획', 'IOT']
        
        if keywords[-1] not in valid_filtering_keywords:
            return False
        
        for keyword in keywords:
            if len(keyword) > 31 or ':' in keyword or '.' in keyword:
                return False
        
        return True
    
    def generate_fallback_keywords(self, contest_title):
        """분석 실패 시 제목에서 기본 키워드 생성"""
        if not contest_title:
            return "공모전, 대회, 참가, 아이디어"
        
        keywords = []
        
        # 기본 키워드 추가
        if "해커톤" in contest_title:
            keywords.append("해커톤")
        if "공모전" in contest_title:
            keywords.append("공모전")
        if "대회" in contest_title:
            keywords.append("대회")
        
        # 대상자 키워드 추가
        if any(word in contest_title for word in ["대학생", "청년", "학생"]):
            keywords.append("대학생")
        
        # 주제 키워드 추가
        if any(word in contest_title for word in ["AI", "인공지능", "데이터", "프로그래밍","기획","디자인","논문"]):
            keywords.append("AI")   
        
        # 중복 제거하고 3개로 제한
        keywords = list(dict.fromkeys(keywords))[:3]
        
        # 필터링 키워드 결정
        filtering_keyword = "아이디어"
        if any(word in contest_title for word in ["AI", "인공지능"]):
            filtering_keyword = "AI"
        elif any(word in contest_title for word in ["데이터", "분석","과학"]):
            filtering_keyword = "데이터분석"
        elif any(word in contest_title for word in ["웹", "앱", "프로그래밍", "개발"]):
            filtering_keyword = "웹/앱"
        elif any(word in contest_title for word in ["기획", "계획", "설계"]):
            filtering_keyword = "기획"
        elif any(word in contest_title for word in ["IOT", "사물인터넷", "통신"]):
            filtering_keyword = "IOT"
        
        # 키워드가 3개 미만이면 기본 키워드로 채움
        while len(keywords) < 3:
            if "공모전" not in keywords:
                keywords.append("공모전")
            elif "대회" not in keywords:
                keywords.append("대회")
            else:
                keywords.append("참가")
        
        # 특수문자 제거
        keywords = [self.clean_keyword(kw) for kw in keywords]
        filtering_keyword = self.clean_keyword(filtering_keyword)
        
        return ', '.join(keywords) + f', {filtering_keyword}'
    
    def validate_and_fix_keywords(self, keywords, contest_title):
        """키워드를 검증하고 수정"""
        if not keywords or keywords == "분석 응답 없음":
            return keywords
        
        keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
        valid_filtering_keywords = ['웹/앱', '데이터분석', 'AI', '아이디어', '기획', 'IOT']
        
        # 필터링 키워드 찾기
        filtering_keyword = None
        regular_keywords = []
        
        for kw in keyword_list:
            if kw in valid_filtering_keywords:
                filtering_keyword = kw
            else:
                regular_keywords.append(kw)
        
        # 필터링 키워드가 없으면 기본값 설정
        if not filtering_keyword:
            filtering_keyword = "아이디어"
        
        # 일반 키워드가 3개 미만이면 제목에서 간단히 추출
        if len(regular_keywords) < 3 and contest_title:
            if "해커톤" in contest_title and "해커톤" not in regular_keywords:
                regular_keywords.append("해커톤")
            if "AI" in contest_title and "AI" not in regular_keywords:
                regular_keywords.append("AI")
            if "데이터" in contest_title and "데이터" not in regular_keywords:
                regular_keywords.append("데이터")
            if "프로그래밍" in contest_title and "프로그래밍" not in regular_keywords:
                regular_keywords.append("프로그래밍")
        
        # 일반 키워드가 3개 초과면 상위 3개만 선택
        if len(regular_keywords) > 3:
            regular_keywords = regular_keywords[:3]
        
        # 일반 키워드가 3개 미만이면 기본 키워드로 채움
        while len(regular_keywords) < 3:
            if "공모전" not in regular_keywords:
                regular_keywords.append("공모전")
            elif "대회" not in regular_keywords:
                regular_keywords.append("대회")
            else:
                regular_keywords.append("참가")
        
        # 중복 제거 및 특수문자 제거
        regular_keywords = list(dict.fromkeys(regular_keywords))
        regular_keywords = [self.clean_keyword(kw) for kw in regular_keywords]
        filtering_keyword = self.clean_keyword(filtering_keyword)
        
        return ', '.join(regular_keywords) + f', {filtering_keyword}'
    
    def clean_keyword(self, keyword):
        """키워드에서 특수문자 제거"""
        cleaned = re.sub(r'[^\w\s가-힣]', '', keyword)
        cleaned = cleaned.strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned
    
    def clean_keywords_string(self, keywords_string):
        """키워드 문자열에서 각 키워드의 특수문자 제거"""
        if not keywords_string:
            return keywords_string
        
        keywords = [self.clean_keyword(kw.strip()) for kw in keywords_string.split(',')]
        keywords = [kw for kw in keywords if kw]
        return ', '.join(keywords)
    
    def get_filtering_tag_from_title(self, title):
        """제목에서 필터링 태그 결정"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['웹', '앱', '앱개발', '웹개발', '프로그래밍', '개발']):
            return "웹/앱"
        elif any(word in title_lower for word in ['데이터', '분석', '데이터분석', '과학', '통계']):
            return "데이터분석"
        elif any(word in title_lower for word in ['ai', '인공지능', '머신러닝', '딥러닝']):
            return "AI"
        elif any(word in title_lower for word in ['기획', '계획', '설계', '전략']):
            return "기획"
        elif any(word in title_lower for word in ['iot', '사물인터넷', '통신', '센서']):
            return "IOT"
        else:
            return "아이디어"
    
    def extract_tags_from_final_contest(self, input_file_path=None, output_file_path=None):
        """all_contests.json 파일에서 포스터 URL을 읽어서 태그를 추출"""
        try:
            if input_file_path is None:
                input_file_path = os.path.join(self.base_dir, "all_contests.json")
            if output_file_path is None:
                output_file_path = os.path.join(self.base_dir, "contest_with_tags.json")

            with open(input_file_path, 'r', encoding='utf-8') as f:
                contests = json.load(f)
            
            print(f"총 {len(contests)}개의 공모전을 분석합니다...")
            
            # output_file_path는 위에서 base_dir 기준으로 설정됨
            
            results = []
            batch_for_db = []
            if os.path.exists(output_file_path):
                try:
                    with open(output_file_path, 'r', encoding='utf-8') as f:
                        results = json.load(f)
                    print(f"기존 결과 파일을 불러왔습니다. {len(results)}개 완료됨")
                except json.JSONDecodeError:
                    print("분석을 시작합니다.")
            
            processed_titles = {item.get('title') for item in results}
            
            for i, contest in enumerate(contests, 1):
                title = contest.get('title', '제목 없음')
                
                if title in processed_titles:
                    print(f"[{i}/{len(contests)}] 이미 처리됨: {title}")
                    continue
                
                print(f"\n[{i}/{len(contests)}] 분석 중: {title}")
                
                poster_url = contest.get('poster_url', '')
                
                if poster_url == 'N/A' or not poster_url:
                    print("  - 포스터 URL이 없습니다.")
                    contest['tags'] = "포스터 없음"
                    contest['filtering'] = self.get_filtering_tag_from_title(title)
                    
                    print(f"  - 추출된 키워드: {contest['tags']}")
                    print(f"  - 필터링 태그: {contest['filtering']}")
                    
                    if 'source' in contest:
                        del contest['source']
                    
                    results.append(contest)
                    batch_for_db.append(contest)
                    continue
                
                try:
                    image_base64 = self.download_and_encode_image(poster_url)
                    
                    if image_base64 is None:
                        print("  - 이미지 다운로드 실패")
                        contest['tags'] = "이미지 다운로드 실패"
                        contest['filtering'] = self.get_filtering_tag_from_title(title)
                        
                        print(f"  - 추출된 키워드: {contest['tags']}")
                        print(f"  - 필터링 태그: {contest['filtering']}")
                        
                        if 'source' in contest:
                            del contest['source']
                        
                        results.append(contest)
                        batch_for_db.append(contest)
                        continue
                    
                    tags = self.analyze_image_with_retry(image_base64, title)
                    
                    # 태그에서 필터링 키워드 분리
                    tag_parts = tags.split(',')
                    if len(tag_parts) >= 4:
                        filtering_keyword = self.clean_keyword(tag_parts[-1].strip())
                        regular_tags = ','.join([self.clean_keyword(kw.strip()) for kw in tag_parts[:-1]])
                        
                        # 제목 기반 필터링 태그 우선 적용
                        title_filtering = self.get_filtering_tag_from_title(title)
                        if title_filtering != filtering_keyword:
                            print(f"  - 제목 기반 필터링 태그로 변경: {filtering_keyword} → {title_filtering}")
                            filtering_keyword = title_filtering
                        
                        contest['tags'] = regular_tags
                        contest['filtering'] = filtering_keyword
                        
                        # 추출된 키워드와 필터링 태그 출력
                        print(f"  - 추출된 키워드: {regular_tags}")
                        print(f"  - 필터링 태그: {filtering_keyword}")
                    else:
                        contest['tags'] = self.clean_keywords_string(tags)
                        contest['filtering'] = "아이디어"
                        print(f"  - 추출된 키워드: {contest['tags']}")
                        print(f"  - 필터링 태그: {contest['filtering']}")
                
                    if 'source' in contest:
                        del contest['source']
                    
                    results.append(contest)
                    batch_for_db.append(contest)
                    
                    # 3개마다 중간 저장
                    if len(results) % 3 == 0:
                        with open(output_file_path, 'w', encoding='utf-8') as f:
                            json.dump(results, f, ensure_ascii=False, indent=2)
                        try:
                            inserted, skipped = self.save_contests_to_db(batch_for_db)
                            print(f"  -> 중간 저장(DB): 추가 {inserted}건, 건너뜀 {skipped}건")
                        except Exception as e:
                            print(f"  -> 중간 저장(DB) 실패: {e}")
                        batch_for_db = []
                    
                    time.sleep(1.5)
                    
                except Exception as e:
                    print(f"  - 분석 중 오류 발생: {e}")
                    contest['tags'] = f"분석 오류: {str(e)}"
                    contest['filtering'] = self.get_filtering_tag_from_title(title)

                    print(f"  - 추출된 키워드: {contest['tags']}")
                    print(f"  - 필터링 태그: {contest['filtering']}")

                    if 'source' in contest:
                        del contest['source']

                    results.append(contest)
                    batch_for_db.append(contest)
            
            # 남은 배치 DB 저장
            if batch_for_db:
                try:
                    inserted, skipped = self.save_contests_to_db(batch_for_db)
                    print(f"  -> 최종 저장(DB): 추가 {inserted}건, 건너뜀 {skipped}건")
                except Exception as e:
                    print(f"  -> 최종 저장(DB) 실패: {e}")

            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"\n분석 완료! 결과가 {output_file_path}에 저장되었습니다.")
            print(f"총 {len(results)}개의 공모전이 처리되었습니다.")
            return results
            
        except Exception as e:
            print(f"파일 처리 오류: {e}")
            return None

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='태그 생성기 - all_contests.json에서 포스터 이미지 태그 추출')
    parser.add_argument('--input-file', default=None,
                        help='입력 파일 경로 (기본값: jobs/all_contests.json)')
    parser.add_argument('--output-file', default=None,
                        help='출력 파일 경로 (기본값: jobs/contest_with_tags.json)')
    parser.add_argument('--ollama-host', default='http://localhost:11434',
                        help='Ollama 서버 호스트 (기본값: http://localhost:11434)')

    args = parser.parse_args()

    generator = TagGenerator(ollama_host=args.ollama_host)

    # 기본 경로 설정 (jobs 디렉토리 기준)
    input_file = args.input_file or os.path.join(generator.base_dir, 'all_contests.json')
    output_file = args.output_file or os.path.join(generator.base_dir, 'contest_with_tags.json')

    if not os.path.exists(input_file):
        print(f"오류: 입력 파일을 찾을 수 없습니다: {input_file}")
        exit(1)

    print(f"입력 파일: {input_file}")
    print(f"출력 파일: {output_file}")

    try:
        print("\n" + "="*50)
        print("태그 추출 시작")
        print("="*50)

        generator.extract_tags_from_final_contest(input_file, output_file)

        print("\n" + "="*50)
        print("태그 추출이 완료되었습니다!")
        print("="*50)

    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()
