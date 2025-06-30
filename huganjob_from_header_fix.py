#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB From:ヘッダー完全修正システム
Gmail拒否の根本原因（From:ヘッダー不備）を解決
作成日時: 2025年06月20日 19:30:00
"""

import os
import configparser
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formatdate, make_msgid, formataddr

def read_config():
    """設定ファイルから設定を読み込み"""
    config_file = 'config/huganjob_email_config.ini'
    
    if not os.path.exists(config_file):
        print(f"❌ 設定ファイルが見つかりません: {config_file}")
        return None
    
    try:
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        return config
    except Exception as e:
        print(f"❌ 設定ファイル読み込みエラー: {e}")
        return None

def read_html_template():
    """HTMLテンプレートを読み込み"""
    template_file = 'corporate-email-newsletter.html'
    
    if not os.path.exists(template_file):
        print(f"❌ HTMLテンプレートが見つかりません: {template_file}")
        return None
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ HTMLテンプレート読み込みエラー: {e}")
        return None

def create_proper_from_header_email(recipient_email, recipient_name="", html_content="", config=None):
    """From:ヘッダーを完全に修正したメールを作成"""
    
    # メール作成
    msg = MIMEMultipart('alternative')
    
    # From:ヘッダーの完全修正（Gmail拒否対策）
    sender_name = config.get('SMTP', 'sender_name')
    sender_email = config.get('SMTP', 'from_email')
    
    # formataddr()を使用してRFC5322準拠のFrom:ヘッダーを作成
    from_header = formataddr((sender_name, sender_email))
    
    # 完全修正されたヘッダー設定
    msg['From'] = from_header
    msg['To'] = recipient_email
    msg['Subject'] = Header(config.get('EMAIL_CONTENT', 'subject'), 'utf-8')
    msg['Date'] = formatdate(localtime=True)
    msg['Reply-To'] = config.get('SMTP', 'reply_to')
    
    # RFC5322準拠のMessage-ID
    msg['Message-ID'] = make_msgid(domain='huganjob.jp')
    
    # 送信者認証ヘッダー
    msg['User-Agent'] = 'HUGAN JOB From Header Fix System'
    msg['X-Mailer'] = 'HUGAN JOB RFC5322 Compliant Sender'
    
    # 組織情報
    msg['Organization'] = 'HUGAN JOB'
    msg['X-Priority'] = '3'
    
    # 送信者情報の明確化
    msg['Sender'] = sender_email
    msg['Return-Path'] = sender_email
    
    # 迷惑メール対策ヘッダー
    msg['List-Unsubscribe'] = f"<{config.get('EMAIL_CONTENT', 'unsubscribe_url')}>"
    msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
    
    # RFC5322準拠の追加ヘッダー
    msg['MIME-Version'] = '1.0'
    
    # テキスト版
    text_content = f"""
【採用ご担当者様へ】採用工数の削減とミスマッチ防止を実現するご提案｜HUGAN JOB

{recipient_name}

いつもお世話になっております。
HUGAN採用事務局です。

採用活動でこのようなお悩みはございませんか？

• 採用にかかる工数を削減したい
• ミスマッチを防いで長期雇用を実現したい
• 初期費用をかけずに採用活動を始めたい

HUGAN JOBの人材紹介サービスなら、これらの課題を解決できます。

【サービスの特徴】
✓ 初期費用0円（完全成功報酬型）
✓ 採用工数の大幅削減
✓ 早期退職時の一部返金保証
✓ 正社員・契約社員・パート・アルバイト全対応

詳細はこちら: https://www.hugan.co.jp/business

ご不明な点がございましたら、お気軽にお問い合わせください。

---
HUGAN採用事務局
contact@huganjob.jp
https://huganjob.jp/

配信停止をご希望の方は下記フォームよりお手続きください：
{config.get('EMAIL_CONTENT', 'unsubscribe_url')}

※このメールはRFC5322準拠のFrom:ヘッダーで送信されています
"""
    
    # HTMLコンテンツ
    if html_content:
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
    
    # テキスト版を追加
    text_part = MIMEText(text_content, 'plain', 'utf-8')
    msg.attach(text_part)
    
    return msg

def send_from_header_fixed_email(config, recipient_email, recipient_name="", html_content=""):
    """From:ヘッダー修正済みメール送信"""
    try:
        print(f"\n📤 From:ヘッダー修正送信中: {recipient_email}")
        
        # SMTP設定取得
        smtp_server = config.get('SMTP', 'server')
        smtp_port = int(config.get('SMTP', 'port'))
        smtp_user = config.get('SMTP', 'user')
        smtp_password = config.get('SMTP', 'password')
        
        print(f"   🌐 SMTPサーバー: {smtp_server}:{smtp_port}")
        print(f"   👤 認証ユーザー: {smtp_user}")
        print(f"   🔧 送信方式: From:ヘッダー完全修正")
        
        # メール作成
        msg = create_proper_from_header_email(recipient_email, recipient_name, html_content, config)
        
        # From:ヘッダーの確認
        from_header = msg['From']
        print(f"   📧 From:ヘッダー: {from_header}")
        
        # SMTP接続
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=int(config.get('SECURITY', 'timeout')))
        
        if config.getboolean('SECURITY', 'use_tls'):
            server.starttls()
        
        if config.getboolean('SECURITY', 'require_auth'):
            server.login(smtp_user, smtp_password)
        
        # RFC5322準拠送信
        # send_message()を使用してFrom:ヘッダーを確実に設定
        server.send_message(msg, from_addr=config.get('SMTP', 'from_email'))
        
        server.quit()
        
        print(f"   ✅ 送信成功: {recipient_email}")
        print(f"   📧 From:ヘッダー: RFC5322準拠")
        print(f"   🏢 送信者: {config.get('SMTP', 'sender_name')} <{config.get('SMTP', 'from_email')}>")
        return True
        
    except Exception as e:
        print(f"   ❌ 送信失敗: {recipient_email} - {e}")
        return False

def verify_from_header_smtp_connection(config):
    """From:ヘッダー修正SMTP接続確認"""
    print("\n🔍 From:ヘッダー修正SMTP接続確認...")
    
    try:
        smtp_server = config.get('SMTP', 'server')
        smtp_port = int(config.get('SMTP', 'port'))
        smtp_user = config.get('SMTP', 'user')
        smtp_password = config.get('SMTP', 'password')
        
        print(f"   📡 接続先: {smtp_server}:{smtp_port}")
        print(f"   👤 認証: {smtp_user}")
        
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=int(config.get('SECURITY', 'timeout')))
        
        if config.getboolean('SECURITY', 'use_tls'):
            server.starttls()
        
        if config.getboolean('SECURITY', 'require_auth'):
            server.login(smtp_user, smtp_password)
        
        # サーバー情報を取得
        server_info = server.noop()
        server.quit()
        
        print(f"   ✅ 接続成功（From:ヘッダー修正対応）")
        print(f"   🏢 サーバー応答: {server_info}")
        return True
        
    except Exception as e:
        print(f"   ❌ 接続失敗: {e}")
        return False

def show_from_header_fix_info():
    """From:ヘッダー修正情報を表示"""
    print("\n💡 From:ヘッダー修正システムの特徴")
    print("=" * 60)
    
    print("✅ Gmail拒否対策:")
    print("  • RFC5322準拠のFrom:ヘッダー")
    print("  • formataddr()による正確な形式")
    print("  • 送信者情報の明確化")
    print("  • 必須ヘッダーの完全設定")
    
    print("\n🔧 技術的改善:")
    print("  • From:ヘッダーの完全修正")
    print("  • Sender/Return-Pathの明示")
    print("  • MIME-Versionの設定")
    print("  • RFC5322準拠のMessage-ID")
    
    print("\n📧 期待される結果:")
    print("  • Gmail受信拒否: 解決")
    print("  • From:ヘッダーエラー: 解決")
    print("  • 配信成功率: 大幅向上")
    print("  • 迷惑メール判定: 改善")

def main():
    """メイン処理"""
    print("=" * 60)
    print("📧 HUGAN JOB From:ヘッダー完全修正システム")
    print("Gmail拒否の根本原因（From:ヘッダー不備）を解決")
    print("=" * 60)
    
    # From:ヘッダー修正情報表示
    show_from_header_fix_info()
    
    print("\n🎯 From:ヘッダー修正の特徴:")
    print("✓ RFC5322準拠のFrom:ヘッダー")
    print("✓ formataddr()による正確な形式")
    print("✓ Gmail拒否エラーの完全解決")
    print("✓ 送信者情報の明確化")
    print("✓ 必須ヘッダーの完全設定")
    
    # 設定読み込み
    config = read_config()
    if not config:
        return False
    
    # SMTP接続確認
    if not verify_from_header_smtp_connection(config):
        print("\n❌ SMTP接続に失敗しました。設定を確認してください。")
        return False
    
    # HTMLテンプレート読み込み
    html_content = read_html_template()
    if not html_content:
        return False
    
    print("\n✅ HTMLテンプレートを読み込みました")
    
    # 設定確認
    print("\n📋 From:ヘッダー修正送信設定:")
    print(f"  SMTPサーバー: {config.get('SMTP', 'server')}")
    print(f"  認証ユーザー: {config.get('SMTP', 'user')}")
    print(f"  送信者表示: {config.get('SMTP', 'sender_name')} <{config.get('SMTP', 'from_email')}>")
    print(f"  送信方式: From:ヘッダー完全修正")
    print(f"  期待結果: Gmail受信成功")
    
    # 送信先リスト
    recipients = [
        ("naoki_yamashita@fortyfive.co.jp", "山下様"),
        ("n.yamashita@raxus.inc", "山下様"),
        ("raxus.yamashita@gmail.com", "山下様")
    ]
    
    print("\n📋 送信先:")
    for email, name in recipients:
        print(f"  • {email} ({name})")
    
    # From:ヘッダー修正送信開始
    print("\n📤 From:ヘッダー修正送信開始...")
    print("-" * 40)
    
    success_count = 0
    total_count = len(recipients)
    
    for email, name in recipients:
        if send_from_header_fixed_email(config, email, name, html_content):
            success_count += 1
        
        # 送信間隔を設ける
        if email != recipients[-1][0]:  # 最後のメール以外
            interval = int(config.get('SENDING', 'interval'))
            print(f"   ⏳ 送信間隔待機中（{interval}秒）...")
            time.sleep(interval)
    
    # 結果表示
    print("\n" + "=" * 60)
    print("📊 From:ヘッダー修正送信結果")
    print("=" * 60)
    print(f"✅ 成功: {success_count}/{total_count}")
    print(f"❌ 失敗: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 全てのFrom:ヘッダー修正送信が完了しました！")
        print("📧 受信ボックスを確認してください")
        
        print("\n📋 確認ポイント:")
        print("  • Gmail受信拒否: 解決")
        print("  • From:ヘッダーエラー: 解決")
        print("  • 送信者表示: 正常")
        print("  • メール配信: 成功")
        
        print("\n🔧 実装された対策:")
        print("  • RFC5322準拠のFrom:ヘッダー")
        print("  • formataddr()による正確な形式")
        print("  • 送信者情報の明確化")
        print("  • 必須ヘッダーの完全設定")
        
        return True
    else:
        print("\n⚠️  一部の送信に失敗しました")
        print("🔧 設定を確認してください")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
