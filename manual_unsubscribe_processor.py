#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB 手動配信停止処理スクリプト
指定されたメールアドレスの配信停止を手動で処理

作成日時: 2025年6月26日
目的: 手動で確認された配信停止申請を処理
"""

import os
import json
import csv
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse

class ManualUnsubscribeProcessor:
    """手動配信停止処理クラス"""
    
    def __init__(self):
        self.company_csv_file = 'data/new_input_test.csv'
        self.unsubscribe_log_file = 'data/huganjob_unsubscribe_log.json'
        self.companies_df = None
        self.unsubscribe_log = []
        
    def load_company_data(self) -> bool:
        """企業データを読み込み"""
        try:
            if not os.path.exists(self.company_csv_file):
                print(f"❌ 企業CSVファイルが見つかりません: {self.company_csv_file}")
                return False
            
            self.companies_df = pd.read_csv(self.company_csv_file, encoding='utf-8-sig')
            print(f"✅ 企業データ読み込み完了: {len(self.companies_df)}社")
            return True
            
        except Exception as e:
            print(f"❌ 企業データ読み込みエラー: {e}")
            return False
    
    def load_unsubscribe_log(self) -> bool:
        """配信停止ログを読み込み"""
        try:
            if os.path.exists(self.unsubscribe_log_file):
                with open(self.unsubscribe_log_file, 'r', encoding='utf-8') as f:
                    self.unsubscribe_log = json.load(f)
                print(f"✅ 配信停止ログ読み込み完了: {len(self.unsubscribe_log)}件")
            else:
                self.unsubscribe_log = []
                print("📝 新規配信停止ログファイルを作成します")
            return True
            
        except Exception as e:
            print(f"❌ 配信停止ログ読み込みエラー: {e}")
            self.unsubscribe_log = []
            return False
    
    def find_company_by_email(self, email: str) -> Optional[Dict]:
        """メールアドレスから企業を検索（ドメインマッチング対応）"""
        try:
            email = email.lower().strip()

            # 1. 完全一致検索
            email_columns = ['採用担当メールアドレス', 'メールアドレス', 'email']

            for col in email_columns:
                if col in self.companies_df.columns:
                    matches = self.companies_df[
                        self.companies_df[col].astype(str).str.lower() == email
                    ]

                    if not matches.empty:
                        company = matches.iloc[0].to_dict()
                        print(f"✅ 企業発見（完全一致）: {company.get('企業名', 'N/A')} (ID: {company.get('ID', 'N/A')})")
                        return company

            # 2. ドメインマッチング検索
            if '@' in email:
                domain = email.split('@')[1]
                print(f"🔍 ドメインマッチング検索: {domain}")

                # 企業ホームページのドメインと照合
                if '企業ホームページ' in self.companies_df.columns:
                    for idx, row in self.companies_df.iterrows():
                        company_url = str(row.get('企業ホームページ', '')).lower()
                        if company_url and company_url != 'nan':
                            # URLからドメインを抽出
                            try:
                                parsed_url = urlparse(company_url if company_url.startswith('http') else f'http://{company_url}')
                                company_domain = parsed_url.netloc.lower()

                                # www.を除去して比較
                                company_domain = company_domain.replace('www.', '')

                                if domain == company_domain:
                                    company = row.to_dict()
                                    print(f"✅ 企業発見（ドメイン一致）: {company.get('企業名', 'N/A')} (ID: {company.get('ID', 'N/A')})")
                                    print(f"   ドメイン: {domain} ↔ {company_domain}")
                                    return company
                            except Exception as e:
                                continue

            print(f"⚠️ 企業が見つかりません: {email}")
            return None

        except Exception as e:
            print(f"❌ 企業検索エラー: {e}")
            return None
    
    def is_already_unsubscribed(self, email: str) -> bool:
        """既に配信停止済みかチェック"""
        email = email.lower().strip()
        
        # 配信停止ログをチェック
        for entry in self.unsubscribe_log:
            if entry.get('email', '').lower() == email:
                return True
        
        # CSVの配信停止フラグをチェック
        if self.companies_df is not None:
            email_columns = ['採用担当メールアドレス', 'メールアドレス', 'email']
            
            for col in email_columns:
                if col in self.companies_df.columns:
                    matches = self.companies_df[
                        self.companies_df[col].astype(str).str.lower() == email
                    ]
                    
                    if not matches.empty:
                        company = matches.iloc[0]
                        # 配信停止フラグをチェック
                        unsubscribe_columns = ['配信停止', 'unsubscribed', '配信停止フラグ']
                        for unsub_col in unsubscribe_columns:
                            if unsub_col in self.companies_df.columns:
                                if str(company.get(unsub_col, '')).lower() in ['true', '1', 'yes', '配信停止']:
                                    return True
        
        return False
    
    def mark_company_unsubscribed(self, company: Dict, email: str, reason: str = "手動配信停止申請") -> bool:
        """企業を配信停止としてマーク"""
        try:
            email = email.lower().strip()
            company_id = company.get('ID')
            company_name = company.get('企業名', 'N/A')
            
            # 配信停止ログに追加
            unsubscribe_entry = {
                'company_id': company_id,
                'company_name': company_name,
                'email': email,
                'reason': reason,
                'timestamp': datetime.now().isoformat(),
                'source': 'manual_processing'
            }
            
            self.unsubscribe_log.append(unsubscribe_entry)
            
            # CSVファイルを更新（配信停止フラグを設定）
            if self.companies_df is not None:
                # 該当企業の行を特定
                company_index = self.companies_df[self.companies_df['ID'] == company_id].index
                
                if not company_index.empty:
                    idx = company_index[0]
                    
                    # 配信停止フラグを設定
                    if '配信停止' not in self.companies_df.columns:
                        self.companies_df['配信停止'] = ''
                    
                    self.companies_df.at[idx, '配信停止'] = '配信停止'
                    
                    # 配信停止日時を記録
                    if '配信停止日時' not in self.companies_df.columns:
                        self.companies_df['配信停止日時'] = ''
                    
                    self.companies_df.at[idx, '配信停止日時'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    print(f"✅ 企業を配信停止としてマーク: {company_name} ({email})")
                    return True
                else:
                    print(f"❌ 企業IDが見つかりません: {company_id}")
                    return False
            else:
                print(f"❌ 企業データが読み込まれていません")
                return False
                
        except Exception as e:
            print(f"❌ 配信停止マークエラー: {e}")
            return False
    
    def save_unsubscribe_log(self) -> bool:
        """配信停止ログを保存"""
        try:
            os.makedirs('data', exist_ok=True)
            with open(self.unsubscribe_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.unsubscribe_log, f, indent=2, ensure_ascii=False)
            print(f"✅ 配信停止ログ保存完了: {len(self.unsubscribe_log)}件")
            return True
            
        except Exception as e:
            print(f"❌ 配信停止ログ保存エラー: {e}")
            return False
    
    def save_company_data(self) -> bool:
        """企業データを保存"""
        try:
            if self.companies_df is not None:
                self.companies_df.to_csv(self.company_csv_file, index=False, encoding='utf-8-sig')
                print(f"✅ 企業データ保存完了")
                return True
            else:
                print(f"❌ 企業データが読み込まれていません")
                return False
                
        except Exception as e:
            print(f"❌ 企業データ保存エラー: {e}")
            return False
    
    def process_unsubscribe_requests(self, email_list: List[str]) -> int:
        """配信停止申請を処理"""
        processed_count = 0
        
        print(f"🔄 配信停止処理開始: {len(email_list)}件")
        
        for email in email_list:
            print(f"\n📧 処理中: {email}")
            
            # 既に配信停止済みかチェック
            if self.is_already_unsubscribed(email):
                print(f"⚠️ 既に配信停止済み: {email}")
                continue
            
            # 企業を検索
            company = self.find_company_by_email(email)
            if not company:
                print(f"❌ 企業が見つかりません: {email}")
                continue
            
            # 配信停止処理
            success = self.mark_company_unsubscribed(
                company=company,
                email=email,
                reason="手動確認による配信停止申請"
            )
            
            if success:
                processed_count += 1
                print(f"✅ 配信停止処理完了: {email}")
            else:
                print(f"❌ 配信停止処理失敗: {email}")
        
        return processed_count

def main():
    """メイン処理"""
    print("=" * 60)
    print("HUGANJOB 手動配信停止処理システム")
    print("=" * 60)
    
    # 指定された配信停止申請（ドメインベース対応）
    unsubscribe_requests = [
        "t-hayakawa@media4u.co.jp",  # 2025/06/26 12:55:35 - ドメインマッチング対象
        "info@n-media.co.jp"        # 2025/06/26 13:23:46 - 既に処理済み
    ]
    
    print(f"📋 処理対象: {len(unsubscribe_requests)}件")
    for i, email in enumerate(unsubscribe_requests, 1):
        print(f"  {i}. {email}")
    
    processor = ManualUnsubscribeProcessor()
    
    # データ読み込み
    if not processor.load_company_data():
        print("❌ 企業データ読み込み失敗")
        return False
    
    if not processor.load_unsubscribe_log():
        print("❌ 配信停止ログ読み込み失敗")
        return False
    
    # 配信停止処理
    processed_count = processor.process_unsubscribe_requests(unsubscribe_requests)
    
    # データ保存
    if processed_count > 0:
        if processor.save_unsubscribe_log() and processor.save_company_data():
            print(f"\n🎉 配信停止処理完了: {processed_count}/{len(unsubscribe_requests)}件")
            print("📊 ダッシュボードで確認してください: http://127.0.0.1:5002/")
        else:
            print("❌ データ保存に失敗しました")
            return False
    else:
        print("\n⚠️ 処理された配信停止申請はありませんでした")
    
    return True

if __name__ == "__main__":
    main()
