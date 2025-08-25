import requests
import time
import json
import logging
import re
import os
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv

class InstagramCrawler:
    def __init__(self, headless=False):  # 디버깅을 위해 헤드리스 모드 비활성화
        """
        인스타그램 크롤러 초기화
        
        Args:
            headless (bool): 브라우저를 백그라운드에서 실행할지 여부
        """
        # 환경 변수 로드
        load_dotenv()
        
        self.setup_logging()
        self.setup_driver(headless)
        self.wait = WebDriverWait(self.driver, 10)
        
        # 로그인 정보
        self.username = os.getenv('INSTAGRAM_USERNAME')
        self.password = os.getenv('INSTAGRAM_PASSWORD')
        
        if not self.username or not self.password:
            self.logger.warning("인스타그램 로그인 정보가 .env 파일에 설정되지 않았습니다.")
            self.logger.warning("INSTAGRAM_USERNAME과 INSTAGRAM_PASSWORD를 설정해주세요.")
        
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('instagram_crawler.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_driver(self, headless):
        """Selenium WebDriver 설정"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.logger.info("WebDriver 초기화 성공")
        except Exception as e:
            self.logger.error(f"WebDriver 초기화 실패: {e}")
            raise
            
    def crawl_account(self, username):
        """
        특정 인스타그램 계정 크롤링
        
        Args:
            username (str): 크롤링할 인스타그램 사용자명
            
        Returns:
            dict: 수집된 계정 정보
        """
        try:
            self.logger.info(f"계정 {username} 크롤링 시작")
            
            # 현재 크롤링 중인 사용자명 저장
            self.current_username = username
            
            # 인스타그램 메인 페이지로 이동
            self.driver.get("https://www.instagram.com/")
            time.sleep(3)
            
            # 로그인 상태 확인 및 필요시 로그인
            if not self._check_login_status():
                self.logger.info("로그인이 필요합니다. 자동 로그인을 시도합니다...")
                if not self._perform_login():
                    self.logger.error("로그인 실패. 크롤링을 중단합니다.")
                    return None
                self.logger.info("로그인 성공!")
            
            # 인스타그램 프로필 페이지로 이동
            profile_url = f"https://www.instagram.com/{username}/#"
            self.driver.get(profile_url)
            
            # 페이지 로딩 대기
            time.sleep(3)
            
            # JavaScript로 동적 로딩되는 게시물들을 기다림
            self.logger.info("게시물 로딩 대기 중...")
            try:
                # 게시물이 로드될 때까지 최대 30초 대기
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'article a[href*="/p/"]'))
                )
                self.logger.info("게시물 로딩 완료")
            except TimeoutException:
                self.logger.warning("게시물 로딩 시간 초과, 계속 진행")
            
            # 추가 대기 시간
            time.sleep(5)
            
            # 페이지 스크롤하여 더 많은 게시물 로드
            self.logger.info("페이지 스크롤하여 게시물 로드 중...")
            try:
                # 페이지 하단으로 스크롤
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                self.logger.info("페이지 스크롤 완료")
            except Exception as e:
                self.logger.warning(f"페이지 스크롤 실패: {e}")
            
            # 최근 게시물 정보 수집
            recent_posts = self._extract_recent_posts()
            
            result = {
                'username': username,
                'crawled_at': datetime.now().isoformat(),
                'recent_posts': recent_posts,
            }
            
            self.logger.info(f"계정 {username} 크롤링 완료")
            return result
            
        except Exception as e:
            self.logger.error(f"계정 {username} 크롤링 실패: {e}")
            return None
            
    def _check_login_status(self):
        """로그인 상태 확인"""
        try:
            # 로그인된 상태를 나타내는 요소들 확인
            login_indicators = [
                'nav[aria-label="Primary navigation"]',  # 메인 네비게이션
                'a[href="/accounts/activity/"]',  # 활동 알림
                'a[href="/direct/inbox/"]',  # DM
                'a[href="/explore/"]',  # 탐색
                'div[data-testid="user-avatar"]',  # 사용자 아바타
                'img[alt*="profile picture"]',  # 프로필 사진
                'a[href="/accounts/edit/"]'  # 프로필 편집
            ]
            
            for indicator in login_indicators:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, indicator)
                    if element:
                        self.logger.info("로그인된 상태로 확인됨")
                        return True
                except NoSuchElementException:
                    continue
            
            # 로그인 페이지 요소 확인
            login_page_indicators = [
                'input[name="username"]',
                'input[name="password"]',
                'button[type="submit"]',
                'form[action*="/accounts/login"]'
            ]
            
            for indicator in login_page_indicators:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, indicator)
                    if element:
                        self.logger.info("로그인 페이지가 표시됨")
                        return False
                except NoSuchElementException:
                    continue
            
            self.logger.info("로그인 상태를 확인할 수 없습니다. 로그인을 시도합니다.")
            return False
            
        except Exception as e:
            self.logger.error(f"로그인 상태 확인 중 오류: {e}")
            return False
            
    def _perform_login(self):
        """인스타그램 로그인 수행"""
        try:
            if not self.username or not self.password:
                self.logger.error("로그인 정보가 없습니다.")
                return False
            
            self.logger.info("로그인 페이지 로딩 중...")
            
            # 로그인 페이지로 이동
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(2)
            
            # 사용자명 입력
            try:
                username_input = self.driver.find_element(By.CSS_SELECTOR, 'input[name="username"]')
                username_input.clear()
                username_input.send_keys(self.username)
                self.logger.info("사용자명 입력 완료")
            except NoSuchElementException:
                self.logger.error("사용자명 입력 필드를 찾을 수 없습니다.")
                return False
            
            # 비밀번호 입력
            try:
                password_input = self.driver.find_element(By.CSS_SELECTOR, 'input[name="password"]')
                password_input.clear()
                password_input.send_keys(self.password)
                self.logger.info("비밀번호 입력 완료")
            except NoSuchElementException:
                self.logger.error("비밀번호 입력 필드를 찾을 수 없습니다.")
                return False
            
            # 로그인 버튼 클릭
            try:
                login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
                login_button.click()
                self.logger.info("로그인 버튼 클릭됨")
            except NoSuchElementException:
                self.logger.error("로그인 버튼을 찾을 수 없습니다.")
                return False
            
                                    # 로그인 완료 대기
            time.sleep(2)
            
            # 로그인 후 팝업 처리 (로그인 정보 저장 여부)
            self._handle_login_popup()
            
            # 로그인 성공 확인
            if self._check_login_status():
                self.logger.info("로그인 성공!")
                return True
            else:
                self.logger.error("로그인 실패")
                return False
    
        except Exception as e:
            self.logger.error(f"로그인 중 오류 발생: {e}")
            return False
            
    def _handle_login_popup(self):
        """로그인 후 나타나는 팝업 처리 (로그인 정보 저장 여부)"""
        try:
            self.logger.info("로그인 후 팝업 처리 중...")
            
            # 팝업이 나타날 때까지 잠시 대기
            time.sleep(3)
            
            # 팝업 관련 div들을 찾기 (더 정확한 선택자들)
            div_selectors = [
                'main>div>div>div'  # 기본 선택자 요소
            ]
            
            divs = []
            for selector in div_selectors:
                try:
                    found_divs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    divs.extend(found_divs)
                except:
                    continue
            
            for div in divs:
                try:
                    div_text = div.text.strip()
                    self.logger.debug(f"div 텍스트 확인: {div_text}")
                    
                    # "저장 안 함" 관련 텍스트가 있는 div 찾기
                    if any(keyword in div_text for keyword in ['나중에 하기', '저장 안 함', 'Don\'t Save', '아니오', 'No', '취소', 'Cancel']):
                        self.logger.info(f"팝업 div 발견: {div_text}")
                        div.click()
                        time.sleep(1)
                        return
                        
                except Exception as e:
                    self.logger.debug(f"div 처리 중 오류 (무시): {e}")
                    continue
            
            # 특정 data-testid를 가진 버튼들도 확인
            specific_selectors = [
                'button[data-testid="login-save-login-info-dialog-not-now-button"]',
                'button[data-testid="login-save-login-info-dialog-not-now"]',
                'button[data-testid="close-button"]'
            ]
            
            for selector in specific_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed():
                        self.logger.info(f"특정 팝업 요소 발견: {selector}")
                        element.click()
                        time.sleep(1)
                        return
                except NoSuchElementException:
                    continue
                except Exception as e:
                    self.logger.debug(f"특정 선택자 처리 중 오류 (무시): {e}")
                    continue
            
            self.logger.info("로그인 후 팝업이 발견되지 않았거나 이미 처리됨")
            
        except Exception as e:
            self.logger.warning(f"팝업 처리 중 오류 (무시): {e}")
            
            
    def _extract_recent_posts(self):
        """최근 게시물 정보 추출"""
        posts = []
        try:
            # 여러 가지 선택자로 게시물 찾기 시도
            post_selectors = [
                'div>div>div>div>div>div>a'
            ]
            
            post_elements = []
            used_selector = None
            
            for selector in post_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        post_elements = elements
                        used_selector = selector
                        self.logger.info(f"게시물 발견! 선택자: {selector}, 개수: {len(elements)}")
                        break
                except Exception as e:
                    self.logger.debug(f"선택자 실패: {selector} - {e}")
                    continue
            
            if not post_elements:
                self.logger.warning("모든 선택자로 게시물을 찾을 수 없습니다")
                # 페이지 소스 저장하여 디버깅
                try:
                    page_source = self.driver.page_source
                    with open("debug_profile_page.html", 'w', encoding='utf-8') as f:
                        f.write(page_source)
                    self.logger.info("프로필 페이지 소스 저장됨: debug_profile_page.html")
                    
                    # 스크린샷도 저장
                    self.driver.save_screenshot("debug_profile_page.png")
                    self.logger.info("프로필 페이지 스크린샷 저장됨: debug_profile_page.png")
                except Exception as e:
                    self.logger.warning(f"디버깅 파일 저장 실패: {e}")
                return posts
            
            # 모든 게시물 URL을 먼저 수집
            post_urls = []
            for post_link in post_elements[:9]:  # 최근 9개 게시물
                try:
                    post_url = post_link.get_attribute('href')
                    if post_url and '/p/' in post_url:
                        post_urls.append(post_url)
                        self.logger.debug(f"게시물 URL 발견: {post_url}")
                except Exception as e:
                    self.logger.warning(f"게시물 URL 추출 실패: {e}")
            
            self.logger.info(f"총 {len(post_urls)}개의 게시물 URL 수집됨 (사용된 선택자: {used_selector})")
            
            # 중복 체크를 위해 DataManager 인스턴스 생성
            from data_manager import DataManager
            data_manager = DataManager()
            
            # 중복되지 않는 게시물 URL만 필터링
            new_post_urls = []
            for post_url in post_urls:
                try:
                    # 데이터베이스에서 해당 URL이 이미 존재하는지 확인
                    with sqlite3.connect(data_manager.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute('SELECT id FROM post_data WHERE post_url = ?', (post_url,))
                        existing_post = cursor.fetchone()
                        
                        if not existing_post:
                            new_post_urls.append(post_url)
                            self.logger.debug(f"새로운 게시물: {post_url}")
                        else:
                            self.logger.info(f"중복 게시물 건너뛰기: {post_url}")
                            
                except Exception as e:
                    self.logger.warning(f"중복 체크 실패: {e}")
                    # 오류 발생 시 안전하게 포함
                    new_post_urls.append(post_url)
            
            self.logger.info(f"중복 체크 완료: {len(post_urls)}개 중 {len(new_post_urls)}개가 새로운 게시물")
            
            # 중복되지 않는 게시물만 상세 정보 수집
            for i, post_url in enumerate(new_post_urls):
                try:
                    self.logger.info(f"새로운 게시물 {i+1}/{len(new_post_urls)} 처리 중: {post_url}")
                    
                    # 게시물 페이지로 이동하여 상세 정보 수집
                    post_info = self._extract_post_details(post_url)
                    if post_info:
                        post_info['post_number'] = i + 1
                        posts.append(post_info)
                        self.logger.info(f"게시물 {i+1} 정보 추출 성공")
                    
                    # 인스타그램 메인 페이지로 돌아가기
                    self.driver.get(f"https://www.instagram.com/{self.current_username}/")
                    time.sleep(3)  # 페이지 로딩 대기
                    
                except Exception as e:
                    self.logger.warning(f"게시물 {i+1} 정보 추출 실패: {e}")
                    
        except Exception as e:
            self.logger.warning(f"게시물 정보 추출 실패: {e}")
            
        return posts
        
    def _extract_post_details(self, post_url):
        """개별 게시물 상세 정보 추출"""
        def _close_more_text_popup():
            """'더 보기' 팝업 닫기"""
            try:
                # "00님의 글 더 보기" 텍스트가 있는 span 찾기
                spans = self.driver.find_elements(By.CSS_SELECTOR, 'div>div>div>div>span')
                
                for span in spans:
                    span_text = span.text.strip()
                    if '님의 글 더 보기' in span_text:
                        self.logger.info(f"'더 보기' 팝업 발견: {span_text}")
                        
                        # aria-label="닫기"인 svg 직접 찾기
                        try:
                            close_svgs = self.driver.find_elements(By.CSS_SELECTOR, 'div>div>svg[aria-label="닫기"]')
                            if close_svgs:
                                self.logger.info("닫기 버튼 발견, 클릭합니다.")
                                close_svgs[0].click()
                                time.sleep(1)
                                return
                        except Exception as e:
                            self.logger.debug(f"닫기 버튼 찾기 실패: {e}")
                            continue
                        
            except Exception as e:
                self.logger.debug(f"'더 보기' 팝업 닫기 실패: {e}")
                pass
        try:
            # 게시물 페이지로 이동
            self.driver.get(post_url)
            time.sleep(3)  # 페이지 로딩 대기
            
            # '더 보기' 팝업 닫기
            _close_more_text_popup()
            
            # 디버깅을 위해 페이지 소스 저장
            # try:
            #     page_source = self.driver.page_source
            #     post_id = post_url.split('/p/')[1].split('/')[0]
            #     filename = f"debug_page_{post_id}.html"
            #     with open(filename, 'w', encoding='utf-8') as f:
            #         f.write(page_source)
            #     self.logger.info(f"페이지 소스 저장됨: {filename}")
                
            #     # 스크린샷도 저장
            #     screenshot_filename = f"debug_screenshot_{post_id}.png"
            #     self.driver.save_screenshot(screenshot_filename)
            #     self.logger.info(f"스크린샷 저장됨: {screenshot_filename}")
            # except Exception as e:
            #     self.logger.warning(f"디버깅 파일 저장 실패: {e}")
            
            post_info = {
                'post_url': post_url,
                'image_url': None,
                'caption': None,
                'posted_at': None,
                'hashtags': [],
                'mentions': [],
                'timestamp': datetime.now().isoformat()
            }
            
            # 이미지 URL 추출
            try:
                img_element = self.driver.find_element(By.CSS_SELECTOR, 'article img')
                post_info['image_url'] = img_element.get_attribute('src')
            except NoSuchElementException:
                pass
                
            # 캡션 추출
            try:
                self.logger.info("캡션 요소 찾기 시도 중...")
                
                # 여러 가지 선택자 시도
                caption_selectors = [
                    'div>span>div>span'
                ]
                
                caption_element = None
                used_selector = None
                
                for selector in caption_selectors:
                    try:
                        caption_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if caption_element and caption_element.text.strip():
                            used_selector = selector
                            self.logger.info(f"캡션 요소 발견! 선택자: {selector}")
                            break
                    except NoSuchElementException:
                        self.logger.debug(f"선택자 실패: {selector}")
                        continue
                
                if caption_element and caption_element.text.strip():
                    caption = caption_element.text.strip()
                    self.logger.info(f"캡션 추출 성공: {caption[:100]}...")
                    post_info['caption'] = caption
                    
                    # 해시태그 추출
                    hashtags = re.findall(r'#\w+', caption)
                    post_info['hashtags'] = hashtags
                    self.logger.info(f"해시태그 추출: {hashtags}")
                    
                    # 멘션 추출
                    mentions = re.findall(r'@\w+', caption)
                    post_info['mentions'] = mentions
                    self.logger.info(f"멘션 추출: {mentions}")
                else:
                    self.logger.warning("캡션을 찾을 수 없습니다")
                    
            except Exception as e:
                self.logger.error(f"캡션 추출 중 오류 발생: {e}")
                pass
                
            # 게시 시간 추출
            try:
                time_element = self.driver.find_element(By.CSS_SELECTOR, 'time')
                post_info['posted_at'] = time_element.get_attribute('datetime')
            except NoSuchElementException:
                pass
                
            return post_info
            
        except Exception as e:
            self.logger.warning(f"게시물 상세 정보 추출 실패: {e}")
            return None
            
    def close(self):
        """브라우저 종료"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            self.logger.info("WebDriver 종료")
            
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
