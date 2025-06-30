#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB CSVデータ復元スクリプト
企業名とウェブサイトの列が入れ替わった問題を修正
"""

import shutil
import os
from datetime import datetime

def restore_csv_data():
    """CSVデータを正しいバックアップから復元"""

    backup_file = 'data/new_input_test_backup_20250626_170646.csv'
    main_file = 'data/new_input_test.csv'

    print("🔄 HUGANJOB CSVデータ復元開始")
    print("=" * 50)

    # バックアップファイルの存在確認
    if not os.path.exists(backup_file):
        print(f"❌ バックアップファイルが見つかりません: {backup_file}")
        return False

    try:
        # バックアップファイルを読み込み
        print(f"📖 バックアップファイル読み込み: {backup_file}")
        with open(backup_file, 'r', encoding='utf-8-sig') as f:
            backup_content = f.read()

        # メインファイルに書き込み
        print(f"✍️ メインファイルに書き込み: {main_file}")
        with open(main_file, 'w', encoding='utf-8-sig') as f:
            f.write(backup_content)

        print(f"✅ データ復元完了: {backup_file} → {main_file}")

        # 復元結果確認
        with open(main_file, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            print(f"📊 復元されたデータ: {len(lines)-1}行（ヘッダー除く）")

            # 最初の数行を確認
            print("\n📋 復元データサンプル:")
            for i, line in enumerate(lines[:6]):
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
    success = restore_csv_data()
    if success:
        print("\n🎉 CSVデータ復元が完了しました")
        print("💡 ダッシュボードを更新して確認してください")
    else:
        print("\n💥 CSVデータ復元に失敗しました")
