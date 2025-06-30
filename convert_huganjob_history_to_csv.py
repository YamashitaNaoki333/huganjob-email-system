#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB送信履歴をCSV形式に変換するスクリプト
huganjob_sending_history.json → new_email_sending_results.csv

作成日時: 2025年06月23日
目的: 開封状況追跡機能の修復
"""

import json
import csv
import os
import uuid
from datetime import datetime
import pandas as pd

def generate_tracking_id_for_existing(company_id, email_address, send_time):
    """既存の送信記録用にトラッキングIDを生成"""
    # 送信時刻をベースにした一意のIDを生成
    timestamp = send_time.replace('T', '').replace(':', '').replace('-', '').replace('.', '')[:14]
    unique_string = f"{company_id}_{email_address}_{timestamp}_{uuid.uuid4().hex[:8]}"
    return unique_string

def load_company_data():
    """企業データを読み込み"""
    try:
        df = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
        companies = {}
        for _, row in df.iterrows():
            companies[int(row['ID'])] = {
                'name': row['企業名'],
                'job_position': row.get('募集職種', '採用担当者'),
                'email': row.get('採用担当メールアドレス', '')
            }
        return companies
    except Exception as e:
        print(f"❌ 企業データ読み込みエラー: {e}")
        return {}

def convert_history_to_csv():
    """送信履歴をCSVに変換"""
    try:
        # 送信履歴ファイルを読み込み
        if not os.path.exists('huganjob_sending_history.json'):
            print("❌ huganjob_sending_history.json が見つかりません")
            return False
        
        with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
            history_data = json.load(f)
        
        # 企業データを読み込み
        companies = load_company_data()
        
        # CSVレコードを作成
        csv_records = []
        
        for record in history_data.get('sending_records', []):
            company_id = record['company_id']
            company_name = record['company_name']
            email_address = record['email_address']
            send_time = record['send_time']
            
            # 企業データから職種を取得
            job_position = '採用担当者'
            if company_id in companies:
                job_position = companies[company_id]['job_position']
            
            # トラッキングIDを生成
            tracking_id = generate_tracking_id_for_existing(company_id, email_address, send_time)
            
            # 送信日時をフォーマット
            try:
                dt = datetime.fromisoformat(send_time.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_time = send_time
            
            csv_record = {
                '企業ID': company_id,
                '企業名': company_name,
                'メールアドレス': email_address,
                '募集職種': job_position,
                '送信日時': formatted_time,
                '送信結果': 'success',
                'トラッキングID': tracking_id,
                'エラーメッセージ': '',
                '件名': f"【{job_position}の人材採用を強化しませんか？】株式会社HUGANからのご提案"
            }
            csv_records.append(csv_record)
        
        # CSVファイルに保存
        filename = 'new_email_sending_results.csv'
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = ['企業ID', '企業名', 'メールアドレス', '募集職種', '送信日時', '送信結果', 'トラッキングID', 'エラーメッセージ', '件名']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # ヘッダーを書き込み
            writer.writeheader()
            
            # レコードを書き込み
            for record in csv_records:
                writer.writerow(record)
        
        print(f"✅ 送信履歴をCSVに変換しました: {filename}")
        print(f"📊 変換件数: {len(csv_records)}件")
        
        # 変換結果を表示
        print("\n📋 変換されたレコード:")
        for record in csv_records:
            print(f"  ID {record['企業ID']}: {record['企業名']} - {record['トラッキングID'][:20]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 変換エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン処理"""
    print("=" * 60)
    print("📧 HUGANJOB送信履歴 → CSV変換ツール")
    print("=" * 60)
    
    # 既存のCSVファイルをバックアップ
    if os.path.exists('new_email_sending_results.csv'):
        backup_name = f"new_email_sending_results_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        os.rename('new_email_sending_results.csv', backup_name)
        print(f"📦 既存ファイルをバックアップしました: {backup_name}")
    
    # 変換実行
    success = convert_history_to_csv()
    
    if success:
        print(f"\n🎉 変換が完了しました！")
        print(f"📄 ファイル: new_email_sending_results.csv")
        print(f"🔍 ダッシュボードで開封状況追跡が利用可能になります")
    else:
        print(f"\n❌ 変換に失敗しました")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
