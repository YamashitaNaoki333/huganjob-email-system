#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB 完全データ復元スクリプト
最も完全なバックアップファイルからデータを復元
"""

import shutil
import os
from datetime import datetime

def complete_restore():
    """最も完全なバックアップファイルからデータを復元"""
    
    source_file = 'data/new_input_test_backup_20250626_170646.csv'
    target_file = 'data/new_input_test.csv'
    
    print("🔄 HUGANJOB 完全データ復元開始")
    print("=" * 60)
    
    # ソースファイルの存在確認
    if not os.path.exists(source_file):
        print(f"❌ ソースファイルが見つかりません: {source_file}")
        return False
    
    try:
        # ソースファイルの情報確認
        with open(source_file, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            total_lines = len(lines)
            header = lines[0].strip()
        
        print(f"📊 ソースファイル情報:")
        print(f"  ファイル: {source_file}")
        print(f"  総行数: {total_lines}行（ヘッダー含む）")
        print(f"  企業数: {total_lines-1}社")
        print(f"  ヘッダー: {header}")
        
        # ファイルをコピー
        print(f"\n📁 ファイル復元中...")
        shutil.copy2(source_file, target_file)
        
        # 復元結果確認
        with open(target_file, 'r', encoding='utf-8-sig') as f:
            restored_lines = f.readlines()
            restored_total = len(restored_lines)
        
        print(f"✅ データ復元完了!")
        print(f"  復元先: {target_file}")
        print(f"  復元行数: {restored_total}行")
        print(f"  復元企業数: {restored_total-1}社")
        
        # サンプルデータ表示
        print(f"\n📋 復元データサンプル:")
        for i, line in enumerate(restored_lines[:6]):
            if i == 0:
                print(f"  ヘッダー: {line.strip()}")
            else:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    print(f"  ID {parts[0]}: {parts[1]} | {parts[2]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 復元エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = complete_restore()
    if success:
        print("\n🎉 完全データ復元が完了しました")
        print("💡 ダッシュボードを更新して確認してください")
        print("🌐 http://127.0.0.1:5002/companies")
    else:
        print("\n💥 完全データ復元に失敗しました")
