import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
from instagram_crawler import InstagramCrawler
from data_manager import DataManager

class InstagramScheduler:
    def __init__(self, accounts=None, interval_hours=24):
        """
        인스타그램 크롤링 스케줄러 초기화
        
        Args:
            accounts (list): 크롤링할 인스타그램 계정 목록
            interval_hours (int): 크롤링 간격 (시간 단위)
        """
        self.accounts = accounts or []
        self.interval_hours = interval_hours
        self.data_manager = DataManager()
        self.setup_logging()
        self.running = False
        self.thread = None
        
    def setup_logging(self):
        """로깅 설정"""
        self.logger = logging.getLogger(__name__)
        
    def add_account(self, username):
        """
        크롤링할 계정 추가
        
        Args:
            username (str): 인스타그램 사용자명
        """
        if username not in self.accounts:
            self.accounts.append(username)
            self.logger.info(f"계정 추가됨: {username}")
        else:
            self.logger.warning(f"이미 존재하는 계정: {username}")
            
    def remove_account(self, username):
        """
        크롤링할 계정 제거
        
        Args:
            username (str): 제거할 인스타그램 사용자명
        """
        if username in self.accounts:
            self.accounts.remove(username)
            self.logger.info(f"계정 제거됨: {username}")
        else:
            self.logger.warning(f"존재하지 않는 계정: {username}")
            
    def set_interval(self, hours):
        """
        크롤링 간격 설정
        
        Args:
            hours (int): 크롤링 간격 (시간 단위)
        """
        self.interval_hours = hours
        self.logger.info(f"크롤링 간격 설정: {hours}시간")
        
    def crawl_single_account(self, username):
        """
        단일 계정 크롤링
        
        Args:
            username (str): 크롤링할 인스타그램 사용자명
        """
        try:
            self.logger.info(f"계정 {username} 크롤링 시작")
            
            with InstagramCrawler(headless=True) as crawler:
                result = crawler.crawl_account(username)
                
                if result:
                    # 데이터 저장
                    if self.data_manager.save_crawl_data(result):
                        self.logger.info(f"계정 {username} 크롤링 및 저장 완료")
                    else:
                        self.logger.error(f"계정 {username} 데이터 저장 실패")
                else:
                    self.logger.error(f"계정 {username} 크롤링 실패")
                    
        except Exception as e:
            self.logger.error(f"계정 {username} 크롤링 중 오류 발생: {e}")
            
    def crawl_all_accounts(self):
        """모든 계정 크롤링"""
        if not self.accounts:
            self.logger.warning("크롤링할 계정이 없습니다.")
            return
            
        self.logger.info(f"전체 {len(self.accounts)}개 계정 크롤링 시작")
        start_time = datetime.now()
        
        for username in self.accounts:
            try:
                self.crawl_single_account(username)
                # 계정 간 간격을 두어 서버 부하 방지
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"계정 {username} 크롤링 실패: {e}")
                
        end_time = datetime.now()
        duration = end_time - start_time
        self.logger.info(f"전체 크롤링 완료. 소요시간: {duration}")
        
    def schedule_crawling(self):
        """크롤링 스케줄 설정"""
        # 매일 지정된 시간에 크롤링 실행
        schedule.every(self.interval_hours).hours.do(self.crawl_all_accounts)
        
        # 즉시 한 번 실행
        self.crawl_all_accounts()
        
        self.logger.info(f"크롤링 스케줄 설정 완료. 간격: {self.interval_hours}시간")
        
    def start(self):
        """스케줄러 시작"""
        if self.running:
            self.logger.warning("스케줄러가 이미 실행 중입니다.")
            return
            
        self.running = True
        self.schedule_crawling()
        
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 스케줄 확인
                
        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()
        
        self.logger.info("스케줄러 시작됨")
        
    def stop(self):
        """스케줄러 중지"""
        if not self.running:
            self.logger.warning("스케줄러가 실행 중이 아닙니다.")
            return
            
        self.running = False
        schedule.clear()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
            
        self.logger.info("스케줄러 중지됨")
        
    def get_status(self):
        """
        현재 스케줄러 상태 조회
        
        Returns:
            dict: 스케줄러 상태 정보
        """
        next_run = schedule.next_run()
        
        return {
            'running': self.running,
            'accounts_count': len(self.accounts),
            'interval_hours': self.interval_hours,
            'next_run': next_run.isoformat() if next_run else None,
            'accounts': self.accounts.copy()
        }
        
    def run_once(self):
        """즉시 한 번 크롤링 실행"""
        self.logger.info("즉시 크롤링 실행")
        self.crawl_all_accounts()
        
    def get_statistics(self):
        """
        크롤링 통계 조회
        
        Returns:
            dict: 통계 정보
        """
        return self.data_manager.get_statistics()
        
    def export_account_data(self, username, output_path=None):
        """
        특정 계정의 데이터 내보내기
        
        Args:
            username (str): 내보낼 사용자명
            output_path (str): 출력 파일 경로
            
        Returns:
            bool: 내보내기 성공 여부
        """
        return self.data_manager.export_to_json(username, output_path)
