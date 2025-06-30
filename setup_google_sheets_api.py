#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Sheets API設定ヘルパー
HUGANJOB配信停止監視システム用

作成日時: 2025年06月24日
目的: Google Sheets APIの設定を簡単に行うためのヘルパースクリプト
"""

import os
import json
import webbrowser
from typing import Dict, Optional

def print_setup_instructions():
    """設定手順を表示"""
    print("=" * 80)
    print("🔧 HUGANJOB Google Sheets API 設定ガイド")
    print("=" * 80)
    print()
    print("📋 設定手順:")
    print("1. Google Cloud Console でプロジェクトを作成")
    print("2. Google Sheets API を有効化")
    print("3. サービスアカウントを作成")
    print("4. 認証情報（JSON）をダウンロード")
    print("5. スプレッドシートにサービスアカウントの編集権限を付与")
    print()
    print("🌐 必要なURL:")
    print("- Google Cloud Console: https://console.cloud.google.com/")
    print("- Google Sheets API: https://console.cloud.google.com/apis/library/sheets.googleapis.com")
    print()

def create_project_setup_guide():
    """プロジェクト設定ガイドを作成"""
    guide_content = """# Google Cloud Console 設定ガイド

## 1. プロジェクト作成
1. Google Cloud Console (https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成
   - プロジェクト名: huganjob-sheets-api (任意)
   - 組織: 個人アカウントの場合は「組織なし」

## 2. Google Sheets API有効化
1. APIとサービス > ライブラリ に移動
2. "Google Sheets API" を検索
3. Google Sheets API を選択して「有効にする」をクリック

## 3. サービスアカウント作成
1. APIとサービス > 認証情報 に移動
2. 「認証情報を作成」> 「サービスアカウント」を選択
3. サービスアカウント詳細:
   - サービスアカウント名: huganjob-sheets-monitor
   - サービスアカウントID: huganjob-sheets-monitor
   - 説明: HUGANJOB配信停止監視システム用
4. 「作成して続行」をクリック
5. ロールは設定不要（「完了」をクリック）

## 4. 認証情報ダウンロード
1. 作成したサービスアカウントをクリック
2. 「キー」タブに移動
3. 「キーを追加」> 「新しいキーを作成」
4. キーのタイプ: JSON を選択
5. 「作成」をクリックしてJSONファイルをダウンロード

## 5. 認証情報ファイル配置
1. ダウンロードしたJSONファイルを以下に配置:
   config/google_sheets_credentials.json
2. ファイル名を正確に合わせてください

## 6. スプレッドシート権限設定
1. 対象スプレッドシートを開く
2. 「共有」ボタンをクリック
3. サービスアカウントのメールアドレスを追加
   - メールアドレス: huganjob-sheets-monitor@[プロジェクトID].iam.gserviceaccount.com
   - 権限: 閲覧者（読み取り専用で十分）
4. 「送信」をクリック

## 7. 必要なPythonライブラリインストール
```bash
pip install google-api-python-client google-auth
```

## 8. 動作テスト
```bash
python huganjob_google_sheets_monitor.py --test
```
"""
    
    os.makedirs('docs', exist_ok=True)
    with open('docs/google_sheets_api_setup.md', 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print("📝 設定ガイドを作成しました: docs/google_sheets_api_setup.md")

def check_credentials_file() -> bool:
    """認証情報ファイルの存在確認"""
    credentials_path = 'config/google_sheets_credentials.json'
    
    if os.path.exists(credentials_path):
        print(f"✅ 認証情報ファイルが見つかりました: {credentials_path}")
        
        try:
            with open(credentials_path, 'r', encoding='utf-8') as f:
                creds = json.load(f)
            
            required_fields = [
                'type', 'project_id', 'private_key_id', 'private_key',
                'client_email', 'client_id', 'auth_uri', 'token_uri'
            ]
            
            missing_fields = [field for field in required_fields if field not in creds]
            
            if missing_fields:
                print(f"⚠️ 認証情報ファイルに不足フィールド: {missing_fields}")
                return False
            
            if creds.get('type') != 'service_account':
                print("⚠️ サービスアカウント形式ではありません")
                return False
            
            if 'your-project' in creds.get('project_id', ''):
                print("⚠️ テンプレートファイルのままです。実際の認証情報に置き換えてください")
                return False
            
            print("✅ 認証情報ファイルの形式は正常です")
            print(f"   プロジェクトID: {creds.get('project_id')}")
            print(f"   サービスアカウント: {creds.get('client_email')}")
            return True
            
        except json.JSONDecodeError:
            print("❌ 認証情報ファイルのJSON形式が不正です")
            return False
        except Exception as e:
            print(f"❌ 認証情報ファイル確認エラー: {e}")
            return False
    else:
        print(f"❌ 認証情報ファイルが見つかりません: {credentials_path}")
        return False

def install_required_packages():
    """必要なパッケージのインストール"""
    print("📦 必要なPythonパッケージをインストールします...")
    
    try:
        import subprocess
        
        packages = [
            'google-api-python-client',
            'google-auth'
        ]
        
        for package in packages:
            print(f"インストール中: {package}")
            result = subprocess.run(
                ['pip', 'install', package],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ {package} インストール完了")
            else:
                print(f"❌ {package} インストール失敗: {result.stderr}")
                return False
        
        print("✅ 全パッケージのインストールが完了しました")
        return True
        
    except Exception as e:
        print(f"❌ パッケージインストールエラー: {e}")
        return False

def test_api_connection():
    """API接続テスト"""
    print("🧪 Google Sheets API接続テストを実行します...")
    
    try:
        from huganjob_google_sheets_monitor import GoogleSheetsMonitor
        
        monitor = GoogleSheetsMonitor()
        
        if monitor.setup_credentials():
            print("✅ 認証成功")
            
            # スプレッドシートデータ取得テスト
            data = monitor.fetch_spreadsheet_data()
            if data is not None:
                print(f"✅ スプレッドシートデータ取得成功: {len(data)}行")
                
                # エントリ解析テスト
                entries = monitor.parse_spreadsheet_entries(data)
                print(f"✅ エントリ解析成功: {len(entries)}件")
                
                if entries:
                    print("📋 最新のエントリ（最大5件）:")
                    for entry in entries[-5:]:
                        print(f"   {entry['timestamp']} | {entry['email']}")
                
                return True
            else:
                print("❌ スプレッドシートデータ取得失敗")
                return False
        else:
            print("❌ 認証失敗")
            return False
            
    except ImportError as e:
        print(f"❌ 必要なライブラリが不足しています: {e}")
        print("pip install google-api-python-client google-auth を実行してください")
        return False
    except Exception as e:
        print(f"❌ API接続テストエラー: {e}")
        return False

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Google Sheets API設定ヘルパー')
    parser.add_argument('--install', action='store_true', help='必要パッケージをインストール')
    parser.add_argument('--check', action='store_true', help='認証情報ファイルを確認')
    parser.add_argument('--test', action='store_true', help='API接続テスト')
    parser.add_argument('--guide', action='store_true', help='設定ガイドを作成')
    parser.add_argument('--all', action='store_true', help='全ての設定手順を実行')
    
    args = parser.parse_args()
    
    if args.all:
        # 全設定手順を実行
        print_setup_instructions()
        create_project_setup_guide()
        
        if not check_credentials_file():
            print("\n❌ 認証情報ファイルを設定してから再実行してください")
            return False
        
        if not install_required_packages():
            return False
        
        return test_api_connection()
    
    elif args.install:
        return install_required_packages()
    
    elif args.check:
        return check_credentials_file()
    
    elif args.test:
        return test_api_connection()
    
    elif args.guide:
        create_project_setup_guide()
        return True
    
    else:
        # デフォルト: 設定手順表示
        print_setup_instructions()
        create_project_setup_guide()
        
        print("🚀 次のステップ:")
        print("1. 設定ガイドに従ってGoogle Cloud Consoleを設定")
        print("2. python setup_google_sheets_api.py --check で認証情報確認")
        print("3. python setup_google_sheets_api.py --install でパッケージインストール")
        print("4. python setup_google_sheets_api.py --test で接続テスト")
        
        return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
