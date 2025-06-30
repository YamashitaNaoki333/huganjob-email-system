#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ID 1965プロセス進行状況確認
"""

import requests
import json
import os
import time
from datetime import datetime

def check_id_1965_progress():
    """ID 1965プロセスの詳細確認"""
    
    print("🔍 ID 1965 プロセス進行状況確認")
    print("=" * 60)
    print(f"確認時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. ダッシュボードからプロセス情報取得
        print("📋 1. 実行中プロセス確認:")
        print("-" * 40)
        
        response = requests.get("http://127.0.0.1:5002/api/get_processes", timeout=5)
        if response.status_code == 200:
            processes = response.json()
            
            target_process = None
            for process in processes:
                if "1965" in process.get('args', ''):
                    target_process = process
                    break
            
            if target_process:
                print(f"  🎯 対象プロセス発見:")
                print(f"    PID: {target_process.get('id', 'N/A')}")
                print(f"    コマンド: {target_process.get('command', 'N/A')}")
                print(f"    引数: {target_process.get('args', 'N/A')}")
                print(f"    状況: {target_process.get('status', 'N/A')}")
                print(f"    開始時刻: {target_process.get('start_time', 'N/A')}")
                print(f"    実行時間: {target_process.get('duration', 'N/A')}")
                print()
            else:
                print("  ❌ ID 1965のプロセスが見つかりません")
                return
        else:
            print(f"  ❌ API エラー: {response.status_code}")
            return
        
        # 2. ID 1965の企業情報確認
        print("🏢 2. ID 1965 企業情報:")
        print("-" * 40)
        
        # CSVから企業情報を読み込み
        import csv
        csv_file = "data/new_input_test.csv"
        if os.path.exists(csv_file):
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('ID') == '1965':
                        print(f"  企業名: {row.get('企業名', 'N/A')}")
                        print(f"  ホームページ: {row.get('企業ホームページ', 'N/A')}")
                        print(f"  メールアドレス: {row.get('採用担当メールアドレス', 'N/A')}")
                        print(f"  募集職種: {row.get('募集職種', 'N/A')}")
                        print(f"  バウンス状態: {row.get('バウンス', 'N/A')}")
                        break
            print()
        
        # 3. メール抽出結果確認
        print("📧 3. メール抽出結果:")
        print("-" * 40)
        
        extraction_file = "huganjob_email_resolution_results.csv"
        if os.path.exists(extraction_file):
            with open(extraction_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('企業ID') == '1965':
                        print(f"  抽出メール: {row.get('抽出メールアドレス', 'N/A')}")
                        print(f"  抽出方法: {row.get('抽出方法', 'N/A')}")
                        print(f"  抽出日時: {row.get('抽出日時', 'N/A')}")
                        break
            print()
        
        # 4. 送信履歴確認
        print("📤 4. 送信履歴確認:")
        print("-" * 40)
        
        history_file = "huganjob_sending_history.json"
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                
            # ID 1965の送信記録を検索
            found_records = []
            if "sending_records" in history_data:
                for record in history_data["sending_records"]:
                    if record.get("company_id") == 1965:
                        found_records.append(record)
            
            if found_records:
                print(f"  送信記録: {len(found_records)}件")
                for i, record in enumerate(found_records[-3:]):  # 最新3件
                    print(f"    {i+1}. 送信時刻: {record.get('send_time', 'N/A')}")
                    print(f"       宛先: {record.get('recipient_email', 'N/A')}")
                    print(f"       結果: {record.get('result', 'N/A')}")
            else:
                print("  送信記録なし")
            print()
        
        # 5. 現在の送信結果ファイル確認
        print("📄 5. 最新送信結果:")
        print("-" * 40)
        
        result_files = [
            "new_email_sending_results.csv",
            "huganjob_sending_results.csv"
        ]
        
        for result_file in result_files:
            if os.path.exists(result_file):
                print(f"  📁 {result_file}:")
                with open(result_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get('企業ID') == '1965' or row.get('ID') == '1965':
                            print(f"    送信結果: {row.get('送信結果', 'N/A')}")
                            print(f"    送信日時: {row.get('送信日時', 'N/A')}")
                            print(f"    エラー: {row.get('エラー詳細', 'N/A')}")
                            break
                print()
        
        # 6. プロセスが長時間実行中の場合の分析
        print("⏱️ 6. 実行時間分析:")
        print("-" * 40)
        
        if target_process:
            duration_str = target_process.get('duration', '0:00:00')
            try:
                # 実行時間を秒に変換
                time_parts = duration_str.split(':')
                if len(time_parts) == 3:
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])
                    seconds = int(time_parts[2])
                    total_seconds = hours * 3600 + minutes * 60 + seconds
                    
                    print(f"  実行時間: {duration_str} ({total_seconds}秒)")
                    
                    if total_seconds > 120:  # 2分以上
                        print("  ⚠️ 実行時間が長すぎます")
                        print("  💡 可能な原因:")
                        print("    - DNS解決の遅延")
                        print("    - SMTP接続の問題")
                        print("    - プロセスのハング")
                        print("    - ネットワークの問題")
                        print()
                        print("  🛠️ 推奨対応:")
                        print("    1. プロセスを停止")
                        print("    2. --skip-dns オプションで再実行")
                        print("    3. ログファイルの確認")
                    elif total_seconds > 60:  # 1分以上
                        print("  ⚠️ 実行時間がやや長めです")
                        print("  💡 DNS解決に時間がかかっている可能性があります")
                    else:
                        print("  ✅ 実行時間は正常範囲内です")
                        
            except Exception as e:
                print(f"  ❌ 実行時間解析エラー: {e}")
        
        # 7. 推奨アクション
        print("\n🎯 7. 推奨アクション:")
        print("-" * 40)
        
        if target_process and target_process.get('status') == 'running':
            duration_str = target_process.get('duration', '0:00:00')
            if ':' in duration_str:
                time_parts = duration_str.split(':')
                if len(time_parts) >= 2:
                    minutes = int(time_parts[1])
                    if minutes >= 2:
                        print("  🛑 プロセス停止を推奨:")
                        print("    - 実行時間が異常に長い")
                        print("    - DNS解決問題の可能性")
                        print()
                        print("  🔄 再実行コマンド:")
                        print("    python huganjob_unified_sender.py --start-id 1965 --end-id 1965 --skip-dns")
                    else:
                        print("  ⏳ もう少し待機:")
                        print("    - 正常な処理時間内")
                        print("    - 1-2分で完了予定")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_id_1965_progress()
