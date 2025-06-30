#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡単なプロセス状況確認
"""

import requests
import json
from datetime import datetime

def simple_check():
    """簡単なプロセス状況確認"""
    
    print("🔍 プロセス状況確認")
    print("=" * 40)
    print(f"確認時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 実行中プロセス確認
        response = requests.get("http://127.0.0.1:5002/api/get_processes", timeout=5)
        if response.status_code == 200:
            processes = response.json()
            print(f"📋 実行中プロセス: {len(processes)}件")
            
            for i, process in enumerate(processes):
                print(f"  {i+1}. {process.get('command', 'N/A')}")
                print(f"     PID: {process.get('pid', 'N/A')}")
                print(f"     状況: {process.get('status', 'N/A')}")
                print(f"     実行時間: {process.get('duration', 'N/A')}")
                print()
        else:
            print(f"❌ API エラー: {response.status_code}")
            
        # 送信履歴の最新確認
        print("📄 最新送信記録:")
        print("-" * 30)
        
        try:
            with open("huganjob_sending_history.json", 'r', encoding='utf-8') as f:
                history = json.load(f)
                
            if history and "sending_records" in history:
                records = history["sending_records"]
                latest = records[-5:]  # 最新5件
                
                for record in latest:
                    print(f"  ID {record.get('company_id')}: {record.get('company_name', 'N/A')[:30]}")
                    print(f"    送信時刻: {record.get('send_time', 'N/A')}")
                    print()
            else:
                print("  送信記録なし")
                
        except Exception as e:
            print(f"  ファイル読み込みエラー: {e}")
            
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    simple_check()
