#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB 配信停止検出検証スクリプト
指定された配信停止申請の検出状況を確認

作成日時: 2025年6月26日
目的: Googleフォームからの配信停止申請が正しく検出・処理されているか確認
"""

import os
import json
import csv
import pandas as pd
import hashlib
from datetime import datetime
from typing import List, Dict, Optional

class UnsubscribeDetectionVerifier:
    """配信停止検出検証クラス"""
    
    def __init__(self):
        self.company_csv_file = 'data/new_input_test.csv'
        self.unsubscribe_log_file = 'data/huganjob_unsubscribe_log.json'
        self.processed_entries_file = 'data/huganjob_sheets_processed.json'
        
        # 検証対象の配信停止申請
        self.target_requests = [
            {
                'timestamp': '2025/06/26 12:55:35',
                'email': 't-hayakawa@media4u.co.jp'
            },
            {
                'timestamp': '2025/06/26 13:23:46',
                'email': 'info@n-media.co.jp'
            }
        ]
    
    def create_entry_hash(self, timestamp: str, email: str) -> str:
        """エントリのハッシュ値を作成（Google Sheets監視システムと同じ方式）"""
        entry_string = f"{timestamp}|{email.lower().strip()}"
        return hashlib.md5(entry_string.encode('utf-8')).hexdigest()
    
    def check_company_database(self):
        """企業データベースでの検出状況を確認"""
        print("🔍 1. 企業データベース検証")
        print("-" * 50)
        
        try:
            if not os.path.exists(self.company_csv_file):
                print(f"❌ 企業CSVファイルが見つかりません: {self.company_csv_file}")
                return
            
            df = pd.read_csv(self.company_csv_file, encoding='utf-8-sig')
            print(f"✅ 企業データ読み込み: {len(df)}社")
            
            for request in self.target_requests:
                email = request['email']
                timestamp = request['timestamp']
                
                print(f"\n📧 検索中: {email} ({timestamp})")
                
                # メールアドレス列で検索
                email_columns = ['採用担当メールアドレス', 'メールアドレス', 'email']
                found = False
                
                for col in email_columns:
                    if col in df.columns:
                        matches = df[df[col].astype(str).str.lower() == email.lower()]
                        if not matches.empty:
                            company = matches.iloc[0]
                            company_id = company.get('ID', 'N/A')
                            company_name = company.get('企業名', 'N/A')
                            unsubscribe_flag = company.get('配信停止', '')
                            unsubscribe_date = company.get('配信停止日時', '')
                            
                            print(f"  ✅ 企業発見: {company_name} (ID: {company_id})")
                            print(f"     列: {col}")
                            print(f"     配信停止フラグ: {unsubscribe_flag}")
                            print(f"     配信停止日時: {unsubscribe_date}")
                            
                            if unsubscribe_flag == '配信停止':
                                print(f"  🚫 配信停止済み")
                            else:
                                print(f"  ⚠️ 配信停止未処理")
                            
                            found = True
                            break
                
                if not found:
                    print(f"  ❌ 企業が見つかりません: {email}")
                    
                    # ドメインで部分検索
                    domain = email.split('@')[1] if '@' in email else ''
                    if domain:
                        print(f"  🔍 ドメイン検索: {domain}")
                        domain_matches = df[df['企業ホームページ'].astype(str).str.contains(domain, case=False, na=False)]
                        if not domain_matches.empty:
                            print(f"  📋 同一ドメインの企業:")
                            for _, company in domain_matches.iterrows():
                                print(f"    - {company.get('企業名', 'N/A')} (ID: {company.get('ID', 'N/A')})")
                                print(f"      メール: {company.get('採用担当メールアドレス', 'N/A')}")
                        else:
                            print(f"  ❌ 同一ドメインの企業も見つかりません")
                            
        except Exception as e:
            print(f"❌ 企業データベース検証エラー: {e}")
    
    def check_unsubscribe_log(self):
        """配信停止ログでの記録状況を確認"""
        print("\n🔍 2. 配信停止ログ検証")
        print("-" * 50)
        
        try:
            if not os.path.exists(self.unsubscribe_log_file):
                print(f"⚠️ 配信停止ログファイルが見つかりません: {self.unsubscribe_log_file}")
                return
            
            with open(self.unsubscribe_log_file, 'r', encoding='utf-8') as f:
                unsubscribe_log = json.load(f)
            
            print(f"✅ 配信停止ログ読み込み: {len(unsubscribe_log)}件")
            
            for request in self.target_requests:
                email = request['email']
                timestamp = request['timestamp']
                
                print(f"\n📧 検索中: {email} ({timestamp})")
                
                found = False
                for entry in unsubscribe_log:
                    if entry.get('email', '').lower() == email.lower():
                        print(f"  ✅ 配信停止ログに記録済み:")
                        print(f"     企業: {entry.get('company_name', 'N/A')} (ID: {entry.get('company_id', 'N/A')})")
                        print(f"     理由: {entry.get('reason', 'N/A')}")
                        print(f"     処理日時: {entry.get('timestamp', 'N/A')}")
                        print(f"     ソース: {entry.get('source', 'N/A')}")
                        found = True
                        break
                
                if not found:
                    print(f"  ❌ 配信停止ログに記録なし: {email}")
                    
        except Exception as e:
            print(f"❌ 配信停止ログ検証エラー: {e}")
    
    def check_google_sheets_processing(self):
        """Google Sheets処理済みエントリでの記録状況を確認"""
        print("\n🔍 3. Google Sheets処理済みエントリ検証")
        print("-" * 50)
        
        try:
            if not os.path.exists(self.processed_entries_file):
                print(f"⚠️ 処理済みエントリファイルが見つかりません: {self.processed_entries_file}")
                return
            
            with open(self.processed_entries_file, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)
            
            processed_hashes = set(processed_data.get('processed_hashes', []))
            last_updated = processed_data.get('last_updated', 'N/A')
            
            print(f"✅ 処理済みエントリ読み込み: {len(processed_hashes)}件")
            print(f"📅 最終更新: {last_updated}")
            
            for request in self.target_requests:
                email = request['email']
                timestamp = request['timestamp']
                
                print(f"\n📧 検証中: {email} ({timestamp})")
                
                # ハッシュ値を計算
                entry_hash = self.create_entry_hash(timestamp, email)
                print(f"  🔑 ハッシュ値: {entry_hash}")
                
                if entry_hash in processed_hashes:
                    print(f"  ✅ 処理済みエントリに記録済み")
                else:
                    print(f"  ❌ 処理済みエントリに記録なし")
                    
        except Exception as e:
            print(f"❌ Google Sheets処理済みエントリ検証エラー: {e}")
    
    def check_google_sheets_credentials(self):
        """Google Sheets API認証情報の確認"""
        print("\n🔍 4. Google Sheets API認証情報検証")
        print("-" * 50)
        
        credentials_file = 'config/google_sheets_credentials.json'
        
        if not os.path.exists(credentials_file):
            print(f"❌ 認証情報ファイルが見つかりません: {credentials_file}")
            return
        
        try:
            with open(credentials_file, 'r', encoding='utf-8') as f:
                credentials = json.load(f)
            
            print(f"✅ 認証情報ファイル存在: {credentials_file}")
            
            # 必要なフィールドをチェック
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            missing_fields = []
            
            for field in required_fields:
                if field not in credentials or not credentials[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"⚠️ 不足している認証情報フィールド: {missing_fields}")
            else:
                print(f"✅ 認証情報フィールド完備")
                
            # プロジェクト情報表示
            print(f"📋 プロジェクトID: {credentials.get('project_id', 'N/A')}")
            print(f"📧 サービスアカウント: {credentials.get('client_email', 'N/A')}")
            
        except Exception as e:
            print(f"❌ 認証情報ファイル読み込みエラー: {e}")
    
    def generate_summary_report(self):
        """検証結果のサマリーレポートを生成"""
        print("\n📊 検証結果サマリー")
        print("=" * 60)
        
        print("📋 検証対象:")
        for i, request in enumerate(self.target_requests, 1):
            print(f"  {i}. {request['timestamp']} | {request['email']}")
        
        print("\n🔍 検証項目:")
        print("  1. ✅ 企業データベース検索")
        print("  2. ✅ 配信停止ログ確認")
        print("  3. ✅ Google Sheets処理済みエントリ確認")
        print("  4. ✅ Google Sheets API認証情報確認")
        
        print("\n💡 推奨アクション:")
        print("  - Google Sheets監視システムの手動実行")
        print("  - 配信停止申請の手動処理")
        print("  - ダッシュボードでの最終確認")

def main():
    """メイン処理"""
    print("=" * 60)
    print("HUGANJOB 配信停止検出検証システム")
    print("=" * 60)
    
    verifier = UnsubscribeDetectionVerifier()
    
    # 各種検証を実行
    verifier.check_company_database()
    verifier.check_unsubscribe_log()
    verifier.check_google_sheets_processing()
    verifier.check_google_sheets_credentials()
    verifier.generate_summary_report()
    
    print("\n🏁 検証完了")

if __name__ == "__main__":
    main()
