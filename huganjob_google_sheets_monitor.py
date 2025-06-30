#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB Google Sheets 配信停止監視システム
Googleフォーム→スプレッドシート→自動配信停止処理

作成日時: 2025年06月24日
目的: Googleスプレッドシートの変更をリアルタイム監視し、自動配信停止処理を実行
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import csv
import hashlib

# Google Sheets API関連のインポート
try:
    from googleapiclient.discovery import build
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    print("⚠️ Google Sheets APIライブラリが見つかりません")
    print("インストール方法: pip install google-api-python-client google-auth")

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/huganjob_sheets_monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GoogleSheetsMonitor:
    """Google Sheets監視システム"""
    
    def __init__(self):
        self.spreadsheet_id = '1uA6LwKOhK-5XOcga8__FZbUw0iBlHusjr0zOXm_K3nU'
        self.range_name = 'フォームの回答 1!A:B'  # タイムスタンプとメールアドレス
        self.service = None
        self.last_check_file = 'data/huganjob_sheets_last_check.json'
        self.processed_entries_file = 'data/huganjob_sheets_processed.json'
        self.processed_entries = set()
        
        # 認証情報ファイルのパス
        self.credentials_file = 'config/google_sheets_credentials.json'
        
    def setup_credentials(self):
        """Google Sheets API認証設定"""
        if not GOOGLE_SHEETS_AVAILABLE:
            logger.error("Google Sheets APIライブラリが利用できません")
            return False
            
        if not os.path.exists(self.credentials_file):
            logger.error(f"認証情報ファイルが見つかりません: {self.credentials_file}")
            logger.info("Google Cloud Consoleでサービスアカウントを作成し、認証情報をダウンロードしてください")
            self.create_credentials_template()
            return False
        
        try:
            # サービスアカウント認証
            scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
            credentials = Credentials.from_service_account_file(
                self.credentials_file, scopes=scopes
            )
            self.service = build('sheets', 'v4', credentials=credentials)
            logger.info("✅ Google Sheets API認証成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ Google Sheets API認証エラー: {e}")
            return False
    
    def create_credentials_template(self):
        """認証情報テンプレートファイルを作成"""
        template = {
            "type": "service_account",
            "project_id": "your-project-id",
            "private_key_id": "your-private-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
            "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
            "client_id": "your-client-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
        }
        
        os.makedirs('config', exist_ok=True)
        with open(self.credentials_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📝 認証情報テンプレートを作成しました: {self.credentials_file}")
        logger.info("Google Cloud Consoleで実際の認証情報に置き換えてください")
    
    def load_processed_entries(self):
        """処理済みエントリを読み込み"""
        try:
            if os.path.exists(self.processed_entries_file):
                with open(self.processed_entries_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_entries = set(data.get('processed_hashes', []))
                logger.info(f"処理済みエントリ読み込み: {len(self.processed_entries)}件")
            else:
                self.processed_entries = set()
                logger.info("処理済みエントリファイルが存在しません。新規作成します。")
        except Exception as e:
            logger.error(f"処理済みエントリ読み込みエラー: {e}")
            self.processed_entries = set()
    
    def save_processed_entries(self):
        """処理済みエントリを保存"""
        try:
            os.makedirs('data', exist_ok=True)
            data = {
                'processed_hashes': list(self.processed_entries),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.processed_entries_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"処理済みエントリ保存: {len(self.processed_entries)}件")
        except Exception as e:
            logger.error(f"処理済みエントリ保存エラー: {e}")
    
    def create_entry_hash(self, timestamp: str, email: str) -> str:
        """エントリのハッシュ値を作成（重複チェック用）"""
        entry_string = f"{timestamp}|{email.lower().strip()}"
        return hashlib.md5(entry_string.encode('utf-8')).hexdigest()
    
    def fetch_spreadsheet_data(self) -> Optional[List[List[str]]]:
        """スプレッドシートからデータを取得"""
        try:
            if not self.service:
                logger.error("Google Sheets APIサービスが初期化されていません")
                return None
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=self.range_name
            ).execute()
            
            values = result.get('values', [])
            logger.info(f"スプレッドシートデータ取得: {len(values)}行")
            return values
            
        except Exception as e:
            logger.error(f"スプレッドシートデータ取得エラー: {e}")
            return None
    
    def parse_spreadsheet_entries(self, data: List[List[str]]) -> List[Dict]:
        """スプレッドシートデータを解析"""
        entries = []
        
        if not data or len(data) < 2:  # ヘッダー行がない場合
            return entries
        
        # ヘッダー行をスキップ（1行目）
        for i, row in enumerate(data[1:], start=2):
            if len(row) >= 2:
                timestamp = row[0].strip()
                email = row[1].strip()
                
                if timestamp and email:
                    entry = {
                        'row_number': i,
                        'timestamp': timestamp,
                        'email': email,
                        'hash': self.create_entry_hash(timestamp, email)
                    }
                    entries.append(entry)
        
        logger.info(f"有効なエントリ解析: {len(entries)}件")
        return entries
    
    def find_new_entries(self, entries: List[Dict]) -> List[Dict]:
        """新規エントリを特定"""
        new_entries = []
        
        for entry in entries:
            if entry['hash'] not in self.processed_entries:
                new_entries.append(entry)
        
        logger.info(f"新規エントリ発見: {len(new_entries)}件")
        return new_entries
    
    def process_unsubscribe_entry(self, entry: Dict) -> bool:
        """配信停止エントリを処理"""
        try:
            email = entry['email']
            timestamp = entry['timestamp']
            
            logger.info(f"配信停止処理開始: {email} (時刻: {timestamp})")
            
            # huganjob_unsubscribe_manager.pyを使用して処理
            from huganjob_unsubscribe_manager import HUGANJOBUnsubscribeManager
            
            manager = HUGANJOBUnsubscribeManager()
            
            # データ読み込み
            if not manager.load_company_data() or not manager.load_unsubscribe_log():
                logger.error(f"データ読み込み失敗: {email}")
                return False
            
            # 企業検索
            company = manager.find_company_by_email(email)
            if not company:
                logger.warning(f"企業が見つかりません: {email}")
                # 見つからない場合でも記録は残す
                self.record_unprocessable_entry(entry, "企業が見つかりません")
                return True  # 処理済みとしてマーク
            
            # 既に配信停止済みかチェック
            if manager.is_already_unsubscribed(email):
                logger.info(f"既に配信停止済み: {email}")
                return True  # 処理済みとしてマーク
            
            # 配信停止処理
            success = manager.mark_company_unsubscribed(
                company=company,
                email=email,
                reason=f"Googleフォーム申請 (時刻: {timestamp})",
                source="google_form_auto"
            )
            
            if success:
                # ログ保存
                manager.save_unsubscribe_log()
                # 企業CSV更新
                manager.update_company_csv()
                
                logger.info(f"✅ 配信停止処理完了: {email} - {company.get('企業名', 'N/A')}")
                return True
            else:
                logger.error(f"❌ 配信停止処理失敗: {email}")
                return False
                
        except Exception as e:
            logger.error(f"配信停止処理エラー: {e}")
            return False
    
    def record_unprocessable_entry(self, entry: Dict, reason: str):
        """処理できないエントリを記録"""
        try:
            unprocessable_file = 'data/huganjob_unprocessable_entries.csv'
            
            # ファイルが存在しない場合はヘッダーを作成
            file_exists = os.path.exists(unprocessable_file)
            
            with open(unprocessable_file, 'a', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                
                if not file_exists:
                    writer.writerow(['タイムスタンプ', 'メールアドレス', '理由', '記録日時'])
                
                writer.writerow([
                    entry['timestamp'],
                    entry['email'],
                    reason,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ])
            
            logger.info(f"処理不可エントリ記録: {entry['email']} - {reason}")
            
        except Exception as e:
            logger.error(f"処理不可エントリ記録エラー: {e}")
    
    def monitor_spreadsheet(self, check_interval: int = 60):
        """スプレッドシート監視メインループ"""
        logger.info("=" * 60)
        logger.info("🔍 HUGANJOB Google Sheets 配信停止監視システム開始")
        logger.info("=" * 60)
        
        # 認証設定
        if not self.setup_credentials():
            logger.error("認証設定に失敗しました。監視を停止します。")
            return False
        
        # 処理済みエントリ読み込み
        self.load_processed_entries()
        
        logger.info(f"📊 監視設定:")
        logger.info(f"   スプレッドシートID: {self.spreadsheet_id}")
        logger.info(f"   監視範囲: {self.range_name}")
        logger.info(f"   チェック間隔: {check_interval}秒")
        logger.info(f"   処理済みエントリ: {len(self.processed_entries)}件")
        
        try:
            while True:
                logger.info(f"\n🔍 スプレッドシートチェック開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # スプレッドシートデータ取得
                data = self.fetch_spreadsheet_data()
                if data is None:
                    logger.warning("データ取得に失敗しました。次回チェックまで待機...")
                    time.sleep(check_interval)
                    continue
                
                # エントリ解析
                entries = self.parse_spreadsheet_entries(data)
                if not entries:
                    logger.info("有効なエントリがありません")
                    time.sleep(check_interval)
                    continue
                
                # 新規エントリ特定
                new_entries = self.find_new_entries(entries)
                
                if new_entries:
                    logger.info(f"🆕 新規配信停止申請を発見: {len(new_entries)}件")
                    
                    # 新規エントリを処理
                    processed_count = 0
                    for entry in new_entries:
                        logger.info(f"処理中: {entry['email']} (行{entry['row_number']})")
                        
                        if self.process_unsubscribe_entry(entry):
                            self.processed_entries.add(entry['hash'])
                            processed_count += 1
                        
                        # 処理間隔
                        time.sleep(1)
                    
                    # 処理済みエントリ保存
                    self.save_processed_entries()
                    
                    logger.info(f"✅ 新規エントリ処理完了: {processed_count}/{len(new_entries)}件")
                else:
                    logger.info("新規エントリはありません")
                
                logger.info(f"⏳ 次回チェックまで{check_interval}秒待機...")
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 監視システムを停止します...")
            self.save_processed_entries()
            return True
        except Exception as e:
            logger.error(f"❌ 監視システムエラー: {e}")
            self.save_processed_entries()
            return False

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='HUGANJOB Google Sheets配信停止監視システム')
    parser.add_argument('--interval', type=int, default=60, help='チェック間隔（秒）')
    parser.add_argument('--test', action='store_true', help='テストモード（1回のみチェック）')
    parser.add_argument('--setup', action='store_true', help='初期設定モード')
    
    args = parser.parse_args()
    
    monitor = GoogleSheetsMonitor()
    
    if args.setup:
        # 初期設定モード
        print("🔧 Google Sheets API初期設定")
        monitor.create_credentials_template()
        print("認証情報ファイルを設定してから再実行してください")
        return True
    
    if args.test:
        # テストモード
        print("🧪 テストモード: 1回のみチェック")
        if monitor.setup_credentials():
            monitor.load_processed_entries()
            data = monitor.fetch_spreadsheet_data()
            if data:
                entries = monitor.parse_spreadsheet_entries(data)
                new_entries = monitor.find_new_entries(entries)
                print(f"📊 結果: 総エントリ{len(entries)}件、新規{len(new_entries)}件")
                for entry in new_entries:
                    print(f"  新規: {entry['email']} ({entry['timestamp']})")
            return True
        else:
            print("❌ 認証設定に失敗しました")
            return False
    
    # 通常の監視モード
    success = monitor.monitor_spreadsheet(args.interval)
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
