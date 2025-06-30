#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB 直接メール送信スクリプト
ID 1-5の企業に対する営業メール送信

作成日時: 2025年06月23日 11:50:00
作成者: AI Assistant
"""

import smtplib
import pandas as pd
import configparser
import logging
import sys
import os
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/huganjob_direct_sender.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_config():
    """設定ファイル読み込み"""
    config = configparser.ConfigParser()
    config.read('config/huganjob_email_config.ini', encoding='utf-8')
    return config

def load_email_template():
    """メールテンプレート読み込み"""
    try:
        with open('corporate-email-newsletter.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"テンプレート読み込みエラー: {e}")
        return None

def load_email_addresses():
    """メールアドレス抽出結果読み込み"""
    try:
        df = pd.read_csv('huganjob_email_resolution_results.csv', encoding='utf-8')
        return df
    except Exception as e:
        logger.error(f"メールアドレス結果読み込みエラー: {e}")
        return None

def create_email_message(config, template, company_name, job_position, recipient_email):
    """メールメッセージ作成"""
    try:
        # テンプレート内の変数を置換
        email_content = template.replace('{{company_name}}', str(company_name))
        email_content = email_content.replace('{{job_position}}', str(job_position))
        
        # 件名作成
        subject_template = config.get('EMAIL_CONTENT', 'subject')
        subject = subject_template.replace('{job_position}', str(job_position))
        
        # メッセージ作成
        msg = MIMEMultipart('alternative')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = formataddr((config.get('SMTP', 'sender_name'), config.get('SMTP', 'from_email')))
        msg['To'] = recipient_email
        msg['Reply-To'] = config.get('SMTP', 'reply_to')
        msg['Date'] = formatdate(localtime=True)
        
        # HTMLパート追加
        html_part = MIMEText(email_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        return msg
        
    except Exception as e:
        logger.error(f"メールメッセージ作成エラー: {e}")
        return None

def send_email(config, msg, recipient_email):
    """メール送信"""
    try:
        # SMTP接続
        smtp_server = config.get('SMTP', 'server')
        smtp_port = int(config.get('SMTP', 'port'))
        smtp_user = config.get('SMTP', 'user')
        smtp_password = config.get('SMTP', 'password')
        
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        
        if config.getboolean('SECURITY', 'use_tls'):
            server.starttls()
        
        if config.getboolean('SECURITY', 'require_auth'):
            server.login(smtp_user, smtp_password)
        
        # メール送信
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✅ メール送信成功: {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ メール送信失敗: {recipient_email} - {e}")
        return False

def main():
    """メイン処理"""
    logger.info("=" * 60)
    logger.info("📧 HUGAN JOB 直接メール送信開始")
    logger.info("=" * 60)
    
    # 設定読み込み
    config = load_config()
    logger.info("✅ 設定ファイル読み込み完了")
    
    # テンプレート読み込み
    template = load_email_template()
    if not template:
        logger.error("❌ テンプレート読み込み失敗")
        return False
    logger.info("✅ メールテンプレート読み込み完了")
    
    # メールアドレス結果読み込み
    email_df = load_email_addresses()
    if email_df is None:
        logger.error("❌ メールアドレス結果読み込み失敗")
        return False
    logger.info("✅ メールアドレス結果読み込み完了")
    
    # デバッグ情報
    logger.info(f"📊 読み込んだデータ行数: {len(email_df)}")
    logger.info(f"📊 データ列名: {list(email_df.columns)}")

    # ID 1-5の企業データ取得
    target_companies = email_df[email_df['company_id'].isin([1, 2, 3, 4, 5])].copy()

    logger.info(f"📊 フィルタ後データ行数: {len(target_companies)}")

    if target_companies.empty:
        logger.error("❌ ID 1-5の企業データが見つかりません")
        logger.info("📊 利用可能なcompany_id一覧:")
        logger.info(f"   {sorted(email_df['company_id'].unique())}")
        return False

    logger.info(f"📋 送信対象企業数: {len(target_companies)}社")

    # メール送信実行
    success_count = 0
    total_count = len(target_companies)

    for index, row in target_companies.iterrows():
        company_id = row['company_id']
        company_name = row['company_name']
        job_position = row['job_position']
        email_address = row['final_email']
        
        logger.info(f"\n📤 送信中: ID {company_id} - {company_name}")
        logger.info(f"   📧 宛先: {email_address}")
        logger.info(f"   💼 職種: {job_position}")
        
        # メールメッセージ作成
        msg = create_email_message(config, template, company_name, job_position, email_address)
        if not msg:
            logger.error(f"❌ メッセージ作成失敗: {company_name}")
            continue
        
        # メール送信
        if send_email(config, msg, email_address):
            success_count += 1
        
        # 送信間隔
        if index < len(target_companies) - 1:
            interval = int(config.get('SENDING', 'interval'))
            logger.info(f"   ⏳ 送信間隔待機中（{interval}秒）...")
            time.sleep(interval)
    
    # 結果表示
    logger.info("\n" + "=" * 60)
    logger.info("📊 送信結果")
    logger.info("=" * 60)
    logger.info(f"✅ 成功: {success_count}/{total_count}")
    logger.info(f"❌ 失敗: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        logger.info("\n🎉 全ての営業メール送信が完了しました！")
        return True
    else:
        logger.info("\n⚠️  一部の送信に失敗しました")
        return False

if __name__ == "__main__":
    # ログディレクトリ作成
    os.makedirs('logs', exist_ok=True)
    
    success = main()
    exit(0 if success else 1)
