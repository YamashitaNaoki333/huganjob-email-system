#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
派生版広告営業メール送信スクリプト
ad.htmlテンプレートを使用した広告運用代行営業メール送信
"""

import os
import csv
import json
import logging
import smtplib
import configparser
import pandas as pd
import re
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formatdate
import argparse
import time
import uuid

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdEmailSender:
    """広告営業メール送信クラス"""

    def __init__(self, config_file='config/derivative_email_config.ini'):
        self.config_file = config_file
        self.config = None
        self.smtp_server = None

    def clean_email_address(self, email):
        """メールアドレスをクリーニング（@より後ろの不要な部分を削除）"""
        if not email:
            return email

        # 文字列として処理
        email_str = str(email).strip()

        # 引用符で囲まれている場合の処理
        if email_str.startswith('"') and '"' in email_str[1:]:
            # "HUGAN JOB <client@hugan.co.jp>"@www4009.sakura.ne.jp のような形式
            quote_end = email_str.find('"', 1)
            if quote_end > 0:
                quoted_part = email_str[1:quote_end]
                # <email@domain> の形式を抽出
                if '<' in quoted_part and '>' in quoted_part:
                    start = quoted_part.find('<') + 1
                    end = quoted_part.find('>')
                    if start > 0 and end > start:
                        return quoted_part[start:end]

        # @マークで分割
        parts = email_str.split('@')
        if len(parts) < 2:
            return email_str

        local_part = parts[0]
        domain_part = parts[1]

        # ドメイン部分から不要な文字を削除
        # 例: "client@hugan.co.jp"@www4009.sakura.ne.jp -> client@hugan.co.jp
        if '"' in domain_part:
            domain_part = domain_part.split('"')[0]

        # 複数の@がある場合の処理（最初のドメインのみ使用）
        if '@' in domain_part:
            domain_part = domain_part.split('@')[0]

        # 空白文字を除去
        domain_part = domain_part.strip()

        return f"{local_part}@{domain_part}"

    def html_to_plain_text(self, html_content):
        """HTMLコンテンツをプレーンテキストに変換"""
        try:
            # HTMLタグを除去
            import re
            # HTMLタグを削除
            text = re.sub(r'<[^>]+>', '', html_content)
            # HTMLエンティティをデコード
            text = text.replace('&nbsp;', ' ')
            text = text.replace('&lt;', '<')
            text = text.replace('&gt;', '>')
            text = text.replace('&amp;', '&')
            text = text.replace('&quot;', '"')
            # 複数の空白を単一の空白に変換
            text = re.sub(r'\s+', ' ', text)
            # 行頭・行末の空白を削除
            text = text.strip()
            return text
        except Exception as e:
            logger.error(f"HTMLからプレーンテキストへの変換に失敗: {e}")
            return html_content
        
    def load_config(self):
        """設定ファイルを読み込み"""
        try:
            self.config = configparser.ConfigParser()
            self.config.read(self.config_file, encoding='utf-8')
            logger.info(f"設定ファイルを読み込みました: {self.config_file}")
        except Exception as e:
            logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
            raise
    
    def load_ad_template(self):
        """corporate-email-newsletter.htmlテンプレートを読み込み"""
        try:
            template_file = 'corporate-email-newsletter.html'
            if not os.path.exists(template_file):
                # フォールバック: templatesディレクトリ
                template_file = 'templates/corporate-email-newsletter.html'
                if not os.path.exists(template_file):
                    # 最後のフォールバック: ad.html
                    template_file = 'ad.html'
                    if not os.path.exists(template_file):
                        logger.error(f"テンプレートファイルが見つかりません: corporate-email-newsletter.html")
                        return None

            # 複数のエンコーディングを試す
            encodings = ['utf-8', 'utf-8-sig', 'shift_jis', 'cp932']
            template_content = None

            for encoding in encodings:
                try:
                    with open(template_file, 'r', encoding=encoding) as f:
                        template_content = f.read()
                    logger.info(f"テンプレートファイルを読み込みました: {template_file} (エンコーディング: {encoding})")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"エンコーディング {encoding} での読み込みに失敗: {e}")
                    continue

            if template_content is None:
                logger.error("すべてのエンコーディングでテンプレートファイルの読み込みに失敗しました")
                return None

            return template_content

        except Exception as e:
            logger.error(f"テンプレートファイルの読み込みに失敗しました: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def generate_email_content(self, company_name, template_content, job_position='人材'):
        """メール内容を生成"""
        try:
            # 文字列の適切な処理を確保
            if isinstance(company_name, bytes):
                company_name = company_name.decode('utf-8', errors='replace')
            if isinstance(template_content, bytes):
                template_content = template_content.decode('utf-8', errors='replace')
            if isinstance(job_position, bytes):
                job_position = job_position.decode('utf-8', errors='replace')

            # テンプレート内の変数を実際の値に置換
            email_content = template_content.replace('{{company_name}}', str(company_name))
            email_content = email_content.replace('{{job_position}}', str(job_position))
            # 後方互換性のため、古い形式も対応
            email_content = email_content.replace('{{会社名}}', str(company_name))

            # 追跡用のユニークIDを生成
            tracking_id = str(uuid.uuid4())

            # 開封追跡用の画像タグを追加
            tracking_pixel = f'<img src="http://127.0.0.1:5002/track/{tracking_id}" width="1" height="1" style="display:none;" />'
            email_content = email_content.replace('</body>', f'{tracking_pixel}</body>')

            return email_content, tracking_id

        except Exception as e:
            logger.error(f"メール内容生成に失敗しました: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None, None
    
    def connect_smtp(self):
        """SMTP接続を確立"""
        try:
            smtp_server = self.config['SMTP']['server']
            smtp_port = int(self.config['SMTP']['port'])
            # SMTP認証用のアドレスを使用（実際の認証用）
            smtp_user = self.config['SMTP'].get('smtp_auth_email', self.config['SMTP']['user'])
            smtp_password = self.config['SMTP']['password']

            self.smtp_server = smtplib.SMTP(smtp_server, smtp_port)
            self.smtp_server.starttls()
            self.smtp_server.login(smtp_user, smtp_password)

            logger.info(f"SMTP接続が確立されました: {smtp_server}:{smtp_port}")
            logger.info(f"認証ユーザー: {smtp_user}")
            return True

        except Exception as e:
            logger.error(f"SMTP接続に失敗しました: {e}")
            return False
    
    def send_email(self, to_email, company_name, template_content):
        """メールを送信（HTMLメール、迷惑メール対策強化版）"""
        try:
            # 文字列の適切な処理を確保
            if isinstance(to_email, bytes):
                to_email = to_email.decode('utf-8', errors='replace')
            if isinstance(company_name, bytes):
                company_name = company_name.decode('utf-8', errors='replace')

            # メール内容を生成
            email_content, tracking_id = self.generate_email_content(company_name, template_content)
            if not email_content:
                return False, None

            # メールメッセージを作成（HTMLメール対応）
            msg = MIMEMultipart('alternative')

            # 送信者設定を取得
            sender_name = self.config['SMTP']['sender_name']
            from_email = self.config['SMTP']['from_email']
            reply_to = self.config['SMTP']['reply_to']
            smtp_auth_email = self.config['SMTP'].get('smtp_auth_email', self.config['SMTP']['user'])

            # メールアドレスをクリーニング
            from_email_clean = self.clean_email_address(from_email)
            to_email_clean = self.clean_email_address(str(to_email))
            reply_to_clean = self.clean_email_address(reply_to)

            # 迷惑メール対策のためのヘッダー設定（文字化け防止）
            # 送信者名を英語表記にして文字化けを防ぐ
            msg['From'] = f"{sender_name} <{from_email_clean}>"
            msg['Reply-To'] = reply_to_clean
            msg['To'] = to_email_clean
            msg['Subject'] = Header("HUGAN JOB 採用サービスのご案内", 'utf-8')

            # 迷惑メール対策のための追加ヘッダー
            msg['Message-ID'] = f"<{tracking_id}@hugan.co.jp>"
            msg['Date'] = formatdate(localtime=True)
            msg['X-Mailer'] = 'HUGAN JOB Marketing System'
            msg['X-Priority'] = '3'
            msg['Precedence'] = 'bulk'

            # プレーンテキスト版を作成（HTMLメールの代替）
            plain_text = self.html_to_plain_text(email_content)
            text_part = MIMEText(plain_text, 'plain', 'utf-8')
            msg.attach(text_part)

            # HTMLパートを追加
            html_part = MIMEText(email_content, 'html', 'utf-8')
            msg.attach(html_part)

            # メール送信（SMTP認証用のアドレスを使用）
            self.smtp_server.sendmail(smtp_auth_email, [to_email_clean], msg.as_string())

            logger.info(f"メール送信成功: {to_email_clean} ({company_name})")
            return True, tracking_id

        except Exception as e:
            logger.error(f"メール送信に失敗しました: {to_email} - {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False, None
    
    def disconnect_smtp(self):
        """SMTP接続を切断"""
        try:
            if self.smtp_server:
                self.smtp_server.quit()
                logger.info("SMTP接続を切断しました")
        except Exception as e:
            logger.error(f"SMTP切断エラー: {e}")
    
    def save_sending_results(self, results):
        """送信結果を保存"""
        try:
            output_file = 'data/derivative_ad_email_sending_results.csv'
            
            # 結果をDataFrameに変換
            df = pd.DataFrame(results)
            
            # CSVファイルとして保存
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            logger.info(f"送信結果を保存しました: {output_file} ({len(results)}件)")
            return True
            
        except Exception as e:
            logger.error(f"送信結果の保存に失敗しました: {e}")
            return False

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='派生版広告営業メール送信')
    parser.add_argument('--input-file', default='data/derivative_ad_input.csv', help='入力CSVファイル')
    parser.add_argument('--email-file', help='メール抽出結果ファイル（自動検出）')
    parser.add_argument('--start-id', type=int, default=1, help='開始ID')
    parser.add_argument('--end-id', type=int, default=10, help='終了ID')
    parser.add_argument('--test-mode', action='store_true', help='テストモード（実際には送信しない）')

    args = parser.parse_args()

    print("📧 派生版広告営業メール送信スクリプト")
    print("=" * 50)
    print(f"入力ファイル: {args.input_file}")
    print(f"送信範囲: ID {args.start_id} - {args.end_id}")
    print(f"テストモード: {'有効' if args.test_mode else '無効'}")
    print("=" * 50)

    try:
        # 入力ファイルの確認
        if not os.path.exists(args.input_file):
            logger.error(f"入力ファイルが見つかりません: {args.input_file}")
            return False

        # メール抽出結果ファイルを自動検出
        email_file = args.email_file
        if not email_file:
            # 最新のメール抽出結果ファイルを検索
            import glob
            email_files = glob.glob('derivative_email_extraction_results_*.csv')
            if email_files:
                email_file = max(email_files, key=os.path.getctime)
                logger.info(f"メール抽出結果ファイルを自動検出: {email_file}")
            else:
                logger.error("メール抽出結果ファイルが見つかりません")
                return False

        # 企業データを読み込み
        df = pd.read_csv(args.input_file, encoding='utf-8-sig')
        logger.info(f"企業データを読み込みました: {len(df)}社")

        # メール抽出結果を読み込み
        email_df = pd.read_csv(email_file, encoding='utf-8-sig')
        logger.info(f"メール抽出結果を読み込みました: {len(email_df)}件")

        # 指定範囲のデータを抽出
        target_companies = df[(df['id'] >= args.start_id) & (df['id'] <= args.end_id)]
        logger.info(f"送信対象: {len(target_companies)}社")

        if len(target_companies) == 0:
            logger.warning("送信対象の企業がありません")
            return False
        
        # メール送信クラスを初期化
        sender = AdEmailSender()
        
        # テンプレートを読み込み
        template_content = sender.load_ad_template()
        if not template_content:
            return False
        
        # SMTP接続（テストモードでない場合）
        if not args.test_mode:
            if not sender.connect_smtp():
                return False
        
        # メール送信処理
        results = []
        success_count = 0

        for _, company in target_companies.iterrows():
            company_id = company['id']
            company_name = company['company_name']

            # メール抽出結果から対応するメールアドレスを取得
            email_row = email_df[email_df['企業ID'] == company_id]
            if email_row.empty:
                logger.warning(f"企業ID {company_id} のメールアドレスが見つかりません: {company_name}")
                continue

            email = email_row.iloc[0]['メールアドレス']
            logger.info(f"送信準備: {company_name} -> {email}")

            if args.test_mode:
                # テストモード
                logger.info(f"[テスト] メール送信: {email} ({company_name})")
                success = True
                tracking_id = str(uuid.uuid4())
            else:
                # 実際の送信
                success, tracking_id = sender.send_email(email, company_name, template_content)

            # 結果を記録
            result = {
                'id': company_id,
                'company_name': company_name,
                'email': email,
                'campaign_type': 'ad_agency',
                'sent_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'tracking_id': tracking_id,
                'status': 'sent' if success else 'failed'
            }
            results.append(result)

            if success:
                success_count += 1

            # 送信間隔（1秒）
            time.sleep(1)
        
        # SMTP接続を切断
        if not args.test_mode:
            sender.disconnect_smtp()
        
        # 結果を保存
        sender.save_sending_results(results)
        
        # 結果表示
        print("\n" + "=" * 50)
        print("📊 送信結果")
        print("=" * 50)
        print(f"送信対象: {len(target_companies)}社")
        print(f"送信成功: {success_count}社")
        print(f"送信失敗: {len(target_companies) - success_count}社")
        print(f"成功率: {(success_count / len(target_companies) * 100):.1f}%")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"メール送信処理中にエラーが発生しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
