#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ダッシュボード表示問題デバッグスクリプト
ID 1948-1950の送信記録がダッシュボードに反映されない問題を調査
"""

import pandas as pd
import json
import os
import sys
from datetime import datetime

def debug_dashboard_display():
    print("🔍 ダッシュボード表示問題デバッグ")
    print("=" * 60)
    
    # 1. 送信履歴確認
    print("📋 1. 送信履歴確認")
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
        
        if target_records:
            print("\n送信履歴詳細:")
            for record in target_records:
                print(f"  ID {record['company_id']}: {record['company_name']}")
                print(f"    メール: {record['email_address']}")
                print(f"    送信時刻: {record['send_time']}")
                print(f"    PID: {record['pid']}")
                print()
        else:
            print("❌ ID 1948-1950 の送信記録が見つかりません")
        
    except Exception as e:
        print(f"❌ 送信履歴確認エラー: {e}")
    
    # 2. 送信結果ファイル確認
    print("📊 2. 送信結果ファイル確認")
    print("-" * 30)
    
    try:
        df_results = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
        target_results = df_results[(df_results['企業ID'] >= 1948) & (df_results['企業ID'] <= 1950)]
        
        print(f"送信結果総数: {len(df_results)}")
        print(f"ID 1948-1950 結果: {len(target_results)}件")
        
        if len(target_results) > 0:
            print("\n送信結果詳細:")
            for _, row in target_results.iterrows():
                print(f"  ID {row['企業ID']}: {row['企業名']}")
                print(f"    メール: {row['メールアドレス']}")
                print(f"    結果: {row['送信結果']}")
                print(f"    送信時刻: {row['送信日時']}")
                print()
        else:
            print("❌ ID 1948-1950 の送信結果が見つかりません")
        
    except Exception as e:
        print(f"❌ 送信結果ファイル確認エラー: {e}")
    
    # 3. ダッシュボードデータ読み込み確認
    print("🌐 3. ダッシュボードデータ読み込み確認")
    print("-" * 30)
    
    try:
        # ダッシュボードが使用するデータ読み込み関数をシミュレート
        sys.path.append('dashboard')
        from derivative_dashboard import load_company_data
        
        companies = load_company_data()
        
        print(f"ダッシュボード読み込み企業数: {len(companies)}")
        
        # ID 1948-1950の企業を検索
        target_companies = []
        for company in companies:
            try:
                company_id = int(company.get('id', 0))
                if 1948 <= company_id <= 1950:
                    target_companies.append(company)
            except:
                continue
        
        print(f"ID 1948-1950 企業数: {len(target_companies)}件")
        
        if target_companies:
            print("\nダッシュボード企業詳細:")
            for company in target_companies:
                print(f"  ID {company['id']}: {company['name']}")
                print(f"    メール: {company.get('email', 'N/A')}")
                print(f"    送信状況: {company.get('sent_status', 'N/A')}")
                print(f"    最終送信: {company.get('last_sent', 'N/A')}")
                print(f"    送信回数: {company.get('sent_count', 0)}")
                print()
        else:
            print("❌ ダッシュボードでID 1948-1950 の企業が見つかりません")
        
    except Exception as e:
        print(f"❌ ダッシュボードデータ読み込みエラー: {e}")
        import traceback
        print(f"スタックトレース: {traceback.format_exc()}")
    
    # 4. データファイル整合性チェック
    print("🔍 4. データファイル整合性チェック")
    print("-" * 30)
    
    try:
        # 企業マスターデータ確認
        df_master = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
        target_master = df_master[(df_master['ID'] >= 1948) & (df_master['ID'] <= 1950)]
        
        print(f"企業マスターデータ総数: {len(df_master)}")
        print(f"ID 1948-1950 マスターデータ: {len(target_master)}件")
        
        if len(target_master) > 0:
            print("\nマスターデータ詳細:")
            for _, row in target_master.iterrows():
                print(f"  ID {row['ID']}: {row['企業名']}")
                print(f"    メール: {row['採用担当メールアドレス']}")
                print(f"    職種: {row['募集職種']}")
                print()
        
        # 送信結果との照合
        if len(target_results) > 0 and len(target_master) > 0:
            print("📊 マスターデータと送信結果の照合:")
            
            master_ids = set(target_master['ID'].astype(int))
            result_ids = set(target_results['企業ID'].astype(int))
            
            print(f"  マスターデータID: {sorted(master_ids)}")
            print(f"  送信結果ID: {sorted(result_ids)}")
            
            missing_in_results = master_ids - result_ids
            extra_in_results = result_ids - master_ids
            
            if missing_in_results:
                print(f"  ⚠️ 送信結果に不足: {sorted(missing_in_results)}")
            if extra_in_results:
                print(f"  ⚠️ 送信結果に余分: {sorted(extra_in_results)}")
            if not missing_in_results and not extra_in_results:
                print("  ✅ マスターデータと送信結果が一致")
        
    except Exception as e:
        print(f"❌ データファイル整合性チェックエラー: {e}")
    
    # 5. ダッシュボード設定確認
    print("⚙️ 5. ダッシュボード設定確認")
    print("-" * 30)
    
    try:
        # ダッシュボード設定ファイル確認
        config_files = [
            'config/huganjob_dashboard_config.json',
            'dashboard/config.json',
            'config.json'
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                print(f"📄 設定ファイル発見: {config_file}")
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"  設定内容: {json.dumps(config, indent=2, ensure_ascii=False)}")
                break
        else:
            print("⚠️ ダッシュボード設定ファイルが見つかりません")
        
    except Exception as e:
        print(f"❌ ダッシュボード設定確認エラー: {e}")

def fix_dashboard_display():
    """ダッシュボード表示問題の修正を試行"""
    print("\n🔧 ダッシュボード表示問題修正")
    print("=" * 60)
    
    try:
        # ダッシュボードのデータ再読み込みAPIを呼び出し
        import requests
        
        print("📡 ダッシュボードデータ再読み込み実行...")
        
        reload_url = "http://127.0.0.1:5002/api/reload_data"
        response = requests.post(reload_url, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ データ再読み込み成功: {result}")
        else:
            print(f"❌ データ再読み込み失敗: {response.status_code}")
            print(f"レスポンス: {response.text}")
        
    except Exception as e:
        print(f"❌ データ再読み込みエラー: {e}")
    
    # キャッシュクリア
    try:
        print("\n🧹 キャッシュクリア実行...")
        
        cache_files = [
            'dashboard_cache.json',
            'company_cache.json',
            'stats_cache.json'
        ]
        
        cleared_files = []
        for cache_file in cache_files:
            if os.path.exists(cache_file):
                os.remove(cache_file)
                cleared_files.append(cache_file)
        
        if cleared_files:
            print(f"✅ キャッシュファイル削除: {cleared_files}")
        else:
            print("ℹ️ 削除対象のキャッシュファイルなし")
        
    except Exception as e:
        print(f"❌ キャッシュクリアエラー: {e}")

def main():
    print("🔍 HUGANJOB ダッシュボード表示問題デバッグ")
    print("=" * 80)
    
    # デバッグ実行
    debug_dashboard_display()
    
    # 修正試行
    fix_dashboard_display()
    
    print("\n🎉 デバッグ・修正処理完了")
    print("=" * 80)
    print("📋 次のステップ:")
    print("1. ダッシュボードページを再読み込み")
    print("2. 企業一覧ページで ID 1948-1950 の表示確認")
    print("3. 問題が継続する場合はダッシュボード再起動")

if __name__ == "__main__":
    main()
