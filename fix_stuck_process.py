#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
スタックしたプロセスの修正
ダッシュボードで実行中のまま表示されているプロセスを停止
"""

import requests
import json

def fix_stuck_process():
    """スタックしたプロセスを修正"""
    
    base_url = "http://127.0.0.1:5002"
    
    print("🔧 スタックしたプロセスの修正")
    print("=" * 50)
    
    try:
        # 実行中プロセスを取得
        response = requests.get(f"{base_url}/api/get_processes", timeout=10)
        if response.status_code == 200:
            processes = response.json()
            
            for process in processes:
                if 'huganjob_text_only_sender' in process.get('command', ''):
                    pid = process.get('pid')
                    print(f"📋 対象プロセス発見:")
                    print(f"  PID: {pid}")
                    print(f"  コマンド: {process.get('command')}")
                    print(f"  状況: {process.get('status')}")
                    print(f"  実行時間: {process.get('duration', 'N/A')}")
                    
                    # プロセスを停止
                    if pid and pid != 'N/A' and pid is not None:
                        print(f"\n🛑 プロセス {pid} を停止中...")
                        stop_response = requests.post(f"{base_url}/api/stop_process/{pid}", timeout=10)
                        if stop_response.status_code == 200:
                            result = stop_response.json()
                            if result.get('success'):
                                print(f"✅ プロセス {pid} を正常に停止しました")
                            else:
                                print(f"❌ プロセス停止失敗: {result.get('message')}")
                        else:
                            print(f"❌ プロセス停止API呼び出し失敗: {stop_response.status_code}")
                    else:
                        print("⚠️ PIDが無効なため、直接停止できません")
                        print("ダッシュボードを再起動することを推奨します")
                    
                    break
            else:
                print("📋 huganjob_text_only_sender関連の実行中プロセスが見つかりません")
        else:
            print(f"❌ プロセス一覧取得失敗: {response.status_code}")
            
        # 修正後の状況確認
        print(f"\n📊 修正後の状況確認:")
        response = requests.get(f"{base_url}/api/get_processes", timeout=10)
        if response.status_code == 200:
            processes = response.json()
            if processes:
                print(f"  実行中プロセス数: {len(processes)}")
                for process in processes:
                    if 'huganjob_text_only_sender' in process.get('command', ''):
                        print(f"  ⚠️ まだ実行中: {process.get('command')}")
                        break
                else:
                    print("  ✅ huganjob_text_only_sender関連プロセスは実行中にありません")
            else:
                print("  ✅ 実行中プロセスなし")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    fix_stuck_process()
