#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
送信履歴ファイルの984番企業データ不整合修正スクリプト
ID欠番修正時に発生した送信履歴の不整合を修正

作成日時: 2025年06月24日
目的: 984番の企業データ不整合問題の解決
"""

import json
import pandas as pd
from datetime import datetime

def analyze_sending_history():
    """送信履歴ファイルの984番記録を分析"""
    print("=== 送信履歴ファイル分析 ===")

    # 送信履歴を読み込み
    with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
        history_data = json.load(f)

    # sending_records配列から984番の記録を検索
    sending_records = history_data.get('sending_records', [])
    records_984 = [record for record in sending_records if record.get('company_id') == 984]
    
    print(f"984番の送信記録数: {len(records_984)}件")
    
    for i, record in enumerate(records_984):
        print(f"\n記録 {i+1}:")
        print(f"  企業ID: {record.get('company_id')}")
        print(f"  企業名: {record.get('company_name')}")
        print(f"  メールアドレス: {record.get('email_address')}")
        print(f"  送信時刻: {record.get('send_time')}")
        print(f"  スクリプト: {record.get('script_name')}")
    
    return records_984

def check_company_data():
    """企業データで984番と968番を確認"""
    print("\n=== 企業データ確認 ===")
    
    df = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
    
    # 984番の企業データ
    company_984 = df[df['ID'] == 984]
    if len(company_984) > 0:
        print(f"ID 984: {company_984.iloc[0]['企業名']} - {company_984.iloc[0]['担当者メールアドレス']}")
    else:
        print("ID 984: 見つかりません")
    
    # 968番の企業データ
    company_968 = df[df['ID'] == 968]
    if len(company_968) > 0:
        print(f"ID 968: {company_968.iloc[0]['企業名']} - {company_968.iloc[0]['担当者メールアドレス']}")
    else:
        print("ID 968: 見つかりません")
    
    # info@r3it.comを使用している企業を検索
    r3it_companies = df[df['担当者メールアドレス'] == 'info@r3it.com']
    print(f"\ninfo@r3it.comを使用している企業:")
    for _, company in r3it_companies.iterrows():
        print(f"  ID {company['ID']}: {company['企業名']}")
    
    return company_984, company_968, r3it_companies

def fix_sending_history():
    """送信履歴ファイルの984番記録を修正"""
    print("\n=== 送信履歴修正 ===")

    # バックアップ作成
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'huganjob_sending_history_backup_984_fix_{timestamp}.json'

    with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
        history_data = json.load(f)

    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)

    print(f"バックアップ作成: {backup_file}")

    # 984番の記録を削除
    sending_records = history_data.get('sending_records', [])
    original_count = len(sending_records)
    sending_records_fixed = [record for record in sending_records if record.get('company_id') != 984]
    removed_count = original_count - len(sending_records_fixed)
    
    print(f"修正前: {original_count}件")
    print(f"修正後: {len(sending_records_fixed)}件")
    print(f"削除数: {removed_count}件")

    if removed_count > 0:
        # 修正後のデータを保存
        history_data['sending_records'] = sending_records_fixed
        with open('huganjob_sending_history.json', 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
        
        print("✅ 送信履歴ファイルの修正が完了しました")
        return True
    else:
        print("❌ 削除対象の記録が見つかりませんでした")
        return False

def verify_fix():
    """修正結果を確認"""
    print("\n=== 修正結果確認 ===")

    with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
        history_data = json.load(f)

    sending_records = history_data.get('sending_records', [])
    records_984 = [record for record in sending_records if record.get('company_id') == 984]
    
    print(f"修正後の984番記録数: {len(records_984)}件")
    
    if len(records_984) == 0:
        print("✅ 984番の不正な記録は正常に削除されました")
        return True
    else:
        print("❌ まだ984番の記録が残っています")
        for record in records_984:
            print(f"  残存記録: {record}")
        return False

def main():
    """メイン処理"""
    print("送信履歴ファイルの984番企業データ不整合修正ツール")
    print("=" * 60)
    
    try:
        # 1. 送信履歴分析
        records_984 = analyze_sending_history()
        
        # 2. 企業データ確認
        check_company_data()
        
        # 3. 問題の説明
        if len(records_984) > 0:
            print(f"\n⚠️ 問題検出:")
            print(f"  送信履歴の984番: 有限会社アールスリーインスティテュート (info@r3it.com)")
            print(f"  企業データの984番: 大阪広域環境施設組合 (‐)")
            print(f"  これはID欠番修正時のデータ不整合です")
            
            # 4. 修正実行
            if fix_sending_history():
                # 5. 修正結果確認
                if verify_fix():
                    print("\n✅ 修正が完了しました")
                    print("ダッシュボードを再起動して変更を確認してください")
                else:
                    print("\n❌ 修正の確認に失敗しました")
            else:
                print("\n❌ 修正に失敗しました")
        else:
            print("\n✅ 984番の不正な記録は見つかりませんでした")
        
        return True
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    main()
