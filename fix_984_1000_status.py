#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
984~1000番の企業の送信ステータス修正スクリプト
メールアドレス未登録なのに送信済みステータスになっている問題を修正

作成日時: 2025年06月24日
目的: ID欠番修正時のデータ不整合問題の解決
"""

import pandas as pd
import os
from datetime import datetime

def analyze_984_1000_range():
    """984~1000番の範囲の企業データを分析"""
    print("=== 984~1000番範囲の企業データ分析 ===")
    
    # 企業データを読み込み
    df_companies = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
    
    # 984~1000番の範囲を抽出
    target_range = df_companies[(df_companies['ID'] >= 984) & (df_companies['ID'] <= 1000)]
    
    print(f"対象範囲の企業数: {len(target_range)}社")
    print("\n企業データ詳細:")
    
    email_unregistered_count = 0
    for _, company in target_range.iterrows():
        company_id = company['ID']
        company_name = company['企業名']
        email = company['担当者メールアドレス']
        
        is_unregistered = (pd.isna(email) or email == '‐' or email == '-' or email.strip() == '')
        if is_unregistered:
            email_unregistered_count += 1
            print(f"  ID {company_id}: {company_name} - メール未登録 ({email})")
        else:
            print(f"  ID {company_id}: {company_name} - メール登録済み ({email})")
    
    print(f"\nメール未登録企業数: {email_unregistered_count}/{len(target_range)}社")
    return target_range, email_unregistered_count

def check_sending_results():
    """送信結果ファイルで984~1000番の記録を確認"""
    print("\n=== 送信結果ファイル確認 ===")
    
    if not os.path.exists('new_email_sending_results.csv'):
        print("送信結果ファイルが見つかりません")
        return []
    
    df_results = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
    
    # 984~1000番の範囲を抽出
    target_results = df_results[(df_results['企業ID'] >= 984) & (df_results['企業ID'] <= 1000)]
    
    print(f"送信結果ファイル内の984~1000番記録数: {len(target_results)}件")
    
    if len(target_results) > 0:
        print("\n送信結果詳細:")
        for _, result in target_results.iterrows():
            print(f"  ID {result['企業ID']}: {result['企業名']} - {result['送信結果']} ({result['送信日時']})")
    
    return target_results

def fix_sending_results():
    """送信結果ファイルから984~1000番の不正な記録を削除"""
    print("\n=== 送信結果ファイル修正 ===")
    
    if not os.path.exists('new_email_sending_results.csv'):
        print("送信結果ファイルが見つかりません")
        return False
    
    # バックアップ作成
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'new_email_sending_results_backup_984_1000_fix_{timestamp}.csv'
    
    df_results = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
    df_results.to_csv(backup_file, index=False, encoding='utf-8-sig')
    print(f"バックアップ作成: {backup_file}")
    
    # 企業データを読み込んでメールアドレス状況を確認
    df_companies = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
    
    # 984~1000番の範囲で削除対象を特定
    original_count = len(df_results)
    removed_records = []
    
    # 削除対象の記録を特定
    for index, result in df_results.iterrows():
        company_id = result['企業ID']
        
        if 984 <= company_id <= 1000:
            # 企業データでメールアドレスを確認
            company_data = df_companies[df_companies['ID'] == company_id]
            
            if len(company_data) > 0:
                email = company_data.iloc[0]['担当者メールアドレス']
                is_unregistered = (pd.isna(email) or email == '‐' or email == '-' or str(email).strip() == '')
                
                if is_unregistered:
                    removed_records.append({
                        'id': company_id,
                        'name': result['企業名'],
                        'email': email,
                        'sent_result': result['送信結果']
                    })
    
    # 削除対象の記録を除外
    if removed_records:
        print(f"\n削除対象記録: {len(removed_records)}件")
        for record in removed_records:
            print(f"  ID {record['id']}: {record['name']} - メール未登録 ({record['email']})")
        
        # 削除実行
        remove_ids = [record['id'] for record in removed_records]
        df_results_fixed = df_results[~df_results['企業ID'].isin(remove_ids)]
        
        # 修正後のファイルを保存
        df_results_fixed.to_csv('new_email_sending_results.csv', index=False, encoding='utf-8-sig')
        
        print(f"\n修正完了:")
        print(f"  修正前: {original_count}件")
        print(f"  修正後: {len(df_results_fixed)}件")
        print(f"  削除数: {len(removed_records)}件")
        
        return True
    else:
        print("削除対象の記録が見つかりませんでした")
        return False

def main():
    """メイン処理"""
    print("984~1000番企業の送信ステータス修正ツール")
    print("=" * 50)
    
    try:
        # 1. 企業データ分析
        target_companies, unregistered_count = analyze_984_1000_range()
        
        # 2. 送信結果確認
        target_results = check_sending_results()
        
        # 3. 修正が必要かチェック
        if len(target_results) > 0 and unregistered_count > 0:
            print(f"\n⚠️ 問題検出: メール未登録企業 {unregistered_count}社に送信記録 {len(target_results)}件")
            
            # 4. 修正実行
            if fix_sending_results():
                print("\n✅ 修正が完了しました")
                print("ダッシュボードを再起動して変更を確認してください")
            else:
                print("\n❌ 修正に失敗しました")
        else:
            print("\n✅ 問題は検出されませんでした")
        
        return True
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    main()
