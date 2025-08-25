#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
from datetime import datetime

def check_database():
    """데이터베이스 내용 확인"""
    db_path = "instagram_data.db"
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("=== 데이터베이스 내용 확인 ===\n")
            
            # 1. account_data 테이블 확인
            print("1. 계정 정보 (account_data):")
            cursor.execute("SELECT * FROM account_data")
            accounts = cursor.fetchall()
            if accounts:
                for account in accounts:
                    print(f"   ID: {account[0]}, User ID: {account[1]}, Username: {account[2]}, 생성일: {account[3]}")
            else:
                print("   저장된 계정 정보가 없습니다.")
            print()
            
            # 2. post_data 테이블 확인
            print("2. 게시물 정보 (post_data):")
            cursor.execute("SELECT * FROM post_data")
            posts = cursor.fetchall()
            if posts:
                for post in posts:
                    print(f"   ID: {post[0]}, Account ID: {post[1]}, Post URL: {post[2]}")
                    print(f"   Post Number: {post[3]}, Image URL: {post[4]}")
                    caption = post[5]
                    if caption:
                        print(f"   Caption: {caption[:100]}...")
                    else:
                        print(f"   Caption: N/A")
                    print(f"   Posted At: {post[6]}, Hashtags: {post[7]}, Mentions: {post[8]}")
                    print(f"   Timestamp: {post[9]}, Created At: {post[10]}")
                    print("   " + "-"*50)
            else:
                print("   저장된 게시물이 없습니다.")
            print()
            
            # 3. crawl_history 테이블 확인
            print("3. 크롤링 히스토리 (crawl_history):")
            cursor.execute("SELECT * FROM crawl_history")
            history = cursor.fetchall()
            if history:
                for record in history:
                    print(f"   ID: {record[0]}, Username: {record[1]}, Status: {record[2]}")
                    print(f"   Crawled At: {record[3]}, Error: {record[4] if record[4] else 'N/A'}")
                    print(f"   Created At: {record[5]}")
                    print("   " + "-"*30)
            else:
                print("   크롤링 히스토리가 없습니다.")
            print()
            
            # 4. 테이블 스키마 확인
            print("4. 테이블 스키마:")
            tables = ['account_data', 'post_data', 'crawl_history']
            for table in tables:
                print(f"\n   {table} 테이블:")
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"     {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULLABLE'}")
            
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    check_database()
