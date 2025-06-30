#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ダッシュボードプロセス状況確認
実行中プロセスと履歴の詳細確認
"""

import requests
import json
from datetime import datetime

def check_dashboard_processes():
    """ダッシュボードのプロセス状況を確認"""
    
    base_url = "http://127.0.0.1:5002"
    
    print("📊 ダッシュボードプロセス状況確認")
    print("=" * 60)
    
    try:
        # 実行中プロセスを確認
        print("\n🔄 実行中プロセス:")
        running_response = requests.get(f"{base_url}/api/get_processes", timeout=10)
        if running_response.status_code == 200:
            running_processes = running_response.json()
            if running_processes:
                for i, process in enumerate(running_processes):
                    print(f"  {i+1}. PID: {process.get('pid', 'N/A')}")
                    print(f"     コマンド: {process.get('command', 'N/A')}")
                    print(f"     説明: {process.get('description', 'N/A')}")
                    print(f"     状況: {process.get('status', 'N/A')}")
                    print(f"     開始時刻: {process.get('start_time', 'N/A')}")
                    if process.get('duration'):
                        print(f"     実行時間: {process.get('duration')}")
                    print()
            else:
                print("  実行中プロセスなし")
        else:
            print(f"  エラー: {running_response.status_code}")
        
        # プロセス履歴を確認
        print("\n📋 プロセス履歴（最新10件）:")
        history_response = requests.get(f"{base_url}/api/get_process_history?limit=10", timeout=10)
        if history_response.status_code == 200:
            history = history_response.json()
            if history:
                for i, process in enumerate(history):
                    print(f"  {i+1}. PID: {process.get('pid', 'N/A')}")
                    print(f"     コマンド: {process.get('command', 'N/A')}")
                    print(f"     状況: {process.get('status', 'N/A')}")
                    print(f"     終了コード: {process.get('return_code', 'N/A')}")
                    print(f"     開始時刻: {process.get('start_time', 'N/A')}")
                    print(f"     終了時刻: {process.get('end_time', 'N/A')}")
                    if process.get('duration'):
                        print(f"     実行時間: {process.get('duration')}")
                    if process.get('error'):
                        print(f"     エラー: {process.get('error')}")
                    print()
            else:
                print("  プロセス履歴なし")
        else:
            print(f"  エラー: {history_response.status_code}")
            
        # huganjob_text_only_sender関連のプロセスを特定
        print("\n🎯 huganjob_text_only_sender関連プロセス:")
        found_target = False
        
        # 実行中プロセスから検索
        if running_response.status_code == 200:
            running_processes = running_response.json()
            for process in running_processes:
                if 'huganjob_text_only_sender' in process.get('command', ''):
                    print(f"  【実行中】PID: {process.get('pid')}")
                    print(f"    コマンド: {process.get('command')}")
                    print(f"    状況: {process.get('status')}")
                    print(f"    実行時間: {process.get('duration', 'N/A')}")
                    found_target = True
        
        # 履歴から検索
        if history_response.status_code == 200:
            history = history_response.json()
            for process in history:
                if 'huganjob_text_only_sender' in process.get('command', ''):
                    print(f"  【履歴】PID: {process.get('pid')}")
                    print(f"    コマンド: {process.get('command')}")
                    print(f"    状況: {process.get('status')}")
                    print(f"    終了コード: {process.get('return_code', 'N/A')}")
                    if process.get('duration'):
                        print(f"    実行時間: {process.get('duration')}")
                    found_target = True
        
        if not found_target:
            print("  huganjob_text_only_sender関連プロセスが見つかりません")
            
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_dashboard_processes()
