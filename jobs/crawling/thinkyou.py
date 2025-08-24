from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import requests
from bs4 import BeautifulSoup
import time
import json

def setup_driver():
    """Chrome 드라이버 설정"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 헤드리스 모드 활성화
    chrome_options.add_argument("--headless")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def select_science_engineering_category(driver):
    """과학/공학 카테고리 체크박스 클릭"""
    try:
        # 페이지 로딩 대기
        time.sleep(3)
        
        # 여러 가능한 선택자로 과학/공학 체크박스 찾기
        checkbox_selectors = [
            # 정확한 ID와 value를 사용한 선택자
            "//input[@id='serfield_07' and @value='5']",
            "//input[@name='serfield' and @value='5']",
            # 기존 선택자들 (백업용)
            "//input[@type='checkbox' and following-sibling::label[contains(text(), '과학/공학')]]",
            "//label[contains(text(), '과학/공학')]/preceding-sibling::input[@type='checkbox']",
            "//input[@type='checkbox' and @value='과학/공학']",
            "//div[contains(@class, 'category')]//input[@type='checkbox' and following-sibling::*[contains(text(), '과학/공학')]]",
            "//input[@type='checkbox' and parent::*[contains(., '과학/공학')]]"
        ]
        
        science_checkbox = None
        for selector in checkbox_selectors:
            try:
                science_checkbox = driver.find_element(By.XPATH, selector)
                break
            except NoSuchElementException:
                continue
        
        if not science_checkbox:
            print("과학/공학 체크박스를 찾을 수 없습니다.")
            return False
        
        # 체크박스가 체크되어 있지 않으면 클릭
        if not science_checkbox.is_selected():
            # JavaScript로 클릭 (더 안정적)
            driver.execute_script("arguments[0].click();", science_checkbox)
            
            # 페이지 로딩 대기
            time.sleep(3)
        else:
            print("과학/공학 카테고리가 이미 선택되어 있습니다.")
        
        return True
        
    except Exception as e:
        print(f"카테고리 선택 중 오류: {e}")
        return False

def get_contest_list_with_status(driver):
    """BeautifulSoup을 사용하여 공모전 목록과 상태 정보 가져오기"""
    try:
        # 현재 페이지의 HTML 가져오기
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 지정된 선택자로 공모전 목록 가져오기
        contest_selector = "#contestArea > div.board_list.contest > div > div.tr"
        contest_elements = soup.select(contest_selector)
        
        if contest_elements:
            
            # 각 공모전의 상태 확인
            active_contests = []
            found_closed_contest = False
            
            for i, contest_element in enumerate(contest_elements[1:], 1):  # 첫 번째는 헤더이므로 제외
                try:
                    # 상태 정보 찾기
                    status_element = contest_element.select_one("div.statNew > p")
                    if status_element:
                        status_text = status_element.get_text(strip=True)
                        
                        # 마감 관련 키워드 확인
                        if status_text == "마감":
                            found_closed_contest = True
                            break  # 마감된 공모전을 발견하면 중단
                        else:
                            active_contests.append(contest_element)
                    else:
                        active_contests.append(contest_element)
                        
                except Exception as e:
                    print(f"공모전 {i} 상태 확인 중 오류: {e}")
                    active_contests.append(contest_element)
            
            return active_contests, found_closed_contest
        else:
            print("공모전 요소를 찾을 수 없습니다.")
            return [], False
        
    except Exception as e:
        print(f"공모전 목록 가져오기 실패: {e}")
        return [], False

def check_next_page_exists(driver):
    """다음 페이지가 존재하는지 확인"""
    try:
        # 다음 페이지 버튼 찾기
        next_page_selectors = [
            "a.next",
            ".pagination a:contains('다음')",
            ".pagination a[title='다음']",
            ".pagination a[aria-label='다음']",
            "a[onclick*='next']",
            ".paging a:last-child"
        ]
        
        for selector in next_page_selectors:
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, selector)
                if next_button and next_button.is_enabled():
                    return next_button
            except NoSuchElementException:
                continue
        
        # BeautifulSoup으로도 확인
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 페이지네이션 영역에서 다음 페이지 링크 찾기
        pagination_selectors = [
            ".pagination a",
            ".paging a",
            ".page a",
            "a[href*='page']"
        ]
        
        for selector in pagination_selectors:
            links = soup.select(selector)
            for link in links:
                link_text = link.get_text(strip=True)
                if link_text in ["다음", ">", "▶", "next", "Next"]:
                    print(f"다음 페이지 링크 발견: {link_text}")
                    return True
        
        print("다음 페이지가 없습니다.")
        return False
        
    except Exception as e:
        print(f"다음 페이지 확인 중 오류: {e}")
        return False

def go_to_next_page(driver):
    """다음 페이지로 이동"""
    try:
        # 다음 페이지 버튼 찾기
        next_page_selectors = [
            "a.next",
            ".pagination a:contains('다음')",
            ".pagination a[title='다음']",
            ".pagination a[aria-label='다음']",
            "a[onclick*='next']",
            ".paging a:last-child"
        ]
        
        for selector in next_page_selectors:
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, selector)
                if next_button and next_button.is_enabled():
                    next_button.click()
                    time.sleep(3)  # 페이지 로딩 대기
                    return True
            except NoSuchElementException:
                continue
        
        # BeautifulSoup으로 링크 찾아서 클릭
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        pagination_selectors = [
            ".pagination a",
            ".paging a",
            ".page a",
            "a[href*='page']"
        ]
        
        for selector in pagination_selectors:
            links = soup.select(selector)
            for link in links:
                link_text = link.get_text(strip=True)
                if link_text in ["다음", ">", "▶", "next", "Next"]:
                    href = link.get('href')
                    if href:
                        if href.startswith('http'):
                            driver.get(href)
                        else:
                            driver.get(f"https://thinkyou.co.kr{href}")
                        time.sleep(3)
                        print("다음 페이지로 이동했습니다.")
                        return True
        
        print("다음 페이지로 이동할 수 없습니다.")
        return False
        
    except Exception as e:
        print(f"다음 페이지 이동 중 오류: {e}")
        return False

def get_contest_list(driver):
    """BeautifulSoup을 사용하여 공모전 목록 가져오기"""
    try:
        # 현재 페이지의 HTML 가져오기
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 지정된 선택자로 공모전 목록 가져오기
        contest_selector = "#contestArea > div.board_list.contest > div > div.tr"
        
        contest_elements = soup.select(contest_selector)
        
        if contest_elements:
            print(f"공모전 요소 {len(contest_elements)}개 발견")
        else:
            print("공모전 요소를 찾을 수 없습니다.")
        
        return contest_elements
        
    except Exception as e:
        print(f"공모전 목록 가져오기 실패: {e}")
        return []

def extract_contest_info(contest_element, excluded_contests=None):
    """공모전 상세 페이지에서 정보 추출 (requests 사용, contestkorea/data.json 형식에 맞춤)"""
    try:
        # 목록에서 기본 정보 추출
        title = ""
        site_url = ""
        
        # 제목과 링크 추출
        link_elem = contest_element.find('a', href=True)
        if link_elem:
            title = link_elem.get_text(strip=True)
            site_url = link_elem.get('href')
            if site_url and not site_url.startswith('http'):
                site_url = "https://thinkyou.co.kr" + site_url
        
        if not title or not site_url:
            print("제목 또는 링크를 찾을 수 없습니다.")
            return None
        
        response = requests.get(site_url, timeout=10)
        response.raise_for_status()
        
        # 상세 페이지 HTML 파싱
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 포스터 이미지 URL 추출
        poster_img = soup.select_one("#printArea > div.contest_view > div > div.thumb > img")
        poster_url = poster_img['src'] if poster_img and poster_img.get('src') else 'N/A'
        # 상대 경로일 경우 절대 경로로 변환
        if poster_url != 'N/A' and poster_url.startswith('/'):
            poster_url = f"https://thinkyou.co.kr{poster_url}"

        
        # 시작일과 종료일 추출
        date = 'N/A'
        tr_elements = soup.select("#printArea > div.contest_view > div > div.rightArea > table > tbody > tr")
        
        for tr in tr_elements:
            th_element = tr.select_one("th")
            if th_element and th_element.get_text(strip=True) == "접수기간":
                td_element = tr.select_one("td")
                if td_element:
                    date = td_element.get_text(strip=True)
                break
        
        if date != 'N/A':
            date_list = date.split('~')
            start_date = date_list[0].strip()
            end_date = date_list[1].strip() if len(date_list) > 1 else 'N/A'
        else:
            start_date = 'N/A'
            end_date = 'N/A'
            
        # 응모자격 확인
        eligible_keywords = ['대학생', '대학원생', '일반인', '누구나', '대학(원)생', '내국인', '대한민국 국민', '나이 무관', '대학/대학원','비전공자', '연구자', '학생']
        is_eligible = False
        eligibility_text = "응모자격 정보를 찾을 수 없음"
        
        try:
            # 응모자격이 있는 dt 요소 찾기
            dt_elements = soup.select("#printArea > div.contest_outline > dl > dt")
            for dt in dt_elements:
                if dt.get_text(strip=True) in ["응모자격", "참여대상", "참가대상", "교육대상"]:
                    # 해당 dt의 다음 dd 요소에서 응모자격 정보 가져오기
                    dd_element = dt.find_next_sibling('dd')
                    if dd_element:
                        eligibility_text = dd_element.get_text(strip=True)
                        
                        # 키워드 확인
                        for keyword in eligible_keywords:
                            if keyword in eligibility_text:
                                is_eligible = True
                                break
                    break
            
            if not is_eligible:
                
                # 초등학교, 중학교, 고등학교 키워드가 있는지 확인
                school_keywords = ['초등학교', '중학교', '고등학교','초등부','중등부','고등부']
                has_school_keyword = any(keyword in eligibility_text for keyword in school_keywords)
                
                if not has_school_keyword:
                    # 제외된 공모전 정보를 excluded_contests에 추가
                    if excluded_contests is not None:
                        excluded_contests.append({
                            "title": title,
                            "응모자격": eligibility_text,
                            "site_url": site_url
                        })
                
                return None
                
        except Exception as e:
            print(f"응모자격 확인 중 오류: {e}")

            if excluded_contests is not None:
                excluded_contests.append({
                    "title": title,
                    "응모자격": f"오류 발생: {str(e)}",
                    "site_url": site_url
                })
            return None
        
        return {
            "title": title,
            "site_url": site_url,
            "poster_url": poster_url,
            "start_date": start_date,
            "end_date": end_date,
        }
        
    except Exception as e:
        print(f"공모전 정보 추출 중 오류: {e}")
        return None

def crawl_thinkyou_contests():
    """씽유 사이트에서 공모전 크롤링 (여러 페이지 순회)"""
    driver = None
    contests = []
    excluded_contests = []  # 응모자격 조건에서 떨어진 공모전들
    page_num = 1
    found_closed_contest = False
    
    try:
        driver = setup_driver()
        url = "https://thinkyou.co.kr/contest/"
        
        driver.get(url)
        
        # 과학/공학 카테고리 선택
        if not select_science_engineering_category(driver):
            print("카테고리 선택 실패")
            return contests
        
        while True:
            
            # 공모전 목록 가져오기 (상태 정보 포함)
            contest_elements, found_closed_contest = get_contest_list_with_status(driver)
            
            if not contest_elements:
                print(f"{page_num}페이지에서 진행중인 공모전을 찾을 수 없습니다.")
                break
            
            # 공모전 정보 추출 (숫자만 있는 항목 제외)
            for i, contest_element in enumerate(contest_elements):
                try:
                    contest_info = extract_contest_info(contest_element, excluded_contests)
                    if contest_info and contest_info['title'] and not contest_info['title'].isdigit():
                        # 상세 페이지에서 정보 추출
                        contests.append(contest_info)        
                except Exception as e:
                    print(f"공모전 {i+1} 정보 추출 실패: {e}")
                    continue
            
            # 마감된 공모전이 발견되었으면 크롤링 중단
            if found_closed_contest:
                print(f"{page_num}페이지에서 마감된 공모전을 발견했습니다. 크롤링을 종료합니다.")
                break
            
            # 다음 페이지가 있는지 확인
            if check_next_page_exists(driver):
                if go_to_next_page(driver):
                    page_num += 1
                    continue
                else:
                    print("다음 페이지로 이동할 수 없습니다.")
                    break
            else:
                print("더 이상 다음 페이지가 없습니다.")
                break
        
        print(f"\n총 {len(contests)}개의 공모전을 찾았습니다. ({page_num}페이지까지 크롤링)")
        print(f"응모자격 조건에서 제외된 공모전: {len(excluded_contests)}개")
        
    except Exception as e:
        print(f"크롤링 중 오류 발생: {e}")
    
    finally:
        if driver:
            driver.quit()
    
    return contests, excluded_contests

def save_to_json(contests, filename="data.json"):
    """결과를 JSON 임시 파일로 저장 (집계기가 병합 저장)."""
    try:
        from pathlib import Path
        # 5개씩만 제한
        limited_contests = contests[:5] if len(contests) > 5 else contests
        print(f"thinkyou: {len(contests)}개 중 {len(limited_contests)}개만 저장")
        
        temp_path = Path(__file__).parent / "thinkyou_temp.json"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(limited_contests, f, ensure_ascii=False, indent=2)
        print(f"임시 결과가 {temp_path}에 저장되었습니다.")
    except Exception as e:
        print(f"파일 저장 중 오류: {e}")

def main():
    """메인 함수"""
    
    # 공모전 크롤링
    contests, excluded_contests = crawl_thinkyou_contests()
    
    # JSON 파일로 저장
    save_to_json(contests)
    
    # 제외된 공모전은 집계기에서 일괄 저장하므로 임시 파일로만 남김
    if excluded_contests:
        from pathlib import Path
        temp_excluded = Path(__file__).parent / "thinkyou_excluded_temp.json"
        with open(temp_excluded, 'w', encoding='utf-8') as f:
            json.dump(excluded_contests, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
