#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSVファイル構造修正スクリプト

CSVファイルの列数不整合を修正し、全ての行を16列構造に統一します。
"""

import pandas as pd
import csv

def fix_csv_structure():
    """CSVファイル構造を修正"""
    
    print("🔧 CSVファイル構造修正開始")
    print("=" * 60)
    
    csv_file = 'data/new_input_test.csv'
    backup_file = 'data/new_input_test_backup.csv'
    
    try:
        # バックアップ作成
        print("1️⃣ バックアップ作成中...")
        import shutil
        shutil.copy2(csv_file, backup_file)
        print(f"   ✅ バックアップ作成完了: {backup_file}")
        
        # CSVファイルを行ごとに読み込み
        print("\n2️⃣ CSVファイル読み込み・修正中...")
        
        fixed_rows = []
        expected_columns = 16
        
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            
            for line_num, row in enumerate(reader, 1):
                current_columns = len(row)
                
                if line_num == 1:
                    # ヘッダー行の確認
                    if current_columns != expected_columns:
                        print(f"   ⚠️ ヘッダー列数不整合: 期待={expected_columns}, 実際={current_columns}")
                        # ヘッダーを16列に調整
                        while len(row) < expected_columns:
                            row.append('')
                        row = row[:expected_columns]
                    fixed_rows.append(row)
                    continue
                
                # データ行の修正
                if current_columns != expected_columns:
                    print(f"   🔧 行 {line_num}: {current_columns}列 → {expected_columns}列に修正")
                    
                    # 列数を16に調整
                    while len(row) < expected_columns:
                        row.append('')
                    row = row[:expected_columns]
                
                fixed_rows.append(row)
        
        print(f"\n3️⃣ 修正されたCSVファイル保存中...")
        
        # 修正されたデータを保存
        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(fixed_rows)
        
        print(f"   ✅ CSVファイル修正完了: {len(fixed_rows)}行")
        
        # 修正結果の検証
        print("\n4️⃣ 修正結果検証中...")
        
        try:
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
            print(f"   ✅ pandas読み込み成功: {len(df)}行, {len(df.columns)}列")
            print(f"   📊 列名: {list(df.columns)}")
            
            # ID 1971-1976の確認
            target_ids = [1971, 1972, 1973, 1974, 1975, 1976]
            for target_id in target_ids:
                mask = df['ID'] == target_id
                if mask.any():
                    row = df[mask].iloc[0]
                    status = row.get('送信ステータス', '未設定')
                    email = row.get('メールアドレス', '未設定')
                    print(f"   ✅ ID {target_id}: {status} ({email})")
                else:
                    print(f"   ⚠️ ID {target_id}: 見つかりません")
            
        except Exception as e:
            print(f"   ❌ pandas読み込みエラー: {e}")
        
        print("\n🎉 CSVファイル構造修正完了")
        
    except Exception as e:
        print(f"❌ CSVファイル修正エラー: {e}")

def main():
    """メイン実行関数"""
    
    print("🚀 HUGANJOBシステム CSVファイル構造修正ツール")
    print("   列数不整合を修正し、16列構造に統一します")
    print()
    
    fix_csv_structure()

if __name__ == "__main__":
    main()
