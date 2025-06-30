#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB 一括メール送信システム
CSVデータを基にした企業向け採用メール一括送信

作成日時: 2025年06月20日 22:00:00
作成者: AI Assistant

機能:
- CSVの担当者メールアドレス優先使用
- 企業名・募集職種の動的挿入
- 送信状況追跡・エラーハンドリング
- 送信レート制限（スパム対策）
"""

import smtplib
import pandas as pd
import configparser
import logging
import sys
import os
import time
import uuid
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate
from pathlib import Path
import argparse

# 自作モジュール
from huganjob_email_address_resolver import HuganJobEmailResolver

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/huganjob_bulk_sender.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class HuganJobBulkEmailSender:
    """HUGAN JOB 一括メール送信クラス"""
    
    def __init__(self, config_file="config/huganjob_email_config.ini"):
        """
        初期化
        
        Args:
            config_file (str): 設定ファイルのパス
        """
        self.config_file = config_file
        self.config = None
        self.smtp_server = None
        self.template_content = None
        self.email_resolver = HuganJobEmailResolver()
        self.sending_results = []
        
        # ログディレクトリ作成
        os.makedirs('logs', exist_ok=True)
        
    def load_config(self):
        """設定ファイルを読み込み"""
        try:
            logger.info(f"設定ファイル読み込み: {self.config_file}")
            
            if not os.path.exists(self.config_file):
                raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_file}")
            
            self.config = configparser.ConfigParser()
            self.config.read(self.config_file, encoding='utf-8')
            
            # 必要なセクションの確認
            required_sections = ['SMTP', 'EMAIL_CONTENT', 'SENDING']
            for section in required_sections:
                if not self.config.has_section(section):
                    raise ValueError(f"設定ファイルに必要なセクションがありません: {section}")
            
            logger.info("設定ファイル読み込み完了")
            return True
            
        except Exception as e:
            logger.error(f"設定ファイル読み込みエラー: {e}")
            return False
    
    def load_email_template(self):
        """メールテンプレートを読み込み"""
        try:
            template_file = self.config.get('EMAIL_CONTENT', 'template_file')
            logger.info(f"テンプレート読み込み: {template_file}")
            
            if not os.path.exists(template_file):
                raise FileNotFoundError(f"テンプレートファイルが見つかりません: {template_file}")
            
            with open(template_file, 'r', encoding='utf-8') as f:
                self.template_content = f.read()
            
            logger.info("テンプレート読み込み完了")
            return True
            
        except Exception as e:
            logger.error(f"テンプレート読み込みエラー: {e}")
            return False
    
    def connect_smtp(self):
        """SMTP接続を確立"""
        try:
            smtp_server = self.config.get('SMTP', 'server')
            smtp_port = self.config.getint('SMTP', 'port')
            smtp_user = self.config.get('SMTP', 'user')
            smtp_password = self.config.get('SMTP', 'password')
            
            logger.info(f"SMTP接続開始: {smtp_server}:{smtp_port}")
            
            self.smtp_server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            self.smtp_server.starttls()
            self.smtp_server.login(smtp_user, smtp_password)
            
            logger.info("SMTP接続成功")
            return True
            
        except Exception as e:
            logger.error(f"SMTP接続エラー: {e}")
            return False
    
    def generate_email_content(self, company_name, job_position):
        """
        メール内容を生成（企業名・職種を動的挿入）
        
        Args:
            company_name (str): 企業名
            job_position (str): 募集職種
            
        Returns:
            tuple: (email_content, tracking_id)
        """
        try:
            # テンプレート内の変数を実際の値に置換
            email_content = self.template_content.replace('{{company_name}}', str(company_name))
            email_content = email_content.replace('{{job_position}}', str(job_position))
            
            # 追跡用のユニークIDを生成
            tracking_id = str(uuid.uuid4())
            
            # 開封追跡用の画像タグを追加
            tracking_pixel = f'<img src="http://127.0.0.1:5002/track/{tracking_id}" width="1" height="1" style="display:none;" />'
            email_content = email_content.replace('</body>', f'{tracking_pixel}</body>')
            
            return email_content, tracking_id
            
        except Exception as e:
            logger.error(f"メール内容生成エラー: {e}")
            return None, None
    
    def send_single_email(self, to_email, company_name, job_position):
        """
        単一メールを送信
        
        Args:
            to_email (str): 送信先メールアドレス
            company_name (str): 企業名
            job_position (str): 募集職種
            
        Returns:
            tuple: (success, tracking_id, error_message)
        """
        try:
            # メール内容生成
            email_content, tracking_id = self.generate_email_content(company_name, job_position)
            if not email_content:
                return False, None, "メール内容生成失敗"
            
            # 件名生成
            subject_template = self.config.get('EMAIL_CONTENT', 'subject')
            subject = subject_template.replace('{job_position}', str(job_position))
            
            # 送信者情報
            sender_name = self.config.get('SMTP', 'sender_name')
            from_email = self.config.get('SMTP', 'from_email')
            reply_to = self.config.get('SMTP', 'reply_to')
            
            # メッセージ作成
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr((sender_name, from_email))
            msg['To'] = to_email
            msg['Subject'] = Header(subject, 'utf-8')
            msg['Reply-To'] = reply_to
            
            # RFC5322準拠のヘッダー追加
            msg['Message-ID'] = f"<{tracking_id}@huganjob.jp>"
            msg['Date'] = formatdate(localtime=True)
            # 🚨 X-Mailerヘッダーを削除（自動送信システム識別回避）
            # ❌ msg['X-Mailer'] = 削除済み（迷惑メール判定要因）
            msg['X-Priority'] = '3'
            msg['Precedence'] = 'bulk'
            
            # HTMLパートを追加
            html_part = MIMEText(email_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # メール送信
            self.smtp_server.sendmail(from_email, [to_email], msg.as_string())
            
            logger.info(f"✅ 送信成功: {company_name} -> {to_email}")
            return True, tracking_id, None
            
        except Exception as e:
            error_msg = f"送信エラー: {e}"
            logger.error(f"❌ {company_name} -> {to_email}: {error_msg}")
            return False, None, error_msg
    
    def bulk_send_emails(self, start_id=None, end_id=None, test_mode=False, max_emails=None):
        """
        一括メール送信
        
        Args:
            start_id (int): 開始企業ID
            end_id (int): 終了企業ID
            test_mode (bool): テストモード
            max_emails (int): 最大送信数
            
        Returns:
            dict: 送信結果統計
        """
        logger.info("=" * 60)
        logger.info("📧 HUGAN JOB 一括メール送信開始")
        logger.info("=" * 60)
        
        # メールアドレス決定
        logger.info("メールアドレス決定処理実行中...")
        if not self.email_resolver.load_companies_data():
            return {"error": "企業データ読み込み失敗"}
        
        self.email_resolver.resolve_email_addresses()
        sendable_companies = self.email_resolver.get_sendable_companies()
        
        if not sendable_companies:
            logger.error("送信可能な企業が見つかりません")
            return {"error": "送信可能企業なし"}
        
        # 送信範囲の決定
        if start_id is not None or end_id is not None:
            filtered_companies = []
            for company in sendable_companies:
                company_id = company['company_id']
                if start_id is not None and company_id < start_id:
                    continue
                if end_id is not None and company_id > end_id:
                    continue
                filtered_companies.append(company)
            sendable_companies = filtered_companies
        
        # 最大送信数制限
        if max_emails and len(sendable_companies) > max_emails:
            sendable_companies = sendable_companies[:max_emails]
        
        logger.info(f"送信対象企業数: {len(sendable_companies)}")
        
        if test_mode:
            logger.info("🧪 テストモード: 実際の送信は行いません")
        
        # 送信設定
        send_interval = self.config.getint('SENDING', 'interval', fallback=5)
        
        # 送信実行
        success_count = 0
        failure_count = 0
        
        for i, company in enumerate(sendable_companies, 1):
            company_name = company['company_name']
            email_address = company['final_email']
            job_position = company['job_position']
            
            logger.info(f"[{i}/{len(sendable_companies)}] 送信準備: {company_name}")
            
            if test_mode:
                # テストモード
                logger.info(f"🧪 テスト: {company_name} -> {email_address} ({job_position})")
                success = True
                tracking_id = str(uuid.uuid4())
                error_msg = None
            else:
                # 実際の送信
                success, tracking_id, error_msg = self.send_single_email(
                    email_address, company_name, job_position
                )
            
            # 結果記録
            result = {
                'company_id': company['company_id'],
                'company_name': company_name,
                'email_address': email_address,
                'job_position': job_position,
                'send_datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'success': success,
                'tracking_id': tracking_id,
                'error_message': error_msg
            }
            self.sending_results.append(result)
            
            if success:
                success_count += 1
            else:
                failure_count += 1
            
            # 送信間隔
            if i < len(sendable_companies):
                logger.info(f"⏳ 送信間隔待機: {send_interval}秒")
                time.sleep(send_interval)
        
        # 統計情報
        stats = {
            'total_companies': len(sendable_companies),
            'success_count': success_count,
            'failure_count': failure_count,
            'success_rate': success_count / len(sendable_companies) * 100 if sendable_companies else 0,
            'test_mode': test_mode
        }
        
        logger.info("=" * 60)
        logger.info("📊 送信結果統計")
        logger.info("=" * 60)
        logger.info(f"送信対象: {stats['total_companies']} 社")
        logger.info(f"成功: {stats['success_count']} 社")
        logger.info(f"失敗: {stats['failure_count']} 社")
        logger.info(f"成功率: {stats['success_rate']:.1f}%")
        if test_mode:
            logger.info("🧪 テストモードで実行")
        logger.info("=" * 60)
        
        return stats

    def save_sending_results(self, output_file=None):
        """
        送信結果をCSVファイルに保存

        Args:
            output_file (str): 出力ファイル名
        """
        if not self.sending_results:
            logger.warning("保存する送信結果がありません")
            return False

        try:
            if output_file is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"huganjob_sending_results_{timestamp}.csv"

            results_df = pd.DataFrame(self.sending_results)
            results_df.to_csv(output_file, index=False, encoding='utf-8')
            logger.info(f"送信結果をCSVに保存: {output_file}")
            return True

        except Exception as e:
            logger.error(f"送信結果保存エラー: {e}")
            return False

    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.smtp_server:
            try:
                self.smtp_server.quit()
                logger.info("SMTP接続を閉じました")
            except:
                pass

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='HUGAN JOB 一括メール送信システム')
    parser.add_argument('--start-id', type=int, help='開始企業ID')
    parser.add_argument('--end-id', type=int, help='終了企業ID')
    parser.add_argument('--max-emails', type=int, help='最大送信数')
    parser.add_argument('--test-mode', action='store_true', help='テストモード（実際の送信なし）')
    parser.add_argument('--config', default='config/huganjob_email_config.ini', help='設定ファイルパス')

    args = parser.parse_args()

    print("=" * 60)
    print("📧 HUGAN JOB 一括メール送信システム")
    print("=" * 60)

    # 送信システム初期化
    sender = HuganJobBulkEmailSender(args.config)

    try:
        # 設定読み込み
        if not sender.load_config():
            print("❌ 設定ファイルの読み込みに失敗しました")
            return False

        # テンプレート読み込み
        if not sender.load_email_template():
            print("❌ メールテンプレートの読み込みに失敗しました")
            return False

        # SMTP接続（テストモードでない場合）
        if not args.test_mode:
            if not sender.connect_smtp():
                print("❌ SMTP接続に失敗しました")
                return False

        # 一括送信実行
        stats = sender.bulk_send_emails(
            start_id=args.start_id,
            end_id=args.end_id,
            test_mode=args.test_mode,
            max_emails=args.max_emails
        )

        if 'error' in stats:
            print(f"❌ 送信処理エラー: {stats['error']}")
            return False

        # 結果保存
        sender.save_sending_results()

        # 結果表示
        print(f"\n✅ 送信処理完了")
        print(f"📊 成功: {stats['success_count']}/{stats['total_companies']} 社")
        print(f"📈 成功率: {stats['success_rate']:.1f}%")

        if args.test_mode:
            print("🧪 テストモードで実行されました")
            print("💡 実際の送信を行う場合は --test-mode オプションを外してください")

        return True

    except KeyboardInterrupt:
        print("\n\n❌ 送信がキャンセルされました")
        return False

    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        sender.cleanup()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ システムエラー: {e}")
        sys.exit(1)
