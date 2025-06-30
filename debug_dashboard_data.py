#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ダッシュボードデータ統合デバッグスクリプト
送信記録が反映されない問題を調査

作成日時: 2025年06月24日
目的: ダッシュボードの企業データと送信結果の統合処理をデバッグ
"""

import pandas as pd
import csv
import os
import json
from datetime import datetime

def debug_company_data():
    """企業データの確認"""
    print("=== 企業データ確認 ===")
    
    df_companies = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
    print(f"企業データ総数: {len(df_companies)}社")
    
    # 問題のあるIDを確認
    problem_ids = [16, 20, 22, 36, 51, 74, 76, 105, 108]
    
    print(f"\n問題IDの企業データ:")
    for check_id in problem_ids:
        company_row = df_companies[df_companies['ID'] == check_id]
        if len(company_row) > 0:
            company = company_row.iloc[0]
            print(f"  ID {check_id}: {company['企業名']} - {company['担当者メールアドレス']}")
        else:
            print(f"  ID {check_id}: 企業データなし")
    
    return df_companies

def debug_sending_results():
    """送信結果データの確認"""
    print("\n=== 送信結果データ確認 ===")
    
    df_results = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
    print(f"送信結果総数: {len(df_results)}件")
    
    # 問題のあるIDを確認
    problem_ids = [16, 20, 22, 36, 51, 74, 76, 105, 108]
    
    print(f"\n問題IDの送信結果:")
    for check_id in problem_ids:
        matching_results = df_results[df_results['企業ID'] == check_id]
        if len(matching_results) > 0:
            result = matching_results.iloc[0]
            print(f"  ID {check_id}: {result['企業名']} - {result['送信結果']} - {result['送信日時']}")
            print(f"    メールアドレス: {result['メールアドレス']}")
            print(f"    トラッキングID: {result['トラッキングID']}")
        else:
            print(f"  ID {check_id}: 送信結果なし")
    
    return df_results

def debug_data_integration():
    """データ統合処理のシミュレーション"""
    print("\n=== データ統合処理シミュレーション ===")
    
    # 企業データ読み込み
    df_companies = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
    companies = []
    
    for _, row in df_companies.iterrows():
        company = {
            'id': int(row['ID']),
            'name': row['企業名'],
            'email': row['担当者メールアドレス'],
            'job_position': row['募集職種'],
            'website': row['企業ホームページ'],
            'email_sent': False,  # デフォルト値
            'sent_date': None,
            'tracking_id': None
        }
        companies.append(company)
    
    print(f"企業データ読み込み完了: {len(companies)}社")
    
    # 企業IDでインデックス作成
    company_by_id = {c['id']: c for c in companies}
    print(f"企業IDインデックス作成完了: {len(company_by_id)}件")
    
    # 送信結果データ統合
    if os.path.exists('new_email_sending_results.csv'):
        print(f"\n送信結果ファイル統合開始...")
        
        with open('new_email_sending_results.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            processed_count = 0
            matched_count = 0
            
            for row in reader:
                company_id_str = row.get('企業ID', '').strip()
                
                if not company_id_str:
                    continue
                
                try:
                    company_id = int(company_id_str)
                except ValueError:
                    print(f"  ⚠️ 企業ID変換エラー: '{company_id_str}'")
                    continue
                
                processed_count += 1
                
                if company_id in company_by_id:
                    company = company_by_id[company_id]
                    sent_result = row.get('送信結果', '').strip()
                    sent_date = row.get('送信日時', '').strip()
                    tracking_id = row.get('トラッキングID', '').strip()
                    
                    if sent_result == 'success':
                        company['email_sent'] = True
                        company['sent_date'] = sent_date
                        company['tracking_id'] = tracking_id
                        matched_count += 1
                        
                        # 問題IDの場合は詳細ログ
                        if company_id in [16, 20, 22, 36, 51, 74, 76, 105, 108]:
                            print(f"  ✅ ID {company_id}: 送信状態更新 - {company['name']}")
                            print(f"    送信結果: {sent_result}")
                            print(f"    送信日時: {sent_date}")
                            print(f"    トラッキングID: {tracking_id}")
                else:
                    print(f"  ⚠️ 企業ID {company_id} が企業データに見つかりません")
        
        print(f"\n送信結果統合完了:")
        print(f"  処理行数: {processed_count}")
        print(f"  マッチ数: {matched_count}")
    
    # 問題IDの最終状態確認
    print(f"\n=== 問題IDの最終状態 ===")
    problem_ids = [16, 20, 22, 36, 51, 74, 76, 105, 108]
    
    for check_id in problem_ids:
        if check_id in company_by_id:
            company = company_by_id[check_id]
            print(f"ID {check_id}: {company['name']}")
            print(f"  email_sent: {company['email_sent']}")
            print(f"  sent_date: {company['sent_date']}")
            print(f"  tracking_id: {company['tracking_id']}")
        else:
            print(f"ID {check_id}: 企業データなし")
    
    return companies

def debug_csv_file_structure():
    """CSVファイル構造の確認"""
    print("\n=== CSVファイル構造確認 ===")
    
    # 送信結果ファイルの構造確認
    if os.path.exists('new_email_sending_results.csv'):
        with open('new_email_sending_results.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            print(f"送信結果ファイルの列名: {headers}")
            
            # 最初の数行を確認
            print(f"\n最初の3行:")
            for i, row in enumerate(reader):
                if i >= 3:
                    break
                print(f"  行{i+1}: 企業ID='{row.get('企業ID', '')}', 送信結果='{row.get('送信結果', '')}'")
    
    # 企業データファイルの構造確認
    if os.path.exists('data/new_input_test.csv'):
        with open('data/new_input_test.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            print(f"\n企業データファイルの列名: {headers}")

def debug_dashboard_load_process():
    """ダッシュボードの読み込み処理をシミュレート"""
    print("\n=== ダッシュボード読み込み処理シミュレーション ===")
    
    # ダッシュボードと同じ処理を実行
    try:
        # 1. 企業データ読み込み
        companies = []
        with open('data/new_input_test.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                company = {
                    'id': int(row['ID']),
                    'name': row['企業名'],
                    'email': row['担当者メールアドレス'],
                    'job_position': row['募集職種'],
                    'website': row['企業ホームページ'],
                    'email_sent': False
                }
                companies.append(company)
        
        print(f"企業データ読み込み: {len(companies)}社")
        
        # 2. 送信結果統合（ダッシュボードと同じロジック）
        company_by_id = {c['id']: c for c in companies}
        
        # メイン送信結果ファイル確認
        primary_file = 'new_email_sending_results.csv'
        if os.path.exists(primary_file):
            print(f"メイン送信結果ファイル使用: {primary_file}")
            
            with open(primary_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                csv_processed = 0
                
                for row in reader:
                    company_id_str = row.get('企業ID', '').strip()
                    sent_result = row.get('送信結果', '').strip()
                    sent_date = row.get('送信日時', '').strip()
                    tracking_id = row.get('トラッキングID', '').strip()
                    
                    if not company_id_str:
                        continue
                    
                    try:
                        company_id = int(company_id_str)
                    except ValueError:
                        continue
                    
                    if company_id in company_by_id:
                        company = company_by_id[company_id]
                        
                        if sent_result == 'success':
                            company['email_sent'] = True
                            company['sent_date'] = sent_date
                            
                            if tracking_id:
                                company['tracking_id'] = tracking_id
                            
                            csv_processed += 1
                            
                            # 問題IDの場合は詳細ログ
                            if company_id in [16, 20, 22, 36, 51, 74, 76, 105, 108]:
                                print(f"  ✅ ID {company_id}: 送信済み設定完了")
                
                print(f"CSV送信結果統合: {csv_processed}社")
        
        # 3. 問題IDの最終確認
        print(f"\n=== 最終確認 ===")
        problem_ids = [16, 20, 22, 36, 51, 74, 76, 105, 108]
        
        sent_count = 0
        for check_id in problem_ids:
            if check_id in company_by_id:
                company = company_by_id[check_id]
                if company['email_sent']:
                    print(f"  ✅ ID {check_id}: 送信済み")
                    sent_count += 1
                else:
                    print(f"  ❌ ID {check_id}: 未送信")
            else:
                print(f"  ⚠️ ID {check_id}: 企業データなし")
        
        print(f"\n問題IDの送信済み数: {sent_count}/{len(problem_ids)}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

def main():
    """メイン処理"""
    print("=" * 60)
    print("🔍 ダッシュボードデータ統合デバッグツール")
    print("=" * 60)
    
    try:
        # 1. 企業データ確認
        debug_company_data()
        
        # 2. 送信結果データ確認
        debug_sending_results()
        
        # 3. CSVファイル構造確認
        debug_csv_file_structure()
        
        # 4. データ統合処理シミュレーション
        debug_data_integration()
        
        # 5. ダッシュボード読み込み処理シミュレーション
        debug_dashboard_load_process()
        
        print(f"\n🎉 デバッグ完了")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
