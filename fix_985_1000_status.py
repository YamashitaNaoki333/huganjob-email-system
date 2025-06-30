#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
985~1000番の企業の送信ステータス修正スクリプト
メールアドレス未登録なのに送信済みステータスになっている問題を修正

作成日時: 2025年06月24日
目的: ID欠番修正時のデータ不整合問題の解決（985~1000番範囲）
"""

import json
import pandas as pd
from datetime import datetime

def analyze_985_1000_range():
    """985~1000番の範囲の企業データを分析"""
    print("=== 985~1000番範囲の企業データ分析 ===")
    
    # 企業データを読み込み
    df_companies = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
    
    # 985~1000番の範囲を抽出
    target_range = df_companies[(df_companies['ID'] >= 985) & (df_companies['ID'] <= 1000)]
    
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

def analyze_sending_history():
    """送信履歴ファイルの985~1000番記録を分析"""
    print("\n=== 送信履歴ファイル分析 ===")
    
    with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
        history_data = json.load(f)
    
    sending_records = history_data.get('sending_records', [])
    
    # 985~1000番の記録を検索
    target_records = [record for record in sending_records 
                     if 985 <= record.get('company_id', 0) <= 1000]
    
    print(f"985~1000番の送信記録数: {len(target_records)}件")
    
    if target_records:
        print("\n送信履歴詳細:")
        for record in target_records:
            company_id = record.get('company_id')
            company_name = record.get('company_name')
            email = record.get('email_address')
            print(f"  ID {company_id}: {company_name} - {email}")
    
    return target_records

def compare_data_mismatch():
    """企業データと送信履歴のデータ不整合を比較"""
    print("\n=== データ不整合比較 ===")
    
    # 企業データを読み込み
    df_companies = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
    
    # 送信履歴を読み込み
    with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
        history_data = json.load(f)
    
    sending_records = history_data.get('sending_records', [])
    target_records = [record for record in sending_records 
                     if 985 <= record.get('company_id', 0) <= 1000]
    
    mismatches = []
    
    for record in target_records:
        company_id = record.get('company_id')
        history_name = record.get('company_name')
        history_email = record.get('email_address')
        
        # 企業データで対応するIDを検索
        company_data = df_companies[df_companies['ID'] == company_id]
        
        if len(company_data) > 0:
            actual_name = company_data.iloc[0]['企業名']
            actual_email = company_data.iloc[0]['担当者メールアドレス']
            
            # 不整合をチェック
            name_mismatch = history_name != actual_name
            email_mismatch = str(actual_email) == '‐' or pd.isna(actual_email)
            
            if name_mismatch or email_mismatch:
                mismatches.append({
                    'id': company_id,
                    'history_name': history_name,
                    'actual_name': actual_name,
                    'history_email': history_email,
                    'actual_email': actual_email,
                    'name_mismatch': name_mismatch,
                    'email_unregistered': email_mismatch
                })
                
                print(f"  ID {company_id}:")
                print(f"    送信履歴: {history_name} ({history_email})")
                print(f"    企業データ: {actual_name} ({actual_email})")
                print(f"    問題: 企業名不一致={name_mismatch}, メール未登録={email_mismatch}")
    
    print(f"\n不整合件数: {len(mismatches)}件")
    return mismatches

def fix_sending_history():
    """送信履歴ファイルの985~1000番記録を修正"""
    print("\n=== 送信履歴修正 ===")
    
    # バックアップ作成
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'huganjob_sending_history_backup_985_1000_fix_{timestamp}.json'
    
    with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
        history_data = json.load(f)
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)
    
    print(f"バックアップ作成: {backup_file}")
    
    # 985~1000番の記録を削除
    sending_records = history_data.get('sending_records', [])
    original_count = len(sending_records)
    
    # 削除対象の記録を特定
    records_to_remove = [record for record in sending_records 
                        if 985 <= record.get('company_id', 0) <= 1000]
    
    # 削除実行
    sending_records_fixed = [record for record in sending_records 
                           if not (985 <= record.get('company_id', 0) <= 1000)]
    
    removed_count = len(records_to_remove)
    
    print(f"修正前: {original_count}件")
    print(f"修正後: {len(sending_records_fixed)}件")
    print(f"削除数: {removed_count}件")
    
    if removed_count > 0:
        print(f"\n削除対象記録: {removed_count}件")
        for record in records_to_remove:
            print(f"  ID {record.get('company_id')}: {record.get('company_name')} - {record.get('email_address')}")
        
        # 修正後のデータを保存
        history_data['sending_records'] = sending_records_fixed
        with open('huganjob_sending_history.json', 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
        
        print("\n✅ 送信履歴ファイルの修正が完了しました")
        return True
    else:
        print("\n❌ 削除対象の記録が見つかりませんでした")
        return False

def verify_fix():
    """修正結果を確認"""
    print("\n=== 修正結果確認 ===")
    
    with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
        history_data = json.load(f)
    
    sending_records = history_data.get('sending_records', [])
    remaining_records = [record for record in sending_records 
                        if 985 <= record.get('company_id', 0) <= 1000]
    
    print(f"修正後の985~1000番記録数: {len(remaining_records)}件")
    
    if len(remaining_records) == 0:
        print("✅ 985~1000番の不正な記録は正常に削除されました")
        return True
    else:
        print("❌ まだ985~1000番の記録が残っています")
        for record in remaining_records:
            print(f"  残存記録: ID {record.get('company_id')}: {record.get('company_name')}")
        return False

def main():
    """メイン処理"""
    print("送信履歴ファイルの985~1000番企業データ不整合修正ツール")
    print("=" * 60)
    
    try:
        # 1. 企業データ分析
        target_companies, unregistered_count = analyze_985_1000_range()
        
        # 2. 送信履歴分析
        target_records = analyze_sending_history()
        
        # 3. データ不整合比較
        mismatches = compare_data_mismatch()
        
        # 4. 修正が必要かチェック
        if len(target_records) > 0 and len(mismatches) > 0:
            print(f"\n⚠️ 問題検出:")
            print(f"  送信履歴記録: {len(target_records)}件")
            print(f"  データ不整合: {len(mismatches)}件")
            print(f"  メール未登録企業: {unregistered_count}社")
            print(f"  これはID欠番修正時のデータ不整合です")
            
            # 5. 修正実行
            if fix_sending_history():
                # 6. 修正結果確認
                if verify_fix():
                    print("\n✅ 修正が完了しました")
                    print("ダッシュボードを再起動して変更を確認してください")
                else:
                    print("\n❌ 修正の確認に失敗しました")
            else:
                print("\n❌ 修正に失敗しました")
        else:
            print("\n✅ 985~1000番の不正な記録は見つかりませんでした")
        
        return True
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    main()
