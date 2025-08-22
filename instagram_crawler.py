import requests
import time
import json
import logging
import re
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class InstagramCrawler:
    def __init__(self, headless=True):
        """
        인스타그램 크롤러 초기화
        
        Args:
            headless (bool): 브라우저를 백그라운드에서 실행할지 여부
        """
        self.setup_logging()
        self.setup_driver(headless)
        self.wait = WebDriverWait(self.driver, 10)
        
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
            
            # 인스타그램 프로필 페이지로 이동
            profile_url = f"https://www.instagram.com/{username}/"
            self.driver.get(profile_url)
            
            # 페이지 로딩 대기
            time.sleep(3)
            
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
            
            
    def _extract_recent_posts(self):
        """최근 게시물 정보 추출"""
        posts = []
        try:
            # 게시물 그리드 찾기 (더 정확한 선택자 사용)
            post_elements = self.driver.find_elements(By.CSS_SELECTOR, 'article a[href*="/p/"]')
            
            for i, post_link in enumerate(post_elements[:9]):  # 최근 9개 게시물
                try:
                    # 게시물 링크 가져오기
                    post_url = post_link.get_attribute('href')
                    
                    # 게시물 페이지로 이동하여 상세 정보 수집
                    post_info = self._extract_post_details(post_url)
                    if post_info:
                        post_info['post_number'] = i + 1
                        posts.append(post_info)
                    
                    # 인스타그램 메인 페이지로 돌아가기
                    self.driver.back()
                    time.sleep(2)  # 페이지 로딩 대기
                    
                except Exception as e:
                    self.logger.warning(f"게시물 {i+1} 정보 추출 실패: {e}")
                    
        except Exception as e:
            self.logger.warning(f"게시물 정보 추출 실패: {e}")
            
        return posts
        
    def _extract_post_details(self, post_url):
        """개별 게시물 상세 정보 추출"""
        try:
            # 게시물 페이지로 이동
            self.driver.get(post_url)
            time.sleep(3)  # 페이지 로딩 대기
            
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
                caption_element = self.driver.find_element(By.CSS_SELECTOR, 'div[data-testid="post-caption"] span')
                caption = caption_element.text
                post_info['caption'] = caption
                
                # 해시태그 추출
                hashtags = re.findall(r'#\w+', caption)
                post_info['hashtags'] = hashtags
                
                # 멘션 추출
                mentions = re.findall(r'@\w+', caption)
                post_info['mentions'] = mentions
                
            except NoSuchElementException:
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
