#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB即座データクリーニング実行
"""

import pandas as pd
import csv
import json
import os

def main():
    # 削除対象企業ID
    target_ids = [2995, 2996, 2997, 4837, 4838, 4839, 4840, 4832, 4833, 4834]

    print("🧹 HUGANJOB即座データクリーニング開始")
    print("="*50)
    print(f"🎯 削除対象企業: {len(target_ids)}社")
    print(f"削除対象ID: {target_ids}")

    # 1. メインCSVファイルの処理
    main_csv = 'data/new_input_test.csv'
    print(f"\n📊 メインCSVファイル処理: {main_csv}")

    try:
        # CSVファイルを読み込み
        df = pd.read_csv(main_csv, encoding='utf-8-sig')
        print(f"読み込み完了: {len(df)}社")

        # 削除対象企業の詳細表示
        print(f"\n🗑️ 削除対象企業詳細:")
        for target_id in target_ids:
            company_row = df[df['ID'] == target_id]
            if not company_row.empty:
                company_name = company_row.iloc[0]['企業名']
                email = company_row.iloc[0].get('担当者メールアドレス', '未登録')
                print(f"  ID {target_id}: {company_name} ({email})")
            else:
                print(f"  ID {target_id}: 企業が見つかりません")

        # 削除前の企業数
        before_count = len(df)

        # 指定IDの企業を削除
        df_cleaned = df[~df['ID'].isin(target_ids)].copy()

        # 削除後の企業数
        after_count = len(df_cleaned)
        deleted_count = before_count - after_count

        print(f"\n✅ 削除完了: {before_count}社 → {after_count}社 ({deleted_count}社削除)")

        # IDを連番に振り直し
        print(f"🔢 IDを連番に振り直し中...")
        df_cleaned['ID'] = range(1, len(df_cleaned) + 1)
        print(f"✅ ID振り直し完了: 1 〜 {len(df_cleaned)}")

        # 保存
        df_cleaned.to_csv(main_csv, index=False, encoding='utf-8-sig')
        print(f"✅ メインCSVファイル保存完了: {main_csv}")

        # 完了報告
        print(f"\n🎉 データクリーニング完了！")
        print(f"📁 バックアップ: data/new_input_test.csv_backup_20250627_150700")
        print(f"📊 最終企業数: {len(df_cleaned)}社")
        print(f"🗑️ 削除企業数: {deleted_count}社")
        print(f"💡 ダッシュボードで確認してください: http://127.0.0.1:5002/companies")

    except Exception as e:
        print(f"❌ メインCSVファイル処理エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
