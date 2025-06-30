#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ハングしているプロセスのデバッグ
"""

import requests
import json
import os
import time
import psutil
from datetime import datetime

def debug_hanging_process():
    """ハングしているプロセスの詳細調査"""
    
    print("🔍 ハングプロセス詳細調査")
    print("=" * 60)
    print(f"調査時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. ダッシュボードプロセス情報
        print("📋 1. ダッシュボードプロセス情報:")
        print("-" * 40)
        
        try:
            response = requests.get("http://127.0.0.1:5002/api/get_processes", timeout=5)
            if response.status_code == 200:
                processes = response.json()
                
                for process in processes:
                    if "1967" in process.get('args', ''):
                        print(f"  🎯 対象プロセス:")
                        print(f"    PID: {process.get('id', 'N/A')}")
                        print(f"    コマンド: {process.get('command', 'N/A')}")
                        print(f"    引数: {process.get('args', 'N/A')}")
                        print(f"    状況: {process.get('status', 'N/A')}")
                        print(f"    開始時刻: {process.get('start_time', 'N/A')}")
                        print(f"    実行時間: {process.get('duration', 'N/A')}")
                        
                        # PIDを取得
                        pid = process.get('id')
                        if pid and pid != 'N/A':
                            return check_system_process(pid)
                        break
                else:
                    print("  ❌ ID 1967のプロセスが見つかりません")
            else:
                print(f"  ❌ API エラー: {response.status_code}")
        except Exception as e:
            print(f"  ❌ API接続エラー: {e}")
        
        # 2. システムプロセス確認
        print("\n💻 2. システムプロセス確認:")
        print("-" * 40)
        
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'status']):
            try:
                if proc.info['name'] == 'python.exe' or proc.info['name'] == 'python':
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if 'huganjob_unified_sender' in cmdline and '1967' in cmdline:
                        python_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if python_processes:
            for proc_info in python_processes:
                print(f"  🐍 Python プロセス発見:")
                print(f"    PID: {proc_info['pid']}")
                print(f"    コマンドライン: {' '.join(proc_info['cmdline'])}")
                print(f"    状況: {proc_info['status']}")
                print(f"    作成時刻: {datetime.fromtimestamp(proc_info['create_time']).strftime('%Y-%m-%d %H:%M:%S')}")
                
                return analyze_process_details(proc_info['pid'])
        else:
            print("  ❌ 該当するPythonプロセスが見つかりません")
        
    except Exception as e:
        print(f"❌ 調査エラー: {e}")

def check_system_process(pid):
    """システムプロセスの詳細確認"""
    
    print(f"\n🔬 3. プロセス詳細分析 (PID: {pid}):")
    print("-" * 40)
    
    try:
        if isinstance(pid, str):
            pid = int(pid)
        
        proc = psutil.Process(pid)
        
        print(f"  プロセス名: {proc.name()}")
        print(f"  状況: {proc.status()}")
        print(f"  CPU使用率: {proc.cpu_percent()}%")
        print(f"  メモリ使用量: {proc.memory_info().rss / 1024 / 1024:.1f} MB")
        print(f"  作成時刻: {datetime.fromtimestamp(proc.create_time()).strftime('%Y-%m-%d %H:%M:%S')}")
        
        # スレッド情報
        threads = proc.threads()
        print(f"  スレッド数: {len(threads)}")
        
        # ファイルハンドル
        try:
            open_files = proc.open_files()
            print(f"  開いているファイル数: {len(open_files)}")
            
            # ログファイルが開かれているかチェック
            for file_info in open_files:
                if 'log' in file_info.path.lower():
                    print(f"    ログファイル: {file_info.path}")
        except psutil.AccessDenied:
            print("  ファイル情報: アクセス拒否")
        
        # ネットワーク接続
        try:
            connections = proc.connections()
            print(f"  ネットワーク接続数: {len(connections)}")
            
            for conn in connections:
                if conn.status == 'ESTABLISHED':
                    print(f"    接続: {conn.laddr} -> {conn.raddr} ({conn.status})")
        except psutil.AccessDenied:
            print("  ネットワーク情報: アクセス拒否")
        
        return analyze_process_details(pid)
        
    except psutil.NoSuchProcess:
        print(f"  ❌ プロセス {pid} が見つかりません")
        return False
    except Exception as e:
        print(f"  ❌ プロセス分析エラー: {e}")
        return False

def analyze_process_details(pid):
    """プロセスの詳細分析"""
    
    print(f"\n🧪 4. ハング原因分析:")
    print("-" * 40)
    
    try:
        proc = psutil.Process(pid)
        
        # CPU使用率チェック
        cpu_percent = proc.cpu_percent(interval=1)
        print(f"  CPU使用率: {cpu_percent}%")
        
        if cpu_percent < 0.1:
            print("  💡 CPU使用率が低い → プロセスが待機状態の可能性")
            print("  🔍 可能な原因:")
            print("    - ファイルI/O待機")
            print("    - ネットワーク待機")
            print("    - ロック待機")
            print("    - sleep/time.sleep()実行中")
        elif cpu_percent > 50:
            print("  ⚠️ CPU使用率が高い → 無限ループの可能性")
        else:
            print("  ✅ CPU使用率は正常範囲")
        
        # メモリ使用量チェック
        memory_mb = proc.memory_info().rss / 1024 / 1024
        print(f"  メモリ使用量: {memory_mb:.1f} MB")
        
        if memory_mb > 500:
            print("  ⚠️ メモリ使用量が多い → メモリリークの可能性")
        
        # プロセス状況分析
        status = proc.status()
        print(f"  プロセス状況: {status}")
        
        if status == 'sleeping':
            print("  💤 プロセスがスリープ中")
            print("  💡 推定原因:")
            print("    - time.sleep()実行中")
            print("    - I/O待機")
            print("    - ネットワーク応答待機")
        elif status == 'running':
            print("  🏃 プロセスが実行中")
        elif status == 'zombie':
            print("  👻 ゾンビプロセス")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 分析エラー: {e}")
        return False

def check_log_files():
    """ログファイルの確認"""
    
    print(f"\n📄 5. ログファイル確認:")
    print("-" * 40)
    
    log_files = [
        "logs/huganjob_unified_sender.log",
        "logs/huganjob_email_sender.log",
        "logs/derivative_dashboard/derivative_dashboard.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"  📁 {log_file}:")
            try:
                # ファイルサイズ
                size = os.path.getsize(log_file)
                print(f"    サイズ: {size:,} bytes")
                
                # 最新の数行
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"    最新行: {lines[-1].strip()}")
                        
                        # ID 1967関連のログを検索
                        for line in lines[-20:]:
                            if '1967' in line:
                                print(f"    ID 1967関連: {line.strip()}")
                                
            except Exception as e:
                print(f"    読み込みエラー: {e}")
        else:
            print(f"  ❌ {log_file}: 見つかりません")

def recommend_actions():
    """推奨アクション"""
    
    print(f"\n🎯 6. 推奨アクション:")
    print("-" * 40)
    
    print("  🛑 即座の対応:")
    print("    1. プロセス強制終了")
    print("    2. ダッシュボードでプロセス停止")
    print("    3. Ctrl+C でプロセス中断")
    print()
    print("  🔄 再実行:")
    print("    python huganjob_unified_sender.py --start-id 1967 --end-id 1967")
    print()
    print("  🧪 デバッグ:")
    print("    1. ログファイル確認")
    print("    2. バウンスメール処理確認")
    print("    3. ファイルロック状況確認")

if __name__ == "__main__":
    debug_hanging_process()
    check_log_files()
    recommend_actions()
    
    print(f"\n調査完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
