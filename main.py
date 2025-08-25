#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import sys
from pathlib import Path
from instagram_scheduler import InstagramScheduler
from config import Config

def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='인스타그램 계정 크롤링 스케줄러')
    parser.add_argument('--accounts', nargs='+', help='크롤링할 인스타그램 계정 목록')
    parser.add_argument('--interval', type=int, default=Config.CRAWL_INTERVAL_HOURS, 
                       help=f'크롤링 간격 (시간, 기본값: {Config.CRAWL_INTERVAL_HOURS})')
    parser.add_argument('--once', action='store_true', help='즉시 한 번만 크롤링 실행')
    parser.add_argument('--add-account', help='새로운 계정 추가')
    parser.add_argument('--remove-account', help='계정 제거')
    parser.add_argument('--list-accounts', action='store_true', help='크롤링 중인 계정 목록 조회')
    parser.add_argument('--status', action='store_true', help='스케줄러 상태 조회')
    parser.add_argument('--statistics', action='store_true', help='크롤링 통계 조회')
    parser.add_argument('--export', help='특정 계정의 데이터를 JSON으로 내보내기')
    parser.add_argument('--config', action='store_true', help='현재 설정값 조회')
    parser.add_argument('--backup', action='store_true', help='데이터베이스 백업')
    parser.add_argument('--restore', help='백업 파일에서 데이터베이스 복원')
    parser.add_argument('--db-info', action='store_true', help='데이터베이스 정보 조회')
    parser.add_argument('--db-init', action='store_true', help='데이터베이스 초기화 (모든 데이터 삭제)')
    parser.add_argument('--db-reset', action='store_true', help='데이터베이스 완전 초기화 (백업 후 모든 데이터 삭제)')
    parser.add_argument('--new-posts', help='특정 계정의 새 게시물 수 조회 (기본값: 7일)')
    parser.add_argument('--latest-posts', help='특정 계정의 최신 게시물 조회')
    
    args = parser.parse_args()
    
    # 로깅 설정
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 스케줄러 초기화
        accounts = args.accounts or Config.DEFAULT_ACCOUNTS
        scheduler = InstagramScheduler(accounts=accounts, interval_hours=args.interval)
        
        # 설정 조회
        if args.config:
            print("=== 현재 설정 ===")
            for key, value in Config.get_all_settings().items():
                print(f"{key}: {value}")
            print(f"크롤링 계정: {accounts}")
            return
        
        # 계정 추가
        if args.add_account:
            scheduler.add_account(args.add_account)
            print(f"계정 추가됨: {args.add_account}")
            return
        
        # 계정 제거
        if args.remove_account:
            scheduler.remove_account(args.remove_account)
            print(f"계정 제거됨: {args.remove_account}")
            return
        
        # 계정 목록 조회
        if args.list_accounts:
            print("=== 크롤링 중인 계정 목록 ===")
            for account in scheduler.accounts:
                print(f"- {account}")
            return
        
        # 상태 조회
        if args.status:
            status = scheduler.get_status()
            print("=== 스케줄러 상태 ===")
            print(f"실행 중: {status['running']}")
            print(f"계정 수: {status['accounts_count']}")
            print(f"크롤링 간격: {status['interval_hours']}시간")
            print(f"다음 실행: {status['next_run']}")
            print(f"계정 목록: {status['accounts']}")
            return
        
        # 통계 조회
        if args.statistics:
            stats = scheduler.get_statistics()
            print("=== 크롤링 통계 ===")
            print(f"전체 계정 수: {stats.get('total_accounts', 0)}")
            print(f"전체 크롤링 수: {stats.get('total_crawls', 0)}")
            print(f"성공한 크롤링 수: {stats.get('successful_crawls', 0)}")
            print(f"성공률: {stats.get('success_rate', 0):.1f}%")
            print(f"마지막 크롤링: {stats.get('last_crawl', 'N/A')}")
            return
        
        # 데이터 내보내기
        if args.export:
            if scheduler.export_account_data(args.export):
                print(f"데이터 내보내기 완료: {args.export}")
            else:
                print(f"데이터 내보내기 실패: {args.export}")
            return
            
        # 데이터베이스 백업
        if args.backup:
            backup_path = scheduler.data_manager.backup_database()
            if backup_path:
                print(f"데이터베이스 백업 완료: {backup_path}")
            else:
                print("데이터베이스 백업 실패")
            return
            
        # 데이터베이스 복원
        if args.restore:
            if scheduler.data_manager.restore_database(args.restore):
                print(f"데이터베이스 복원 완료: {args.restore}")
            else:
                print(f"데이터베이스 복원 실패: {args.restore}")
            return
            
        # 데이터베이스 정보 조회
        if args.db_info:
            db_info = scheduler.data_manager.get_database_info()
            print("=== 데이터베이스 정보 ===")
            print(f"경로: {db_info.get('database_path', 'N/A')}")
            print(f"존재: {db_info.get('exists', False)}")
            if db_info.get('exists'):
                print(f"크기: {db_info.get('size_mb', 0)} MB")
                print(f"생성일: {db_info.get('created_at', 'N/A')}")
                print(f"수정일: {db_info.get('modified_at', 'N/A')}")
                print(f"테이블: {db_info.get('tables', [])}")
                print("테이블별 레코드 수:")
                for table, count in db_info.get('table_counts', {}).items():
                    print(f"  - {table}: {count}개")
            return
            
        # 데이터베이스 초기화 (데이터만 삭제)
        if args.db_init:
            print("⚠️  경고: 모든 데이터가 삭제됩니다!")
            confirm = input("정말로 진행하시겠습니까? (yes/no): ")
            if confirm.lower() == 'yes':
                if scheduler.data_manager.initialize_database():
                    print("데이터베이스 초기화 완료")
                else:
                    print("데이터베이스 초기화 실패")
            else:
                print("초기화가 취소되었습니다.")
            return
            
        # 데이터베이스 완전 초기화 (백업 후 모든 데이터 삭제)
        if args.db_reset:
            print("⚠️  경고: 데이터베이스가 백업된 후 모든 데이터가 삭제됩니다!")
            confirm = input("정말로 진행하시겠습니까? (yes/no): ")
            if confirm.lower() == 'yes':
                if scheduler.data_manager.reset_database():
                    print("데이터베이스 완전 초기화 완료")
                else:
                    print("데이터베이스 완전 초기화 실패")
            else:
                print("완전 초기화가 취소되었습니다.")
            return
            
        # 새 게시물 수 조회
        if args.new_posts:
            new_posts_count = scheduler.data_manager.get_new_posts_count(args.new_posts, days=7)
            print(f"=== {args.new_posts} 계정의 새 게시물 현황 ===")
            print(f"최근 7일간 새로 저장된 게시물: {new_posts_count}개")
            return
            
        # 최신 게시물 조회
        if args.latest_posts:
            latest_posts = scheduler.data_manager.get_latest_posts(args.latest_posts, limit=10)
            print(f"=== {args.latest_posts} 계정의 최신 게시물 ===")
            if latest_posts:
                for i, post in enumerate(latest_posts, 1):
                    print(f"\n{i}. 게시물")
                    print(f"   URL: {post.get('post_url', 'N/A')}")
                    
                    # 캡션이 None이 아닌 경우에만 슬라이싱 적용
                    caption = post.get('caption')
                    if caption:
                        print(f"   캡션: {caption[:100]}...")
                    else:
                        print(f"   캡션: N/A")
                    
                    print(f"   게시시간: {post.get('posted_at', 'N/A')}")
                    print(f"   저장시간: {post.get('created_at', 'N/A')}")
            else:
                print("저장된 게시물이 없습니다.")
            return
        
        # 즉시 실행
        if args.once:
            logger.info("즉시 크롤링 실행")
            scheduler.run_once()
            return
        
        # 스케줄러 시작
        if not accounts:
            logger.error("크롤링할 계정이 없습니다. --accounts 옵션으로 계정을 지정하거나 config.py에서 기본값을 설정하세요.")
            return
        
        logger.info(f"스케줄러 시작 - 계정: {accounts}, 간격: {args.interval}시간")
        print(f"크롤링 시작: {accounts}")
        print(f"크롤링 간격: {args.interval}시간")
        print("Ctrl+C로 중지할 수 있습니다.")
        
        try:
            scheduler.start()
            
            # 메인 루프
            while True:
                import time
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("사용자에 의해 중지됨")
            print("\n스케줄러를 중지합니다...")
            scheduler.stop()
            
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        print(f"오류가 발생했습니다: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
