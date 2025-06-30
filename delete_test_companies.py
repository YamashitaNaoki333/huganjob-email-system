#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB テスト企業削除ツール
指定されたテスト企業を削除してIDを再採番
"""

import pandas as pd
import os
from datetime import datetime

def delete_test_companies():
    """テスト企業を削除してIDを再採番"""
    
    print("🗑️ HUGANJOB テスト企業削除ツール")
    print("="*50)
    
    # 削除対象のID
    test_company_ids = [2995, 2996, 2997, 4837, 4838, 4839, 4840, 4832, 4833, 4834]
    
    input_file = 'data/new_input_test.csv'
    backup_file = f'data/new_input_test_before_test_deletion_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    # バックアップ作成
    print(f"📁 バックアップ作成: {backup_file}")
    try:
        import shutil
        shutil.copy2(input_file, backup_file)
        print(f"✅ バックアップ完了")
    except Exception as e:
        print(f"❌ バックアップエラー: {e}")
        return
    
    # CSVファイルを読み込み
    print(f"\n📊 CSVファイル読み込み: {input_file}")
    
    try:
        df = pd.read_csv(input_file, encoding='utf-8-sig')
        print(f"読み込み完了: {len(df)}行")
        
        # 削除前の状況確認
        print(f"\n🔍 削除対象企業の確認:")
        for test_id in test_company_ids:
            matching_rows = df[df['ID'] == test_id]
            if not matching_rows.empty:
                row = matching_rows.iloc[0]
                print(f"  ID {test_id}: {row['企業名']} ({row.get('担当者メールアドレス', '未登録')})")
            else:
                print(f"  ID {test_id}: 見つかりません")
        
        # テスト企業を削除
        print(f"\n🗑️ テスト企業を削除中...")
        df_filtered = df[~df['ID'].isin(test_company_ids)]
        deleted_count = len(df) - len(df_filtered)
        print(f"削除完了: {deleted_count}社を削除")
        
        # IDを再採番
        print(f"\n🔢 IDを再採番中...")
        df_filtered = df_filtered.reset_index(drop=True)
        df_filtered['ID'] = range(1, len(df_filtered) + 1)
        
        # 修正されたCSVファイルを保存
        print(f"\n💾 修正されたCSVファイルを保存中...")
        df_filtered.to_csv(input_file, index=False, encoding='utf-8-sig')
        
        print(f"✅ テスト企業削除完了")
        print(f"📊 削除前: {len(df)}社")
        print(f"📊 削除後: {len(df_filtered)}社")
        print(f"📊 削除数: {deleted_count}社")
        print(f"📁 バックアップ: {backup_file}")
        print(f"📁 更新済み: {input_file}")
        print(f"💡 ダッシュボードで確認してください: http://127.0.0.1:5002/companies")
        
        return True
        
    except Exception as e:
        print(f"❌ テスト企業削除エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    delete_test_companies()
