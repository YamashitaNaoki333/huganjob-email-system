#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB CSVファイル復元・クリーニングツール
正しい構造のバックアップから復元し、指定企業を削除
"""

import pandas as pd
import shutil
from datetime import datetime

def restore_and_clean_csv():
    """CSVファイルを復元してクリーニング"""
    
    print("🔧 HUGANJOB CSVファイル復元・クリーニングツール")
    print("="*60)
    
    # ファイルパス
    backup_file = 'data/new_input_test.csv_backup_20250627_151302'
    target_file = 'data/new_input_test.csv'
    
    # 削除対象企業ID（元の指定）
    target_ids = [2995, 2996, 2997, 4837, 4838, 4839, 4840, 4832, 4833, 4834]
    
    print(f"📁 バックアップファイル: {backup_file}")
    print(f"🎯 削除対象企業: {len(target_ids)}社")
    print(f"削除対象ID: {target_ids}")
    
    try:
        # 1. バックアップファイルから復元
        print(f"\n📊 バックアップファイルから復元中...")
        df = pd.read_csv(backup_file, encoding='utf-8-sig')
        print(f"読み込み完了: {len(df)}社")
        
        # 2. 列構造の確認
        print(f"\n📋 列構造確認:")
        print(f"列数: {len(df.columns)}")
        print(f"列名: {list(df.columns)}")
        
        # 3. 削除対象企業の確認
        print(f"\n🗑️ 削除対象企業詳細:")
        deleted_count = 0
        for target_id in target_ids:
            company_row = df[df['ID'] == target_id]
            if not company_row.empty:
                company_name = company_row.iloc[0]['企業名']
                email = company_row.iloc[0].get('担当者メールアドレス', '未登録')
                website = company_row.iloc[0].get('企業ホームページ', '未登録')
                job = company_row.iloc[0].get('募集職種', '未登録')
                print(f"  ID {target_id}: {company_name}")
                print(f"    ウェブサイト: {website}")
                print(f"    メール: {email}")
                print(f"    職種: {job}")
                deleted_count += 1
            else:
                print(f"  ID {target_id}: 企業が見つかりません")
        
        # 4. 削除前の企業数
        before_count = len(df)
        
        # 5. 指定IDの企業を削除
        print(f"\n🔄 企業削除処理中...")
        df_cleaned = df[~df['ID'].isin(target_ids)].copy()
        
        # 6. 削除後の企業数
        after_count = len(df_cleaned)
        actual_deleted = before_count - after_count
        
        print(f"✅ 削除完了: {before_count}社 → {after_count}社 ({actual_deleted}社削除)")
        
        # 7. IDを連番に振り直し
        print(f"🔢 IDを連番に振り直し中...")
        df_cleaned['ID'] = range(1, len(df_cleaned) + 1)
        print(f"✅ ID振り直し完了: 1 〜 {len(df_cleaned)}")
        
        # 8. 最終バックアップ作成
        final_backup = f'data/new_input_test_final_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        shutil.copy2(target_file, final_backup)
        print(f"📁 最終バックアップ作成: {final_backup}")
        
        # 9. 修正されたファイルを保存
        print(f"💾 修正されたCSVファイルを保存中...")
        df_cleaned.to_csv(target_file, index=False, encoding='utf-8-sig')
        print(f"✅ CSVファイル保存完了: {target_file}")
        
        # 10. 修正結果の確認
        print(f"\n🔍 修正結果確認...")
        df_check = pd.read_csv(target_file, encoding='utf-8-sig')
        print(f"✅ pandas読み込み成功: {len(df_check)}行, {len(df_check.columns)}列")
        print(f"📋 列名: {list(df_check.columns)}")
        
        # 11. 最初の5行を表示
        print(f"\n📄 修正後の最初の5行:")
        for i in range(min(5, len(df_check))):
            row = df_check.iloc[i]
            print(f"  ID {row['ID']}: {row['企業名']} | {row['企業ホームページ']} | {row['募集職種']}")
        
        print(f"\n🎉 CSVファイル復元・クリーニング完了！")
        print(f"📊 最終企業数: {len(df_cleaned)}社")
        print(f"🗑️ 削除企業数: {actual_deleted}社")
        print(f"📁 バックアップ: {final_backup}")
        print(f"📁 修正済み: {target_file}")
        print(f"💡 ダッシュボードで確認してください: http://127.0.0.1:5002/companies")
        
        return True
        
    except Exception as e:
        print(f"❌ CSVファイル復元・クリーニングエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    restore_and_clean_csv()
