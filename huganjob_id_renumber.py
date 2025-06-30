#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB企業データのID連番修正スクリプト
企業データの重複統合処理で生じたID欠番を修正し、1から連番になるように再採番

作成日時: 2025年06月24日
目的: ID欠番問題の解決とデータ整合性の確保
"""

import pandas as pd
import csv
import os
import json
import glob
import shutil
from datetime import datetime

def backup_files():
    """重要ファイルのバックアップを作成"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_files = []
    
    files_to_backup = [
        'data/new_input_test.csv',
        'new_email_sending_results.csv',
        'huganjob_email_resolution_results.csv'
    ]
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = f"{file_path}_backup_{timestamp}"
            shutil.copy2(file_path, backup_path)
            backup_files.append(backup_path)
            print(f"📦 バックアップ作成: {backup_path}")
    
    return backup_files

def analyze_current_ids():
    """現在のID状況を分析"""
    print("=== 現在のID状況分析 ===")
    
    # 企業データ読み込み
    df = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
    actual_ids = sorted(df['ID'].tolist())
    
    print(f"総企業数: {len(actual_ids)}")
    print(f"ID範囲: {min(actual_ids)} - {max(actual_ids)}")
    
    # 1-1000範囲の欠番確認
    expected_ids_1000 = set(range(1, 1001))
    actual_ids_1000 = set([id for id in actual_ids if id <= 1000])
    missing_ids = sorted(list(expected_ids_1000 - actual_ids_1000))
    
    print(f"1-1000範囲の企業数: {len(actual_ids_1000)}")
    print(f"欠番数: {len(missing_ids)}")
    print(f"欠番ID: {missing_ids}")
    
    # 1000超過ID確認
    over_1000_ids = [id for id in actual_ids if id > 1000]
    print(f"1000超過企業数: {len(over_1000_ids)}")
    
    return df, missing_ids, over_1000_ids

def create_id_mapping(df):
    """新しいID連番マッピングを作成"""
    print("\n=== ID連番マッピング作成 ===")
    
    # 現在のIDを取得してソート
    current_ids = sorted(df['ID'].tolist())
    
    # 新しいIDマッピング（1から連番）
    id_mapping = {}
    for new_id, old_id in enumerate(current_ids, 1):
        id_mapping[old_id] = new_id
    
    print(f"マッピング作成完了: {len(id_mapping)}件")
    print(f"新ID範囲: 1 - {len(current_ids)}")
    
    # マッピング例を表示
    print("\nマッピング例（最初の10件）:")
    for i, (old_id, new_id) in enumerate(list(id_mapping.items())[:10]):
        print(f"  {old_id} → {new_id}")
    
    return id_mapping

def update_company_data(df, id_mapping):
    """企業データのIDを更新"""
    print("\n=== 企業データID更新 ===")
    
    # IDを新しい連番に更新
    df['ID'] = df['ID'].map(id_mapping)
    
    # IDでソート
    df = df.sort_values('ID').reset_index(drop=True)
    
    # 更新されたデータを保存
    df.to_csv('data/new_input_test.csv', index=False, encoding='utf-8-sig')
    print(f"✅ 企業データ更新完了: {len(df)}社")
    print(f"新ID範囲: {df['ID'].min()} - {df['ID'].max()}")
    
    return df

def update_sending_results(id_mapping):
    """送信結果ファイルのIDを更新"""
    print("\n=== 送信結果ファイルID更新 ===")
    
    # メイン送信結果ファイル
    if os.path.exists('new_email_sending_results.csv'):
        try:
            df_results = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
            
            # 企業IDを更新
            df_results['企業ID'] = df_results['企業ID'].astype(int).map(id_mapping)
            
            # NaNを除去（マッピングにないIDは削除）
            df_results = df_results.dropna(subset=['企業ID'])
            df_results['企業ID'] = df_results['企業ID'].astype(int)
            
            # IDでソート
            df_results = df_results.sort_values('企業ID').reset_index(drop=True)
            
            # 保存
            df_results.to_csv('new_email_sending_results.csv', index=False, encoding='utf-8-sig')
            print(f"✅ メイン送信結果更新完了: {len(df_results)}件")
            
        except Exception as e:
            print(f"⚠️ メイン送信結果更新エラー: {e}")
    
    # HUGANJOB送信結果ファイル
    huganjob_files = [f for f in os.listdir('.') if f.startswith('huganjob_sending_results_') and f.endswith('.csv')]
    for file_name in huganjob_files:
        try:
            df_huganjob = pd.read_csv(file_name, encoding='utf-8-sig')
            
            if '企業ID' in df_huganjob.columns:
                df_huganjob['企業ID'] = df_huganjob['企業ID'].astype(int).map(id_mapping)
                df_huganjob = df_huganjob.dropna(subset=['企業ID'])
                df_huganjob['企業ID'] = df_huganjob['企業ID'].astype(int)
                df_huganjob = df_huganjob.sort_values('企業ID').reset_index(drop=True)
                df_huganjob.to_csv(file_name, index=False, encoding='utf-8-sig')
                print(f"✅ {file_name} 更新完了: {len(df_huganjob)}件")
                
        except Exception as e:
            print(f"⚠️ {file_name} 更新エラー: {e}")

def update_email_resolution_results(id_mapping):
    """メールアドレス抽出結果のIDを更新"""
    print("\n=== メールアドレス抽出結果ID更新 ===")
    
    if os.path.exists('huganjob_email_resolution_results.csv'):
        try:
            df_email = pd.read_csv('huganjob_email_resolution_results.csv', encoding='utf-8')
            
            # company_idを更新
            df_email['company_id'] = df_email['company_id'].astype(int).map(id_mapping)
            
            # NaNを除去
            df_email = df_email.dropna(subset=['company_id'])
            df_email['company_id'] = df_email['company_id'].astype(int)
            
            # IDでソート
            df_email = df_email.sort_values('company_id').reset_index(drop=True)
            
            # 保存
            df_email.to_csv('huganjob_email_resolution_results.csv', index=False, encoding='utf-8')
            print(f"✅ メールアドレス抽出結果更新完了: {len(df_email)}件")
            
        except Exception as e:
            print(f"⚠️ メールアドレス抽出結果更新エラー: {e}")

def verify_renumbering():
    """ID連番修正の検証"""
    print("\n=== ID連番修正検証 ===")
    
    # 企業データ検証
    df = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
    ids = sorted(df['ID'].tolist())
    
    print(f"総企業数: {len(ids)}")
    print(f"ID範囲: {min(ids)} - {max(ids)}")
    
    # 連番性確認
    expected_ids = list(range(1, len(ids) + 1))
    is_sequential = ids == expected_ids
    
    if is_sequential:
        print("✅ ID連番修正成功: 完全な連番になりました")
    else:
        missing = set(expected_ids) - set(ids)
        duplicates = len(ids) - len(set(ids))
        print(f"❌ ID連番修正に問題があります")
        print(f"   欠番: {sorted(list(missing))}")
        print(f"   重複: {duplicates}件")
    
    return is_sequential

def save_mapping_log(id_mapping, backup_files):
    """IDマッピングログを保存"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_data = {
        'timestamp': timestamp,
        'operation': 'ID_RENUMBERING',
        'total_companies': len(id_mapping),
        'backup_files': backup_files,
        'id_mapping': id_mapping,
        'summary': {
            'old_id_range': f"{min(id_mapping.keys())} - {max(id_mapping.keys())}",
            'new_id_range': f"{min(id_mapping.values())} - {max(id_mapping.values())}",
            'mapping_count': len(id_mapping)
        }
    }
    
    log_file = f"huganjob_id_renumbering_log_{timestamp}.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📝 IDマッピングログ保存: {log_file}")
    return log_file

def main():
    """メイン処理"""
    print("=" * 60)
    print("🔧 HUGANJOB企業データID連番修正ツール")
    print("=" * 60)
    
    try:
        # 1. バックアップ作成
        backup_files_list = backup_files()
        
        # 2. 現在のID状況分析
        df, missing_ids, over_1000_ids = analyze_current_ids()
        
        # 3. IDマッピング作成
        id_mapping = create_id_mapping(df)
        
        # 4. 企業データ更新
        df_updated = update_company_data(df, id_mapping)
        
        # 5. 送信結果ファイル更新
        update_sending_results(id_mapping)
        
        # 6. メールアドレス抽出結果更新
        update_email_resolution_results(id_mapping)
        
        # 7. 検証
        is_success = verify_renumbering()
        
        # 8. ログ保存
        log_file = save_mapping_log(id_mapping, backup_files_list)

        if is_success:
            print(f"\n🎉 ID連番修正が完了しました！")
            print(f"📊 総企業数: {len(df_updated)}")
            print(f"🔢 新ID範囲: 1 - {len(df_updated)}")
            print(f"📝 ログファイル: {log_file}")
            print(f"📦 バックアップ: {len(backup_files_list)}ファイル")
        else:
            print(f"\n❌ ID連番修正に問題が発生しました")
            print(f"バックアップファイルから復元してください")
        
        return is_success
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        print(f"バックアップファイルから復元してください")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
