#!/usr/bin/env python3
"""
HUGANJOB 進捗確認スクリプト
現在の送信状況とシステム状態を確認
"""

import pandas as pd
import json
from datetime import datetime
import os

def check_email_progress():
    """メール送信進捗の確認"""
    print("📧 メール送信進捗確認")
    print("=" * 50)
    
    try:
        # CSVファイル読み込み
        df = pd.read_csv('data/new_input_test.csv')
        total_companies = len(df)
        
        print(f"📊 総企業数: {total_companies:,}社")
        
        # 送信状況の集計
        if '送信ステータス' in df.columns:
            sent_count = len(df[df['送信ステータス'] == '送信済み'])
            print(f"✅ 送信済み: {sent_count:,}社")
            print(f"📈 送信進捗: {sent_count/total_companies*100:.1f}%")
            
            # 最新の送信ID確認
            sent_df = df[df['送信ステータス'] == '送信済み']
            if not sent_df.empty:
                latest_id = sent_df['ID'].max()
                print(f"🎯 最新送信ID: {latest_id}")
                
                # 最新送信の詳細
                latest_row = df[df['ID'] == latest_id].iloc[0]
                print(f"🏢 最新送信企業: {latest_row['企業名']}")
                if '送信日時' in df.columns:
                    print(f"⏰ 最新送信時刻: {latest_row['送信日時']}")
        
        # バウンス状況
        if 'バウンス状態' in df.columns:
            bounce_count = len(df[df['バウンス状態'].notna() & (df['バウンス状態'] != '')])
            print(f"⚠️ バウンス企業: {bounce_count:,}社")
        
        # 配信停止状況
        if '配信停止状態' in df.columns:
            unsubscribe_count = len(df[df['配信停止状態'].notna() & (df['配信停止状態'] != '')])
            print(f"🚫 配信停止企業: {unsubscribe_count:,}社")
            
    except Exception as e:
        print(f"❌ エラー: {e}")

def check_git_status():
    """Git状況の確認"""
    print("\n🔧 Git状況確認")
    print("=" * 50)
    
    try:
        import subprocess
        
        # Git初期化確認
        if os.path.exists('.git'):
            print("✅ Gitリポジトリ: 初期化済み")
            
            # ブランチ確認
            result = subprocess.run(['git', 'branch'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"🌿 現在のブランチ: {result.stdout.strip()}")
            
            # リモート確認
            result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                print("🌐 リモートリポジトリ: 設定済み")
                for line in result.stdout.strip().split('\n'):
                    print(f"   {line}")
            else:
                print("⚠️ リモートリポジトリ: 未設定")
            
            # 状況確認
            result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
            if result.returncode == 0:
                if result.stdout.strip():
                    print("📝 変更されたファイル:")
                    for line in result.stdout.strip().split('\n'):
                        print(f"   {line}")
                else:
                    print("✅ 作業ディレクトリ: クリーン")
        else:
            print("❌ Gitリポジトリ: 未初期化")
            
    except Exception as e:
        print(f"❌ Git確認エラー: {e}")

def check_dashboard_status():
    """ダッシュボード状況確認"""
    print("\n📊 ダッシュボード状況確認")
    print("=" * 50)
    
    try:
        # PIDファイル確認
        if os.path.exists('new_dashboard.pid'):
            with open('new_dashboard.pid', 'r') as f:
                pid_info = json.load(f)
            
            print("✅ ダッシュボード: 実行中")
            print(f"🔗 URL: {pid_info.get('url', 'http://127.0.0.1:5002/')}")
            print(f"🆔 PID: {pid_info.get('pid', 'N/A')}")
            print(f"⏰ 開始時刻: {pid_info.get('start_time', 'N/A')}")
        else:
            print("⚠️ ダッシュボード: 停止中")
            
    except Exception as e:
        print(f"❌ ダッシュボード確認エラー: {e}")

def check_system_files():
    """重要システムファイルの確認"""
    print("\n📁 重要ファイル確認")
    print("=" * 50)
    
    important_files = [
        ('data/new_input_test.csv', '企業データベース'),
        ('config/huganjob_email_config.ini', 'メール設定'),
        ('huganjob_unified_sender.py', '統合送信システム'),
        ('dashboard/derivative_dashboard.py', 'ダッシュボード'),
        ('.gitignore', 'Git除外設定'),
        ('README.md', 'プロジェクト説明')
    ]
    
    for file_path, description in important_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {description}: {file_path} ({size:,} bytes)")
        else:
            print(f"❌ {description}: {file_path} (存在しません)")

def main():
    """メイン処理"""
    print("🔍 HUGANJOB システム進捗確認")
    print("=" * 60)
    print(f"📅 確認日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 作業ディレクトリ: {os.getcwd()}")
    
    # 各種確認実行
    check_email_progress()
    check_git_status()
    check_dashboard_status()
    check_system_files()
    
    print("\n🎯 次のアクション推奨")
    print("=" * 50)
    print("1. Git連携完了: リモートプッシュ実行")
    print("2. メール送信継続: 現在のプロセス監視")
    print("3. ダッシュボード確認: http://127.0.0.1:5002/")
    
    print("\n✅ 進捗確認完了")

if __name__ == "__main__":
    main()
