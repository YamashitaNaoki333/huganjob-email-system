#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
企業ID 2051-2100の送信状況調査スクリプト
- CSVファイルの送信状況確認
- ダッシュボード表示状況確認
- 送信履歴ファイル確認
"""

import os
import csv
import json
import pandas as pd
from datetime import datetime

def check_csv_sending_status():
    """CSVファイルの送信状況を確認"""
    print("🔍 1. CSVファイル送信状況確認")
    print("-" * 50)
    
    csv_file = 'data/new_input_test.csv'
    if not os.path.exists(csv_file):
        print(f"❌ CSVファイルが見つかりません: {csv_file}")
        return
    
    try:
        # 企業ID 2051-2100の範囲を確認
        target_ids = list(range(2051, 2101))
        sent_count = 0
        unsent_count = 0
        
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader)  # ヘッダー行をスキップ
            
            print(f"CSVヘッダー: {header}")
            print(f"列数: {len(header)}")
            
            for row_num, row in enumerate(reader, start=2):
                if len(row) > 0:
                    try:
                        company_id = int(row[0])
                        if company_id in target_ids:
                            company_name = row[1] if len(row) > 1 else "N/A"
                            email_address = row[11] if len(row) > 11 else ""
                            sending_status = row[12] if len(row) > 12 else ""
                            sending_date = row[13] if len(row) > 13 else ""
                            
                            if sending_status == '送信済み':
                                sent_count += 1
                                print(f"✅ ID {company_id}: {company_name} - 送信済み ({sending_date})")
                            else:
                                unsent_count += 1
                                print(f"❌ ID {company_id}: {company_name} - 未送信")
                                
                    except (ValueError, IndexError) as e:
                        print(f"⚠️ 行 {row_num} 解析エラー: {e}")
        
        print(f"\n📊 集計結果:")
        print(f"   送信済み: {sent_count}社")
        print(f"   未送信: {unsent_count}社")
        print(f"   合計: {sent_count + unsent_count}社")
        
    except Exception as e:
        print(f"❌ CSVファイル読み込みエラー: {e}")

def check_sending_history():
    """送信履歴ファイルを確認"""
    print("\n🔍 2. 送信履歴ファイル確認")
    print("-" * 50)
    
    # HUGANJOB送信履歴ファイル確認
    history_file = 'huganjob_sending_history.json'
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            target_ids = list(range(2051, 2101))
            found_records = []
            
            for record in history_data:
                company_id = record.get('company_id')
                if company_id in target_ids:
                    found_records.append(record)
            
            print(f"📋 HUGANJOB送信履歴: {len(found_records)}件見つかりました")
            for record in found_records:
                print(f"   ID {record.get('company_id')}: {record.get('company_name')} - {record.get('timestamp')}")
                
        except Exception as e:
            print(f"❌ 送信履歴読み込みエラー: {e}")
    else:
        print(f"⚠️ 送信履歴ファイルが見つかりません: {history_file}")
    
    # 送信結果CSVファイル確認
    results_file = 'new_email_sending_results.csv'
    if os.path.exists(results_file):
        try:
            with open(results_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                target_ids = list(range(2051, 2101))
                found_results = []
                
                for row in reader:
                    try:
                        company_id = int(row.get('企業ID', 0))
                        if company_id in target_ids:
                            found_results.append(row)
                    except ValueError:
                        continue
            
            print(f"📋 送信結果CSV: {len(found_results)}件見つかりました")
            for result in found_results:
                print(f"   ID {result.get('企業ID')}: {result.get('企業名')} - {result.get('送信結果')} ({result.get('送信日時')})")
                
        except Exception as e:
            print(f"❌ 送信結果CSV読み込みエラー: {e}")
    else:
        print(f"⚠️ 送信結果CSVファイルが見つかりません: {results_file}")

def check_dashboard_api():
    """ダッシュボードAPI経由で企業情報を確認"""
    print("\n🔍 3. ダッシュボードAPI確認")
    print("-" * 50)
    
    try:
        import requests
        
        # 企業ID 2051-2100の範囲をページネーションで取得
        # 1ページあたり50件として、ページ42-43あたりに該当
        target_pages = [42, 43]  # 概算
        
        for page in target_pages:
            try:
                url = f"http://127.0.0.1:5002/api/companies?page={page}&per_page=50&filter=all"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    companies = data.get('companies', [])
                    
                    print(f"📄 ページ {page}: {len(companies)}社取得")
                    
                    for company in companies:
                        company_id = int(company.get('id', 0))
                        if 2051 <= company_id <= 2100:
                            email_sent = company.get('email_sent', False)
                            sent_date = company.get('sent_date', '')
                            email = company.get('email', '')
                            
                            status = "送信済み" if email_sent else "未送信"
                            print(f"   ID {company_id}: {company.get('name')} - {status} ({sent_date})")
                            print(f"      メール: {email}")
                else:
                    print(f"❌ API呼び出し失敗 (ページ {page}): {response.status_code}")
                    
            except Exception as e:
                print(f"❌ ページ {page} API呼び出しエラー: {e}")
                
    except ImportError:
        print("⚠️ requestsライブラリが利用できません")
    except Exception as e:
        print(f"❌ ダッシュボードAPI確認エラー: {e}")

def main():
    """メイン処理"""
    print("=" * 60)
    print("企業ID 2051-2100 送信状況調査")
    print("=" * 60)
    
    # 1. CSVファイル確認
    check_csv_sending_status()
    
    # 2. 送信履歴確認
    check_sending_history()
    
    # 3. ダッシュボードAPI確認
    check_dashboard_api()
    
    print("\n" + "=" * 60)
    print("調査完了")
    print("=" * 60)

if __name__ == "__main__":
    main()
