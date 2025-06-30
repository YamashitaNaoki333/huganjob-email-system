#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
現在実行中のプロセス状況を調査
"""

import requests
import json
import time
import os
import csv
from datetime import datetime

def check_current_process():
    """現在実行中のプロセス状況を調査"""
    
    base_url = "http://127.0.0.1:5002"
    
    print("🔍 現在実行中のプロセス状況調査")
    print("=" * 60)
    print(f"調査時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. 実行中プロセスを確認
        print("📋 1. 実行中プロセス一覧:")
        print("-" * 40)
        
        response = requests.get(f"{base_url}/api/get_processes", timeout=10)
        if response.status_code == 200:
            processes = response.json()
            if processes:
                for i, process in enumerate(processes):
                    print(f"  プロセス {i+1}:")
                    print(f"    PID: {process.get('pid', 'N/A')}")
                    print(f"    コマンド: {process.get('command', 'N/A')}")
                    print(f"    説明: {process.get('description', 'N/A')}")
                    print(f"    状況: {process.get('status', 'N/A')}")
                    print(f"    開始時刻: {process.get('start_time', 'N/A')}")
                    print(f"    実行時間: {process.get('duration', 'N/A')}")
                    print()
                    
                    # huganjob_unified_senderプロセスを特定
                    if 'huganjob_unified_sender' in process.get('command', ''):
                        print(f"  🎯 対象プロセス発見: huganjob_unified_sender")
                        print(f"    ID範囲: 1951-1970")
                        print(f"    実行時間: {process.get('duration', 'N/A')}")
                        print()
            else:
                print("  実行中プロセスなし")
        else:
            print(f"  エラー: HTTP {response.status_code}")
            
        # 2. プロセス履歴を確認
        print("📚 2. 最近のプロセス履歴:")
        print("-" * 40)
        
        response = requests.get(f"{base_url}/api/get_process_history?limit=10", timeout=10)
        if response.status_code == 200:
            history = response.json()
            if history:
                for i, process in enumerate(history[:5]):  # 最新5件
                    print(f"  履歴 {i+1}:")
                    print(f"    コマンド: {process.get('command', 'N/A')}")
                    print(f"    状況: {process.get('status', 'N/A')}")
                    print(f"    開始時刻: {process.get('start_time', 'N/A')}")
                    print(f"    終了時刻: {process.get('end_time', 'N/A')}")
                    print(f"    実行時間: {process.get('duration', 'N/A')}")
                    print()
            else:
                print("  履歴なし")
        else:
            print(f"  エラー: HTTP {response.status_code}")
            
        # 3. 送信結果ファイルの最新状況を確認
        print("📄 3. 送信結果ファイル確認:")
        print("-" * 40)
        
        # 送信履歴ファイル確認
        history_file = "huganjob_sending_history.json"
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                
            # 最新の送信記録を確認
            if history_data:
                latest_entries = sorted(history_data, key=lambda x: x.get('送信日時', ''), reverse=True)[:5]
                print(f"  最新送信記録 ({len(history_data)}件中、最新5件):")
                for entry in latest_entries:
                    print(f"    ID {entry.get('企業ID', 'N/A')}: {entry.get('企業名', 'N/A')}")
                    print(f"      送信日時: {entry.get('送信日時', 'N/A')}")
                    print(f"      送信結果: {entry.get('送信結果', 'N/A')}")
                    print()
            else:
                print("  送信履歴なし")
        else:
            print("  送信履歴ファイルが見つかりません")
            
        # 4. ID 1951-1970の範囲で送信済み企業を確認
        print("🎯 4. ID 1951-1970 送信状況:")
        print("-" * 40)
        
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                
            # ID 1951-1970の範囲で確認
            target_range = []
            for entry in history_data:
                company_id = entry.get('企業ID')
                if company_id and str(company_id).isdigit():
                    company_id = int(company_id)
                    if 1951 <= company_id <= 1970:
                        target_range.append(entry)
                        
            if target_range:
                print(f"  送信済み: {len(target_range)}件")
                for entry in sorted(target_range, key=lambda x: int(x.get('企業ID', 0))):
                    print(f"    ID {entry.get('企業ID')}: {entry.get('企業名', 'N/A')[:30]} - {entry.get('送信結果', 'N/A')}")
            else:
                print("  ID 1951-1970の範囲で送信記録なし")
                
        # 5. ログファイル確認
        print("📝 5. ログファイル確認:")
        print("-" * 40)
        
        log_files = [
            "logs/huganjob_unified_sender.log",
            "logs/huganjob_email_sender.log"
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                print(f"  {log_file}: 存在")
                # ファイルサイズ確認
                size = os.path.getsize(log_file)
                print(f"    サイズ: {size:,} bytes")
                
                # 最新の数行を確認
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if lines:
                            print(f"    最新行: {lines[-1].strip()}")
                except Exception as e:
                    print(f"    読み込みエラー: {e}")
            else:
                print(f"  {log_file}: 見つかりません")
                
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_current_process()
