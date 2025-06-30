#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ID 1948-1950 手動送信スクリプト
"""

import pandas as pd
import json
import os
from datetime import datetime
from huganjob_unified_sender import UnifiedEmailSender

def manual_send_1948_1950():
    print("🚀 ID 1948-1950 手動送信開始")
    print("=" * 60)
    
    # 1. データ準備
    try:
        df = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
        target_data = df[(df['ID'] >= 1948) & (df['ID'] <= 1950)]
        
        print(f"📋 対象企業数: {len(target_data)}社")
        
        companies = []
        for _, row in target_data.iterrows():
            company = {
                'id': int(row['ID']),
                'name': row['企業名'],
                'email': row['採用担当メールアドレス'],
                'job_position': row['募集職種']
            }
            companies.append(company)
            print(f"  ID {company['id']}: {company['name']} - {company['email']} ({company['job_position']})")
        
    except Exception as e:
        print(f"❌ データ準備エラー: {e}")
        return False
    
    # 2. 送信実行
    print(f"\n📤 送信実行開始...")
    print("-" * 60)
    
    try:
        sender = UnifiedEmailSender(email_format='html_only')
        
        # 設定読み込み
        if not sender.load_config():
            print("❌ 設定読み込み失敗")
            return False
        
        if not sender.load_html_template():
            print("❌ HTMLテンプレート読み込み失敗")
            return False
        
        # 各企業に個別送信
        results = {'success': 0, 'failed': 0, 'skipped': 0, 'unsubscribed': 0}
        
        for i, company in enumerate(companies):
            print(f"\n📤 {i+1}/{len(companies)}: ID {company['id']} {company['name']}")
            print(f"   📧 宛先: {company['email']}")
            print(f"   💼 職種: {company['job_position']}")
            
            try:
                result = sender.send_email_with_prevention(
                    company['id'], company['name'],
                    company['job_position'], company['email']
                )
                results[result] += 1
                print(f"   📊 結果: {result}")
                
                # 送信間隔
                if i < len(companies) - 1:
                    print(f"   ⏳ 5秒待機...")
                    import time
                    time.sleep(5)
                
            except Exception as send_error:
                print(f"   ❌ 送信エラー: {send_error}")
                results['failed'] += 1
        
        # 結果表示
        print(f"\n" + "=" * 60)
        print("📊 手動送信結果")
        print("=" * 60)
        print(f"✅ 成功: {results['success']}/{len(companies)}")
        print(f"⚠️ スキップ: {results['skipped']}/{len(companies)}")
        print(f"🛑 配信停止: {results['unsubscribed']}/{len(companies)}")
        print(f"❌ 失敗: {results['failed']}/{len(companies)}")
        
        # 送信結果保存
        print(f"\n💾 送信結果保存...")
        sender.save_sending_results()
        
        return results['success'] > 0
        
    except Exception as e:
        print(f"❌ 送信実行エラー: {e}")
        import traceback
        print(f"スタックトレース: {traceback.format_exc()}")
        return False

def check_current_status():
    """現在の送信状況確認"""
    print("📊 現在の送信状況確認")
    print("=" * 40)
    
    # 送信履歴確認
    try:
        with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        # ID 1948-1950の記録を検索
        target_records = []
        for record in history['sending_records']:
            try:
                company_id = int(record['company_id'])
                if 1948 <= company_id <= 1950:
                    target_records.append(record)
            except:
                continue
        
        print(f"ID 1948-1950 送信履歴: {len(target_records)}件")
        for record in target_records:
            print(f"  ID {record['company_id']}: {record['company_name']} ({record['send_time']})")
        
    except Exception as e:
        print(f"送信履歴確認エラー: {e}")
    
    # 送信結果確認
    try:
        df_results = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
        target_results = df_results[(df_results['企業ID'] >= 1948) & (df_results['企業ID'] <= 1950)]
        
        print(f"\nID 1948-1950 送信結果: {len(target_results)}件")
        for _, row in target_results.iterrows():
            print(f"  ID {row['企業ID']}: {row['企業名']} - {row['送信結果']} ({row['送信日時']})")
        
    except Exception as e:
        print(f"送信結果確認エラー: {e}")

def main():
    print("🔍 ID 1948-1950 送信状況調査・修正")
    print("=" * 80)
    
    # 現在の状況確認
    check_current_status()
    
    print("\n" + "=" * 80)
    
    # 手動送信実行
    success = manual_send_1948_1950()
    
    print(f"\n🏁 処理完了: {'成功' if success else '失敗'}")
    
    # 最終確認
    print("\n" + "=" * 80)
    print("📊 最終確認")
    check_current_status()

if __name__ == "__main__":
    main()
