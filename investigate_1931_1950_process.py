#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
18:36に実行されたID 1931-1950プロセスの詳細調査
"""

import json
import pandas as pd
from datetime import datetime

def investigate_process():
    print("🔍 18:36実行プロセス「huganjob_unified_sender.py (ID 1931-1950)」調査")
    print("=" * 80)
    
    # 送信履歴から18:36頃の記録を確認
    try:
        with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        # 18:36頃の送信記録を検索
        target_records = []
        for record in history['sending_records']:
            send_time = record.get('send_time', '')
            if '2025-06-25T18:36' in send_time:
                target_records.append(record)
        
        print(f"📋 18:36頃の送信記録: {len(target_records)}件")
        
        if target_records:
            print("\n送信詳細:")
            for record in target_records:
                print(f"  ID {record['company_id']}: {record['company_name']}")
                print(f"    メール: {record['email_address']}")
                print(f"    送信時刻: {record['send_time']}")
                print(f"    PID: {record['pid']}")
                print()
            
            # 送信範囲を確認
            company_ids = [int(r['company_id']) for r in target_records]
            min_id = min(company_ids)
            max_id = max(company_ids)
            print(f"送信範囲: ID {min_id} ～ {max_id} ({len(target_records)}社)")
            
            # プロセス実行時間を計算
            send_times = [r['send_time'] for r in target_records]
            start_time = min(send_times)
            end_time = max(send_times)
            print(f"実行時間: {start_time} ～ {end_time}")
            
            # 実行時間を計算
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            duration = end_dt - start_dt
            print(f"実行時間: {duration}")
            
        else:
            print("❌ 18:36頃の送信記録が見つかりません")
        
        return target_records
        
    except Exception as e:
        print(f"❌ 送信履歴確認エラー: {e}")
        return []

def check_sending_results():
    """送信結果ファイルでID 1931-1950を確認"""
    print("\n📊 送信結果ファイル確認")
    print("=" * 50)
    
    try:
        df = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
        
        # ID 1931-1950の記録を抽出
        target_results = df[(df['企業ID'] >= 1931) & (df['企業ID'] <= 1950)]
        
        print(f"ID 1931-1950の送信結果記録数: {len(target_results)}件")
        
        if len(target_results) > 0:
            print("\n送信結果詳細:")
            for _, row in target_results.iterrows():
                print(f"  ID {row['企業ID']}: {row['企業名']}")
                print(f"    結果: {row['送信結果']}")
                print(f"    送信日時: {row['送信日時']}")
                print()
            
            # 成功・失敗の統計
            success_count = len(target_results[target_results['送信結果'] == 'success'])
            print(f"送信成功: {success_count}件")
            print(f"送信失敗: {len(target_results) - success_count}件")
        
        return target_results
        
    except Exception as e:
        print(f"❌ 送信結果確認エラー: {e}")
        return pd.DataFrame()

def check_process_completion():
    """プロセス完了状況を確認"""
    print("\n🎯 プロセス完了状況確認")
    print("=" * 50)
    
    try:
        # 送信履歴の最新状況
        with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        # 最新の送信記録
        latest_records = history['sending_records'][-10:]
        
        print("最新10件の送信記録:")
        for record in latest_records:
            print(f"  ID {record['company_id']}: {record['company_name']} ({record['send_time'][-8:]})")
        
        # 最大送信ID
        max_id = 0
        for record in history['sending_records']:
            try:
                company_id = int(record['company_id'])
                max_id = max(max_id, company_id)
            except:
                continue
        
        print(f"\n現在の最大送信ID: {max_id}")
        
        # ID 1931-1950の送信状況
        sent_1931_1950 = []
        for record in history['sending_records']:
            try:
                company_id = int(record['company_id'])
                if 1931 <= company_id <= 1950:
                    sent_1931_1950.append(company_id)
            except:
                continue
        
        print(f"ID 1931-1950送信済み: {len(sent_1931_1950)}社")
        if sent_1931_1950:
            print(f"送信済みID: {sorted(sent_1931_1950)}")
        
        # 未送信ID確認
        all_1931_1950 = set(range(1931, 1951))
        sent_set = set(sent_1931_1950)
        unsent = all_1931_1950 - sent_set
        
        if unsent:
            print(f"未送信ID: {sorted(unsent)}")
        else:
            print("✅ ID 1931-1950すべて送信完了")
        
    except Exception as e:
        print(f"❌ プロセス完了確認エラー: {e}")

def main():
    print("🔍 HUGANJOB プロセス調査レポート")
    print("プロセス: huganjob_unified_sender.py (ID 1931-1950)")
    print("実行時刻: 18:36:32")
    print("実行時間: 0:01:37")
    print("=" * 80)
    
    # 各調査を実行
    history_records = investigate_process()
    result_records = check_sending_results()
    check_process_completion()
    
    # 結論
    print("\n🎯 調査結果サマリー")
    print("=" * 50)
    
    if len(history_records) > 0:
        print(f"✅ 送信履歴: {len(history_records)}社の記録確認")
        company_ids = [int(r['company_id']) for r in history_records]
        print(f"   送信範囲: ID {min(company_ids)} ～ {max(company_ids)}")
    else:
        print("❌ 送信履歴: 該当記録なし")
    
    if len(result_records) > 0:
        success_count = len(result_records[result_records['送信結果'] == 'success'])
        print(f"✅ 送信結果: {len(result_records)}社の記録確認")
        print(f"   成功: {success_count}社, 失敗: {len(result_records) - success_count}社")
    else:
        print("❌ 送信結果: 該当記録なし")

if __name__ == "__main__":
    main()
