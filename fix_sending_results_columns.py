#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
送信結果CSVファイルの列修正スクリプト
送信結果列にトラッキングIDが混入している問題を修正

作成日時: 2025年06月24日
目的: 送信結果CSVファイルの正規化
"""

import pandas as pd
import csv
import os
import shutil
from datetime import datetime

def analyze_current_csv():
    """現在のCSVファイルの状況を分析"""
    print("=== 現在のCSVファイル分析 ===")
    
    df = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
    print(f"総レコード数: {len(df)}")
    print(f"列名: {list(df.columns)}")
    
    # 送信結果列の値の種類を確認
    print(f"\n送信結果列の値の種類:")
    unique_results = df['送信結果'].value_counts()
    print(f"  success: {unique_results.get('success', 0)}件")
    print(f"  skipped: {unique_results.get('skipped', 0)}件")
    print(f"  bounced: {unique_results.get('bounced', 0)}件")
    
    # トラッキングIDのような値を確認
    tracking_like = df[df['送信結果'].str.contains('_', na=False)]
    print(f"  トラッキングID形式: {len(tracking_like)}件")
    
    return df

def fix_csv_columns():
    """CSVファイルの列を修正"""
    print("\n=== CSVファイル修正開始 ===")
    
    # バックアップ作成
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"new_email_sending_results.csv_column_fix_backup_{timestamp}"
    shutil.copy2('new_email_sending_results.csv', backup_file)
    print(f"バックアップ作成: {backup_file}")
    
    # CSVファイルを読み込み
    df = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
    
    # 修正カウンター
    fixed_count = 0
    
    # 各行を確認して修正
    for index, row in df.iterrows():
        sending_result = str(row['送信結果']).strip()
        
        # トラッキングID形式の場合は修正
        if '_' in sending_result and '@' in sending_result:
            # トラッキングID形式の場合は成功とみなす
            df.at[index, '送信結果'] = 'success'
            
            # トラッキングID列が空の場合は設定
            if pd.isna(row['トラッキングID']) or str(row['トラッキングID']).strip() == 'nan':
                df.at[index, 'トラッキングID'] = sending_result
            
            fixed_count += 1
            
            # 修正例を表示（最初の10件）
            if fixed_count <= 10:
                print(f"  修正 {fixed_count}: ID {row['企業ID']} - {row['企業名']}")
                print(f"    修正前: 送信結果=\"{sending_result}\"")
                print(f"    修正後: 送信結果=\"success\", トラッキングID=\"{sending_result}\"")
    
    print(f"\n修正完了: {fixed_count}件")
    
    # 修正後のファイルを保存
    df.to_csv('new_email_sending_results.csv', index=False, encoding='utf-8-sig')
    print(f"修正済みファイル保存完了")
    
    return df

def verify_fix():
    """修正結果の検証"""
    print("\n=== 修正結果検証 ===")
    
    df = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
    
    # 送信結果の値の種類を確認
    unique_results = df['送信結果'].value_counts()
    print(f"修正後の送信結果:")
    for result, count in unique_results.items():
        print(f"  {result}: {count}件")
    
    # 問題IDの確認
    problem_ids = [16, 20, 22, 36, 51, 74, 76, 105, 108]
    print(f"\n問題IDの修正確認:")
    
    success_count = 0
    for check_id in problem_ids:
        matching_results = df[df['企業ID'] == check_id]
        if len(matching_results) > 0:
            result = matching_results.iloc[0]
            sending_result = result['送信結果']
            tracking_id = result['トラッキングID']
            
            if sending_result == 'success':
                print(f"  ✅ ID {check_id}: {result['企業名']} - {sending_result}")
                success_count += 1
            else:
                print(f"  ❌ ID {check_id}: {result['企業名']} - {sending_result}")
        else:
            print(f"  ⚠️ ID {check_id}: データなし")
    
    print(f"\n問題IDの修正成功数: {success_count}/{len(problem_ids)}")
    
    return success_count == len(problem_ids) - 1  # ID 108はskippedなので除外

def test_dashboard_integration():
    """ダッシュボード統合処理のテスト"""
    print("\n=== ダッシュボード統合処理テスト ===")
    
    # 企業データ読み込み
    companies = []
    with open('data/new_input_test.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            company = {
                'id': int(row['ID']),
                'name': row['企業名'],
                'email_sent': False
            }
            companies.append(company)
    
    company_by_id = {c['id']: c for c in companies}
    
    # 送信結果統合
    with open('new_email_sending_results.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        success_count = 0
        
        for row in reader:
            company_id_str = row.get('企業ID', '').strip()
            sent_result = row.get('送信結果', '').strip()
            
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
                    success_count += 1
    
    print(f"統合処理結果: {success_count}社が送信済みに設定")
    
    # 問題IDの確認
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
    
    print(f"\n問題IDの送信済み数: {sent_count}/{len(problem_ids)}")
    
    return sent_count

def main():
    """メイン処理"""
    print("=" * 60)
    print("🔧 送信結果CSVファイル列修正ツール")
    print("=" * 60)
    
    try:
        # 1. 現在の状況分析
        analyze_current_csv()
        
        # 2. CSVファイル修正
        fix_csv_columns()
        
        # 3. 修正結果検証
        is_success = verify_fix()
        
        # 4. ダッシュボード統合テスト
        sent_count = test_dashboard_integration()
        
        if is_success and sent_count >= 8:  # ID 108はskippedなので8以上で成功
            print(f"\n🎉 送信結果CSVファイル修正が完了しました！")
            print(f"📊 修正結果: 問題IDの送信記録が正常に表示されるようになります")
        else:
            print(f"\n⚠️ 修正に一部問題があります")
            print(f"バックアップファイルから復元してください")
        
        return is_success
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
