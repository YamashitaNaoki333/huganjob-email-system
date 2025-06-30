#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ID 1931-1950プロセス問題の詳細分析
"""

import json
import pandas as pd
from datetime import datetime

def analyze_issue():
    print("🔍 ID 1931-1950プロセス問題分析")
    print("=" * 60)
    
    # 1. 送信履歴の詳細確認
    print("📋 送信履歴分析")
    print("-" * 30)
    
    try:
        with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        # 18:36-18:44の全記録を確認
        target_records = []
        for record in history['sending_records']:
            send_time = record.get('send_time', '')
            if '2025-06-25T18:36' in send_time or '2025-06-25T18:37' in send_time:
                target_records.append(record)
        
        print(f"18:36-18:37の送信記録: {len(target_records)}件")
        
        for record in target_records:
            print(f"  ID {record['company_id']}: {record['company_name']}")
            print(f"    時刻: {record['send_time']}")
            print(f"    PID: {record['pid']}")
        
        # 最後の送信記録
        if target_records:
            last_record = target_records[-1]
            last_id = int(last_record['company_id'])
            print(f"\n最後の送信: ID {last_id} ({last_record['send_time']})")
        
    except Exception as e:
        print(f"❌ 送信履歴エラー: {e}")
    
    # 2. 企業データの確認
    print(f"\n🏢 企業データ分析 (ID 1937-1950)")
    print("-" * 30)
    
    try:
        df = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
        target_companies = df[(df['ID'] >= 1937) & (df['ID'] <= 1950)]
        
        print(f"対象企業数: {len(target_companies)}社")
        
        for _, row in target_companies.iterrows():
            email = row.get('担当者メールアドレス', '')
            print(f"  ID {row['ID']}: {row['企業名']}")
            print(f"    メール: {email}")
            print(f"    職種: {row.get('募集職種', 'N/A')}")
            
            # メールアドレスの妥当性チェック
            if pd.isna(email) or str(email).strip() in ['-', '‐', '']:
                print(f"    ⚠️ メールアドレス不備")
            elif '@' not in str(email):
                print(f"    ⚠️ 無効なメールアドレス")
            else:
                print(f"    ✅ 有効なメールアドレス")
            print()
        
    except Exception as e:
        print(f"❌ 企業データエラー: {e}")
    
    # 3. 送信結果ファイルの確認
    print(f"\n📊 送信結果ファイル分析")
    print("-" * 30)
    
    try:
        df_results = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
        
        # ID 1931以降の記録を確認
        target_results = df_results[df_results['企業ID'] >= 1931]
        
        print(f"ID 1931以降の送信結果: {len(target_results)}件")
        
        if len(target_results) == 0:
            print("❌ ID 1931以降の送信結果記録が存在しません")
            print("   → 送信プロセスが途中でエラーになった可能性")
        else:
            print("✅ 送信結果記録あり")
            for _, row in target_results.iterrows():
                print(f"  ID {row['企業ID']}: {row['送信結果']}")
        
    except Exception as e:
        print(f"❌ 送信結果エラー: {e}")
    
    # 4. プロセス実行時間の分析
    print(f"\n⏱️ プロセス実行時間分析")
    print("-" * 30)
    
    try:
        # 送信履歴から実行時間を計算
        with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        # 18:36の記録を取得
        records_1836 = []
        for record in history['sending_records']:
            send_time = record.get('send_time', '')
            if '2025-06-25T18:36' in send_time or '2025-06-25T18:37' in send_time:
                records_1836.append(record)
        
        if records_1836:
            start_time = records_1836[0]['send_time']
            end_time = records_1836[-1]['send_time']
            
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            actual_duration = end_dt - start_dt
            
            print(f"実際の送信時間: {actual_duration}")
            print(f"報告された実行時間: 7分26秒")
            print(f"差分: {datetime.strptime('0:07:26', '%H:%M:%S').time()} - {actual_duration}")
            
            # 送信間隔の分析
            intervals = []
            for i in range(1, len(records_1836)):
                prev_time = datetime.fromisoformat(records_1836[i-1]['send_time'])
                curr_time = datetime.fromisoformat(records_1836[i]['send_time'])
                interval = curr_time - prev_time
                intervals.append(interval.total_seconds())
            
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                print(f"平均送信間隔: {avg_interval:.1f}秒")
                print(f"予想される20社送信時間: {avg_interval * 19 / 60:.1f}分")
        
    except Exception as e:
        print(f"❌ 実行時間分析エラー: {e}")

def main():
    print("🔍 HUGANJOB ID 1931-1950 プロセス問題分析レポート")
    print("=" * 80)
    print("問題: 7分26秒実行されたが、6社しか送信されていない")
    print("=" * 80)
    
    analyze_issue()
    
    print("\n🎯 分析結果サマリー")
    print("=" * 50)
    print("1. 送信履歴: ID 1931-1936の6社のみ記録")
    print("2. 実行時間: 約26秒（7分26秒ではない）")
    print("3. 送信結果: ID 1931以降の記録なし")
    print("4. 推定原因: プロセスが途中でエラー終了")
    print("\n推奨対応:")
    print("- ID 1937-1950の14社を再送信")
    print("- エラーログの詳細確認")
    print("- 送信結果ファイルの修復")

if __name__ == "__main__":
    main()
