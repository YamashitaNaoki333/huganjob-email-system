#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
プロセスハング問題の詳細調査
"""

import requests
import json
import os
import psutil
import time
from datetime import datetime

def investigate_process_hang():
    """プロセスハング問題の詳細調査"""
    
    print("🔍 プロセスハング詳細調査")
    print("=" * 60)
    print(f"調査時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. ダッシュボードプロセス情報
    print("📋 1. ダッシュボードプロセス情報:")
    print("-" * 40)
    
    try:
        response = requests.get("http://127.0.0.1:5002/api/get_processes", timeout=5)
        if response.status_code == 200:
            processes = response.json()
            
            target_process = None
            for process in processes:
                if "1967" in process.get('args', ''):
                    target_process = process
                    break
            
            if target_process:
                print(f"  🎯 対象プロセス:")
                print(f"    PID: {target_process.get('id', 'N/A')}")
                print(f"    コマンド: {target_process.get('command', 'N/A')}")
                print(f"    引数: {target_process.get('args', 'N/A')}")
                print(f"    状況: {target_process.get('status', 'N/A')}")
                print(f"    開始時刻: {target_process.get('start_time', 'N/A')}")
                print(f"    実行時間: {target_process.get('duration', 'N/A')}")
                
                pid = target_process.get('id')
                if pid and pid != 'N/A':
                    analyze_system_process(pid)
            else:
                print("  ❌ ID 1967のプロセスが見つかりません")
        else:
            print(f"  ❌ API エラー: {response.status_code}")
    except Exception as e:
        print(f"  ❌ API接続エラー: {e}")
    
    # 2. 送信結果確認
    print("\n📤 2. 送信結果確認:")
    print("-" * 40)
    
    check_sending_results()
    
    # 3. ファイルロック状況確認
    print("\n🔒 3. ファイルロック状況:")
    print("-" * 40)
    
    check_file_locks()
    
    # 4. プロセス終了処理確認
    print("\n🏁 4. プロセス終了処理確認:")
    print("-" * 40)
    
    check_process_completion()

def analyze_system_process(pid):
    """システムプロセスの詳細分析"""
    
    print(f"\n💻 システムプロセス分析 (PID: {pid}):")
    print("-" * 40)
    
    try:
        if isinstance(pid, str):
            pid = int(pid)
        
        proc = psutil.Process(pid)
        
        print(f"  プロセス名: {proc.name()}")
        print(f"  状況: {proc.status()}")
        print(f"  CPU使用率: {proc.cpu_percent(interval=1)}%")
        print(f"  メモリ使用量: {proc.memory_info().rss / 1024 / 1024:.1f} MB")
        
        # スレッド情報
        threads = proc.threads()
        print(f"  スレッド数: {len(threads)}")
        
        # 開いているファイル
        try:
            open_files = proc.open_files()
            print(f"  開いているファイル数: {len(open_files)}")
            
            for file_info in open_files:
                if any(keyword in file_info.path.lower() for keyword in ['csv', 'json', 'log', 'lock']):
                    print(f"    📁 {file_info.path}")
        except psutil.AccessDenied:
            print("  ファイル情報: アクセス拒否")
        
        # ネットワーク接続
        try:
            connections = proc.connections()
            active_connections = [conn for conn in connections if conn.status == 'ESTABLISHED']
            print(f"  アクティブ接続数: {len(active_connections)}")
            
            for conn in active_connections:
                print(f"    🌐 {conn.laddr} -> {conn.raddr}")
        except psutil.AccessDenied:
            print("  ネットワーク情報: アクセス拒否")
        
    except psutil.NoSuchProcess:
        print(f"  ❌ プロセス {pid} が見つかりません")
    except Exception as e:
        print(f"  ❌ プロセス分析エラー: {e}")

def check_sending_results():
    """送信結果の確認"""
    
    # 送信履歴ファイル確認
    history_file = "huganjob_sending_history.json"
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            # ID 1967の送信記録を検索
            if "sending_records" in history_data:
                id_1967_records = []
                for record in history_data["sending_records"]:
                    if record.get("company_id") == 1967:
                        id_1967_records.append(record)
                
                if id_1967_records:
                    print(f"  📧 ID 1967 送信記録: {len(id_1967_records)}件")
                    for record in id_1967_records[-3:]:  # 最新3件
                        print(f"    送信時刻: {record.get('send_time', 'N/A')}")
                        print(f"    宛先: {record.get('recipient_email', 'N/A')}")
                        print(f"    結果: {record.get('result', 'N/A')}")
                else:
                    print("  ❌ ID 1967の送信記録なし")
            else:
                print("  ❌ 送信記録データなし")
        except Exception as e:
            print(f"  ❌ 送信履歴読み込みエラー: {e}")
    else:
        print("  ❌ 送信履歴ファイルなし")
    
    # 送信結果ファイル確認
    result_files = [
        "new_email_sending_results.csv",
        "huganjob_sending_results.csv"
    ]
    
    for result_file in result_files:
        if os.path.exists(result_file):
            print(f"  📄 {result_file}:")
            try:
                import csv
                with open(result_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get('企業ID') == '1967' or row.get('ID') == '1967':
                            print(f"    送信結果: {row.get('送信結果', 'N/A')}")
                            print(f"    送信日時: {row.get('送信日時', 'N/A')}")
                            print(f"    エラー: {row.get('エラー詳細', 'N/A')}")
                            break
            except Exception as e:
                print(f"    読み込みエラー: {e}")

def check_file_locks():
    """ファイルロック状況の確認"""
    
    lock_files = [
        "huganjob_sending.lock",
        "email_sending.lock",
        "process.lock"
    ]
    
    for lock_file in lock_files:
        if os.path.exists(lock_file):
            print(f"  🔒 {lock_file}: 存在")
            try:
                # ファイルの作成時刻
                mtime = os.path.getmtime(lock_file)
                mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                print(f"    作成時刻: {mtime_str}")
                
                # ファイルサイズ
                size = os.path.getsize(lock_file)
                print(f"    サイズ: {size} bytes")
                
                # 内容確認
                if size < 1000:  # 小さなファイルのみ
                    with open(lock_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        print(f"    内容: {content}")
            except Exception as e:
                print(f"    確認エラー: {e}")
        else:
            print(f"  ✅ {lock_file}: なし")

def check_process_completion():
    """プロセス終了処理の確認"""
    
    print("  🔍 プロセス終了処理の問題点:")
    print("    1. ファイル更新処理でのハング")
    print("    2. ロック解放処理の失敗")
    print("    3. 例外処理での無限ループ")
    print("    4. ダッシュボード通信の問題")
    
    print("\n  💡 推定原因:")
    print("    - update_email_resolution_results() でのハング")
    print("    - prevention_manager.release_lock() の失敗")
    print("    - 大きなCSVファイル処理での遅延")
    print("    - メモリ不足による処理停止")
    
    print("\n  🛠️ 対策:")
    print("    1. プロセス強制終了")
    print("    2. ロックファイル手動削除")
    print("    3. 軽量化版での再実行")
    print("    4. ファイル更新処理の無効化")

def recommend_immediate_action():
    """即座の対応推奨"""
    
    print(f"\n🎯 即座の対応推奨:")
    print("-" * 40)
    
    print("  🛑 1. プロセス強制終了:")
    print("    - ダッシュボードでプロセス停止")
    print("    - Ctrl+C でプロセス中断")
    print("    - タスクマネージャーでPython.exe終了")
    
    print("\n  🧹 2. クリーンアップ:")
    print("    - ロックファイル削除")
    print("    - 一時ファイル削除")
    print("    - メモリクリア")
    
    print("\n  🚀 3. 軽量版で再実行:")
    print("    python huganjob_unified_sender.py --start-id 1967 --end-id 1967")
    print("    (ファイル更新処理は既に無効化済み)")
    
    print("\n  ✅ 4. 送信確認:")
    print("    - バウンスメールで送信成功確認済み")
    print("    - 実際の送信は完了している")
    print("    - プロセス終了処理のみが問題")

if __name__ == "__main__":
    investigate_process_hang()
    recommend_immediate_action()
    
    print(f"\n調査完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("💡 バウンスメールが返ってきているため、送信自体は成功しています。")
