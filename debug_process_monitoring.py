#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
プロセス監視システムの問題調査
ダッシュボードとプロセス終了検出の問題を解明
"""

import requests
import json
import psutil
import time
import os
from datetime import datetime

def debug_process_monitoring():
    """プロセス監視システムの詳細調査"""
    
    print("🔍 プロセス監視システム問題調査")
    print("=" * 70)
    print(f"調査時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. ダッシュボードプロセス一覧確認
    print("📋 1. ダッシュボードプロセス一覧:")
    print("-" * 50)
    
    try:
        response = requests.get("http://127.0.0.1:5002/api/get_processes", timeout=5)
        if response.status_code == 200:
            processes = response.json()
            
            print(f"  登録プロセス数: {len(processes)}")
            
            for i, process in enumerate(processes):
                print(f"\n  プロセス {i+1}:")
                print(f"    ID: {process.get('id', 'N/A')}")
                print(f"    コマンド: {process.get('command', 'N/A')}")
                print(f"    引数: {process.get('args', 'N/A')}")
                print(f"    状況: {process.get('status', 'N/A')}")
                print(f"    開始時刻: {process.get('start_time', 'N/A')}")
                print(f"    実行時間: {process.get('duration', 'N/A')}")
                print(f"    説明: {process.get('description', 'N/A')}")
                
                # 1969のプロセスを特定
                if "1969" in process.get('args', ''):
                    print(f"    🎯 対象プロセス発見: ID 1969")
                    analyze_specific_process(process)
        else:
            print(f"  ❌ API エラー: {response.status_code}")
    except Exception as e:
        print(f"  ❌ API接続エラー: {e}")
    
    # 2. システムプロセス確認
    print(f"\n💻 2. システムプロセス確認:")
    print("-" * 50)
    
    check_system_processes()
    
    # 3. ダッシュボード監視機能確認
    print(f"\n🔍 3. ダッシュボード監視機能確認:")
    print("-" * 50)
    
    check_dashboard_monitoring()
    
    # 4. プロセス終了検出問題の分析
    print(f"\n🧪 4. プロセス終了検出問題分析:")
    print("-" * 50)
    
    analyze_process_termination_detection()

def analyze_specific_process(process_info):
    """特定プロセスの詳細分析"""
    
    print(f"\n    🔬 詳細分析:")
    
    pid = process_info.get('id')
    if pid and pid != 'N/A':
        try:
            pid = int(pid)
            
            # システムプロセス確認
            if psutil.pid_exists(pid):
                proc = psutil.Process(pid)
                print(f"      システム状況: {proc.status()}")
                print(f"      CPU使用率: {proc.cpu_percent()}%")
                print(f"      メモリ使用量: {proc.memory_info().rss / 1024 / 1024:.1f} MB")
                
                # プロセスが実際に動いているか
                if proc.status() == 'zombie':
                    print(f"      ⚠️ ゾンビプロセス検出")
                elif proc.status() == 'sleeping':
                    print(f"      💤 プロセススリープ中")
                elif proc.status() == 'running':
                    print(f"      🏃 プロセス実行中")
                else:
                    print(f"      ❓ 不明な状況: {proc.status()}")
            else:
                print(f"      ❌ システムプロセス存在しない（PID: {pid}）")
                print(f"      💡 ダッシュボードが終了プロセスを検出できていない")
                
        except Exception as e:
            print(f"      ❌ プロセス分析エラー: {e}")

def check_system_processes():
    """システムプロセスの確認"""
    
    python_processes = []
    huganjob_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status', 'create_time']):
        try:
            if proc.info['name'] in ['python.exe', 'python']:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                
                if 'huganjob' in cmdline.lower():
                    huganjob_processes.append({
                        'pid': proc.info['pid'],
                        'cmdline': cmdline,
                        'status': proc.info['status'],
                        'create_time': datetime.fromtimestamp(proc.info['create_time']).strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                python_processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    print(f"  Pythonプロセス総数: {len(python_processes)}")
    print(f"  HUGANJOBプロセス数: {len(huganjob_processes)}")
    
    if huganjob_processes:
        print(f"\n  🎯 HUGANJOBプロセス詳細:")
        for proc in huganjob_processes:
            print(f"    PID {proc['pid']}: {proc['status']}")
            print(f"      コマンド: {proc['cmdline'][:100]}...")
            print(f"      作成時刻: {proc['create_time']}")
            
            # ID 1969を含むプロセスを特定
            if '1969' in proc['cmdline']:
                print(f"      🎯 ID 1969プロセス発見")
                if proc['status'] == 'zombie':
                    print(f"      ⚠️ ゾンビプロセス - ダッシュボードが検出できていない")
                elif proc['status'] == 'sleeping':
                    print(f"      💤 スリープ中 - 処理完了済みの可能性")
    else:
        print(f"  ✅ HUGANJOBプロセスなし（全て終了済み）")

def check_dashboard_monitoring():
    """ダッシュボード監視機能の確認"""
    
    try:
        # プロセス履歴確認
        response = requests.get("http://127.0.0.1:5002/api/get_process_history?limit=10", timeout=5)
        if response.status_code == 200:
            history = response.json()
            
            print(f"  プロセス履歴件数: {len(history)}")
            
            # 最近の履歴を確認
            for i, proc in enumerate(history[:5]):
                print(f"\n    履歴 {i+1}:")
                print(f"      コマンド: {proc.get('command', 'N/A')}")
                print(f"      状況: {proc.get('status', 'N/A')}")
                print(f"      開始時刻: {proc.get('start_time', 'N/A')}")
                print(f"      終了時刻: {proc.get('end_time', 'N/A')}")
                
                # ID 1969の履歴を確認
                if '1969' in proc.get('args', ''):
                    print(f"      🎯 ID 1969履歴発見")
                    if proc.get('status') == 'completed':
                        print(f"      ✅ 正常終了記録あり")
                    elif proc.get('status') == 'running':
                        print(f"      ⚠️ 実行中のまま記録")
        else:
            print(f"  ❌ 履歴API エラー: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 履歴確認エラー: {e}")

def analyze_process_termination_detection():
    """プロセス終了検出問題の分析"""
    
    print(f"  🔍 推定される問題:")
    print(f"    1. プロセス監視スレッドの問題")
    print(f"    2. プロセス終了検出の遅延")
    print(f"    3. ゾンビプロセスの処理不備")
    print(f"    4. ダッシュボード内部状態の不整合")
    
    print(f"\n  💡 考えられる原因:")
    print(f"    - monitor_process()関数でのプロセス終了検出失敗")
    print(f"    - subprocess.Popenのpoll()メソッドの問題")
    print(f"    - プロセス状態更新の非同期処理問題")
    print(f"    - Windowsでのプロセス終了検出の特殊性")
    
    print(f"\n  🛠️ 解決策:")
    print(f"    1. プロセス強制終了とダッシュボード再起動")
    print(f"    2. プロセス監視機能の改善")
    print(f"    3. 明示的なプロセス終了通知機能の追加")
    print(f"    4. ダッシュボードのプロセス状態リセット機能")

def test_process_termination():
    """プロセス終了検出のテスト"""
    
    print(f"\n🧪 5. プロセス終了検出テスト:")
    print("-" * 50)
    
    try:
        # 簡単なテストプロセスを起動
        print(f"  テストプロセス起動中...")
        
        test_data = {
            'start_id': 9999,
            'end_id': 9999
        }
        
        response = requests.post(
            "http://127.0.0.1:5002/api/huganjob/text_send",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                process_id = result.get('process_id')
                print(f"  ✅ テストプロセス開始: {process_id}")
                
                # 5秒後にプロセス状況確認
                time.sleep(5)
                
                response = requests.get("http://127.0.0.1:5002/api/get_processes", timeout=5)
                if response.status_code == 200:
                    processes = response.json()
                    
                    test_process = None
                    for proc in processes:
                        if str(proc.get('id')) == str(process_id):
                            test_process = proc
                            break
                    
                    if test_process:
                        print(f"  📊 テストプロセス状況: {test_process.get('status')}")
                        print(f"  ⏱️ 実行時間: {test_process.get('duration')}")
                    else:
                        print(f"  ✅ テストプロセス終了済み（正常）")
            else:
                print(f"  ❌ テストプロセス開始失敗: {result.get('message')}")
        else:
            print(f"  ❌ テストAPI エラー: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ テストエラー: {e}")

def recommend_solutions():
    """解決策の推奨"""
    
    print(f"\n🎯 6. 推奨解決策:")
    print("-" * 50)
    
    print(f"  🛑 即座の対応:")
    print(f"    1. 現在の実行中プロセスを手動停止")
    print(f"    2. ダッシュボードを再起動")
    print(f"    3. プロセス状態をリセット")
    
    print(f"\n  🔧 根本対策:")
    print(f"    1. プロセス監視機能の改善")
    print(f"    2. 明示的なプロセス終了通知の実装")
    print(f"    3. ゾンビプロセス検出・クリーンアップ機能")
    print(f"    4. プロセス状態の定期的な同期")
    
    print(f"\n  ⚡ 緊急回避策:")
    print(f"    - 軽量送信システム（huganjob_lightweight_sender.py）の使用")
    print(f"    - ダッシュボードを使わない直接実行")
    print(f"    - プロセス監視の無効化")

if __name__ == "__main__":
    debug_process_monitoring()
    test_process_termination()
    recommend_solutions()
    
    print(f"\n調査完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💡 結論: ダッシュボードのプロセス監視システムに問題があります")
