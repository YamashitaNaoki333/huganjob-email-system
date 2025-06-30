#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
送信記録復元スクリプト
送信履歴から欠落した送信結果を復元し、統計を修正
"""

import json
import csv
import pandas as pd
from datetime import datetime
import os
import shutil

def main():
    print("=" * 60)
    print("🔧 送信記録復元処理開始")
    print("=" * 60)
    
    # バックアップ作成
    backup_file = f"new_email_sending_results_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    shutil.copy('new_email_sending_results.csv', backup_file)
    print(f"📁 バックアップ作成: {backup_file}")
    
    # 送信履歴を読み込み
    try:
        with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        print(f"📋 送信履歴読み込み: {len(history['sending_records'])}件")
        
        # 送信履歴を企業IDでインデックス化
        history_by_id = {}
        for record in history['sending_records']:
            try:
                company_id = int(record['company_id'])
                history_by_id[company_id] = record
            except:
                continue
        
        print(f"📋 送信履歴のユニーク企業ID数: {len(history_by_id)}社")
        
    except Exception as e:
        print(f"❌ 送信履歴読み込みエラー: {e}")
        return False
    
    # 現在の送信結果を読み込み
    try:
        df_results = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
        existing_ids = set(df_results['企業ID'].tolist())
        print(f"📋 既存送信結果: {len(existing_ids)}社")
        
    except Exception as e:
        print(f"❌ 送信結果読み込みエラー: {e}")
        return False
    
    # 企業データベースを読み込み
    try:
        df_companies = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
        companies_by_id = {}
        for _, company in df_companies.iterrows():
            companies_by_id[company['ID']] = company
        
        print(f"📋 企業データベース: {len(companies_by_id)}社")
        
    except Exception as e:
        print(f"❌ 企業データベース読み込みエラー: {e}")
        return False
    
    # 欠落した記録を特定
    history_ids = set(history_by_id.keys())
    missing_ids = history_ids - existing_ids
    
    print(f"\n🔍 欠落記録分析:")
    print(f"   送信履歴にある企業ID: {len(history_ids)}社")
    print(f"   送信結果にある企業ID: {len(existing_ids)}社")
    print(f"   欠落している企業ID: {len(missing_ids)}社")
    
    if not missing_ids:
        print("✅ 欠落記録はありません")
        return True
    
    # 欠落記録を復元
    print(f"\n🔧 欠落記録復元開始:")
    restored_records = []
    
    for company_id in sorted(missing_ids):
        if company_id in history_by_id and company_id in companies_by_id:
            history_record = history_by_id[company_id]
            company_record = companies_by_id[company_id]
            
            # 送信結果レコードを作成
            restored_record = {
                '企業ID': company_id,
                '企業名': company_record['企業名'],
                '担当者メールアドレス': company_record.get('担当者メールアドレス', ''),
                '募集職種': company_record.get('募集職種', ''),
                '送信日時': history_record['send_time'].replace('T', ' ').replace('Z', ''),
                '送信結果': 'success',  # 送信履歴にあるということは送信成功
                'トラッキングID': history_record.get('tracking_id', ''),
                '送信エラー': ''
            }
            
            restored_records.append(restored_record)
    
    print(f"   復元対象記録数: {len(restored_records)}件")
    
    if restored_records:
        # 既存の送信結果と復元記録を結合
        df_restored = pd.DataFrame(restored_records)
        df_combined = pd.concat([df_results, df_restored], ignore_index=True)
        
        # 企業IDでソート
        df_combined = df_combined.sort_values('企業ID')
        
        # 復元されたファイルを保存
        restored_file = 'new_email_sending_results_restored.csv'
        df_combined.to_csv(restored_file, index=False, encoding='utf-8-sig')
        
        print(f"✅ 復元ファイル作成: {restored_file}")
        print(f"   総記録数: {len(df_combined)}件")
        print(f"   ユニーク企業ID数: {df_combined['企業ID'].nunique()}社")
        
        # 元ファイルを置き換え
        shutil.copy(restored_file, 'new_email_sending_results.csv')
        print(f"✅ メインファイル更新完了")
        
        # 復元された記録の詳細表示
        print(f"\n📋 復元記録の詳細（最初の10件）:")
        for record in restored_records[:10]:
            print(f"   ID {record['企業ID']}: {record['企業名']} - {record['送信日時']}")
        
        if len(restored_records) > 10:
            print(f"   ... 他 {len(restored_records) - 10}件")
    
    # 統計情報を更新
    print(f"\n📊 復元後の統計:")
    df_final = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
    
    total_records = len(df_final)
    unique_companies = df_final['企業ID'].nunique()
    success_count = len(df_final[df_final['送信結果'] == 'success'])
    
    print(f"   総送信記録数: {total_records}件")
    print(f"   ユニーク企業数: {unique_companies}社")
    print(f"   送信成功数: {success_count}件")
    
    # 送信結果の内訳
    result_counts = df_final['送信結果'].value_counts()
    print(f"\n📈 送信結果内訳:")
    for result, count in result_counts.items():
        print(f"   {result}: {count}件")
    
    # 企業データベースとの整合性確認
    total_companies = len(df_companies)
    coverage = (unique_companies / total_companies) * 100
    
    print(f"\n🎯 カバレッジ分析:")
    print(f"   総企業数: {total_companies}社")
    print(f"   送信済み企業数: {unique_companies}社")
    print(f"   カバレッジ: {coverage:.2f}%")
    
    # 配信停止企業を除外した実質的なカバレッジ
    try:
        unsubscribe_log_path = 'data/huganjob_unsubscribe_log.csv'
        unsubscribed_count = 0
        if os.path.exists(unsubscribe_log_path):
            df_unsubscribe = pd.read_csv(unsubscribe_log_path, encoding='utf-8-sig')
            unsubscribed_count = len(df_unsubscribe)
        
        effective_total = total_companies - unsubscribed_count
        effective_coverage = (unique_companies / effective_total) * 100
        
        print(f"   配信停止企業数: {unsubscribed_count}社")
        print(f"   実質対象企業数: {effective_total}社")
        print(f"   実質カバレッジ: {effective_coverage:.2f}%")
        
    except Exception as e:
        print(f"   配信停止企業数確認エラー: {e}")
    
    print(f"\n✅ 送信記録復元処理完了")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
