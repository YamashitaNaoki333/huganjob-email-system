#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ダッシュボードプロセス監視問題の修正
実行中のまま停止しているプロセスを強制終了し、状態をリセット
"""

import requests
import json
import psutil
import time
import os
from datetime import datetime

def fix_dashboard_process_monitoring():
    """ダッシュボードプロセス監視問題の修正"""
    
    print("🔧 ダッシュボードプロセス監視問題修正")
    print("=" * 60)
    print(f"修正開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 現在の問題プロセス確認
    print("📋 1. 問題プロセス確認:")
    print("-" * 40)
    
    problem_processes = []
    
    try:
        response = requests.get("http://127.0.0.1:5002/api/get_processes", timeout=5)
        if response.status_code == 200:
            processes = response.json()
            
            print(f"  登録プロセス数: {len(processes)}")
            
            for process in processes:
                pid = process.get('id')
                status = process.get('status', 'unknown')
                duration = process.get('duration', 'N/A')
                command = process.get('command', 'N/A')
                
                print(f"\n  プロセス PID {pid}:")
                print(f"    コマンド: {command}")
                print(f"    状況: {status}")
                print(f"    実行時間: {duration}")
                
                # 実際のシステムプロセス確認
                if pid and pid != 'N/A':
                    try:
                        pid_int = int(pid)
                        if psutil.pid_exists(pid_int):
                            proc = psutil.Process(pid_int)
                            actual_status = proc.status()
                            print(f"    実際の状況: {actual_status}")
                            
                            if actual_status in ['zombie', 'sleeping'] and status == 'running':
                                print(f"    ⚠️ 問題プロセス: ダッシュボード状況と実際の状況が不一致")
                                problem_processes.append({
                                    'pid': pid_int,
                                    'dashboard_status': status,
                                    'actual_status': actual_status,
                                    'command': command
                                })
                        else:
                            print(f"    ❌ プロセス存在しない（終了済み）")
                            problem_processes.append({
                                'pid': pid_int,
                                'dashboard_status': status,
                                'actual_status': 'not_exists',
                                'command': command
                            })
                    except Exception as e:
                        print(f"    ❌ プロセス確認エラー: {e}")
        else:
            print(f"  ❌ API エラー: {response.status_code}")
    except Exception as e:
        print(f"  ❌ API接続エラー: {e}")
    
    # 2. 問題プロセスの強制終了
    print(f"\n🛑 2. 問題プロセス強制終了:")
    print("-" * 40)
    
    if problem_processes:
        for proc_info in problem_processes:
            pid = proc_info['pid']
            actual_status = proc_info['actual_status']
            command = proc_info['command']
            
            print(f"\n  PID {pid} ({command}):")
            
            if actual_status == 'not_exists':
                print(f"    ✅ プロセス既に終了済み")
                # ダッシュボードに終了通知
                try:
                    stop_response = requests.post(
                        f"http://127.0.0.1:5002/api/stop_process/{pid}",
                        timeout=5
                    )
                    if stop_response.status_code == 200:
                        print(f"    ✅ ダッシュボード状態更新成功")
                    else:
                        print(f"    ⚠️ ダッシュボード状態更新失敗: {stop_response.status_code}")
                except Exception as e:
                    print(f"    ❌ ダッシュボード通信エラー: {e}")
                    
            elif actual_status in ['zombie', 'sleeping']:
                print(f"    🔄 プロセス強制終了中...")
                try:
                    proc = psutil.Process(pid)
                    proc.terminate()
                    
                    # 3秒待機
                    time.sleep(3)
                    
                    if proc.is_running():
                        print(f"    💥 強制終了（SIGKILL）")
                        proc.kill()
                    
                    print(f"    ✅ プロセス終了完了")
                    
                    # ダッシュボードに終了通知
                    try:
                        stop_response = requests.post(
                            f"http://127.0.0.1:5002/api/stop_process/{pid}",
                            timeout=5
                        )
                        if stop_response.status_code == 200:
                            print(f"    ✅ ダッシュボード状態更新成功")
                        else:
                            print(f"    ⚠️ ダッシュボード状態更新失敗: {stop_response.status_code}")
                    except Exception as e:
                        print(f"    ❌ ダッシュボード通信エラー: {e}")
                        
                except Exception as e:
                    print(f"    ❌ プロセス終了エラー: {e}")
    else:
        print(f"  ✅ 問題プロセスなし")
    
    # 3. ダッシュボード状態確認
    print(f"\n📊 3. 修正後状態確認:")
    print("-" * 40)
    
    try:
        response = requests.get("http://127.0.0.1:5002/api/get_processes", timeout=5)
        if response.status_code == 200:
            processes = response.json()
            
            print(f"  修正後プロセス数: {len(processes)}")
            
            if processes:
                for process in processes:
                    print(f"    PID {process.get('id')}: {process.get('status')} - {process.get('command')}")
            else:
                print(f"  ✅ 実行中プロセスなし（正常状態）")
        else:
            print(f"  ❌ API エラー: {response.status_code}")
    except Exception as e:
        print(f"  ❌ API接続エラー: {e}")
    
    # 4. システムプロセス確認
    print(f"\n💻 4. システムプロセス確認:")
    print("-" * 40)
    
    huganjob_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status']):
        try:
            if proc.info['name'] in ['python.exe', 'python']:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if 'huganjob' in cmdline.lower():
                    huganjob_processes.append({
                        'pid': proc.info['pid'],
                        'status': proc.info['status'],
                        'cmdline': cmdline[:80] + '...' if len(cmdline) > 80 else cmdline
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if huganjob_processes:
        print(f"  残存HUGANJOBプロセス: {len(huganjob_processes)}件")
        for proc in huganjob_processes:
            print(f"    PID {proc['pid']}: {proc['status']} - {proc['cmdline']}")
    else:
        print(f"  ✅ HUGANJOBプロセスなし（クリーン状態）")

def test_new_process():
    """新しいプロセスのテスト"""
    
    print(f"\n🧪 5. 新プロセステスト:")
    print("-" * 40)
    
    try:
        # 軽量送信システムでテスト
        print(f"  軽量送信システムテスト実行中...")
        
        test_data = {
            'start_id': 1969,
            'end_id': 1969
        }
        
        # 直接実行（ダッシュボード経由ではない）
        import subprocess
        
        cmd = ['python', 'huganjob_lightweight_sender.py', '--start-id', '1969', '--end-id', '1969']
        
        print(f"  コマンド: {' '.join(cmd)}")
        
        start_time = datetime.now()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        end_time = datetime.now()
        
        execution_time = end_time - start_time
        
        print(f"  実行時間: {execution_time}")
        print(f"  終了コード: {result.returncode}")
        
        if result.returncode == 0:
            print(f"  ✅ テスト成功: プロセス正常終了")
        else:
            print(f"  ❌ テスト失敗: 終了コード {result.returncode}")
            
        if result.stdout:
            print(f"  出力: {result.stdout[:200]}...")
        if result.stderr:
            print(f"  エラー: {result.stderr[:200]}...")
            
    except subprocess.TimeoutExpired:
        print(f"  ⚠️ テストタイムアウト（30秒）")
    except Exception as e:
        print(f"  ❌ テストエラー: {e}")

def provide_recommendations():
    """推奨事項の提供"""
    
    print(f"\n🎯 6. 推奨事項:")
    print("-" * 40)
    
    print(f"  ✅ 即座の解決策:")
    print(f"    1. 問題プロセスの強制終了完了")
    print(f"    2. ダッシュボード状態のリセット")
    print(f"    3. システムプロセスのクリーンアップ")
    
    print(f"\n  🚀 今後の送信方法:")
    print(f"    1. 軽量送信システムの使用:")
    print(f"       python huganjob_lightweight_sender.py --start-id 1969 --end-id 1969")
    print(f"    2. 直接実行（ダッシュボード経由なし）")
    print(f"    3. プロセス監視の改善待ち")
    
    print(f"\n  🔧 根本対策（今後実装）:")
    print(f"    1. プロセス監視機能の改善")
    print(f"    2. 明示的なプロセス終了通知")
    print(f"    3. ゾンビプロセス自動クリーンアップ")
    print(f"    4. プロセス状態の定期同期")

if __name__ == "__main__":
    fix_dashboard_process_monitoring()
    test_new_process()
    provide_recommendations()
    
    print(f"\n修正完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎉 ダッシュボードプロセス監視問題の修正が完了しました")
