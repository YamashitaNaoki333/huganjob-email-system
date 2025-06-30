#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ID 1200前後の境界記録を詳細確認
"""

import pandas as pd

def main():
    print("=" * 60)
    print("📊 ID 1200前後の境界記録詳細確認")
    print("=" * 60)
    
    # メインファイルでID 1200前後の記録を詳しく確認
    try:
        df = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
        
        print("📋 ID 1195-1305の記録:")
        nearby_records = df[(df['企業ID'] >= 1195) & (df['企業ID'] <= 1305)]
        nearby_records_sorted = nearby_records.sort_values('企業ID')
        
        for _, record in nearby_records_sorted.iterrows():
            company_id = record['企業ID']
            company_name = record['企業名']
            send_time = record['送信日時']
            print(f"ID {company_id}: {company_name} - {send_time}")
        
        print(f"\n📈 ID 1195-1305の統計:")
        print(f"記録数: {len(nearby_records)}件")
        if len(nearby_records) > 0:
            print(f"最小ID: {nearby_records['企業ID'].min()}")
            print(f"最大ID: {nearby_records['企業ID'].max()}")
        
        # ID 1300以降の記録を確認
        print(f"\n📋 ID 1300以降の記録（最初の10件）:")
        after_1300 = df[df['企業ID'] >= 1300].sort_values('企業ID')
        
        for _, record in after_1300.head(10).iterrows():
            company_id = record['企業ID']
            company_name = record['企業名']
            send_time = record['送信日時']
            print(f"ID {company_id}: {company_name} - {send_time}")
        
        # 欠落範囲の確認
        print(f"\n🔍 欠落範囲の詳細確認:")
        all_ids = set(df['企業ID'].tolist())
        
        # 1200から1310までの連続性をチェック
        for check_id in range(1200, 1311):
            if check_id in all_ids:
                record = df[df['企業ID'] == check_id].iloc[0]
                print(f"✅ ID {check_id}: {record['企業名']} - {record['送信日時']}")
            else:
                print(f"❌ ID {check_id}: 記録なし")
        
        # 送信履歴との照合
        print(f"\n📋 送信履歴との照合:")
        import json
        
        try:
            with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            # ID 1200-1310の送信履歴を確認
            history_ids = {}
            for record in history['sending_records']:
                try:
                    company_id = int(record['company_id'])
                    if 1200 <= company_id <= 1310:
                        history_ids[company_id] = record
                except:
                    continue
            
            print(f"送信履歴でID 1200-1310の記録数: {len(history_ids)}件")
            
            for check_id in range(1200, 1311):
                in_results = check_id in all_ids
                in_history = check_id in history_ids
                
                status = ""
                if in_results and in_history:
                    status = "✅ 両方にあり"
                elif in_results and not in_history:
                    status = "⚠️ 送信結果のみ"
                elif not in_results and in_history:
                    status = "❌ 送信履歴のみ"
                else:
                    status = "❓ 両方になし"
                
                print(f"ID {check_id}: {status}")
                
                if in_history and not in_results:
                    history_record = history_ids[check_id]
                    print(f"  送信履歴: {history_record['company_name']} - {history_record['send_time']}")
        
        except Exception as e:
            print(f"送信履歴確認エラー: {e}")
    
    except Exception as e:
        print(f"メインファイル確認エラー: {e}")

if __name__ == "__main__":
    main()
