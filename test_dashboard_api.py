#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ダッシュボードAPIテスト
フレキシブル送信APIのテスト
"""

import requests
import json

def test_flexible_send_api():
    """フレキシブル送信APIのテスト"""

    # まずダッシュボードの基本接続をテスト
    base_url = "http://127.0.0.1:5002"
    try:
        response = requests.get(base_url, timeout=5)
        print(f"ダッシュボード接続テスト: {response.status_code}")
    except Exception as e:
        print(f"❌ ダッシュボード接続失敗: {e}")
        return

    url = "http://127.0.0.1:5002/api/huganjob/flexible_send"
    
    data = {
        "start_id": 1,
        "end_id": 5,
        "email_format": "text_only"
    }
    
    print("📧 ダッシュボードAPIテスト開始")
    print("=" * 50)
    print(f"URL: {url}")
    print(f"データ: {json.dumps(data, indent=2)}")
    print("=" * 50)
    
    try:
        response = requests.post(url, json=data, timeout=30)
        
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンス: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ API呼び出し成功")
                print(f"プロセスID: {result.get('process_id')}")
                print(f"システム: {result.get('system')}")
                print(f"メール形式: {result.get('email_type')}")

                # プロセス状況を確認
                process_id = result.get('process_id')
                if process_id:
                    print(f"\n📊 プロセス状況確認中...")
                    import time
                    time.sleep(2)

                    # プロセス履歴を確認
                    history_url = f"http://127.0.0.1:5002/api/get_process_history?limit=10"
                    try:
                        history_response = requests.get(history_url, timeout=10)
                        if history_response.status_code == 200:
                            history = history_response.json()
                            print(f"プロセス履歴（最新10件）:")
                            for i, process in enumerate(history):
                                print(f"  {i+1}. PID: {process.get('pid', 'N/A')}, "
                                      f"コマンド: {process.get('command', 'N/A')}, "
                                      f"状況: {process.get('status', 'unknown')}, "
                                      f"終了コード: {process.get('return_code', 'N/A')}")
                                if str(process.get('pid')) == str(process_id):
                                    print(f"    ↑ 対象プロセス発見!")
                                    print(f"    実行時間: {process.get('duration', 'N/A')}")
                                    if process.get('error'):
                                        print(f"    エラー: {process.get('error')}")
                        else:
                            print(f"プロセス履歴取得失敗: {history_response.status_code}")
                    except Exception as e:
                        print(f"プロセス履歴取得エラー: {e}")

            else:
                print("❌ API呼び出し失敗")
                print(f"エラー: {result.get('message')}")
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 接続エラー: {e}")

if __name__ == "__main__":
    test_flexible_send_api()
