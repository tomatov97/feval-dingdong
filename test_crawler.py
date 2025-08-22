#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
인스타그램 크롤러 테스트 스크립트
"""

import logging
from instagram_crawler import InstagramCrawler
from data_manager import DataManager
from config import Config

def test_crawler():
    """크롤러 테스트"""
    print("=== 인스타그램 크롤러 테스트 ===")
    
    # 테스트할 계정 (실제 존재하는 계정으로 변경하세요)
    test_username = "instagram"  # 인스타그램 공식 계정
    
    try:
        print(f"계정 '{test_username}' 크롤링 테스트 시작...")
        
        with InstagramCrawler(headless=True) as crawler:
            result = crawler.crawl_account(test_username)
            
            if result:
                print("✅ 크롤링 성공!")
                print(f"수집된 데이터:")
                print(f"- 사용자명: {result['username']}")
                print(f"- 크롤링 시간: {result['crawled_at']}")
                print(f"- 팔로워 수: {result.get('follower_info', {}).get('followers', 'N/A')}")
                print(f"- 게시물 수: {len(result.get('recent_posts', []))}")
                
                # 데이터 저장 테스트
                data_manager = DataManager()
                if data_manager.save_crawl_data(result):
                    print("✅ 데이터 저장 성공!")
                else:
                    print("❌ 데이터 저장 실패!")
                    
            else:
                print("❌ 크롤링 실패!")
                
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        logging.error(f"테스트 오류: {e}")

def test_data_manager():
    """데이터 관리자 테스트"""
    print("\n=== 데이터 관리자 테스트 ===")
    
    try:
        data_manager = DataManager()
        
        # 통계 조회
        stats = data_manager.get_statistics()
        print("데이터베이스 통계:")
        print(f"- 전체 계정 수: {stats.get('total_accounts', 0)}")
        print(f"- 전체 크롤링 수: {stats.get('total_crawls', 0)}")
        print(f"- 성공률: {stats.get('success_rate', 0):.1f}%")
        
        print("✅ 데이터 관리자 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 데이터 관리자 테스트 실패: {e}")

def main():
    """메인 테스트 함수"""
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("인스타그램 크롤링 시스템 테스트를 시작합니다...")
    print("주의: 실제 인스타그램 계정에 접근하므로 적절한 간격을 두고 테스트하세요.")
    print()
    
    # 사용자 확인
    response = input("테스트를 진행하시겠습니까? (y/N): ")
    if response.lower() != 'y':
        print("테스트를 취소했습니다.")
        return
    
    try:
        # 크롤러 테스트
        test_crawler()
        
        # 데이터 관리자 테스트
        test_data_manager()
        
        print("\n🎉 모든 테스트가 완료되었습니다!")
        
    except KeyboardInterrupt:
        print("\n\n테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 중 예상치 못한 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
