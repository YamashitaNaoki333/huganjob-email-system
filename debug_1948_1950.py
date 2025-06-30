#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ID 1948-1950 送信問題デバッグスクリプト
"""

import pandas as pd
import json
import os
from datetime import datetime

def debug_1948_1950():
    print("🔍 ID 1948-1950 送信問題デバッグ")
    print("=" * 60)
    
    # 1. CSVデータ確認
    print("📋 1. CSVデータ確認")
    print("-" * 30)
    
    try:
        df = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
        target_data = df[(df['ID'] >= 1948) & (df['ID'] <= 1950)]
        
        print(f"CSVファイル総行数: {len(df)}")
        print(f"ID 1948-1950 データ数: {len(target_data)}")
        print()
        
        for _, row in target_data.iterrows():
            print(f"ID {row['ID']}: {row['企業名']}")
            print(f"  メール: {row['採用担当メールアドレス']}")
            print(f"  職種: {row['募集職種']}")
            print()
        
    except Exception as e:
        print(f"❌ CSVデータ確認エラー: {e}")
    
    # 2. 送信履歴確認
    print("📋 2. 送信履歴確認")
    print("-" * 30)
    
    try:
        with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        # ID 1948-1950の送信記録を検索
        target_records = []
        for record in history['sending_records']:
            try:
                company_id = int(record['company_id'])
                if 1948 <= company_id <= 1950:
                    target_records.append(record)
            except:
                continue
        
        print(f"送信履歴総数: {len(history['sending_records'])}")
        print(f"ID 1948-1950 送信記録: {len(target_records)}件")
        print()
        
        if target_records:
            for record in target_records:
                print(f"ID {record['company_id']}: {record['company_name']}")
                print(f"  送信時刻: {record['send_time']}")
                print(f"  PID: {record['pid']}")
                print()
        else:
            print("❌ ID 1948-1950 の送信記録が見つかりません")
        
        # 最後の送信記録を確認
        if history['sending_records']:
            last_record = history['sending_records'][-1]
            print(f"最後の送信記録: ID {last_record['company_id']} ({last_record['send_time']})")
        
    except Exception as e:
        print(f"❌ 送信履歴確認エラー: {e}")
    
    # 3. 送信結果ファイル確認
    print("\n📋 3. 送信結果ファイル確認")
    print("-" * 30)
    
    try:
        df_results = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
        target_results = df_results[(df_results['企業ID'] >= 1948) & (df_results['企業ID'] <= 1950)]
        
        print(f"送信結果総数: {len(df_results)}")
        print(f"ID 1948-1950 結果: {len(target_results)}件")
        print()
        
        if len(target_results) > 0:
            for _, row in target_results.iterrows():
                print(f"ID {row['企業ID']}: {row['企業名']}")
                print(f"  結果: {row['送信結果']}")
                print(f"  送信時刻: {row['送信日時']}")
                print()
        else:
            print("❌ ID 1948-1950 の送信結果が見つかりません")
        
        # 最後の送信結果を確認
        if len(df_results) > 0:
            last_result = df_results.iloc[-1]
            print(f"最後の送信結果: ID {last_result['企業ID']} ({last_result['送信日時']})")
        
    except Exception as e:
        print(f"❌ 送信結果ファイル確認エラー: {e}")
    
    # 4. メールアドレス抽出結果確認
    print("\n📋 4. メールアドレス抽出結果確認")
    print("-" * 30)
    
    try:
        if os.path.exists('huganjob_email_resolution_results.csv'):
            email_df = pd.read_csv('huganjob_email_resolution_results.csv', encoding='utf-8')
            target_emails = email_df[(email_df['company_id'] >= 1948) & (email_df['company_id'] <= 1950)]
            
            print(f"メール抽出結果総数: {len(email_df)}")
            print(f"ID 1948-1950 抽出結果: {len(target_emails)}件")
            print()
            
            if len(target_emails) > 0:
                for _, row in target_emails.iterrows():
                    print(f"ID {row['company_id']}: {row['company_name']}")
                    print(f"  CSV: {row['csv_email']}")
                    print(f"  最終: {row['final_email']}")
                    print(f"  方法: {row['extraction_method']}")
                    print()
            else:
                print("⚠️ ID 1948-1950 のメール抽出結果なし")
        else:
            print("⚠️ メールアドレス抽出結果ファイルが存在しません")
        
    except Exception as e:
        print(f"❌ メールアドレス抽出結果確認エラー: {e}")
    
    # 5. 配信停止チェック
    print("\n📋 5. 配信停止チェック")
    print("-" * 30)
    
    try:
        if os.path.exists('data/huganjob_unsubscribe_log.csv'):
            unsubscribe_df = pd.read_csv('data/huganjob_unsubscribe_log.csv', encoding='utf-8-sig')
            
            # ID 1948-1950の企業が配信停止されているかチェック
            target_companies = [
                ('1948', '株式会社ミック', 'oonishi@mctv.ne.jp'),
                ('1949', '株式会社マルイチ', 'somu@ma-ru-i-chi.co.jp'),
                ('1950', 'ブリンクスジャパン株式会社', 'hr.japan@brinks.com')
            ]
            
            print(f"配信停止ログ総数: {len(unsubscribe_df)}")
            
            for company_id, company_name, email in target_companies:
                # 企業IDまたはメールアドレスで検索
                unsubscribed = unsubscribe_df[
                    (unsubscribe_df['企業ID'].astype(str) == company_id) |
                    (unsubscribe_df['メールアドレス'].str.lower() == email.lower())
                ]
                
                if len(unsubscribed) > 0:
                    print(f"🚫 ID {company_id} ({company_name}): 配信停止済み")
                    for _, row in unsubscribed.iterrows():
                        print(f"  理由: {row['配信停止理由']}")
                        print(f"  日時: {row['配信停止日時']}")
                else:
                    print(f"✅ ID {company_id} ({company_name}): 配信停止なし")
        else:
            print("⚠️ 配信停止ログファイルが存在しません")
        
    except Exception as e:
        print(f"❌ 配信停止チェックエラー: {e}")
    
    # 6. 送信プロセス分析
    print("\n📋 6. 送信プロセス分析")
    print("-" * 30)
    
    # 送信履歴から送信プロセスの流れを分析
    try:
        with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        # 最新の送信プロセス（PID 4448）の記録を抽出
        latest_pid_records = []
        for record in history['sending_records']:
            if record.get('pid') == 4448:  # 最新の送信プロセス
                latest_pid_records.append(record)
        
        print(f"最新プロセス（PID 4448）の送信記録: {len(latest_pid_records)}件")
        
        if latest_pid_records:
            # 送信順序を確認
            latest_pid_records.sort(key=lambda x: x['send_time'])
            
            print("送信順序:")
            for i, record in enumerate(latest_pid_records):
                print(f"  {i+1}. ID {record['company_id']}: {record['company_name']} ({record['send_time']})")
            
            # 最後の送信記録
            last_record = latest_pid_records[-1]
            last_id = int(last_record['company_id'])
            
            print(f"\n最後の送信: ID {last_id}")
            print(f"期待範囲: ID 1937-1950")
            
            if last_id < 1950:
                print(f"❌ 送信が途中で停止: ID {last_id + 1} 以降が未送信")
                print(f"未送信ID: {list(range(last_id + 1, 1951))}")
            else:
                print("✅ 全範囲送信完了")
        
    except Exception as e:
        print(f"❌ 送信プロセス分析エラー: {e}")

def main():
    debug_1948_1950()

if __name__ == "__main__":
    main()
