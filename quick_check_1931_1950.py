#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ID 1931-1950の簡単確認
"""

import pandas as pd
import json

def main():
    print("🔍 ID 1931-1950 簡単確認")
    print("=" * 50)
    
    # 企業データ確認
    try:
        df = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
        target = df[(df['ID'] >= 1931) & (df['ID'] <= 1950)]
        
        print(f"企業データ: {len(target)}社")
        print("\n最初の5社:")
        for _, row in target.head().iterrows():
            email = row.get('担当者メールアドレス', '')
            print(f"  ID {row['ID']}: {row['企業名']}")
            print(f"    メール: {email}")
            print()
        
    except Exception as e:
        print(f"企業データエラー: {e}")
    
    # 送信履歴確認
    try:
        with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        sent_ids = []
        for record in history['sending_records']:
            try:
                cid = int(record['company_id'])
                if 1931 <= cid <= 1950:
                    sent_ids.append(cid)
            except:
                continue
        
        print(f"送信済みID: {len(sent_ids)}件")
        if sent_ids:
            print(f"送信済みID一覧: {sorted(sent_ids)}")
        
        # 最大送信ID確認
        max_sent_id = 0
        for record in history['sending_records']:
            try:
                cid = int(record['company_id'])
                max_sent_id = max(max_sent_id, cid)
            except:
                continue
        
        print(f"最大送信ID: {max_sent_id}")
        
    except Exception as e:
        print(f"送信履歴エラー: {e}")

if __name__ == "__main__":
    main()
