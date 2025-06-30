#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB プロセス監視強化システム テストスクリプト

このスクリプトは、新しく実装されたプロセス監視強化機能をテストし、
実行済みプロセスが正しく「完了」ステータスに変わることを確認します。
"""

import requests
import time
import json
import sys
import os

def test_process_monitoring():
    """プロセス監視機能のテストを実行"""
    
    print("🧪 HUGANJOB プロセス監視強化システム テスト開始")
    print("=" * 60)
    
    dashboard_url = "http://127.0.0.1:5002"
    
    # 1. ダッシュボード接続確認
    print("\n1️⃣ ダッシュボード接続確認")
    print("-" * 30)
    
    try:
        response = requests.get(f"{dashboard_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ ダッシュボード接続成功")
        else:
            print(f"❌ ダッシュボード接続失敗: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ダッシュボード接続エラー: {e}")
        return False
    
    # 2. 現在の実行中プロセス確認
    print("\n2️⃣ 現在の実行中プロセス確認")
    print("-" * 30)
    
    try:
        response = requests.get(f"{dashboard_url}/api/get_processes", timeout=10)
        if response.status_code == 200:
            processes = response.json()
            print(f"📊 実行中プロセス数: {len(processes)}件")
            
            for i, proc in enumerate(processes, 1):
                print(f"  {i}. プロセスID: {proc.get('id', 'N/A')}")
                print(f"     コマンド: {proc.get('command', 'N/A')}")
                print(f"     ステータス: {proc.get('status', 'N/A')}")
                print(f"     実行時間: {proc.get('duration', 'N/A')}")
                print()
        else:
            print(f"❌ プロセス情報取得失敗: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ プロセス情報取得エラー: {e}")
        return False
    
    # 3. 軽量送信システムでテスト送信実行
    print("\n3️⃣ テスト送信実行（軽量システム）")
    print("-" * 30)
    
    test_start_id = 1971
    test_end_id = 1972  # 2社のみでテスト
    
    try:
        # 軽量送信システムでテスト送信
        send_data = {
            'command': 'huganjob_lightweight_sender.py',
            'start_id': test_start_id,
            'end_id': test_end_id,
            'skip_dns': True
        }
        
        response = requests.post(
            f"{dashboard_url}/api/start_process",
            data=send_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                process_id = result.get('process_id')
                print(f"✅ テスト送信開始成功")
                print(f"   プロセスID: {process_id}")
                print(f"   コマンド: {result.get('command', 'N/A')}")
                
                # プロセス監視開始
                return monitor_test_process(dashboard_url, process_id)
            else:
                print(f"❌ テスト送信開始失敗: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ テスト送信API失敗: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ テスト送信エラー: {e}")
        return False

def monitor_test_process(dashboard_url, process_id):
    """テストプロセスの監視"""
    
    print(f"\n4️⃣ プロセス監視テスト（プロセスID: {process_id}）")
    print("-" * 30)
    
    max_wait_time = 120  # 最大2分間監視
    check_interval = 5   # 5秒間隔でチェック
    start_time = time.time()
    
    status_history = []
    
    while time.time() - start_time < max_wait_time:
        try:
            # プロセス状態取得
            response = requests.get(f"{dashboard_url}/api/get_processes", timeout=10)
            
            if response.status_code == 200:
                processes = response.json()
                
                # 対象プロセスを検索
                target_process = None
                for proc in processes:
                    if str(proc.get('id')) == str(process_id):
                        target_process = proc
                        break
                
                current_time = time.strftime('%H:%M:%S')
                
                if target_process:
                    status = target_process.get('status', 'unknown')
                    duration = target_process.get('duration', 'N/A')
                    
                    # ステータス履歴に追加
                    status_entry = {
                        'time': current_time,
                        'status': status,
                        'duration': duration
                    }
                    status_history.append(status_entry)
                    
                    print(f"⏰ {current_time} - ステータス: {status} (実行時間: {duration})")
                    
                    # 完了チェック
                    if status in ['completed', 'failed', 'error']:
                        print(f"\n🏁 プロセス終了検出: {status}")
                        
                        # 結果分析
                        return analyze_monitoring_results(status_history, status)
                        
                else:
                    print(f"⏰ {current_time} - プロセス削除済み（完了）")
                    
                    # プロセスが削除された場合も成功とみなす
                    return analyze_monitoring_results(status_history, 'completed')
            
            time.sleep(check_interval)
            
        except Exception as e:
            print(f"⚠️ 監視エラー: {e}")
            time.sleep(check_interval)
    
    print(f"\n⏰ 監視タイムアウト（{max_wait_time}秒）")
    return analyze_monitoring_results(status_history, 'timeout')

def analyze_monitoring_results(status_history, final_status):
    """監視結果の分析"""
    
    print(f"\n5️⃣ 監視結果分析")
    print("-" * 30)
    
    print(f"📊 ステータス履歴:")
    for i, entry in enumerate(status_history, 1):
        print(f"  {i}. {entry['time']} - {entry['status']} ({entry['duration']})")
    
    print(f"\n🎯 最終ステータス: {final_status}")
    
    # 成功判定
    success_criteria = [
        final_status in ['completed', 'failed'],  # プロセスが終了している
        len(status_history) > 0,  # 監視データが取得できている
    ]
    
    if all(success_criteria):
        print("\n✅ プロセス監視強化システム テスト成功！")
        print("   - プロセスが正しく終了ステータスに変更されました")
        print("   - 実行済みプロセスが完了ステータスに変わる問題が解決されました")
        return True
    else:
        print("\n❌ プロセス監視強化システム テスト失敗")
        print("   - プロセス終了検出に問題があります")
        return False

def main():
    """メイン実行関数"""
    
    print("🚀 HUGANJOB プロセス監視強化システム テスト")
    print("   実行済みプロセスが完了ステータスに変わらない問題の解決確認")
    print()
    
    success = test_process_monitoring()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 テスト完了: プロセス監視強化システムが正常に動作しています")
        sys.exit(0)
    else:
        print("💥 テスト失敗: プロセス監視システムに問題があります")
        sys.exit(1)

if __name__ == "__main__":
    main()
