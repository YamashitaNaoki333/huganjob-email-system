#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB CSVファイルのデータ順序修正ツール
データが間違った列に入っているCSVファイルを正しい順序に修正
"""

import pandas as pd
import csv
import os
from datetime import datetime
from urllib.parse import urlparse

def extract_company_name_from_url(url):
    """URLから企業名を推定"""
    if not url or url == '‐':
        return '企業名不明'
    
    try:
        domain = urlparse(url).netloc
        if domain:
            # www. を除去
            domain = domain.replace('www.', '')
            # .co.jp, .com などを除去して企業名の推定
            parts = domain.split('.')
            if len(parts) > 0:
                company_base = parts[0]
                # 一般的な企業名パターンに変換
                if company_base:
                    return f"{company_base.upper()}株式会社"
        return '企業名不明'
    except:
        return '企業名不明'

def fix_csv_data_order():
    """CSVファイルのデータ順序を修正"""
    
    print("🔧 HUGANJOB CSVファイルデータ順序修正ツール")
    print("="*60)
    
    input_file = 'data/new_input_test.csv'
    backup_file = f'data/new_input_test_data_order_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
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
        # CSVファイルを読み込み
        df = pd.read_csv(input_file, encoding='utf-8-sig')
        print(f"読み込み完了: {len(df)}行")
        print(f"現在の列名: {list(df.columns)}")
        
        # 最初の5行のデータを表示
        print(f"\n🔍 修正前のデータ例:")
        for i in range(min(5, len(df))):
            row = df.iloc[i]
            print(f"  ID {row['ID']}: 企業名='{row['企業名']}', ホームページ='{row['企業ホームページ']}', メール='{row['担当者メールアドレス']}', 職種='{row['募集職種']}'")
        
        # データを正しい順序に修正
        print(f"\n🔄 データ順序を修正中...")
        
        corrected_data = []
        
        for _, row in df.iterrows():
            # 現在の間違った順序から正しい順序にマッピング
            # 現在: ID, 企業名(URL), 企業ホームページ(‐), 担当者メールアドレス(職種), 募集職種(バウンス状態), ...
            
            # 正しいデータを構築
            corrected_row = {
                'ID': row['ID'],
                '企業名': extract_company_name_from_url(row['企業名']),  # URLから企業名を推定
                '企業ホームページ': row['企業名'],  # 現在の「企業名」列にURLが入っている
                '担当者メールアドレス': row.get('メールアドレス', '‐'),  # 列12のメールアドレス
                '募集職種': row['担当者メールアドレス'],  # 現在の「担当者メールアドレス」列に職種が入っている
                'バウンス状態': row.get('募集職種', ''),  # 現在の「募集職種」列にバウンス状態が入っている
                'バウンス日時': row.get('バウンス状態', ''),
                'バウンス理由': row.get('バウンス日時', ''),
                '配信停止状態': row.get('バウンス理由', ''),
                '配信停止日時': row.get('配信停止状態', ''),
                '配信停止理由': row.get('配信停止日時', ''),
                'メールアドレス': row.get('メールアドレス', '‐'),
                '送信ステータス': row.get('送信ステータス', ''),
                '送信日時': row.get('送信日時', ''),
                'エラーメッセージ': row.get('エラーメッセージ', ''),
                'バウンスタイプ': row.get('バウンスタイプ', '')
            }
            
            corrected_data.append(corrected_row)
        
        # 修正されたデータフレームを作成
        df_corrected = pd.DataFrame(corrected_data)
        
        # 修正されたCSVファイルを保存
        print(f"💾 修正されたCSVファイルを保存中...")
        df_corrected.to_csv(input_file, index=False, encoding='utf-8-sig')
        
        print(f"✅ CSVファイル修正完了: {len(df_corrected)}行")
        
        # 修正結果の確認
        print(f"\n🔍 修正後のデータ例:")
        for i in range(min(5, len(df_corrected))):
            row = df_corrected.iloc[i]
            print(f"  ID {row['ID']}: 企業名='{row['企業名']}', ホームページ='{row['企業ホームページ']}', メール='{row['担当者メールアドレス']}', 職種='{row['募集職種']}'")
        
        print(f"\n🎉 CSVファイルのデータ順序修正完了！")
        print(f"📁 バックアップ: {backup_file}")
        print(f"📁 修正済み: {input_file}")
        print(f"💡 ダッシュボードで確認してください: http://127.0.0.1:5003/companies")
        
        return True
        
    except Exception as e:
        print(f"❌ CSVファイル修正エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_csv_data_order()
