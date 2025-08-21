import requests
from bs4 import BeautifulSoup
import json

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
        title_selector = "#wrap > div.container.list_wrap > div.left_cont > div.view_cont_area > div.view_top_area.clfx > h1"

        # 정보 추출
        title_element = soup.select_one(title_selector)
        title = title_element.get_text(strip=True) if title_element else 'N/A'
        
        # 대상 필터링 - 대학생, 대학원생, 일반인, 누구나만 허용
        eligible_keywords = ['대학생', '대학원생', '일반인', '누구나']
        is_eligible = False
        
        # 대상 정보 크롤링
        target_element = soup.select_one("#wrap > div.container.list_wrap > div.left_cont > div.view_cont_area > div.view_top_area.clfx > div.clfx > div.txt_area > table > tbody > tr:nth-child(3) > td")
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
        
        poster_img = soup.select_one("#wrap > div.container.list_wrap > div.left_cont > div.view_cont_area > div.view_top_area.clfx > div.clfx > div.img_area > div > img")
        poster_url = poster_img['src'] if poster_img and poster_img.get('src') else 'N/A'
        # 상대 경로일 경우 절대 경로로 변환
        if poster_url != 'N/A' and poster_url.startswith('/'):
            poster_url = f"https://www.contestkorea.com{poster_url}"

        date_element = soup.select_one("#wrap > div.container.list_wrap > div.left_cont > div.view_cont_area > div.view_top_area.clfx > div.clfx > div.txt_area > table > tbody > tr:nth-child(4) > td")
        date = date_element.get_text(strip=True) if date_element else 'N/A'
        
        if date != 'N/A':
            date_list = date.split('~')
            start_date = date_list[0].strip()
            end_date = date_list[1].strip() if len(date_list) > 1 else 'N/A'
        else:
            start_date = 'N/A'
            end_date = 'N/A'

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

def crawl_contest_korea(i, excluded_contests=None):
    """
    콘테스트코리아 목록 페이지에서 모든 공모전 정보를 크롤링합니다.
    """

    list_url = f"https://www.contestkorea.com/sub/list.php?displayrow=12&int_gbn=1&Txt_sGn=1&Txt_key=all&Txt_word=&Txt_bcode=030310001&Txt_code1=&Txt_aarea=&Txt_area=&Txt_sortkey=a.int_sort&Txt_sortword=desc&Txt_ahost=&Txt_host=&Txt_award=&Txt_award2=&Txt_code3=&Txt_tipyn=&Txt_comment=&Txt_resultyn=&Txt_actcode=&page={i}"
    
    try:
        response = requests.get(list_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 모든 공모전 항목(li) 선택
        contest_list = soup.select('div.list_style_2 > ul > li')
        
        all_contests_data = []

        for item in contest_list:
            # 각 항목에서 a 태그와 href 속성 추출
            link_tag = item.select_one('div.title > a')
            if link_tag:
                relative_url = link_tag.get('href')
                if relative_url:
                    # URL 생성 시 중복 /sub/ 방지
                    if relative_url.startswith('/sub/'):
                        detail_url = f"https://www.contestkorea.com{relative_url}"
                    else:
                        detail_url = f"https://www.contestkorea.com/sub/{relative_url}"
                    
                    # 상세 정보 크롤링
                    contest_data = get_contest_details(detail_url, excluded_contests)
                    if contest_data:
                        all_contests_data.append(contest_data)
                    else:
                        pass
                else:
                    print("Could not find href in link tag.")
            else:
                print("Could not find link in an item.")

        return all_contests_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching list page {list_url}: {e}")
        return []
    except Exception as e:  
        print(f"An unexpected error occurred: {e}")
        return []


def save_all_data(all_data):
    """
    모든 데이터를 임시 JSON에 저장합니다 (집계기가 병합 저장).
    """
    from pathlib import Path
    temp_path = Path(__file__).parent / "contestkorea_temp.json"
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    print(f"\nAll data saved to {temp_path}")
    print(f"Total contests saved: {len(all_data)}")

def save_excluded_temp(excluded_contests):
    """제외된 공모전을 임시 파일로 저장 (집계기가 병합 저장)."""
    from pathlib import Path
    temp_path = Path(__file__).parent / "contestkorea_excluded_temp.json"
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(excluded_contests, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    all_contests = []
    excluded_contests = []  # 대상 조건에서 제외된 공모전들
    
    for i in range(1, 5):
        page_data = crawl_contest_korea(i, excluded_contests)
        all_contests.extend(page_data)
    
    save_all_data(all_contests)
    
    # 제외된 공모전은 집계기에서 저장 → 임시 파일로만 남김
    if excluded_contests:
        save_excluded_temp(excluded_contests)
        print(f"총 {len(excluded_contests)}개의 공모전이 조건 미충족으로 제외(임시 저장).")