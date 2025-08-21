"""
통합 공모전 크롤러
teamup-backend/jobs/crawling 폴더의 모든 크롤링 파일들을 순차적으로 실행합니다.
"""
import sys
import json
import logging
import subprocess
import time
import hashlib
import requests
from datetime import datetime
from pathlib import Path

# 현재 파일의 디렉토리를 기준으로 crawling 폴더 경로 설정
CURRENT_DIR = Path(__file__).parent
CRAWLING_DIR = CURRENT_DIR / "crawling"
DATA_DIR = CURRENT_DIR / "data"

# 데이터 디렉토리 생성
DATA_DIR.mkdir(exist_ok=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class CrawlingExecutor:
    """크롤링 파일들을 실행하는 클래스"""
    
    def __init__(self):
        self.crawling_dir = CRAWLING_DIR
        self.all_contests = []
        self.excluded_contests = []
        self.duplicate_posters = []
    
    def get_crawling_files(self):
        """crawling 폴더에서 실행할 Python 파일들을 찾습니다."""
        crawling_files = []
        
        if not self.crawling_dir.exists():
            logger.error(f"crawling 폴더를 찾을 수 없습니다: {self.crawling_dir}")
            return crawling_files
        
        for file_path in self.crawling_dir.glob("*.py"):
            if file_path.is_file() and file_path.name != "__init__.py":
                crawling_files.append(file_path)
        
        # 실행 순서 정의 (thinkyou -> linkareer -> contestkorea)
        execution_order = ["thinkyou.py", "linkareer.py", "contestkorea.py"]
        sorted_files = []
        
        for filename in execution_order:
            for file_path in crawling_files:
                if file_path.name == filename:
                    sorted_files.append(file_path)
                    break
        
        # 순서에 없는 파일들도 추가
        for file_path in crawling_files:
            if file_path not in sorted_files:
                sorted_files.append(file_path)
        
        return sorted_files
    
    def execute_crawling_file(self, file_path):
        """개별 크롤링 파일을 실행합니다."""
        site_name = file_path.stem
        
        logger.info(f"\n{site_name} 크롤링 시작")
        
        try:
            # Python 파일을 subprocess로 실행
            result = subprocess.run(
                [sys.executable, str(file_path)],
                capture_output=True,
                text=True,
                cwd=str(self.crawling_dir),
                timeout=300  # 5분 타임아웃
            )
            
            if result.returncode == 0:
                logger.info(f"{site_name} 크롤링 성공!")
                if result.stdout:
                    logger.info(f"출력: {result.stdout.strip()}")
                # 크롤링 결과 파일 읽기 (각 크롤러가 생성하는 임시 파일)
                temp_file = self.crawling_dir / f"{site_name}_temp.json"
                if temp_file.exists():
                    try:
                        with open(temp_file, 'r', encoding='utf-8') as f:
                            contests = json.load(f)
                        if isinstance(contests, list):
                            self.all_contests.extend(contests)
                            logger.info(f"{site_name}: {len(contests)}개 공모전 수집")
                        else:
                            logger.warning(f"{site_name} 임시 파일 포맷이 리스트가 아님: {temp_file}")
                    except Exception as e:
                        logger.error(f"{site_name} 임시 파일 읽기 오류: {e}")
                    finally:
                        try:
                            temp_file.unlink()
                        except Exception:
                            pass

                # 제외된 공모전 임시 파일 읽기
                excluded_temp = self.crawling_dir / f"{site_name}_excluded_temp.json"
                if excluded_temp.exists():
                    try:
                        with open(excluded_temp, 'r', encoding='utf-8') as f:
                            excluded = json.load(f)
                        if isinstance(excluded, list):
                            self.excluded_contests.extend(excluded)
                            logger.info(f"{site_name}: 제외 {len(excluded)}개 누적")
                    except Exception as e:
                        logger.error(f"{site_name} 제외 임시 파일 읽기 오류: {e}")
                    finally:
                        try:
                            excluded_temp.unlink()
                        except Exception:
                            pass
                
            else:
                logger.error(f"{site_name} 크롤링 실패!")
                if result.stderr:
                    logger.error(f"오류: {result.stderr.strip()}")
                if result.stdout:
                    logger.info(f"출력: {result.stdout.strip()}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"{site_name} 크롤링 타임아웃 (5분 초과)")
        except Exception as e:
            logger.error(f"{site_name} 크롤링 중 예외 발생: {e}")
    
    def save_all_results(self):
        """모든 크롤링 결과를 통합하여 저장합니다 (마감 지난 공모전 제거 + 포스터 해시 중복 제거, 중복은 별도 파일로 저장)."""
        try:
            all_contests_path = DATA_DIR / "all_contests.json"
            existing_contests = []
            if all_contests_path.exists():
                try:
                    with open(all_contests_path, 'r', encoding='utf-8') as f:
                        existing_contests = json.load(f) or []
                except Exception as e:
                    logger.warning(f"기존 데이터 읽기 실패, 새로 생성합니다: {e}")
                    existing_contests = []
            merged, duplicates = self._merge_by_poster_hash(existing_contests, self.all_contests)
            with open(all_contests_path, 'w', encoding='utf-8') as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)
            logger.info(f"통합 저장 완료(중복 제거 포함): {len(merged)}개 공모전")
            logger.info(f"저장 경로: {all_contests_path}")

            # 중복 포스터 정보 저장
            self.duplicate_posters = duplicates
            duplicate_path = DATA_DIR / "duplicate_posters.json"
            with open(duplicate_path, 'w', encoding='utf-8') as f:
                json.dump(self.duplicate_posters, f, ensure_ascii=False, indent=2)
            logger.info(f"중복 포스터 저장: {len(self.duplicate_posters)}건 → {duplicate_path}")
        except Exception as e:
            logger.error(f"데이터 저장 중 오류: {e}")

    def _parse_end_date(self, end_date_str: str):
        if not end_date_str:
            return None
        fmt_list = ["%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d", "%Y %m %d"]
        for fmt in fmt_list:
            try:
                return datetime.strptime(end_date_str, fmt).date()
            except ValueError:
                continue
        return None

    def _is_not_expired(self, contest: dict) -> bool:
        try:
            end_str = contest.get("end_date")
            if not end_str:
                return True
            end_dt = self._parse_end_date(end_str)
            if end_dt is None:
                return True
            return end_dt >= datetime.now().date()
        except Exception:
            return True

    def _get_image_hash(self, url: str):
        try:
            if not url or url == "N/A":
                return None
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            return hashlib.md5(resp.content).hexdigest()
        except Exception:
            return None

    def _merge_by_poster_hash(self, existing_list: list, new_list: list):
        # 1) 기존 데이터에서 마감 지난 공모전 제거
        filtered_existing = [c for c in existing_list if isinstance(c, dict) and self._is_not_expired(c)]
        # 2) 기존 데이터의 포스터 해시셋 생성
        existing_hashes = set()
        duplicates = []
        seen_existing = set()
        for c in filtered_existing:
            h = self._get_image_hash(c.get("poster_url", ""))
            if not h:
                continue
            if h in seen_existing:
                duplicates.append({
                    "reason": "existing-duplicate",
                    "hash": h,
                    "title": c.get("title"),
                    "site_url": c.get("site_url"),
                    "poster_url": c.get("poster_url"),
                })
            seen_existing.add(h)
            existing_hashes.add(h)
        # 3) 신규 데이터에서 중복 제거 후 병합
        unique_new = []
        seen_new = set()
        for c in new_list:
            if not isinstance(c, dict):
                continue
            h = self._get_image_hash(c.get("poster_url", ""))
            if h is None:
                unique_new.append(c)
                continue
            if h in existing_hashes or h in seen_new:
                duplicates.append({
                    "reason": "conflict-with-existing" if h in existing_hashes else "duplicate-in-new",
                    "hash": h,
                    "title": c.get("title"),
                    "site_url": c.get("site_url"),
                    "poster_url": c.get("poster_url"),
                })
                continue
            if h not in existing_hashes:
                unique_new.append(c)
                existing_hashes.add(h)
                seen_new.add(h)
        return filtered_existing + unique_new, duplicates

    def save_excluded_results(self):
        """제외된 공모전 결과를 통합 저장합니다 (기존 데이터 유지, 중복 처리 없음)."""
        try:
            excluded_path = DATA_DIR / "excluded_contests.json"
            existing = []
            if excluded_path.exists():
                try:
                    with open(excluded_path, 'r', encoding='utf-8') as f:
                        existing = json.load(f) or []
                except Exception as e:
                    logger.warning(f"기존 제외 데이터 읽기 실패, 새로 생성합니다: {e}")
                    existing = []
            merged = (existing if isinstance(existing, list) else []) + self.excluded_contests
            with open(excluded_path, 'w', encoding='utf-8') as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)
            logger.info(f"제외 목록 저장 완료: {len(merged)}건")
            logger.info(f"저장 경로: {excluded_path}")
        except Exception as e:
            logger.error(f"제외 데이터 저장 중 오류: {e}")
    
    def run_all_crawling(self):
        """모든 크롤링을 실행합니다."""
        
        start_time = time.time()
        
        # 크롤링 파일들 찾기
        crawling_files = self.get_crawling_files()
        
        if not crawling_files:
            logger.error("실행할 크롤링 파일을 찾을 수 없습니다.")
            return
        
        for file_path in crawling_files:
            logger.info(f"  - {file_path.name}")
        
        # 각 크롤링 파일 실행
        for file_path in crawling_files:
            self.execute_crawling_file(file_path)
            time.sleep(2)  # 파일 간 간격

        # 크롤링 완료 후 결과 저장 (마감 제거 + 해시 중복 제거)
        if self.all_contests:
            self.save_all_results()
        
        # 제외 목록 저장
        if self.excluded_contests:
            self.save_excluded_results()


def main():
    """메인 함수"""
    executor = CrawlingExecutor()
    return executor.run_all_crawling()


if __name__ == "__main__":
    main() 