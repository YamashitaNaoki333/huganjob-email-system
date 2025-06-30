#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ID 1937-1950送信結果の詳細確認
"""

import json
import pandas as pd
from datetime import datetime

def verify_results():
    print("📊 ID 1937-1950 送信結果詳細確認")
    print("=" * 60)
    
    # 送信履歴確認
    print("📋 送信履歴確認")
    print("-" * 30)
    
    try:
        with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        # ID 1937-1950の送信記録を抽出
        target_records = []
        for record in history['sending_records']:
            try:
                company_id = int(record['company_id'])
                if 1937 <= company_id <= 1950:
                    target_records.append(record)
            except:
                continue
        
        print(f"総送信記録数: {len(target_records)}件")
        
        # 企業IDごとにグループ化
        company_groups = {}
        for record in target_records:
            company_id = record['company_id']
            if company_id not in company_groups:
                company_groups[company_id] = []
            company_groups[company_id].append(record)
        
        print(f"送信企業数: {len(company_groups)}社")
        print()
        
        # 各企業の送信詳細
        for company_id in sorted(company_groups.keys(), key=int):
            records = company_groups[company_id]
            print(f"ID {company_id}: {records[0]['company_name']}")
            print(f"  メール: {records[0]['email_address']}")
            print(f"  送信回数: {len(records)}回")
            
            for i, record in enumerate(records):
                print(f"    {i+1}. {record['send_time']} (PID: {record['pid']})")
            print()
        
    except Exception as e:
        print(f"❌ 送信履歴確認エラー: {e}")
    
    # 送信結果ファイル確認
    print("📊 送信結果ファイル確認")
    print("-" * 30)
    
    try:
        df = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
        target_results = df[(df['企業ID'] >= 1937) & (df['企業ID'] <= 1950)]
        
        print(f"送信結果記録数: {len(target_results)}件")
        
        # 成功・失敗の統計
        success_count = len(target_results[target_results['送信結果'] == 'success'])
        failed_count = len(target_results) - success_count
        
        print(f"送信成功: {success_count}件")
        print(f"送信失敗: {failed_count}件")
        print()
        
        # 企業別詳細
        print("企業別送信結果:")
        for _, row in target_results.iterrows():
            status_icon = "✅" if row['送信結果'] == 'success' else "❌"
            print(f"  {status_icon} ID {row['企業ID']}: {row['企業名']}")
            print(f"     職種: {row['募集職種']}")
            print(f"     送信時刻: {row['送信日時']}")
            print(f"     結果: {row['送信結果']}")
            if row['送信結果'] != 'success':
                print(f"     エラー: {row.get('エラーメッセージ', 'N/A')}")
            print()
        
    except Exception as e:
        print(f"❌ 送信結果ファイル確認エラー: {e}")
    
    # 重複送信チェック
    print("🔍 重複送信チェック")
    print("-" * 30)
    
    try:
        # 送信履歴から重複をチェック
        company_send_counts = {}
        for record in target_records:
            company_id = record['company_id']
            company_send_counts[company_id] = company_send_counts.get(company_id, 0) + 1
        
        duplicates = {k: v for k, v in company_send_counts.items() if v > 1}
        
        if duplicates:
            print(f"重複送信企業: {len(duplicates)}社")
            for company_id, count in duplicates.items():
                print(f"  ID {company_id}: {count}回送信")
        else:
            print("✅ 重複送信なし")
        
    except Exception as e:
        print(f"❌ 重複チェックエラー: {e}")
    
    # 送信範囲完了確認
    print("\n🎯 送信範囲完了確認")
    print("-" * 30)
    
    expected_ids = set(range(1937, 1951))  # 1937-1950
    sent_ids = set()
    
    try:
        for record in target_records:
            sent_ids.add(int(record['company_id']))
        
        missing_ids = expected_ids - sent_ids
        extra_ids = sent_ids - expected_ids
        
        print(f"期待範囲: ID 1937-1950 ({len(expected_ids)}社)")
        print(f"送信済み: {len(sent_ids)}社")
        
        if missing_ids:
            print(f"❌ 未送信: {sorted(missing_ids)}")
        else:
            print("✅ 全社送信完了")
        
        if extra_ids:
            print(f"⚠️ 範囲外送信: {sorted(extra_ids)}")
        
    except Exception as e:
        print(f"❌ 範囲確認エラー: {e}")

def main():
    print("🔍 HUGANJOB ID 1937-1950 送信結果検証")
    print("=" * 80)
    
    verify_results()
    
    print("\n🎉 検証完了")

if __name__ == "__main__":
    main()
