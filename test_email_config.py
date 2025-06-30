#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
メール設定テストスクリプト
設定ファイルの読み込みと基本的な動作確認
"""

import os
import configparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formatdate

def test_config():
    """設定ファイルのテスト"""
    print("=" * 60)
    print("📧 HUGAN JOB メール設定テスト")
    print("=" * 60)
    
    # 設定ファイルを読み込み
    config_file = 'config/derivative_email_config.ini'
    if not os.path.exists(config_file):
        print(f"❌ 設定ファイルが見つかりません: {config_file}")
        return False
    
    try:
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        print("✅ 設定ファイルを読み込みました")
    except Exception as e:
        print(f"❌ 設定ファイルの読み込みに失敗: {e}")
        return False
    
    # 設定内容を表示
    print("\n📋 SMTP設定:")
    print(f"  サーバー: {config.get('SMTP', 'server')}")
    print(f"  ポート: {config.get('SMTP', 'port')}")
    print(f"  認証ユーザー: {config.get('SMTP', 'smtp_auth_email', fallback=config.get('SMTP', 'user'))}")
    print(f"  送信者名: {config.get('SMTP', 'sender_name')}")
    print(f"  送信者アドレス: {config.get('SMTP', 'from_email')}")
    print(f"  返信先アドレス: {config.get('SMTP', 'reply_to')}")
    
    print("\n📋 迷惑メール対策設定:")
    if config.has_section('ANTI_SPAM'):
        print(f"  HTMLメール: {config.get('ANTI_SPAM', 'use_html_format')}")
        print(f"  追跡ピクセル: {config.get('ANTI_SPAM', 'add_tracking_pixel')}")
        print(f"  マルチパート: {config.get('ANTI_SPAM', 'use_multipart_alternative')}")
        print(f"  送信間隔: {config.get('ANTI_SPAM', 'send_interval')}秒")
    else:
        print("  迷惑メール対策設定なし")
    
    return True

def test_smtp_connection():
    """SMTP接続テスト"""
    print("\n🔗 SMTP接続テスト")
    print("-" * 40)
    
    # 設定ファイルを読み込み
    config = configparser.ConfigParser()
    config.read('config/derivative_email_config.ini', encoding='utf-8')
    
    try:
        smtp_server = config.get('SMTP', 'server')
        smtp_port = int(config.get('SMTP', 'port'))
        smtp_user = config.get('SMTP', 'smtp_auth_email', fallback=config.get('SMTP', 'user'))
        smtp_password = config.get('SMTP', 'password')
        
        print(f"📡 接続中: {smtp_server}:{smtp_port}")
        print(f"👤 認証ユーザー: {smtp_user}")
        
        # SMTP接続
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.quit()
        
        print("✅ SMTP接続成功")
        return True
        
    except Exception as e:
        print(f"❌ SMTP接続失敗: {e}")
        return False

def create_test_email():
    """テストメールの作成"""
    print("\n📧 テストメール作成")
    print("-" * 40)
    
    # 設定ファイルを読み込み
    config = configparser.ConfigParser()
    config.read('config/derivative_email_config.ini', encoding='utf-8')
    
    try:
        sender_name = config.get('SMTP', 'sender_name')
        from_email = config.get('SMTP', 'from_email')
        reply_to = config.get('SMTP', 'reply_to')
        
        # メールメッセージを作成
        msg = MIMEMultipart('alternative')
        
        # ヘッダー設定
        msg['From'] = f"{sender_name} <{from_email}>"
        msg['Reply-To'] = reply_to
        msg['To'] = "test@example.com"
        msg['Subject'] = Header("【採用ご担当者様へ】採用工数の削減とミスマッチ防止を実現するご提案｜HUGAN JOB", 'utf-8')
        
        # 迷惑メール対策ヘッダー
        msg['Message-ID'] = f"<test-{int(time.time())}@hugan.co.jp>"
        msg['Date'] = formatdate(localtime=True)
        msg['X-Mailer'] = 'HUGAN JOB Marketing System'
        msg['X-Priority'] = '3'
        
        # プレーンテキスト版
        plain_text = """
テスト企業 採用ご担当者様

いつもお世話になっております。
HUGAN JOB採用事務局です。

採用活動でお困りのことはございませんか？

HUGAN JOBでは、以下のサービスで採用活動をサポートしております：

■ 主なサービス内容
・採用工数の削減
・ミスマッチ防止
・効率的な人材紹介
・採用プロセスの最適化

詳細につきましては、お気軽にお問い合わせください。

---
HUGAN JOB採用事務局
Email: client@hugan.co.jp

※このメールは営業目的で送信しております。
※配信停止をご希望の場合は、返信にてお知らせください。
"""
        
        text_part = MIMEText(plain_text.strip(), 'plain', 'utf-8')
        msg.attach(text_part)
        
        # HTMLテンプレートの確認
        template_path = 'corporate-email-newsletter.html'
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
            
            # 会社名を置換
            html_content = html_template.replace('{{会社名}}', 'テスト企業')
            
            # HTMLパートを追加
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            print("✅ HTMLメール作成成功")
        else:
            print("⚠️ HTMLテンプレートが見つかりません（プレーンテキストのみ）")
        
        print(f"📧 送信者: {msg['From']}")
        print(f"📧 返信先: {msg['Reply-To']}")
        print(f"📧 件名: {msg['Subject']}")
        print(f"📧 メッセージID: {msg['Message-ID']}")
        
        return True
        
    except Exception as e:
        print(f"❌ テストメール作成失敗: {e}")
        return False

def main():
    """メイン処理"""
    import time
    
    success = True
    
    # 設定ファイルテスト
    if not test_config():
        success = False
    
    # SMTP接続テスト
    if not test_smtp_connection():
        success = False
    
    # テストメール作成
    if not create_test_email():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 全てのテストが成功しました")
        print("📧 メール送信システムは正常に動作する準備ができています")
    else:
        print("❌ 一部のテストが失敗しました")
        print("🔧 設定を確認してください")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    import time
    success = main()
    exit(0 if success else 1)
