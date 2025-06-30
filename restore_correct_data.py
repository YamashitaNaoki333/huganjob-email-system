#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB 正しいデータ復元ツール
正しい企業名が保存されているバックアップから復元
"""

import pandas as pd
import shutil
from datetime import datetime

def restore_correct_data():
    """正しいデータを復元"""
    
    print("🔧 HUGANJOB 正しいデータ復元ツール")
    print("="*50)
    
    # 正しいデータが保存されているバックアップファイル
    correct_backup = 'data/new_input_test.csv_backup_20250627_151302'
    target_file = 'data/new_input_test.csv'
    
    print(f"📁 正しいバックアップファイル: {correct_backup}")
    print(f"🎯 復元先ファイル: {target_file}")
    
    try:
        # 現在のファイルをバックアップ
        current_backup = f'data/new_input_test_wrong_data_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        shutil.copy2(target_file, current_backup)
        print(f"📁 現在のファイルをバックアップ: {current_backup}")
        
        # 正しいバックアップファイルを読み込み
        print(f"\n📊 正しいバックアップファイルを読み込み中...")
        df_correct = pd.read_csv(correct_backup, encoding='utf-8-sig')
        print(f"読み込み完了: {len(df_correct)}行")
        
        # 最初の5行のデータを表示
        print(f"\n🔍 正しいデータ例:")
        for i in range(min(5, len(df_correct))):
            row = df_correct.iloc[i]
            print(f"  ID {row['ID']}: 企業名='{row['企業名']}', ホームページ='{row['企業ホームページ']}', メール='{row['担当者メールアドレス']}', 職種='{row['募集職種']}'")
        
        # 正しいデータを保存
        print(f"\n💾 正しいデータを復元中...")
        df_correct.to_csv(target_file, index=False, encoding='utf-8-sig')
        print(f"✅ データ復元完了: {target_file}")
        
        # 復元結果の確認
        print(f"\n🔍 復元後のデータ確認...")
        df_check = pd.read_csv(target_file, encoding='utf-8-sig')
        print(f"✅ pandas読み込み成功: {len(df_check)}行, {len(df_check.columns)}列")
        
        # 最初の5行を表示
        print(f"\n📄 復元後のデータ例:")
        for i in range(min(5, len(df_check))):
            row = df_check.iloc[i]
            print(f"  ID {row['ID']}: 企業名='{row['企業名']}', ホームページ='{row['企業ホームページ']}', メール='{row['担当者メールアドレス']}', 職種='{row['募集職種']}'")
        
        print(f"\n🎉 正しいデータ復元完了！")
        print(f"📊 総企業数: {len(df_check)}社")
        print(f"📁 間違ったデータのバックアップ: {current_backup}")
        print(f"📁 復元済みファイル: {target_file}")
        print(f"💡 ダッシュボードで確認してください: http://127.0.0.1:5003/companies")
        
        return True
        
    except Exception as e:
        print(f"❌ データ復元エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    restore_correct_data()
