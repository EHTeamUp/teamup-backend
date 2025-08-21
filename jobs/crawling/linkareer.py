import requests
from bs4 import BeautifulSoup
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def get_contest_details(url, excluded_contests=None):
    """
    상세 페이지 URL을 받아 공모전 상세 정보를 크롤링합니다.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # HTTP 오류가 발생하면 예외를 발생시킵니다.
        soup = BeautifulSoup(response.text, 'html.parser')

        # 각 정보에 대한 선택자 (Selector)
        # 선택자는 웹사이트 구조 변경 시 업데이트 필요
        title_selector = "#__next > div.id-__StyledWrapper-sc-7c6de891-0.iifCfu > div > main > div > div > section:nth-child(1) > header > h1"

        # 정보 추출
        title_element = soup.select_one(title_selector)
        title = title_element.get_text(strip=True) if title_element else 'N/A'
        
        # 대상 필터링 - 대학생, 대학원생, 일반인, 누구나만 허용
        eligible_keywords = ['대학생', '대학원생', '일반인', '누구나','대상 제한 없음']
        is_eligible = False
        
        # 대상 정보 크롤링
        target_element = soup.select_one("#__next > div.id-__StyledWrapper-sc-7c6de891-0.iifCfu > div > main > div > div > section:nth-child(1) > div > article > div.ActivityInfomationField__StyledWrapper-sc-2edfa11d-0.bKwmrS > dl:nth-child(2) > dd")
        target = target_element.get_text(strip=True) if target_element else 'N/A'
        # 탭 문자 제거
        if target != 'N/A':
            target = target.replace('\t', '')
        
        if target != 'N/A':
            for keyword in eligible_keywords:
                if keyword in target:
                    is_eligible = True
                    break
        
        # 대상이 조건에 맞지 않으면 None 반환
        if not is_eligible:
            # 제외된 공모전 정보를 excluded_contests에 추가
            if excluded_contests is not None:
                excluded_contests.append({
                    "title": title,
                    "대상": target,
                    "site_url": url
                })
            return None
        
        poster_img = soup.select_one("#__next > div.id-__StyledWrapper-sc-7c6de891-0.iifCfu > div > main > div > div > section:nth-child(1) > div > div > div > div > figure > img")
        poster_url = poster_img['src'] if poster_img and poster_img.get('src') else 'N/A'
        # 상대 경로일 경우 절대 경로로 변환
        if poster_url != 'N/A' and poster_url.startswith('/'):
            poster_url = f"https://linkareer.com/{poster_url}"

        start_date_element = soup.select_one("#__next > div.id-__StyledWrapper-sc-7c6de891-0.iifCfu > div > main > div > div > section:nth-child(1) > div > article > div.ActivityInfomationField__StyledWrapper-sc-2edfa11d-0.bKwmrS > dl.RecruitPeriodField__StyledWrapper-sc-aaa21d80-0.eZkpum.ActivityInformationFieldBase__StyledWrapper-sc-2fb9f521-0.hXGgNs > dd > div > span:nth-child(2)")
        start_date = start_date_element.get_text(strip=True) if start_date_element else 'N/A'
        
        end_date_element = soup.select_one("#__next > div.id-__StyledWrapper-sc-7c6de891-0.iifCfu > div > main > div > div > section:nth-child(1) > div > article > div.ActivityInfomationField__StyledWrapper-sc-2edfa11d-0.bKwmrS > dl.RecruitPeriodField__StyledWrapper-sc-aaa21d80-0.eZkpum.ActivityInformationFieldBase__StyledWrapper-sc-2fb9f521-0.hXGgNs > dd > span:nth-child(3)")
        end_date = end_date_element.get_text(strip=True) if end_date_element else 'N/A'
        
        return {
            "title": title,
            "site_url": url,
            "poster_url": poster_url,
            "start_date": start_date,
            "end_date": end_date,
        }

    except Exception as e:
        print(f"An error occurred while parsing {url}: {e}")
        return None

def setup_driver():
    """
    Chrome WebDriver 설정
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 헤드리스 모드
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Chrome WebDriver 초기화 실패: {e}")
        print("Chrome WebDriver가 설치되어 있는지 확인하세요.")
        return None

def crawl_linkareer(i, driver=None, excluded_contests=None):
    """
    링커리어 목록 페이지에서 모든 공모전 정보를 크롤링합니다.
    Selenium을 사용하여 동적 페이지를 처리합니다.
    """

    list_url = f"https://linkareer.com/list/contest?filterBy_categoryIDs=35&filterType=CATEGORY&orderBy_direction=DESC&orderBy_field=CREATED_AT&page={i}"
    
    try:
        if driver is None:
            # requests를 사용한 기존 방식 (동적 콘텐츠가 없는 경우)
            response = requests.get(list_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            contest_list = soup.select('div.activity-list-card-item-wrapper')
        else:
            # Selenium을 사용한 동적 페이지 처리     
            # 페이지 로드 전에 쿠키와 캐시 클리어
            driver.delete_all_cookies()
            
            driver.get(list_url)
            
            # 페이지가 완전히 로드될 때까지 대기
            wait = WebDriverWait(driver, 15)  # 대기 시간 증가
            
            # 공모전 목록이 로드될 때까지 대기
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="activity-list-card"]')))
            except:
                print(f"페이지 {i}에서 공모전 목록을 찾을 수 없습니다.")
                return []
            
            # 페이지가 완전히 로드될 때까지 추가 대기
            time.sleep(5)  # 대기 시간 증가
            
            # 현재 페이지의 HTML 가져오기
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 공모전 항목들 찾기
            contest_list = soup.select('div[class*="activity-list-card"]')
            
            if not contest_list:
                # 다른 선택자 시도
                contest_list = soup.select('a[href*="/activity/"]')
        
        all_contests_data = []

        for idx, item in enumerate(contest_list):
            try:
                # 링크 찾기
                if item.name == 'a':
                    link_tag = item
                else:
                    link_tag = item.select_one('a[href*="/activity/"]')
                
                if link_tag:
                    relative_url = link_tag.get('href')
                    if relative_url:
                        # 상대 경로를 절대 경로로 변환
                        if relative_url.startswith('/'):
                            detail_url = f"https://linkareer.com{relative_url}"
                        else:
                            detail_url = relative_url
                        
                        # 상세 정보 크롤링
                        contest_data = get_contest_details(detail_url, excluded_contests)
                        if contest_data:
                            all_contests_data.append(contest_data)
                        else:
                            pass
                    else:
                        print(f"  [{idx+1}/{len(contest_list)}] href 속성을 찾을 수 없습니다.")
                else:
                    print(f"  [{idx+1}/{len(contest_list)}] 링크를 찾을 수 없습니다.")
                    
            except Exception as e:
                print(f"  [{idx+1}/{len(contest_list)}] 항목 처리 중 오류: {e}")
        return all_contests_data

    except Exception as e:
        print(f"페이지 {i} 크롤링 중 오류: {e}")
        return []


def save_all_data(all_data):
    """
    모든 데이터를 임시 JSON에 저장합니다 (집계기가 병합 저장).
    """
    from pathlib import Path
    temp_path = Path(__file__).parent / "linkareer_temp.json"
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    print(f"\nAll data saved to {temp_path}")
    print(f"Total contests saved: {len(all_data)}")

def save_excluded_temp(excluded_contests):
    """제외된 공모전을 임시 파일로 저장 (집계기가 병합 저장)."""
    from pathlib import Path
    temp_path = Path(__file__).parent / "linkareer_excluded_temp.json"
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(excluded_contests, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    try:
        all_contests = []
        excluded_contests = []  # 대상 조건에서 제외된 공모전들
        
        # 1-3 페이지 크롤링 (각 페이지마다 새로운 WebDriver 인스턴스 생성)
        for i in range(1, 4):
            # 각 페이지마다 새로운 WebDriver 인스턴스 생성
            driver = setup_driver()
            if not driver:
                print(f"페이지 {i}: WebDriver 초기화 실패. requests 방식으로 시도합니다.")
                driver = None
            
            try:
                page_data = crawl_linkareer(i, driver, excluded_contests)
                all_contests.extend(page_data)
                print(f"페이지 {i}: {len(page_data)}개 공모전 수집 완료")
                
            finally:
                # 각 페이지 처리 후 WebDriver 종료
                if driver:
                    driver.quit()
       
            # 페이지 간 대기 (WebDriver 재시작 시간 고려)
            if i < 3:  # 마지막 페이지가 아니면 대기
                time.sleep(3)
        
        # 데이터 저장
        save_all_data(all_contests)
        
        # 제외된 공모전은 집계기에서 저장 → 임시 파일로만 남김
        if excluded_contests:
            save_excluded_temp(excluded_contests)
            print(f"총 {len(excluded_contests)}개의 공모전이 조건 미충족으로 제외(임시 저장).")
            
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()