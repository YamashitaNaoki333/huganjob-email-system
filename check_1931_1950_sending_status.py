#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ID 1931-1950の送信状況確認スクリプト
"""

import json
import csv
import pandas as pd
from datetime import datetime

def check_sending_history():
    """送信履歴でID 1931-1950を確認"""
    print("📋 送信履歴確認（huganjob_sending_history.json）")
    print("=" * 60)
    
    try:
        with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        # ID 1931-1950の記録を検索
        target_records = []
        for record in history['sending_records']:
            try:
                company_id = int(record['company_id'])
                if 1931 <= company_id <= 1950:
                    target_records.append(record)
            except:
                continue
        
        print(f"ID 1931-1950の送信記録数: {len(target_records)}件")
        
        if target_records:
            print("\n送信済み企業:")
            for record in sorted(target_records, key=lambda x: int(x['company_id'])):
                print(f"  ID {record['company_id']}: {record['company_name']}")
                print(f"    メール: {record['email_address']}")
                print(f"    送信時刻: {record['send_time']}")
                print()
        else:
            print("❌ ID 1931-1950の送信記録は見つかりませんでした")
        
        return target_records
        
    except Exception as e:
        print(f"❌ 送信履歴確認エラー: {e}")
        return []

def check_sending_results():
    """送信結果ファイルでID 1931-1950を確認"""
    print("\n📊 送信結果確認（new_email_sending_results.csv）")
    print("=" * 60)
    
    try:
        df = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
        
        # ID 1931-1950の記録を抽出
        target_results = df[(df['企業ID'] >= 1931) & (df['企業ID'] <= 1950)]
        
        print(f"ID 1931-1950の送信結果記録数: {len(target_results)}件")
        
        if len(target_results) > 0:
            print("\n送信結果詳細:")
            for _, row in target_results.iterrows():
                print(f"  ID {row['企業ID']}: {row['企業名']}")
                print(f"    メール: {row['メールアドレス']}")
                print(f"    結果: {row['送信結果']}")
                print(f"    送信日時: {row['送信日時']}")
                print()
        else:
            print("❌ ID 1931-1950の送信結果記録は見つかりませんでした")
        
        return target_results
        
    except Exception as e:
        print(f"❌ 送信結果確認エラー: {e}")
        return pd.DataFrame()

def check_company_data():
    """企業データでID 1931-1950を確認"""
    print("\n🏢 企業データ確認（data/new_input_test.csv）")
    print("=" * 60)
    
    try:
        df = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
        
        # ID 1931-1950の企業を抽出
        target_companies = df[(df['ID'] >= 1931) & (df['ID'] <= 1950)]
        
        print(f"ID 1931-1950の企業数: {len(target_companies)}社")
        
        if len(target_companies) > 0:
            print("\n企業一覧:")
            for _, row in target_companies.iterrows():
                email_col = '担当者メールアドレス'  # 正しい列名
                email_value = row.get(email_col, '')
                email_status = "メールあり" if pd.notna(email_value) and str(email_value).strip() not in ['-', '‐', ''] else "メールなし"
                print(f"  ID {row['ID']}: {row['企業名']} ({email_status})")
                if pd.notna(email_value) and str(email_value).strip() not in ['-', '‐', '']:
                    print(f"    メール: {email_value}")
                print(f"    職種: {row.get('募集職種', 'N/A')}")
                print()
        else:
            print("❌ ID 1931-1950の企業データは見つかりませんでした")
        
        return target_companies
        
    except Exception as e:
        print(f"❌ 企業データ確認エラー: {e}")
        return pd.DataFrame()

def check_overall_sending_status():
    """全体の送信状況を確認"""
    print("\n📈 全体送信状況サマリー")
    print("=" * 60)
    
    try:
        # 送信履歴の最大ID確認
        with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        max_id = 0
        min_id = float('inf')
        total_sent = len(history['sending_records'])
        
        for record in history['sending_records']:
            try:
                company_id = int(record['company_id'])
                max_id = max(max_id, company_id)
                min_id = min(min_id, company_id)
            except:
                continue
        
        print(f"送信履歴統計:")
        print(f"  総送信数: {total_sent}社")
        print(f"  送信ID範囲: {min_id} ～ {max_id}")
        
        # 企業データの総数確認
        df_companies = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
        total_companies = len(df_companies)
        max_company_id = df_companies['ID'].max()
        
        print(f"\n企業データ統計:")
        print(f"  総企業数: {total_companies}社")
        print(f"  最大ID: {max_company_id}")
        
        # 送信率計算
        sending_rate = (total_sent / total_companies) * 100 if total_companies > 0 else 0
        print(f"\n送信率: {sending_rate:.1f}% ({total_sent}/{total_companies})")
        
        # ID 1931-1950の位置確認
        if max_id >= 1931:
            print(f"\n✅ ID 1931より前まで送信済み（最大送信ID: {max_id}）")
        else:
            print(f"\n❌ ID 1931まで未到達（最大送信ID: {max_id}）")
        
    except Exception as e:
        print(f"❌ 全体状況確認エラー: {e}")

def main():
    print("🔍 HUGANJOB送信状況確認 - ID 1931-1950")
    print("=" * 80)
    
    # 各データソースを確認
    history_records = check_sending_history()
    result_records = check_sending_results()
    company_data = check_company_data()
    
    # 全体状況確認
    check_overall_sending_status()
    
    # 結論
    print("\n🎯 結論")
    print("=" * 60)
    
    if len(history_records) > 0:
        print(f"✅ ID 1931-1950: {len(history_records)}社が送信済み")
    else:
        print("❌ ID 1931-1950: 送信記録なし")
    
    if len(result_records) > 0:
        print(f"✅ 送信結果ファイル: {len(result_records)}件の記録あり")
    else:
        print("❌ 送信結果ファイル: 記録なし")
    
    if len(company_data) > 0:
        print(f"✅ 企業データ: {len(company_data)}社が存在")
        email_col = '担当者メールアドレス'  # 正しい列名
        email_available = len(company_data[
            (pd.notna(company_data[email_col])) &
            (company_data[email_col].astype(str).str.strip().isin(['-', '‐', '']) == False)
        ])
        print(f"   メールアドレス利用可能: {email_available}社")
    else:
        print("❌ 企業データ: 該当企業なし")

if __name__ == "__main__":
    main()
