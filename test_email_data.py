#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB データ確認テストスクリプト
"""

import pandas as pd
import sys

def main():
    print("=" * 60)
    print("📊 HUGAN JOB データ確認テスト")
    print("=" * 60)
    
    try:
        # メールアドレス結果読み込み
        print("📂 huganjob_email_resolution_results.csv を読み込み中...")
        df = pd.read_csv('huganjob_email_resolution_results.csv', encoding='utf-8')
        
        print(f"✅ データ読み込み成功")
        print(f"📊 総行数: {len(df)}")
        print(f"📊 列名: {list(df.columns)}")
        
        # ID 1-5のデータ確認
        target_data = df[df['company_id'].isin([1, 2, 3, 4, 5])].copy()
        print(f"📊 ID 1-5のデータ行数: {len(target_data)}")
        
        if len(target_data) > 0:
            print("\n📋 ID 1-5の企業データ:")
            for index, row in target_data.iterrows():
                print(f"  ID {row['company_id']}: {row['company_name']} - {row['final_email']} ({row['job_position']})")
        else:
            print("❌ ID 1-5のデータが見つかりません")
            print(f"📊 利用可能なcompany_id: {sorted(df['company_id'].unique())}")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
