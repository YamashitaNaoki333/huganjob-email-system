#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB 配信停止管理システム
Googleフォーム連携による配信停止処理の自動化

作成日時: 2025年06月24日
目的: Googleフォームからの配信停止申請を自動処理し、企業データベースを更新
"""

import csv
import json
import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import requests
from urllib.parse import urlparse

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/huganjob_unsubscribe_manager.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HUGANJOBUnsubscribeManager:
    """HUGANJOB配信停止管理システム"""
    
    def __init__(self):
        self.company_csv_path = 'data/new_input_test.csv'
        self.unsubscribe_log_path = 'data/huganjob_unsubscribe_log.csv'
        self.google_form_url = 'https://forms.gle/49BTNfSgUeNkH7rz5'
        
        # 手動で確認された配信停止申請
        self.manual_unsubscribe_requests = [
            'info@keyman.co.jp',
            'saiyo@nikken-r.co.jp',
            'info@ams-inc.co.jp',
            'info@omni-yoshida.co.jp',
            'info@grow-ship.com',
            # 2025-06-25 反響があった企業（再送防止）
            'info@vasteculture.com',  # ヴァスト・キュルチュール株式会社（ID: 1229）
            'info@bravely-inc.jp'     # 株式会社BRAVELY（ID: 1848）
        ]
        
        self.companies_data = []
        self.unsubscribe_log = []
        
    def load_company_data(self) -> bool:
        """企業データを読み込み"""
        try:
            with open(self.company_csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                self.companies_data = list(reader)
            
            logger.info(f"企業データ読み込み完了: {len(self.companies_data)}社")
            return True
            
        except Exception as e:
            logger.error(f"企業データ読み込みエラー: {e}")
            return False
    
    def load_unsubscribe_log(self) -> bool:
        """配信停止ログを読み込み"""
        try:
            if os.path.exists(self.unsubscribe_log_path):
                with open(self.unsubscribe_log_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    self.unsubscribe_log = list(reader)
                logger.info(f"配信停止ログ読み込み完了: {len(self.unsubscribe_log)}件")
            else:
                logger.info("配信停止ログファイルが存在しません。新規作成します。")
                self.unsubscribe_log = []
            return True
            
        except Exception as e:
            logger.error(f"配信停止ログ読み込みエラー: {e}")
            return False
    
    def find_company_by_email(self, email: str) -> Optional[Dict]:
        """メールアドレスから企業を検索"""
        email_lower = email.lower().strip()
        
        for company in self.companies_data:
            # 担当者メールアドレスとの照合
            company_email = company.get('担当者メールアドレス', '').lower().strip()
            if company_email and company_email == email_lower:
                return company
            
            # ドメインベースでの照合
            if '@' in email_lower:
                domain = email_lower.split('@')[1]
                company_url = company.get('企業ホームページ', '')
                if company_url:
                    try:
                        parsed_url = urlparse(company_url)
                        company_domain = parsed_url.netloc.lower()
                        # www.を除去して比較
                        company_domain = company_domain.replace('www.', '')
                        if domain == company_domain:
                            return company
                    except:
                        continue
        
        return None
    
    def process_manual_unsubscribe_requests(self) -> int:
        """手動で確認された配信停止申請を処理"""
        processed_count = 0
        
        logger.info("手動配信停止申請の処理を開始")
        
        for email in self.manual_unsubscribe_requests:
            company = self.find_company_by_email(email)
            
            if company:
                # 既に配信停止済みかチェック
                if self.is_already_unsubscribed(email):
                    logger.info(f"既に配信停止済み: {email} - {company.get('企業名', 'N/A')}")
                    continue
                
                # 配信停止処理
                success = self.mark_company_unsubscribed(
                    company=company,
                    email=email,
                    reason="手動確認による配信停止申請",
                    source="manual_verification"
                )
                
                if success:
                    processed_count += 1
                    logger.info(f"配信停止処理完了: {email} - {company.get('企業名', 'N/A')}")
                else:
                    logger.error(f"配信停止処理失敗: {email}")
            else:
                logger.warning(f"企業が見つかりません: {email}")
        
        logger.info(f"手動配信停止申請処理完了: {processed_count}件処理")
        return processed_count
    
    def is_already_unsubscribed(self, email: str) -> bool:
        """既に配信停止済みかチェック"""
        email_lower = email.lower().strip()
        
        for log_entry in self.unsubscribe_log:
            if log_entry.get('メールアドレス', '').lower().strip() == email_lower:
                return True
        
        return False
    
    def mark_company_unsubscribed(self, company: Dict, email: str, reason: str, source: str) -> bool:
        """企業を配信停止状態にマーク"""
        try:
            # 配信停止ログに追加
            unsubscribe_entry = {
                '企業ID': company.get('ID', ''),
                '企業名': company.get('企業名', ''),
                'メールアドレス': email,
                '配信停止日時': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '配信停止理由': reason,
                '申請元': source,
                '処理状況': '完了'
            }
            
            self.unsubscribe_log.append(unsubscribe_entry)
            
            # 企業データに配信停止フラグを追加（将来の拡張用）
            company['配信停止状態'] = 'unsubscribed'
            company['配信停止日時'] = unsubscribe_entry['配信停止日時']
            company['配信停止理由'] = reason
            
            return True
            
        except Exception as e:
            logger.error(f"配信停止マーク処理エラー: {e}")
            return False
    
    def save_unsubscribe_log(self) -> bool:
        """配信停止ログを保存"""
        try:
            fieldnames = [
                '企業ID', '企業名', 'メールアドレス', '配信停止日時', 
                '配信停止理由', '申請元', '処理状況'
            ]
            
            with open(self.unsubscribe_log_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.unsubscribe_log)
            
            logger.info(f"配信停止ログ保存完了: {len(self.unsubscribe_log)}件")
            return True
            
        except Exception as e:
            logger.error(f"配信停止ログ保存エラー: {e}")
            return False
    
    def update_company_csv(self) -> bool:
        """企業CSVファイルを更新（配信停止情報を追加）"""
        try:
            # バックアップ作成
            backup_path = f"{self.company_csv_path}_backup_unsubscribe_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            with open(self.company_csv_path, 'r', encoding='utf-8-sig') as src:
                with open(backup_path, 'w', encoding='utf-8-sig') as dst:
                    dst.write(src.read())
            
            logger.info(f"バックアップ作成: {backup_path}")
            
            # 新しいヘッダーに配信停止関連列を追加
            fieldnames = [
                'ID', '企業名', '企業ホームページ', '担当者メールアドレス', '募集職種',
                'バウンス状態', 'バウンス日時', 'バウンス理由',
                '配信停止状態', '配信停止日時', '配信停止理由'
            ]
            
            # 企業データを更新して保存
            with open(self.company_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for company in self.companies_data:
                    # 配信停止関連の列がない場合は空文字で埋める
                    for field in ['配信停止状態', '配信停止日時', '配信停止理由']:
                        if field not in company:
                            company[field] = ''
                    
                    writer.writerow(company)
            
            logger.info("企業CSVファイル更新完了")
            return True
            
        except Exception as e:
            logger.error(f"企業CSVファイル更新エラー: {e}")
            return False
    
    def generate_unsubscribe_report(self) -> Dict:
        """配信停止レポートを生成"""
        report = {
            'total_companies': len(self.companies_data),
            'total_unsubscribed': len(self.unsubscribe_log),
            'unsubscribe_rate': 0.0,
            'recent_unsubscribes': [],
            'unsubscribe_by_source': {}
        }
        
        if report['total_companies'] > 0:
            report['unsubscribe_rate'] = (report['total_unsubscribed'] / report['total_companies']) * 100
        
        # 最近の配信停止（直近10件）
        sorted_log = sorted(
            self.unsubscribe_log, 
            key=lambda x: x.get('配信停止日時', ''), 
            reverse=True
        )
        report['recent_unsubscribes'] = sorted_log[:10]
        
        # 申請元別統計
        for entry in self.unsubscribe_log:
            source = entry.get('申請元', 'unknown')
            report['unsubscribe_by_source'][source] = report['unsubscribe_by_source'].get(source, 0) + 1
        
        return report
    
    def run_unsubscribe_processing(self) -> bool:
        """配信停止処理のメイン実行"""
        logger.info("HUGANJOB配信停止処理開始")
        
        try:
            # データ読み込み
            if not self.load_company_data():
                return False
            
            if not self.load_unsubscribe_log():
                return False
            
            # 手動配信停止申請の処理
            processed_count = self.process_manual_unsubscribe_requests()
            
            # ログ保存
            if not self.save_unsubscribe_log():
                return False
            
            # 企業CSVファイル更新
            if not self.update_company_csv():
                return False
            
            # レポート生成
            report = self.generate_unsubscribe_report()
            
            logger.info("=== 配信停止処理レポート ===")
            logger.info(f"総企業数: {report['total_companies']}")
            logger.info(f"配信停止企業数: {report['total_unsubscribed']}")
            logger.info(f"配信停止率: {report['unsubscribe_rate']:.2f}%")
            logger.info(f"今回処理件数: {processed_count}")
            
            logger.info("HUGANJOB配信停止処理完了")
            return True
            
        except Exception as e:
            logger.error(f"配信停止処理エラー: {e}")
            return False

    def check_unsubscribe_status(self, email: str) -> Optional[Dict]:
        """特定のメールアドレスの配信停止状況を確認"""
        email_lower = email.lower().strip()

        for entry in self.unsubscribe_log:
            if entry.get('メールアドレス', '').lower().strip() == email_lower:
                return entry

        return None

    def list_unsubscribed_companies(self) -> List[Dict]:
        """配信停止済み企業の一覧を取得"""
        return self.unsubscribe_log.copy()

    def export_unsubscribe_list_for_sending(self) -> List[str]:
        """送信システム用の配信停止メールアドレスリストを出力"""
        unsubscribed_emails = []

        for entry in self.unsubscribe_log:
            email = entry.get('メールアドレス', '').strip()
            if email:
                unsubscribed_emails.append(email.lower())

        return unsubscribed_emails

def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description='HUGANJOB配信停止管理システム')
    parser.add_argument('--check-email', help='特定のメールアドレスの配信停止状況を確認')
    parser.add_argument('--list-unsubscribed', action='store_true', help='配信停止済み企業一覧を表示')
    parser.add_argument('--export-list', action='store_true', help='送信システム用配信停止リストを出力')
    parser.add_argument('--process', action='store_true', help='配信停止処理を実行')

    args = parser.parse_args()

    manager = HUGANJOBUnsubscribeManager()

    # データ読み込み
    if not manager.load_company_data() or not manager.load_unsubscribe_log():
        print("❌ データ読み込みエラー")
        return False

    if args.check_email:
        # 特定メールアドレスの確認
        status = manager.check_unsubscribe_status(args.check_email)
        if status:
            print(f"✅ 配信停止済み: {args.check_email}")
            print(f"   企業名: {status.get('企業名', 'N/A')}")
            print(f"   停止日時: {status.get('配信停止日時', 'N/A')}")
            print(f"   理由: {status.get('配信停止理由', 'N/A')}")
        else:
            print(f"❌ 配信停止記録なし: {args.check_email}")

    elif args.list_unsubscribed:
        # 配信停止済み企業一覧
        unsubscribed = manager.list_unsubscribed_companies()
        print(f"📋 配信停止済み企業一覧 ({len(unsubscribed)}件)")
        print("-" * 80)
        for entry in unsubscribed:
            print(f"ID: {entry.get('企業ID', 'N/A'):<5} | "
                  f"{entry.get('企業名', 'N/A'):<30} | "
                  f"{entry.get('メールアドレス', 'N/A'):<30} | "
                  f"{entry.get('配信停止日時', 'N/A')}")

    elif args.export_list:
        # 送信システム用リスト出力
        emails = manager.export_unsubscribe_list_for_sending()
        print(f"📤 配信停止メールアドレスリスト ({len(emails)}件)")
        for email in emails:
            print(email)

    elif args.process:
        # 配信停止処理実行
        success = manager.run_unsubscribe_processing()
        if success:
            print("✅ 配信停止処理が正常に完了しました")
        else:
            print("❌ 配信停止処理でエラーが発生しました")
        return success

    else:
        # デフォルト: 処理実行
        success = manager.run_unsubscribe_processing()
        if success:
            print("✅ 配信停止処理が正常に完了しました")
        else:
            print("❌ 配信停止処理でエラーが発生しました")
        return success

    return True

if __name__ == "__main__":
    main()
