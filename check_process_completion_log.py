#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
プロセス完了ログ確認スクリプト

新しく実装されたプロセス監視強化システムが作成する
プロセス完了ログを確認するためのスクリプトです。
"""

import os
import json
from datetime import datetime

def check_completion_log():
    """プロセス完了ログを確認"""
    
    print("📋 プロセス完了ログ確認")
    print("=" * 50)
    
    log_file = 'logs/process_completion.log'
    
    if not os.path.exists(log_file):
        print("❌ プロセス完了ログファイルが見つかりません")
        print(f"   ファイルパス: {log_file}")
        return
    
    print(f"✅ プロセス完了ログファイル発見: {log_file}")
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"📊 ログエントリ数: {len(lines)}件")
        print()
        
        if lines:
            print("🔍 最新のプロセス完了記録:")
            print("-" * 30)
            
            # 最新の5件を表示
            for i, line in enumerate(lines[-5:], 1):
                try:
                    # タイムスタンプとJSONデータを分離
                    timestamp_str, json_str = line.strip().split(': ', 1)
                    completion_data = json.loads(json_str)
                    
                    print(f"{i}. {timestamp_str}")
                    print(f"   プロセスID: {completion_data.get('process_id', 'N/A')}")
                    print(f"   コマンド: {completion_data.get('command', 'N/A')}")
                    print(f"   ステータス: {completion_data.get('status', 'N/A')}")
                    print(f"   終了コード: {completion_data.get('return_code', 'N/A')}")
                    print(f"   実行時間: {completion_data.get('duration', 'N/A')}")
                    print()
                    
                except Exception as e:
                    print(f"   ❌ ログ解析エラー: {e}")
                    print(f"   生データ: {line.strip()}")
                    print()
        else:
            print("📝 ログエントリがありません")
    
    except Exception as e:
        print(f"❌ ログファイル読み取りエラー: {e}")

def main():
    """メイン実行関数"""
    check_completion_log()

if __name__ == "__main__":
    main()
