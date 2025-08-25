import json
import sqlite3
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path

class DataManager:
    def __init__(self, db_path="instagram_data.db"):
        """
        데이터 관리자 초기화
        
        Args:
            db_path (str): SQLite 데이터베이스 파일 경로
        """
        self.db_path = db_path
        self.setup_logging()
        self.setup_database()
        
    def setup_logging(self):
        """로깅 설정"""
        self.logger = logging.getLogger(__name__)
        
    def setup_database(self):
        """데이터베이스 및 테이블 초기화 (기존 데이터 유지)"""
        try:
            # 데이터베이스 파일이 이미 존재하는지 확인
            db_exists = Path(self.db_path).exists()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 계정 정보 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS account_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        username TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 게시물 정보 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS post_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account_id INTEGER,
                        post_url TEXT UNIQUE NOT NULL,
                        post_number INTEGER,
                        image_url TEXT,
                        caption TEXT,
                        posted_at TEXT,
                        hashtags TEXT,
                        mentions TEXT,
                        timestamp TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (account_id) REFERENCES account_data (id)
                    )
                ''')
                
                # 크롤링 히스토리 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS crawl_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        status TEXT NOT NULL,
                        crawled_at TEXT NOT NULL,
                        error_message TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                
                if db_exists:
                    self.logger.info("기존 데이터베이스 연결 완료")
                else:
                    self.logger.info("새 데이터베이스 생성 완료")
                
        except Exception as e:
            self.logger.error(f"데이터베이스 설정 실패: {e}")
            raise
            
    def save_crawl_data(self, crawl_result):
        """
        크롤링 결과를 데이터베이스에 저장
        
        Args:
            crawl_result (dict): 크롤링 결과 데이터
        """
        if not crawl_result:
            self.logger.warning("저장할 데이터가 없습니다.")
            return False
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 계정 정보 저장 (간소화된 구조)
                cursor.execute('''
                    INSERT INTO account_data 
                    (user_id, username)
                    VALUES (?, ?)
                ''', (
                    crawl_result['username'],  # user_id로 username 사용
                    crawl_result['username']
                ))
                
                account_id = cursor.lastrowid
                
                # 게시물 정보 저장 (새로운 게시글만)
                new_posts_count = 0
                for post in crawl_result.get('recent_posts', []):
                    try:
                        # 게시물 URL이 이미 존재하는지 확인
                        cursor.execute('SELECT id FROM post_data WHERE post_url = ?', (post['post_url'],))
                        existing_post = cursor.fetchone()
                        
                        if not existing_post:
                            # 새로운 게시글인 경우에만 저장
                            cursor.execute('''
                                INSERT INTO post_data 
                                (account_id, post_url, post_number, image_url, caption, 
                                 posted_at, hashtags, mentions, timestamp)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                account_id, 
                                post['post_url'],
                                post['post_number'], 
                                post['image_url'], 
                                post['caption'],
                                post['posted_at'],
                                json.dumps(post['hashtags'], ensure_ascii=False),
                                json.dumps(post['mentions'], ensure_ascii=False),
                                post['timestamp']
                            ))
                            new_posts_count += 1
                        else:
                            self.logger.info(f"게시물 이미 존재함: {post['post_url']}")
                            
                    except Exception as e:
                        self.logger.warning(f"게시물 저장 실패: {e}")
                
                self.logger.info(f"새로운 게시물 {new_posts_count}개 저장됨")
                
                # 크롤링 성공 기록
                cursor.execute('''
                    INSERT INTO crawl_history (username, status, crawled_at)
                    VALUES (?, ?, ?)
                ''', (crawl_result['username'], 'SUCCESS', crawl_result['crawled_at']))
                
                conn.commit()
                self.logger.info(f"데이터 저장 완료: {crawl_result['username']}")
                return True
                
        except Exception as e:
            self.logger.error(f"데이터 저장 실패: {e}")
            self._record_crawl_error(crawl_result['username'], str(e))
            return False
            
    def _record_crawl_error(self, username, error_message):
        """크롤링 오류 기록"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO crawl_history (username, status, crawled_at, error_message)
                    VALUES (?, ?, ?, ?)
                ''', (username, 'ERROR', datetime.now().isoformat(), error_message))
                conn.commit()
        except Exception as e:
            self.logger.error(f"오류 기록 실패: {e}")
            
    def get_account_history(self, username, limit=10):
        """
        특정 계정의 크롤링 히스토리 조회
        
        Args:
            username (str): 조회할 사용자명
            limit (int): 조회할 레코드 수
            
        Returns:
            list: 크롤링 히스토리 목록
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT * FROM account_data 
                    WHERE username = ? 
                    ORDER BY crawled_at DESC 
                    LIMIT ?
                '''
                df = pd.read_sql_query(query, conn, params=(username, limit))
                return df.to_dict('records')
        except Exception as e:
            self.logger.error(f"히스토리 조회 실패: {e}")
            return []
            
    def get_follower_trend(self, username, days=30):
        """
        팔로워 수 변화 추이 조회
        
        Args:
            username (str): 조회할 사용자명
            days (int): 조회할 일수
            
        Returns:
            list: 팔로워 수 변화 데이터
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT crawled_at, followers 
                    FROM account_data 
                    WHERE username = ? 
                    AND crawled_at >= datetime('now', '-{} days')
                    ORDER BY crawled_at ASC
                '''.format(days)
                df = pd.read_sql_query(query, conn, params=(username,))
                return df.to_dict('records')
        except Exception as e:
            self.logger.error(f"팔로워 추이 조회 실패: {e}")
            return []
            
    def export_to_json(self, username, output_path=None):
        """
        특정 계정의 데이터를 JSON 파일로 내보내기
        
        Args:
            username (str): 내보낼 사용자명
            output_path (str): 출력 파일 경로
            
        Returns:
            bool: 내보내기 성공 여부
        """
        try:
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"instagram_data_{username}_{timestamp}.json"
                
            data = {
                'username': username,
                'exported_at': datetime.now().isoformat(),
                'account_history': self.get_account_history(username, limit=100),
                'follower_trend': self.get_follower_trend(username, days=365)
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"데이터 내보내기 완료: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"데이터 내보내기 실패: {e}")
            return False
            
    def get_statistics(self):
        """
        전체 크롤링 통계 조회
        
        Returns:
            dict: 통계 정보
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 전체 계정 수
                cursor.execute("SELECT COUNT(DISTINCT username) FROM account_data")
                total_accounts = cursor.fetchone()[0]
                
                # 전체 크롤링 수
                cursor.execute("SELECT COUNT(*) FROM crawl_history")
                total_crawls = cursor.fetchone()[0]
                
                # 성공한 크롤링 수
                cursor.execute("SELECT COUNT(*) FROM crawl_history WHERE status = 'SUCCESS'")
                successful_crawls = cursor.fetchone()[0]
                
                # 최근 크롤링 시간
                cursor.execute("SELECT MAX(crawled_at) FROM crawl_history")
                last_crawl = cursor.fetchone()[0]
                
                return {
                    'total_accounts': total_accounts,
                    'total_crawls': total_crawls,
                    'successful_crawls': successful_crawls,
                    'success_rate': (successful_crawls / total_crawls * 100) if total_crawls > 0 else 0,
                    'last_crawl': last_crawl
                }
                
        except Exception as e:
            self.logger.error(f"통계 조회 실패: {e}")
            return {}
            
    def backup_database(self, backup_path=None):
        """
        데이터베이스 백업
        
        Args:
            backup_path (str): 백업 파일 경로 (None이면 자동 생성)
            
        Returns:
            str: 백업 파일 경로
        """
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup_instagram_data_{timestamp}.db"
            
            import shutil
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"데이터베이스 백업 완료: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"데이터베이스 백업 실패: {e}")
            return None
            
    def restore_database(self, backup_path):
        """
        데이터베이스 복원
        
        Args:
            backup_path (str): 복원할 백업 파일 경로
            
        Returns:
            bool: 복원 성공 여부
        """
        try:
            if not Path(backup_path).exists():
                self.logger.error(f"백업 파일이 존재하지 않습니다: {backup_path}")
                return False
                
            # 현재 데이터베이스 백업
            current_backup = self.backup_database()
            
            # 백업 파일로 복원
            import shutil
            shutil.copy2(backup_path, self.db_path)
            
            self.logger.info(f"데이터베이스 복원 완료: {backup_path}")
            self.logger.info(f"현재 데이터베이스 백업: {current_backup}")
            return True
            
        except Exception as e:
            self.logger.error(f"데이터베이스 복원 실패: {e}")
            return False
            
    def get_database_info(self):
        """
        데이터베이스 정보 조회
        
        Returns:
            dict: 데이터베이스 정보
        """
        try:
            db_path = Path(self.db_path)
            db_exists = db_path.exists()
            
            info = {
                'database_path': str(self.db_path),
                'exists': db_exists,
                'size_mb': round(db_path.stat().st_size / (1024 * 1024), 2) if db_exists else 0,
                'created_at': datetime.fromtimestamp(db_path.stat().st_ctime).isoformat() if db_exists else None,
                'modified_at': datetime.fromtimestamp(db_path.stat().st_mtime).isoformat() if db_exists else None
            }
            
            if db_exists:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # 테이블 정보
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    info['tables'] = tables
                    
                    # 각 테이블의 레코드 수
                    table_counts = {}
                    for table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        table_counts[table] = cursor.fetchone()[0]
                    info['table_counts'] = table_counts
                    
            return info
            
        except Exception as e:
            self.logger.error(f"데이터베이스 정보 조회 실패: {e}")
            return {}
            
    def get_new_posts_count(self, username, days=7):
        """
        특정 기간 동안 새로 저장된 게시물 수 조회
        
        Args:
            username (str): 조회할 사용자명
            days (int): 조회할 일수
            
        Returns:
            int: 새로운 게시물 수
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT COUNT(*) FROM post_data p
                    JOIN account_data a ON p.account_id = a.id
                    WHERE a.username = ? 
                    AND p.created_at >= datetime('now', '-{} days')
                '''.format(days)
                cursor = conn.cursor()
                cursor.execute(query, (username,))
                return cursor.fetchone()[0]
        except Exception as e:
            self.logger.error(f"새 게시물 수 조회 실패: {e}")
            return 0
            
    def get_latest_posts(self, username, limit=10):
        """
        특정 계정의 최신 게시물 조회
        
        Args:
            username (str): 조회할 사용자명
            limit (int): 조회할 게시물 수
            
        Returns:
            list: 최신 게시물 목록
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT p.*, a.username 
                    FROM post_data p
                    JOIN account_data a ON p.account_id = a.id
                    WHERE a.username = ?
                    ORDER BY p.created_at DESC
                    LIMIT ?
                '''
                df = pd.read_sql_query(query, conn, params=(username, limit))
                return df.to_dict('records')
        except Exception as e:
            self.logger.error(f"최신 게시물 조회 실패: {e}")
            return []
            
    def initialize_database(self):
        """
        데이터베이스 초기화 (데이터만 삭제, 테이블 구조 유지)
        
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            self.logger.info("데이터베이스 초기화 시작")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 각 테이블의 데이터만 삭제
                tables = ['post_data', 'account_data', 'crawl_history']
                for table in tables:
                    try:
                        cursor.execute(f"DELETE FROM {table}")
                        deleted_count = cursor.rowcount
                        self.logger.info(f"{table} 테이블에서 {deleted_count}개 레코드 삭제됨")
                    except Exception as e:
                        self.logger.warning(f"{table} 테이블 삭제 실패: {e}")
                
                # AUTOINCREMENT 값 초기화
                cursor.execute("DELETE FROM sqlite_sequence")
                
                conn.commit()
                self.logger.info("데이터베이스 초기화 완료")
                return True
                
        except Exception as e:
            self.logger.error(f"데이터베이스 초기화 실패: {e}")
            return False
            
    def reset_database(self):
        """
        데이터베이스 완전 초기화 (백업 후 모든 데이터 및 테이블 삭제)
        
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            self.logger.info("데이터베이스 완전 초기화 시작")
            
            # 먼저 백업 생성
            backup_path = self.backup_database()
            if backup_path:
                self.logger.info(f"백업 생성 완료: {backup_path}")
            else:
                self.logger.warning("백업 생성 실패, 계속 진행")
            
            # 데이터베이스 파일 삭제
            try:
                import os
                if os.path.exists(self.db_path):
                    os.remove(self.db_path)
                    self.logger.info("기존 데이터베이스 파일 삭제됨")
            except Exception as e:
                self.logger.error(f"데이터베이스 파일 삭제 실패: {e}")
                return False
            
            # 새로운 데이터베이스 및 테이블 생성
            try:
                self.setup_database()
                self.logger.info("새 데이터베이스 및 테이블 생성 완료")
                return True
            except Exception as e:
                self.logger.error(f"새 데이터베이스 생성 실패: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"데이터베이스 완전 초기화 실패: {e}")
            return False
