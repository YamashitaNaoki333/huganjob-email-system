#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡単なテストメール送信スクリプト
SMTP接続とメール送信の動作確認用
"""

import smtplib
import configparser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr, formatdate

def main():
    try:
        print("📧 簡単なテストメール送信開始")
        
        # 設定読み込み
        config = configparser.ConfigParser()
        config.read('config/huganjob_email_config.ini', encoding='utf-8')
        
        # SMTP設定
        smtp_server = config.get('SMTP', 'server')
        smtp_port = int(config.get('SMTP', 'port'))
        smtp_user = config.get('SMTP', 'user')
        smtp_password = config.get('SMTP', 'password')
        
        print(f"SMTP: {smtp_server}:{smtp_port}")
        print(f"User: {smtp_user}")
        
        # テストメール作成
        msg = MIMEMultipart()
        msg['Subject'] = Header('HUGANJOB テストメール', 'utf-8')
        msg['From'] = formataddr((config.get('SMTP', 'sender_name'), config.get('SMTP', 'from_email')))
        msg['To'] = 'naoki_yamashita@fortyfive.co.jp'
        msg['Date'] = formatdate(localtime=True)
        
        # 本文
        body = """
        <html>
        <body>
        <h2>HUGANJOB テストメール</h2>
        <p>これはHUGANJOB営業メール送信システムのテストメールです。</p>
        <p>送信日時: 2025年06月23日</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        
        # SMTP接続・送信
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        print("✅ テストメール送信成功")
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"結果: {'成功' if success else '失敗'}")
