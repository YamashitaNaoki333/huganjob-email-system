#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HUGAN JOB メール設定セットアップスクリプト
client@hugan.co.jp用のメール設定を対話的に行います
"""

import os
import configparser
import getpass
import smtplib
from email.mime.text import MIMEText
from email.header import Header

def main():
    print("=" * 60)
    print("🏢 HUGAN JOB メール設定セットアップ")
    print("=" * 60)
    print()
    
    # 現在の設定を表示
    config_file = 'config/derivative_email_config.ini'
    if os.path.exists(config_file):
        print("📋 現在の設定:")
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        
        if 'SMTP' in config:
            print(f"  送信者名: {config.get('SMTP', 'sender_name', fallback='未設定')}")
            print(f"  メールアドレス: {config.get('SMTP', 'from_email', fallback='未設定')}")
            print(f"  SMTPサーバー: {config.get('SMTP', 'server', fallback='未設定')}")
            print(f"  ポート: {config.get('SMTP', 'port', fallback='未設定')}")
            print(f"  パスワード: {'設定済み' if config.get('SMTP', 'password', fallback='') != '[要設定]' else '未設定'}")
        print()
    
    # パスワード入力
    print("🔐 メールアカウント設定")
    print("client@hugan.co.jp のパスワードを入力してください:")
    password = getpass.getpass("パスワード: ")
    
    if not password:
        print("❌ パスワードが入力されませんでした。")
        return False
    
    # SMTPサーバー設定の確認
    print("\n📡 SMTPサーバー設定")
    print("デフォルト設定を使用しますか？")
    print("  サーバー: smtp.hugan.co.jp")
    print("  ポート: 587")
    
    use_default = input("デフォルト設定を使用する場合は Enter、カスタム設定の場合は 'n' を入力: ").strip().lower()
    
    if use_default == 'n':
        smtp_server = input("SMTPサーバー: ").strip()
        smtp_port = input("ポート番号 (587): ").strip() or "587"
    else:
        smtp_server = "smtp.hugan.co.jp"
        smtp_port = "587"
    
    # 設定ファイルを更新
    print("\n💾 設定ファイルを更新中...")
    
    config = configparser.ConfigParser()
    config.read(config_file, encoding='utf-8')
    
    # SMTP設定を更新
    if 'SMTP' not in config:
        config.add_section('SMTP')
    
    config.set('SMTP', 'server', smtp_server)
    config.set('SMTP', 'port', smtp_port)
    config.set('SMTP', 'user', 'client@hugan.co.jp')
    config.set('SMTP', 'username', 'client@hugan.co.jp')
    config.set('SMTP', 'password', password)
    config.set('SMTP', 'sender_name', 'HUGAN採用事務局')
    config.set('SMTP', 'from_name', 'HUGAN採用事務局')
    config.set('SMTP', 'from_email', 'client@hugan.co.jp')
    config.set('SMTP', 'reply_to', 'client@hugan.co.jp')
    
    # email設定を更新
    if 'email' not in config:
        config.add_section('email')
    
    imap_server = smtp_server.replace('smtp', 'imap')
    config.set('email', 'imap_server', imap_server)
    config.set('email', 'imap_port', '993')
    config.set('email', 'username', 'client@hugan.co.jp')
    config.set('email', 'password', password)
    
    # IMAP設定を更新
    if 'IMAP' not in config:
        config.add_section('IMAP')
    
    config.set('IMAP', 'server', imap_server)
    config.set('IMAP', 'port', '993')
    
    # ファイルに保存
    with open(config_file, 'w', encoding='utf-8') as f:
        config.write(f)
    
    print("✅ 設定ファイルが更新されました。")
    
    # 接続テスト
    print("\n🔍 SMTP接続テスト中...")
    
    try:
        # SMTP接続テスト
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login('client@hugan.co.jp', password)
        server.quit()
        
        print("✅ SMTP接続テスト成功！")
        
        # テストメール送信の確認
        print("\n📧 テストメール送信")
        send_test = input("テストメールを送信しますか？ (y/N): ").strip().lower()
        
        if send_test == 'y':
            test_email = input("テスト送信先メールアドレス: ").strip()
            if test_email:
                send_test_email(smtp_server, int(smtp_port), 'client@hugan.co.jp', password, test_email)
        
        print("\n🎉 HUGAN JOB メール設定が完了しました！")
        print("\n次のステップ:")
        print("1. テストモードでメール送信を実行:")
        print("   python core_scripts/derivative_ad_email_sender.py --start-id 1 --end-id 1 --test-mode")
        print("2. 問題がなければ本番送信を実行")
        
        return True
        
    except Exception as e:
        print(f"❌ SMTP接続テスト失敗: {e}")
        print("\n🔧 トラブルシューティング:")
        print("1. メールアドレスとパスワードを確認してください")
        print("2. SMTPサーバーアドレスを確認してください")
        print("3. ネットワーク接続を確認してください")
        print("4. HUGAN_EMAIL_SETUP_GUIDE.md を参照してください")
        
        return False

def send_test_email(smtp_server, smtp_port, email, password, test_email):
    """テストメールを送信"""
    try:
        # メール作成
        msg = MIMEText("HUGAN JOB メール設定テストメールです。", 'plain', 'utf-8')
        msg['From'] = f"HUGAN採用事務局 <{email}>"
        msg['To'] = test_email
        msg['Subject'] = Header("HUGAN JOB メール設定テスト", 'utf-8')
        
        # 送信
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email, password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ テストメールを {test_email} に送信しました。")
        
    except Exception as e:
        print(f"❌ テストメール送信失敗: {e}")

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
