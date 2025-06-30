#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB送信結果データ修復スクリプト
ID連番修正で消失した送信結果データを復元し、正しいIDマッピングを適用

作成日時: 2025年06月24日
目的: 送信結果データの整合性復元
"""

import pandas as pd
import csv
import os
import json
import shutil
import glob
from datetime import datetime

def load_id_mapping():
    """IDマッピングログから変換テーブルを読み込み"""
    print("=== IDマッピング読み込み ===")
    
    # 最新のIDマッピングログを検索
    log_files = glob.glob('huganjob_id_renumbering_log_*.json')
    if not log_files:
        print("❌ IDマッピングログが見つかりません")
        return None
    
    latest_log = max(log_files)
    print(f"📝 使用するログファイル: {latest_log}")
    
    with open(latest_log, 'r', encoding='utf-8') as f:
        log_data = json.load(f)
    
    id_mapping = log_data['id_mapping']
    # 文字列キーを整数に変換
    id_mapping = {int(k): v for k, v in id_mapping.items()}
    
    print(f"✅ IDマッピング読み込み完了: {len(id_mapping)}件")
    return id_mapping

def restore_sending_results():
    """送信結果データを復元"""
    print("\n=== 送信結果データ復元 ===")
    
    # バックアップファイルから復元
    backup_file = 'new_email_sending_results.csv_backup_20250624_130248'
    if not os.path.exists(backup_file):
        print(f"❌ バックアップファイルが見つかりません: {backup_file}")
        return False
    
    # IDマッピングを読み込み
    id_mapping = load_id_mapping()
    if not id_mapping:
        return False
    
    # バックアップデータを読み込み
    print(f"📂 バックアップファイル読み込み: {backup_file}")
    df_backup = pd.read_csv(backup_file, encoding='utf-8-sig')
    print(f"📊 バックアップレコード数: {len(df_backup)}")
    
    # 企業IDを新しいIDに変換
    print("🔄 企業ID変換処理中...")
    df_backup['企業ID'] = df_backup['企業ID'].astype(int).map(id_mapping)
    
    # マッピングできなかったレコードを除去
    before_count = len(df_backup)
    df_backup = df_backup.dropna(subset=['企業ID'])
    after_count = len(df_backup)
    
    if before_count != after_count:
        print(f"⚠️ マッピング不可レコード除去: {before_count - after_count}件")
    
    # 企業IDを整数に変換
    df_backup['企業ID'] = df_backup['企業ID'].astype(int)
    
    # IDでソート
    df_backup = df_backup.sort_values('企業ID').reset_index(drop=True)
    
    # 現在のファイルをバックアップ
    current_backup = f"new_email_sending_results.csv_before_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if os.path.exists('new_email_sending_results.csv'):
        shutil.copy2('new_email_sending_results.csv', current_backup)
        print(f"📦 現在ファイルのバックアップ: {current_backup}")
    
    # 復元されたデータを保存
    df_backup.to_csv('new_email_sending_results.csv', index=False, encoding='utf-8-sig')
    print(f"✅ 送信結果データ復元完了: {len(df_backup)}件")
    
    return True

def verify_restoration():
    """復元結果の検証"""
    print("\n=== 復元結果検証 ===")
    
    # 企業データと送信結果の整合性確認
    df_companies = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
    df_results = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
    
    company_ids = set(df_companies['ID'].astype(int))
    result_ids = set(df_results['企業ID'].astype(int))
    
    print(f"📊 企業データ: {len(company_ids)}社 (ID範囲: {min(company_ids)}-{max(company_ids)})")
    print(f"📊 送信結果: {len(result_ids)}社 (ID範囲: {min(result_ids)}-{max(result_ids)})")
    
    # 送信結果に存在するが企業データにない企業ID
    orphan_ids = result_ids - company_ids
    if orphan_ids:
        print(f"⚠️ 企業データにない送信結果: {len(orphan_ids)}件")
        print(f"   ID: {sorted(list(orphan_ids))[:10]}...")
    else:
        print("✅ 送信結果の企業IDは全て企業データに存在")
    
    # 連番性確認
    expected_company_ids = set(range(1, len(company_ids) + 1))
    if company_ids == expected_company_ids:
        print("✅ 企業データID連番性: 正常")
    else:
        print("❌ 企業データID連番性: 異常")
    
    # 送信結果の統計
    success_count = len(df_results[df_results['送信結果'] == 'success'])
    total_count = len(df_results)
    
    print(f"\n📈 送信結果統計:")
    print(f"   総送信数: {total_count}件")
    print(f"   成功送信: {success_count}件")
    print(f"   成功率: {success_count/total_count*100:.1f}%" if total_count > 0 else "   成功率: 0%")
    
    return True

def fix_huganjob_results():
    """HUGANJOB送信結果ファイルも修正"""
    print("\n=== HUGANJOB送信結果ファイル修正 ===")
    
    # IDマッピングを読み込み
    id_mapping = load_id_mapping()
    if not id_mapping:
        return False
    
    # HUGANJOB送信結果ファイルを検索
    huganjob_files = glob.glob('huganjob_sending_results_*.csv')
    
    for file_name in huganjob_files:
        try:
            print(f"🔧 修正中: {file_name}")
            
            # バックアップ作成
            backup_name = f"{file_name}_before_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(file_name, backup_name)
            
            # ファイル読み込み
            df = pd.read_csv(file_name, encoding='utf-8-sig')
            
            if '企業ID' in df.columns:
                # 企業IDを変換
                original_count = len(df)
                df['企業ID'] = df['企業ID'].astype(int).map(id_mapping)
                df = df.dropna(subset=['企業ID'])
                df['企業ID'] = df['企業ID'].astype(int)
                df = df.sort_values('企業ID').reset_index(drop=True)
                
                # 保存
                df.to_csv(file_name, index=False, encoding='utf-8-sig')
                print(f"   ✅ 修正完了: {original_count} → {len(df)}件")
            else:
                print(f"   ⚠️ 企業ID列が見つかりません")
                
        except Exception as e:
            print(f"   ❌ エラー: {e}")
    
    return True

def main():
    """メイン処理"""
    print("=" * 60)
    print("🔧 HUGANJOB送信結果データ修復ツール")
    print("=" * 60)
    
    try:
        # 1. 送信結果データ復元
        if not restore_sending_results():
            print("❌ 送信結果データ復元に失敗しました")
            return False
        
        # 2. HUGANJOB送信結果ファイル修正
        if not fix_huganjob_results():
            print("❌ HUGANJOB送信結果ファイル修正に失敗しました")
            return False
        
        # 3. 復元結果検証
        if not verify_restoration():
            print("❌ 復元結果検証に失敗しました")
            return False
        
        print(f"\n🎉 送信結果データ修復が完了しました！")
        print(f"📝 バックアップファイルは保持されています")
        
        return True
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
