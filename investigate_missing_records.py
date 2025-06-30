#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
送信記録の不足調査スクリプト
1859社に送信したはずが1770社分しか記録されていない問題を調査
"""

import csv
import pandas as pd
from collections import defaultdict

def main():
    print("=" * 60)
    print("📊 送信記録不足調査")
    print("=" * 60)
    
    # 送信結果を読み込み
    try:
        df_results = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
        print(f"✅ 送信記録総数: {len(df_results)}件")
        print(f"   最小企業ID: {df_results['企業ID'].min()}")
        print(f"   最大企業ID: {df_results['企業ID'].max()}")
        print(f"   ユニークな企業ID数: {df_results['企業ID'].nunique()}")
    except Exception as e:
        print(f"❌ 送信結果読み込みエラー: {e}")
        return
    
    # 企業データベースを読み込み
    try:
        df_companies = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
        print(f"✅ 企業データベース総数: {len(df_companies)}社")
        print(f"   企業データベース最小ID: {df_companies['ID'].min()}")
        print(f"   企業データベース最大ID: {df_companies['ID'].max()}")
    except Exception as e:
        print(f"❌ 企業データベース読み込みエラー: {e}")
        return
    
    # 送信記録にない企業IDを特定
    sent_ids = set(df_results['企業ID'].tolist())
    all_ids = set(df_companies['ID'].tolist())
    missing_ids = all_ids - sent_ids
    
    print(f"\n🔍 分析結果:")
    print(f"   送信記録にない企業ID数: {len(missing_ids)}社")
    
    if len(missing_ids) <= 50:
        print(f"   送信記録にない企業ID: {sorted(missing_ids)}")
    else:
        missing_list = sorted(missing_ids)
        print(f"   送信記録にない企業ID（最初の20件）: {missing_list[:20]}")
        print(f"   送信記録にない企業ID（最後の20件）: {missing_list[-20:]}")
    
    # 送信結果の状況を分析
    print(f"\n📈 送信結果の状況:")
    result_counts = df_results['送信結果'].value_counts()
    for result, count in result_counts.items():
        print(f"   {result}: {count}件")
    
    # 送信記録にない企業の詳細を確認
    if len(missing_ids) > 0:
        print(f"\n📋 送信記録にない企業の詳細（最初の10社）:")
        missing_companies = df_companies[df_companies['ID'].isin(sorted(missing_ids)[:10])]
        for _, company in missing_companies.iterrows():
            print(f"   ID {company['ID']}: {company['企業名']} - {company.get('担当者メールアドレス', 'N/A')}")
    
    # 重複送信記録の確認
    duplicate_ids = df_results[df_results.duplicated(subset=['企業ID'], keep=False)]
    if len(duplicate_ids) > 0:
        print(f"\n⚠️ 重複送信記録:")
        print(f"   重複している企業ID数: {duplicate_ids['企業ID'].nunique()}社")
        for company_id in duplicate_ids['企業ID'].unique()[:5]:
            duplicates = df_results[df_results['企業ID'] == company_id]
            print(f"   ID {company_id}: {len(duplicates)}回送信")
    
    # 送信履歴ファイルも確認
    print(f"\n📁 送信履歴ファイル確認:")
    try:
        import json
        with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        history_records = history.get('sending_records', [])
        print(f"   送信履歴記録数: {len(history_records)}件")
        
        if history_records:
            history_ids = set()
            for record in history_records:
                try:
                    history_ids.add(int(record['company_id']))
                except:
                    continue
            
            print(f"   送信履歴のユニーク企業ID数: {len(history_ids)}社")
            
            # 送信履歴にあるが送信結果にない企業ID
            history_only = history_ids - sent_ids
            if history_only:
                print(f"   送信履歴にあるが送信結果にない企業ID数: {len(history_only)}社")
                if len(history_only) <= 20:
                    print(f"   該当企業ID: {sorted(history_only)}")
    
    except Exception as e:
        print(f"   送信履歴ファイル読み込みエラー: {e}")
    
    # 他の送信結果ファイルも確認
    print(f"\n📂 その他の送信結果ファイル確認:")
    import glob
    import os
    
    other_files = []
    for pattern in ['sent_emails_record_*.csv', '*sending_results*.csv', '*email_results*.csv']:
        other_files.extend(glob.glob(pattern))
    
    for file_path in other_files:
        if file_path != 'new_email_sending_results.csv' and os.path.exists(file_path):
            try:
                df_other = pd.read_csv(file_path, encoding='utf-8-sig')
                print(f"   {file_path}: {len(df_other)}件")
                
                # 企業IDがある場合は詳細確認
                if '企業ID' in df_other.columns:
                    other_ids = set(df_other['企業ID'].tolist())
                    overlap_with_main = len(sent_ids & other_ids)
                    unique_to_other = len(other_ids - sent_ids)
                    print(f"     メインファイルとの重複: {overlap_with_main}件")
                    print(f"     このファイル独自: {unique_to_other}件")
                    
                    # 不足分を補完できるかチェック
                    if unique_to_other > 0:
                        complementary_ids = (other_ids - sent_ids) & missing_ids
                        if complementary_ids:
                            print(f"     不足分を補完可能: {len(complementary_ids)}社")
                            
            except Exception as e:
                print(f"   {file_path}: 読み込みエラー - {e}")

if __name__ == "__main__":
    main()
