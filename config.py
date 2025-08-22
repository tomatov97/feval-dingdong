import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """인스타그램 크롤링 설정"""
    
    # 크롤링 설정
    CRAWL_INTERVAL_HOURS = int(os.getenv('CRAWL_INTERVAL_HOURS', 24))
    HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'true').lower() == 'true'
    
    # 브라우저 설정
    BROWSER_TIMEOUT = int(os.getenv('BROWSER_TIMEOUT', 10))
    PAGE_LOAD_WAIT = int(os.getenv('PAGE_LOAD_WAIT', 3))
    ACCOUNT_INTERVAL_SECONDS = int(os.getenv('ACCOUNT_INTERVAL_SECONDS', 5))
    
    # 데이터베이스 설정
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'instagram_data.db')
    
    # 로깅 설정
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'instagram_crawler.log')
    
    # 크롤링할 계정 목록 (기본값)
    DEFAULT_ACCOUNTS = [
        # 여기에 크롤링하고 싶은 인스타그램 계정들을 추가하세요
        # 'example_user1',
        # 'example_user2',
    ]
    
    # User-Agent 설정
    USER_AGENT = os.getenv('USER_AGENT', 
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    )
    
    # 크롤링 제한 설정
    MAX_POSTS_PER_ACCOUNT = int(os.getenv('MAX_POSTS_PER_ACCOUNT', 9))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    
    # 출력 설정
    EXPORT_DIRECTORY = os.getenv('EXPORT_DIRECTORY', 'exports')
    
    @classmethod
    def get_all_settings(cls):
        """모든 설정값 반환"""
        return {
            'crawl_interval_hours': cls.CRAWL_INTERVAL_HOURS,
            'headless_mode': cls.HEADLESS_MODE,
            'browser_timeout': cls.BROWSER_TIMEOUT,
            'page_load_wait': cls.PAGE_LOAD_WAIT,
            'account_interval_seconds': cls.ACCOUNT_INTERVAL_SECONDS,
            'database_path': cls.DATABASE_PATH,
            'log_level': cls.LOG_LEVEL,
            'log_file': cls.LOG_FILE,
            'max_posts_per_account': cls.MAX_POSTS_PER_ACCOUNT,
            'max_retries': cls.MAX_RETRIES,
            'export_directory': cls.EXPORT_DIRECTORY
        }
