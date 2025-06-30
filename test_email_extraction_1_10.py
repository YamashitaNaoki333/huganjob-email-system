#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB メールアドレス抽出テスト（ID 1-10）
"""

import pandas as pd
import logging
import sys
import os

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_email_extraction():
    """ID 1-10の企業でメールアドレス抽出をテスト"""
    
    print("=" * 60)
    print("📧 HUGAN JOB メールアドレス抽出テスト（ID 1-10）")
    print("=" * 60)
    
    # CSVファイル読み込み
    csv_file = "data/new_input_test.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ CSVファイルが見つかりません: {csv_file}")
        return False
    
    try:
        df = pd.read_csv(csv_file, encoding='utf-8')
        print(f"✅ CSVファイル読み込み成功: {len(df)}社")
        
        # ID 1-10の企業を抽出
        test_companies = df[(df['ID'] >= 1) & (df['ID'] <= 10)]
        print(f"🎯 テスト対象: {len(test_companies)}社（ID 1-10）")
        
        if len(test_companies) == 0:
            print("❌ ID 1-10の企業が見つかりません")
            return False
        
        print("\n📋 企業一覧:")
        for index, row in test_companies.iterrows():
            company_id = row['ID']
            company_name = row['企業名']
            website_url = row['企業ホームページ']
            csv_email = row['担当者メールアドレス']
            job_position = row['募集職種']
            
            print(f"\n{company_id:2d}. {company_name}")
            print(f"    HP: {website_url}")
            print(f"    CSV Email: {csv_email}")
            print(f"    職種: {job_position}")
            
            # メールアドレスの状況を確認
            if pd.isna(csv_email) or csv_email in ['‐', '-', '', ' ']:
                print(f"    📧 状況: CSVにメールアドレスなし → ウェブ抽出が必要")
            else:
                print(f"    📧 状況: CSVにメールアドレスあり → 直接使用可能")
        
        print(f"\n✅ テスト完了: {len(test_companies)}社の情報を確認しました")
        
        # 統計情報
        csv_has_email = test_companies[~test_companies['担当者メールアドレス'].isin(['‐', '-', '', ' ']) & 
                                      ~test_companies['担当者メールアドレス'].isna()]
        csv_no_email = test_companies[test_companies['担当者メールアドレス'].isin(['‐', '-', '', ' ']) | 
                                     test_companies['担当者メールアドレス'].isna()]
        
        print(f"\n📊 統計:")
        print(f"  CSVにメールアドレスあり: {len(csv_has_email)}社")
        print(f"  CSVにメールアドレスなし: {len(csv_no_email)}社")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    test_email_extraction()
