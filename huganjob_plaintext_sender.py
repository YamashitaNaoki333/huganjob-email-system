#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB プレーンテキスト専用送信システム
迷惑メール判定対策版 - HTMLを完全に削除したプレーンテキスト送信

作成日: 2025年6月27日
目的: 迷惑メール判定問題の完全解決
特徴: 
- HTMLを完全削除
- 最小限のヘッダー
- 自然な文面
- 配信停止リンク最適化
"""

import smtplib
import csv
import json
import time
import argparse
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid, formataddr
from email.header import Header
import pandas as pd
import os
from urllib.parse import urlparse

class HuganjobPlaintextSender:
    def __init__(self):
        # SMTP設定
        self.smtp_server = "smtp.huganjob.jp"
        self.smtp_port = 587
        self.smtp_username = "contact@huganjob.jp"
        self.smtp_password = "gD34bEmB"
        
        # 送信者情報
        self.sender_name = "竹下隼平【株式会社HUGAN】"
        self.sender_email = "contact@huganjob.jp"
        
        # ファイルパス
        self.csv_file = "data/new_input_test.csv"
        self.results_file = "huganjob_plaintext_results.csv"
        self.history_file = "huganjob_plaintext_history.json"
        self.unsubscribe_log = "data/huganjob_unsubscribe_log.json"
        
        # 送信間隔（迷惑メール対策）
        self.send_interval = 60  # 60秒間隔
        
        # ログ設定
        self.setup_logging()
        
        # 送信履歴
        self.sending_history = self.load_sending_history()
        
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/huganjob_plaintext_sender.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_sending_history(self):
        """送信履歴を読み込み"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"送信履歴読み込みエラー: {e}")
            return {}
            
    def save_sending_history(self):
        """送信履歴を保存"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.sending_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"送信履歴保存エラー: {e}")
            
    def load_unsubscribe_log(self):
        """配信停止ログを読み込み"""
        try:
            if os.path.exists(self.unsubscribe_log):
                with open(self.unsubscribe_log, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            self.logger.error(f"配信停止ログ読み込みエラー: {e}")
            return []
            
    def check_unsubscribe_status(self, recipient_email, company_data=None):
        """配信停止状況をチェック（ドメインベース対応）"""
        unsubscribe_log = self.load_unsubscribe_log()
        recipient_email_lower = recipient_email.lower().strip()
        
        for entry in unsubscribe_log:
            # 完全一致チェック
            if entry.get('email', '').lower().strip() == recipient_email_lower:
                return True, entry.get('reason', '配信停止申請')
                
            # ドメインベースチェック
            if company_data and '@' in recipient_email_lower:
                recipient_domain = recipient_email_lower.split('@')[1]
                
                # 企業ホームページのドメインと照合
                company_url = company_data.get('企業ホームページ', '')
                if company_url and company_url not in ['‐', '-', '']:
                    try:
                        if not company_url.startswith(('http://', 'https://')):
                            company_url = 'https://' + company_url
                        parsed_url = urlparse(company_url)
                        company_domain = parsed_url.netloc.lower().replace('www.', '')
                        
                        if recipient_domain == company_domain:
                            return True, f"ドメイン一致による配信停止（{entry.get('reason', '配信停止申請')}）"
                    except Exception:
                        pass
                        
        return False, None
        
    def create_plaintext_email(self, company_name, job_position, recipient_email):
        """プレーンテキストメールを作成"""
        
        # 件名（自然で営業色を抑えた表現）
        subject = f"{job_position}の採用について - HUGAN JOB"
        
        # メール本文（自然で読みやすい文章）
        body = f"""{company_name} 採用ご担当者様

いつもお疲れ様です。
株式会社HUGANの竹下と申します。

{company_name}様の{job_position}の採用活動について、
弊社の人材紹介サービスでお手伝いできることがございます。

【弊社サービスの特徴】
・採用工数の削減
・ミスマッチの防止
・質の高い人材のご紹介

もしご興味をお持ちいただけましたら、
お気軽にお問い合わせください。

【お問い合わせ先】
株式会社HUGAN
担当: 竹下隼平
Email: contact@huganjob.jp

※配信停止をご希望の場合は、このメールにご返信ください。

--
株式会社HUGAN
竹下隼平
Email: contact@huganjob.jp"""

        # MIMETextでプレーンテキストメールを作成
        msg = MIMEText(body, 'plain', 'utf-8')
        
        # 最小限のヘッダー（迷惑メール判定回避・RFC5322準拠）
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = formataddr((self.sender_name, self.sender_email))
        msg['To'] = recipient_email
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid(domain='huganjob.jp')
        
        return msg, subject
        
    def send_email(self, start_id=None, end_id=None):
        """メール送信実行"""
        
        # 企業データを読み込み
        try:
            df = pd.read_csv(self.csv_file, encoding='utf-8-sig')
        except Exception as e:
            self.logger.error(f"CSVファイル読み込みエラー: {e}")
            return
            
        # ID範囲でフィルタリング
        if start_id is not None:
            df = df[df['ID'] >= start_id]
        if end_id is not None:
            df = df[df['ID'] <= end_id]
            
        self.logger.info(f"送信対象: {len(df)}社")
        
        # 送信結果記録用
        results = []
        
        # SMTP接続
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            for index, row in df.iterrows():
                try:
                    company_id = str(row['ID'])
                    company_name = row['企業名']
                    job_position = row['募集職種'].split('/')[0] if pd.notna(row['募集職種']) else 'システムエンジニア'
                    
                    # メールアドレス決定
                    email_address = row.get('担当者メールアドレス', '')
                    if pd.isna(email_address) or email_address in ['', '未登録', '-', '‐']:
                        # 企業ホームページからドメイン生成
                        website = row.get('企業ホームページ', '')
                        if website and website not in ['‐', '-', '']:
                            try:
                                if not website.startswith(('http://', 'https://')):
                                    website = 'https://' + website
                                parsed_url = urlparse(website)
                                domain = parsed_url.netloc.replace('www.', '')
                                email_address = f"info@{domain}"
                            except:
                                self.logger.warning(f"ID {company_id}: ドメイン生成失敗")
                                continue
                        else:
                            self.logger.warning(f"ID {company_id}: メールアドレス不明")
                            continue
                    
                    # 配信停止チェック（一時的に無効化）
                    # is_unsubscribed, unsubscribe_reason = self.check_unsubscribe_status(
                    #     email_address, row.to_dict()
                    # )
                    # if is_unsubscribed:
                    #     self.logger.info(f"ID {company_id}: 配信停止済み - {unsubscribe_reason}")
                    #     results.append({
                    #         'company_id': company_id,
                    #         'company_name': company_name,
                    #         'email': email_address,
                    #         'status': '配信停止済み',
                    #         'timestamp': datetime.now().isoformat(),
                    #         'reason': unsubscribe_reason
                    #     })
                    #     continue
                    
                    # メール作成
                    msg, subject = self.create_plaintext_email(
                        company_name, job_position, email_address
                    )
                    
                    # メール送信
                    server.send_message(msg)
                    
                    # 送信成功記録
                    timestamp = datetime.now().isoformat()
                    self.sending_history[company_id] = {
                        'company_name': company_name,
                        'email': email_address,
                        'subject': subject,
                        'timestamp': timestamp,
                        'status': '送信成功'
                    }
                    
                    results.append({
                        'company_id': company_id,
                        'company_name': company_name,
                        'email': email_address,
                        'status': '送信成功',
                        'timestamp': timestamp,
                        'subject': subject
                    })
                    
                    self.logger.info(f"ID {company_id}: {company_name} - 送信成功 ({email_address})")
                    
                    # 送信間隔（迷惑メール対策）
                    time.sleep(self.send_interval)
                    
                except Exception as e:
                    self.logger.error(f"ID {company_id}: 送信エラー - {e}")
                    results.append({
                        'company_id': company_id,
                        'company_name': company_name,
                        'email': email_address if 'email_address' in locals() else '',
                        'status': '送信失敗',
                        'timestamp': datetime.now().isoformat(),
                        'error': str(e)
                    })
                    
            server.quit()
            
        except Exception as e:
            self.logger.error(f"SMTP接続エラー: {e}")
            return
            
        # 結果保存
        self.save_results(results)
        self.save_sending_history()
        
        self.logger.info(f"送信完了: {len(results)}件処理")
        
    def save_results(self, results):
        """送信結果をCSVファイルに保存"""
        try:
            # 既存ファイルがあるかチェック
            file_exists = os.path.exists(self.results_file)
            
            # CSVファイルに追記
            with open(self.results_file, 'a', newline='', encoding='utf-8-sig') as f:
                fieldnames = ['company_id', 'company_name', 'email', 'status', 'timestamp', 'subject', 'reason', 'error']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # ヘッダー書き込み（新規ファイルの場合）
                if not file_exists:
                    writer.writeheader()
                
                # データ書き込み
                for result in results:
                    writer.writerow(result)
                    
            self.logger.info(f"送信結果保存完了: {self.results_file}")
            
        except Exception as e:
            self.logger.error(f"送信結果保存エラー: {e}")

def main():
    parser = argparse.ArgumentParser(description='HUGANJOB プレーンテキスト専用送信システム')
    parser.add_argument('--start-id', type=int, help='送信開始ID')
    parser.add_argument('--end-id', type=int, help='送信終了ID')
    
    args = parser.parse_args()
    
    sender = HuganjobPlaintextSender()
    sender.send_email(args.start_id, args.end_id)

if __name__ == "__main__":
    main()
