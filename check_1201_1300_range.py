#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ID 1201-1300範囲の送信状況詳細調査
"""

import json
import csv
import os
from datetime import datetime

def main():
    print("=" * 60)
    print("🔍 ID 1201-1300範囲の送信状況調査")
    print("=" * 60)
    
    # 送信履歴から1201-1300の範囲を確認
    try:
        with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        records_1201_1300 = []
        for record in history['sending_records']:
            try:
                company_id = int(record['company_id'])
                if 1201 <= company_id <= 1300:
                    records_1201_1300.append(record)
            except:
                continue
        
        print(f"📋 送信履歴でID 1201-1300の記録数: {len(records_1201_1300)}件")
        
        if records_1201_1300:
            print("\n最初の10件:")
            for record in records_1201_1300[:10]:
                print(f"  ID {record['company_id']}: {record['company_name']} - {record['send_time']}")
            
            # 送信時刻の範囲を確認
            send_times = [record['send_time'] for record in records_1201_1300]
            print(f"\n送信時刻範囲:")
            print(f"  最初: {min(send_times)}")
            print(f"  最後: {max(send_times)}")
        
    except Exception as e:
        print(f"❌ 送信履歴確認エラー: {e}")
    
    # 企業データベースから1201-1300の企業情報を確認
    try:
        import pandas as pd
        df_companies = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
        companies_1201_1300 = df_companies[(df_companies['ID'] >= 1201) & (df_companies['ID'] <= 1300)]
        
        print(f"\n📊 企業データベースでID 1201-1300の企業数: {len(companies_1201_1300)}社")
        
        if len(companies_1201_1300) > 0:
            print("\n最初の10社:")
            for _, company in companies_1201_1300.head(10).iterrows():
                email = company.get('担当者メールアドレス', 'N/A')
                print(f"  ID {company['ID']}: {company['企業名']} - {email}")
        
    except Exception as e:
        print(f"❌ 企業データベース確認エラー: {e}")
    
    # 他の送信結果ファイルでID 1201-1300を検索
    print(f"\n📂 他の送信結果ファイルでID 1201-1300を検索:")
    
    import glob
    result_files = glob.glob('*sending_results*.csv') + glob.glob('sent_emails_*.csv')
    
    for file_path in result_files:
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                if '企業ID' in df.columns:
                    range_records = df[(df['企業ID'] >= 1201) & (df['企業ID'] <= 1300)]
                    if len(range_records) > 0:
                        print(f"  {file_path}: {len(range_records)}件")
                        if len(range_records) <= 5:
                            for _, record in range_records.iterrows():
                                print(f"    ID {record['企業ID']}: {record.get('企業名', 'N/A')}")
            except Exception as e:
                print(f"  {file_path}: 読み込みエラー - {e}")
    
    # ID範囲別の送信結果ファイルを確認
    print(f"\n📁 ID範囲別送信結果ファイル確認:")
    id_range_files = glob.glob('sent_emails_record_id*.csv')
    
    for file_path in id_range_files:
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            if '企業ID' in df.columns:
                min_id = df['企業ID'].min()
                max_id = df['企業ID'].max()
                count = len(df)
                print(f"  {file_path}: ID {min_id}-{max_id} ({count}件)")
                
                # 1201-1300の範囲と重複するかチェック
                if min_id <= 1300 and max_id >= 1201:
                    overlap = df[(df['企業ID'] >= 1201) & (df['企業ID'] <= 1300)]
                    if len(overlap) > 0:
                        print(f"    ★ ID 1201-1300の範囲に{len(overlap)}件含む")
        except Exception as e:
            print(f"  {file_path}: 読み込みエラー - {e}")

if __name__ == "__main__":
    main()
