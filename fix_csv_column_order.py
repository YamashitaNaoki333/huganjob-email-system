#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB CSVファイルの列順序修正ツール
データの順序が間違っているCSVファイルを正しい順序に修正します
"""

import pandas as pd
import csv
import os
from datetime import datetime

def fix_csv_column_order():
    """CSVファイルの列順序を修正"""
    
    print("🔧 HUGANJOB CSVファイル列順序修正ツール")
    print("="*50)
    
    input_file = 'data/new_input_test.csv'
    backup_file = f'data/new_input_test_backup_column_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    # バックアップ作成
    print(f"📁 バックアップ作成: {backup_file}")
    try:
        import shutil
        shutil.copy2(input_file, backup_file)
        print(f"✅ バックアップ完了")
    except Exception as e:
        print(f"❌ バックアップエラー: {e}")
        return
    
    # 現在のCSVファイルを読み込み
    print(f"\n📊 CSVファイル読み込み: {input_file}")
    
    try:
        # 手動でCSVを読み込み（列の順序が間違っているため）
        rows = []
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader)
            print(f"現在のヘッダー: {header}")
            
            for row in reader:
                if len(row) >= 16:  # 最低限の列数を確認
                    rows.append(row)
        
        print(f"読み込み行数: {len(rows)}行")
        
        # 正しい列順序でデータを再構築
        print(f"\n🔄 データ構造を修正中...")
        
        corrected_rows = []
        
        for row in rows:
            # 現在の間違った順序から正しい順序にマッピング
            # 現在: ID,企業名(URL),企業ホームページ(‐),担当者メールアドレス(職種),募集職種(空白),...
            # 正しい順序に修正
            
            corrected_row = [
                row[0],  # ID (正しい)
                '',      # 企業名 (後で設定)
                row[1],  # 企業ホームページ (現在の「企業名」列にURLが入っている)
                row[2],  # 担当者メールアドレス (現在は「‐」が入っている)
                row[3],  # 募集職種 (現在の「担当者メールアドレス」列に職種が入っている)
                row[4] if len(row) > 4 else '',   # バウンス状態
                row[5] if len(row) > 5 else '',   # バウンス日時
                row[6] if len(row) > 6 else '',   # バウンス理由
                row[7] if len(row) > 7 else '',   # 配信停止状態
                row[8] if len(row) > 8 else '',   # 配信停止日時
                row[9] if len(row) > 9 else '',   # 配信停止理由
                row[11] if len(row) > 11 else '', # メールアドレス
                row[12] if len(row) > 12 else '', # 送信ステータス
                row[13] if len(row) > 13 else '', # 送信日時
                row[14] if len(row) > 14 else '', # エラーメッセージ
                row[15] if len(row) > 15 else ''  # バウンスタイプ
            ]
            
            # 企業名をURLから推定（簡易的な処理）
            website_url = corrected_row[2]
            if website_url and website_url != '‐':
                # URLから企業名を推定（ドメイン名から）
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(website_url).netloc
                    if domain:
                        # www. を除去
                        domain = domain.replace('www.', '')
                        # .co.jp, .com などを除去して企業名の推定
                        company_name = domain.split('.')[0]
                        corrected_row[1] = f"企業名_{company_name}"  # 仮の企業名
                    else:
                        corrected_row[1] = "企業名不明"
                except:
                    corrected_row[1] = "企業名不明"
            else:
                corrected_row[1] = "企業名不明"
            
            corrected_rows.append(corrected_row)
        
        # 正しいヘッダーを設定
        correct_header = [
            'ID', '企業名', '企業ホームページ', '担当者メールアドレス', '募集職種',
            'バウンス状態', 'バウンス日時', 'バウンス理由', '配信停止状態', '配信停止日時', '配信停止理由',
            'メールアドレス', '送信ステータス', '送信日時', 'エラーメッセージ', 'バウンスタイプ'
        ]
        
        # 修正されたCSVファイルを保存
        print(f"💾 修正されたCSVファイルを保存中...")
        
        with open(input_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(correct_header)
            writer.writerows(corrected_rows)
        
        print(f"✅ CSVファイル修正完了: {len(corrected_rows)}行")
        print(f"📊 正しいヘッダー: {correct_header}")
        
        # 修正結果の確認
        print(f"\n🔍 修正結果確認...")
        df_check = pd.read_csv(input_file, encoding='utf-8-sig')
        print(f"✅ pandas読み込み成功: {len(df_check)}行, {len(df_check.columns)}列")
        print(f"📋 列名: {list(df_check.columns)}")
        
        # 最初の5行を表示
        print(f"\n📄 修正後の最初の5行:")
        for i in range(min(5, len(df_check))):
            row = df_check.iloc[i]
            print(f"  ID {row['ID']}: {row['企業名']} | {row['企業ホームページ']} | {row['募集職種']}")
        
        print(f"\n🎉 CSVファイルの列順序修正完了！")
        print(f"📁 バックアップ: {backup_file}")
        print(f"📁 修正済み: {input_file}")
        print(f"💡 ダッシュボードで確認してください: http://127.0.0.1:5002/companies")
        
    except Exception as e:
        print(f"❌ CSVファイル修正エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_csv_column_order()
