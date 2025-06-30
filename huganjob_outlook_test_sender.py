#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB Outlook互換性テスト送信システム
Outlook互換版HTMLメールテンプレートのテスト送信

作成日: 2025年06月20日
目的: Outlookでの背景色表示問題解決のためのテスト送信
"""

import smtplib
import configparser
import os
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
import time

def load_config():
    """設定ファイルを読み込み"""
    config = configparser.ConfigParser()
    config_path = 'config/huganjob_email_config.ini'
    
    if not os.path.exists(config_path):
        print(f"設定ファイルが見つかりません: {config_path}")
        return None
    
    config.read(config_path, encoding='utf-8')
    return config

def create_outlook_test_email(recipient_email, recipient_name="テスト企業"):
    """Outlook互換性テスト用メール作成"""
    msg = MIMEMultipart('alternative')
    
    # 件名（Outlook互換性テスト用）
    msg['Subject'] = '【HUGAN JOB】Outlook表示テスト - 初期費用0円の人材紹介サービス'
    
    # プレーンテキスト版
    text_content = f"""
{recipient_name} ご担当者様

HUGAN JOB Outlook表示テストメールです。

【テスト内容】
- HTMLメールの背景色表示確認
- Outlook互換性の検証
- CSSインライン化の効果確認

このメールがHTMLで正しく表示されているかご確認ください。

---
HUGAN JOB 企業様向け人材紹介サービス
Email: contact@huganjob.jp
配信停止: https://forms.gle/49BTNfSgUeNkH7rz5

送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
送信先: {recipient_email}
テスト版: Outlook互換性確認
"""
    
    text_part = MIMEText(text_content.strip(), 'plain', 'utf-8')
    msg.attach(text_part)
    
    # メインHTMLテンプレート読み込み
    html_template_path = 'corporate-email-newsletter.html'
    if os.path.exists(html_template_path):
        with open(html_template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # テンプレート変数の置換
        html_content = html_content.replace('{{会社名}}', recipient_name)

        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        print("  HTMLメール作成完了")
    else:
        print(f"  HTMLテンプレートが見つかりません: {html_template_path}")
        print("  プレーンテキストのみで送信")
    
    return msg

def send_outlook_test_email(config, recipient_email, recipient_name="テスト企業"):
    """Outlook互換性テスト送信"""
    try:
        print(f"\nOutlook互換性テスト送信開始")
        print(f"   送信先: {recipient_email}")
        print(f"   企業名: {recipient_name}")

        # SMTP設定取得
        smtp_server = config.get('SMTP', 'server')
        smtp_port = config.getint('SMTP', 'port')
        smtp_user = config.get('SMTP', 'user')
        smtp_password = config.get('SMTP', 'password')
        sender_name = config.get('SMTP', 'sender_name')
        sender_email = config.get('SMTP', 'from_email')

        print(f"   SMTPサーバー: {smtp_server}:{smtp_port}")
        print(f"   送信者: {sender_name} <{sender_email}>")

        # メール作成
        msg = create_outlook_test_email(recipient_email, recipient_name)

        # RFC5322準拠のFrom:ヘッダー設定
        from_header = formataddr((sender_name, sender_email))
        msg['From'] = from_header
        msg['To'] = recipient_email
        msg['Reply-To'] = sender_email

        print(f"   From:ヘッダー: {from_header}")

        # SMTP接続・送信
        print("  SMTP接続中...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)

            print("  メール送信中...")
            server.send_message(msg)

        print(f"  Outlook互換性テスト送信成功: {recipient_email}")
        return True

    except Exception as e:
        print(f"  送信エラー: {str(e)}")
        return False

def main():
    """メイン処理"""
    print("=" * 60)
    print("HUGAN JOB Outlook互換性テスト送信システム")
    print("=" * 60)
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 設定読み込み
    print("設定ファイル読み込み中...")
    config = load_config()
    if not config:
        print("設定ファイルの読み込みに失敗しました")
        return

    print("設定ファイル読み込み完了")

    # テスト送信先の入力
    print("\nテスト送信設定")
    
    # デフォルトのテスト送信先
    default_email = "naoki_yamashita@fortyfive.co.jp"
    
    test_email = input(f"テスト送信先メールアドレス (Enter={default_email}): ").strip()
    if not test_email:
        test_email = default_email
    
    test_company = input("テスト企業名 (Enter=テスト企業): ").strip()
    if not test_company:
        test_company = "テスト企業"
    
    print(f"\n送信設定確認")
    print(f"   送信先: {test_email}")
    print(f"   企業名: {test_company}")
    print(f"   テンプレート: corporate-email-newsletter.html")

    # 確認
    confirm = input("\n送信を実行しますか？ (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("送信をキャンセルしました")
        return

    # テスト送信実行
    print("\nOutlook互換性テスト送信実行")
    success = send_outlook_test_email(config, test_email, test_company)

    if success:
        print("\n" + "=" * 60)
        print("Outlook互換性テスト送信完了")
        print("=" * 60)
        print()
        print("確認事項:")
        print("1. メールが正常に受信されているか")
        print("2. HTMLメールとして表示されているか")
        print("3. 背景色が正しく表示されているか")
        print("4. Outlookでの表示に問題がないか")
        print("5. モバイル端末での表示確認")
        print()
        print("特に確認すべきポイント:")
        print("- ヘッダー部分の青色背景 (#3498db)")
        print("- ヒーロー部分の濃いグレー背景 (#2c3e50)")
        print("- メリット部分の薄いグレー背景 (#f8f9fa)")
        print("- CTA部分の濃いグレー背景 (#2c3e50)")
        print("- フッター部分の濃いグレー背景 (#2c3e50)")
        print()
        print("テスト結果をお知らせください")
    else:
        print("\nOutlook互換性テスト送信に失敗しました")

if __name__ == "__main__":
    main()
