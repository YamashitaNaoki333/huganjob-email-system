#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB 完全新規送信システム
桜サーバー情報一切なし - 0から再構築
作成日時: 2025年06月20日 18:30:00
"""

import os
import configparser
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formatdate, make_msgid

def read_fresh_config():
    """完全新規設定ファイルから設定を読み込み"""
    config_file = 'config/huganjob_email_config.ini'
    
    if not os.path.exists(config_file):
        print(f"❌ 新規設定ファイルが見つかりません: {config_file}")
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

def create_fresh_email(recipient_email, recipient_name="", html_content="", config=None):
    """完全新規メールを作成（桜サーバー情報一切なし）"""
    
    # メール作成
    msg = MIMEMultipart('alternative')
    
    # 完全新規ヘッダー設定（桜サーバー情報一切なし）
    msg['From'] = f"{config.get('SMTP', 'sender_name')} <{config.get('SMTP', 'from_email')}>"
    msg['To'] = recipient_email
    msg['Subject'] = Header(config.get('EMAIL_CONTENT', 'subject'), 'utf-8')
    msg['Date'] = formatdate(localtime=True)
    msg['Reply-To'] = config.get('SMTP', 'reply_to')
    
    # huganjob.jpドメイン統一設定
    msg['Message-ID'] = make_msgid(domain='huganjob.jp')
    msg['User-Agent'] = 'HUGAN JOB Fresh System'
    msg['X-Mailer'] = 'HUGAN JOB Fresh Sender v1.0'
    
    # 組織情報
    msg['Organization'] = 'HUGAN JOB'
    msg['X-Priority'] = '3'
    
    # 迷惑メール対策ヘッダー
    msg['List-Unsubscribe'] = f"<{config.get('EMAIL_CONTENT', 'unsubscribe_url')}>"
    msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
    
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

※このメールは完全新規システムからhuganjob.jpより送信されています
"""
    
    # HTMLコンテンツ
    if html_content:
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
    
    # テキスト版を追加
    text_part = MIMEText(text_content, 'plain', 'utf-8')
    msg.attach(text_part)
    
    return msg

def send_fresh_email(config, recipient_email, recipient_name="", html_content=""):
    """完全新規送信（桜サーバー情報一切なし）"""
    try:
        print(f"\n📤 完全新規送信中: {recipient_email}")
        
        # SMTP設定取得
        smtp_server = config.get('SMTP', 'server')
        smtp_port = int(config.get('SMTP', 'port'))
        smtp_user = config.get('SMTP', 'user')
        smtp_password = config.get('SMTP', 'password')
        
        print(f"   🌐 SMTPサーバー: {smtp_server}:{smtp_port}")
        print(f"   👤 認証ユーザー: {smtp_user}")
        print(f"   🔧 送信方式: 完全新規システム")
        
        # メール作成
        msg = create_fresh_email(recipient_email, recipient_name, html_content, config)
        
        # SMTP接続
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=int(config.get('SECURITY', 'timeout')))
        
        if config.getboolean('SECURITY', 'use_tls'):
            server.starttls()
        
        if config.getboolean('SECURITY', 'require_auth'):
            server.login(smtp_user, smtp_password)
        
        # 完全新規送信（send_message()のみ使用）
        server.send_message(msg)
        
        server.quit()
        
        print(f"   ✅ 送信成功: {recipient_email}")
        print(f"   📧 送信者: {config.get('SMTP', 'sender_name')} <{config.get('SMTP', 'from_email')}>")
        print(f"   🏢 ドメイン: huganjob.jp のみ")
        return True
        
    except Exception as e:
        print(f"   ❌ 送信失敗: {recipient_email} - {e}")
        return False

def verify_fresh_smtp_connection(config):
    """完全新規SMTP接続確認"""
    print("\n🔍 完全新規SMTP接続確認...")
    
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
        
        print(f"   ✅ 接続成功（完全新規設定）")
        print(f"   🏢 サーバー応答: {server_info}")
        return True
        
    except Exception as e:
        print(f"   ❌ 接続失敗: {e}")
        return False

def show_fresh_system_info():
    """完全新規システム情報を表示"""
    print("\n💡 完全新規システムの特徴")
    print("=" * 60)
    
    print("✅ 完全新規設定:")
    print("  • 桜サーバー情報一切なし")
    print("  • huganjob.jpドメインのみ使用")
    print("  • 0から再構築された設定")
    print("  • クリーンなメールヘッダー")
    
    print("\n🔧 SMTP設定:")
    print("  • サーバー名: smtp.huganjob.jp")
    print("  • ポート: 587")
    print("  • ユーザー名: contact@huganjob.jp")
    print("  • 認証方式: 通常のパスワード認証")
    print("  • 接続の保護: STARTTLS")
    
    print("\n📧 期待される結果:")
    print("  • from: HUGAN採用事務局 <contact@huganjob.jp>")
    print("  • mailed-by: huganjob.jp")
    print("  • signed-by: huganjob.jp")
    print("  • 桜サーバー表示: 一切なし")

def main():
    """メイン処理"""
    print("=" * 60)
    print("📧 HUGAN JOB 完全新規送信システム")
    print("桜サーバー情報一切なし - 0から再構築")
    print("=" * 60)
    
    # 完全新規システム情報表示
    show_fresh_system_info()
    
    print("\n🎯 完全新規送信の特徴:")
    print("✓ 桜サーバー情報一切なし")
    print("✓ huganjob.jpドメインのみ使用")
    print("✓ send_message()メソッドのみ使用")
    print("✓ 0から再構築された設定")
    print("✓ 完全クリーンなメール配信")
    
    # 設定読み込み
    config = read_fresh_config()
    if not config:
        return False
    
    # SMTP接続確認
    if not verify_fresh_smtp_connection(config):
        print("\n❌ SMTP接続に失敗しました。設定を確認してください。")
        return False
    
    # HTMLテンプレート読み込み
    html_content = read_html_template()
    if not html_content:
        return False
    
    print("\n✅ HTMLテンプレートを読み込みました")
    
    # 設定確認
    print("\n📋 完全新規送信設定:")
    print(f"  SMTPサーバー: {config.get('SMTP', 'server')}")
    print(f"  認証ユーザー: {config.get('SMTP', 'user')}")
    print(f"  送信者表示: {config.get('SMTP', 'sender_name')} <{config.get('SMTP', 'from_email')}>")
    print(f"  送信方式: 完全新規システム")
    print(f"  期待結果: huganjob.jpのみ表示")
    
    # 送信先リスト
    recipients = [
        ("naoki_yamashita@fortyfive.co.jp", "山下様"),
        ("n.yamashita@raxus.inc", "山下様"),
        ("raxus.yamashita@gmail.com", "山下様")
    ]
    
    print("\n📋 送信先:")
    for email, name in recipients:
        print(f"  • {email} ({name})")
    
    # 完全新規送信開始
    print("\n📤 完全新規送信開始...")
    print("-" * 40)
    
    success_count = 0
    total_count = len(recipients)
    
    for email, name in recipients:
        if send_fresh_email(config, email, name, html_content):
            success_count += 1
        
        # 送信間隔を設ける
        if email != recipients[-1][0]:  # 最後のメール以外
            interval = int(config.get('SENDING', 'interval'))
            print(f"   ⏳ 送信間隔待機中（{interval}秒）...")
            time.sleep(interval)
    
    # 結果表示
    print("\n" + "=" * 60)
    print("📊 完全新規送信結果")
    print("=" * 60)
    print(f"✅ 成功: {success_count}/{total_count}")
    print(f"❌ 失敗: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 全ての完全新規送信が完了しました！")
        print("📧 受信ボックスを確認してください")
        
        print("\n📋 確認ポイント:")
        print("  • from: HUGAN採用事務局 <contact@huganjob.jp>")
        print("  • mailed-by: huganjob.jp")
        print("  • signed-by: huganjob.jp")
        print("  • 桜サーバー表示: 一切なし")
        print("  • huganjob.jpのみ表示")
        
        print("\n🔧 実装された対策:")
        print("  • 桜サーバー情報完全削除")
        print("  • 0から再構築された設定")
        print("  • send_message()メソッドのみ使用")
        print("  • 完全クリーンなメールヘッダー設定")
        
        return True
    else:
        print("\n⚠️  一部の送信に失敗しました")
        print("🔧 設定を確認してください")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
