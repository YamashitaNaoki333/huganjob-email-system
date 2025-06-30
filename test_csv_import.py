#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSVインポート機能テストスクリプト
"""

import requests
import json
import os

def test_csv_import():
    """CSVインポート機能をテスト"""
    
    # ダッシュボードのURL
    base_url = "http://127.0.0.1:5002"
    
    print("=== CSVインポート機能テスト ===")
    
    # 1. 現在の企業数を取得
    print("\n1. 現在の企業数を確認...")
    try:
        # 企業一覧ページから企業数を取得
        response = requests.get(f"{base_url}/companies")
        if response.status_code == 200:
            print("✅ ダッシュボードにアクセス成功")
        else:
            print(f"❌ ダッシュボードアクセス失敗: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ ダッシュボードアクセスエラー: {e}")
        return
    
    # 2. CSVファイルをアップロード
    print("\n2. CSVファイルをアップロード...")
    csv_file_path = "test_import.csv"
    
    if not os.path.exists(csv_file_path):
        print(f"❌ テストCSVファイルが見つかりません: {csv_file_path}")
        return
    
    try:
        with open(csv_file_path, 'rb') as f:
            files = {'csv_file': f}
            response = requests.post(f"{base_url}/api/csv-import", files=files)
            
        if response.status_code == 200:
            result = response.json()
            print("✅ CSVファイルアップロード成功")
            print(f"   解析結果: {result.get('success', False)}")
            
            if result.get('success'):
                temp_file = result.get('temp_file')
                print(f"   一時ファイル: {temp_file}")
                
                # 3. インポート確定
                print("\n3. インポート確定...")
                confirm_data = {
                    'temp_file': temp_file,
                    'skip_duplicates': True
                }
                
                response = requests.post(
                    f"{base_url}/api/csv-import-confirm",
                    json=confirm_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ CSVインポート確定成功")
                    print(f"   成功: {result.get('success', False)}")
                    print(f"   処理済み: {result.get('total_processed', 0)}件")
                    print(f"   追加: {result.get('added', 0)}件")
                    print(f"   スキップ: {result.get('skipped', 0)}件")
                    print(f"   エラー: {result.get('errors', 0)}件")
                    
                    if result.get('added', 0) > 0:
                        print("\n🎉 新規企業の追加に成功しました！")
                        print("   ダッシュボードで確認してください。")
                    else:
                        print("\n⚠️ 新規企業は追加されませんでした（重複の可能性）")
                        
                else:
                    print(f"❌ インポート確定失敗: {response.status_code}")
                    print(f"   レスポンス: {response.text}")
            else:
                print(f"❌ CSVファイル解析失敗: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ CSVファイルアップロード失敗: {response.status_code}")
            print(f"   レスポンス: {response.text}")
            
    except Exception as e:
        print(f"❌ CSVインポートエラー: {e}")
    
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    test_csv_import()
