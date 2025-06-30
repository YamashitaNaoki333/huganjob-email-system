#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB SendGrid完全独立送信システム
桜サーバー完全回避 - SendGrid経由送信
作成日時: 2025年06月20日 19:00:00
"""

import os
import configparser
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formatdate, make_msgid

def create_sendgrid_config_if_not_exists():
    """SendGrid設定ファイルが存在しない場合は作成"""
    config_file = 'config/sendgrid_independent_config.ini'
    
    if not os.path.exists(config_file):
        print("📝 SendGrid設定ファイルを作成中...")
        
        config_dir = 'config'
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        config_content = """# HUGAN JOB SendGrid完全独立設定
# 桜サーバー完全回避 - SendGrid経由送信

[SMTP]
# SendGrid SMTP設定（桜サーバー完全回避）
server = smtp.sendgrid.net
port = 587
user = apikey
password = [SendGrid APIキーを設定してください]
sender_name = HUGAN採用事務局
from_email = contact@huganjob.jp
reply_to = contact@huganjob.jp

[SENDGRID]
api_key = [SendGrid APIキーを設定してください]
from_email = contact@huganjob.jp
from_name = HUGAN採用事務局
domain_authentication = huganjob.jp

[EMAIL_CONTENT]
subject = 【採用ご担当者様へ】採用工数の削減とミスマッチ防止を実現するご提案｜HUGAN JOB
template_file = corporate-email-newsletter.html
unsubscribe_url = https://forms.gle/49BTNfSgUeNkH7rz5

[SENDING]
interval = 5
max_per_hour = 50
method = send_message

[SECURITY]
use_tls = true
require_auth = true
timeout = 30

[INDEPENDENCE]
# 桜サーバー完全回避確認
sakura_free = true
independent_smtp = true
dns_independent = true
"""
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"✅ SendGrid設定ファイルを作成: {config_file}")
        print("\n🔧 次のステップ:")
        print("1. SendGridアカウントを作成: https://sendgrid.com/")
        print("2. APIキーを取得")
        print("3. 設定ファイルのAPIキーを更新")
        print("4. huganjob.jpドメインを認証")
        
        return False
    
    return True

def read_sendgrid_config():
    """SendGrid設定を読み込み"""
    config_file = 'config/sendgrid_independent_config.ini'
    
    if not create_sendgrid_config_if_not_exists():
        return None
    
    try:
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        
        # APIキーが設定されているかチェック
        api_key = config.get('SMTP', 'password')
        if api_key == '[SendGrid APIキーを設定してください]':
            print("❌ SendGrid APIキーが設定されていません")
            print("🔧 設定ファイルを編集してAPIキーを設定してください")
            print(f"📄 設定ファイル: {config_file}")
            return None
        
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

def create_sendgrid_email(recipient_email, recipient_name="", html_content="", config=None):
    """SendGrid用メールを作成（桜サーバー完全回避）"""
    
    # メール作成
    msg = MIMEMultipart('alternative')
    
    # SendGrid完全独立ヘッダー設定
    msg['From'] = f"{config.get('SMTP', 'sender_name')} <{config.get('SMTP', 'from_email')}>"
    msg['To'] = recipient_email
    msg['Subject'] = Header(config.get('EMAIL_CONTENT', 'subject'), 'utf-8')
    msg['Date'] = formatdate(localtime=True)
    msg['Reply-To'] = config.get('SMTP', 'reply_to')
    
    # huganjob.jpドメイン統一設定
    msg['Message-ID'] = make_msgid(domain='huganjob.jp')
    msg['User-Agent'] = 'HUGAN JOB SendGrid Independent System'
    msg['X-Mailer'] = 'HUGAN JOB SendGrid Sender v1.0'
    
    # SendGrid特有のヘッダー
    msg['X-SMTPAPI'] = '{"category": ["huganjob_independent"]}'
    msg['X-SendGrid-Source'] = 'huganjob.jp'
    
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

※このメールはSendGrid経由でcontact@huganjob.jpから送信されています（桜サーバー完全回避）
"""
    
    # HTMLコンテンツ
    if html_content:
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
    
    # テキスト版を追加
    text_part = MIMEText(text_content, 'plain', 'utf-8')
    msg.attach(text_part)
    
    return msg

def send_sendgrid_email(config, recipient_email, recipient_name="", html_content=""):
    """SendGrid経由でメール送信（桜サーバー完全回避）"""
    try:
        print(f"\n📤 SendGrid独立送信中: {recipient_email}")
        
        # SendGrid SMTP設定取得
        smtp_server = config.get('SMTP', 'server')
        smtp_port = int(config.get('SMTP', 'port'))
        smtp_user = config.get('SMTP', 'user')
        smtp_password = config.get('SMTP', 'password')
        
        print(f"   🌐 SMTPサーバー: {smtp_server}:{smtp_port}")
        print(f"   👤 認証: {smtp_user}")
        print(f"   🔧 送信方式: SendGrid完全独立")
        print(f"   🚫 桜サーバー: 完全回避")
        
        # メール作成
        msg = create_sendgrid_email(recipient_email, recipient_name, html_content, config)
        
        # SendGrid SMTP接続
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=int(config.get('SECURITY', 'timeout')))
        
        if config.getboolean('SECURITY', 'use_tls'):
            server.starttls()
        
        if config.getboolean('SECURITY', 'require_auth'):
            server.login(smtp_user, smtp_password)
        
        # SendGrid経由送信（桜サーバー完全回避）
        server.send_message(msg)
        
        server.quit()
        
        print(f"   ✅ 送信成功: {recipient_email}")
        print(f"   📧 送信者: {config.get('SMTP', 'sender_name')} <{config.get('SMTP', 'from_email')}>")
        print(f"   🏢 経由: SendGrid (smtp.sendgrid.net)")
        print(f"   🚫 桜サーバー経由: 完全回避")
        return True
        
    except Exception as e:
        print(f"   ❌ 送信失敗: {recipient_email} - {e}")
        return False

def verify_sendgrid_connection(config):
    """SendGrid接続確認"""
    print("\n🔍 SendGrid独立接続確認...")
    
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
        
        print(f"   ✅ SendGrid接続成功")
        print(f"   🏢 サーバー応答: {server_info}")
        print(f"   🚫 桜サーバー: 完全回避")
        return True
        
    except Exception as e:
        print(f"   ❌ SendGrid接続失敗: {e}")
        return False

def show_sendgrid_setup_guide():
    """SendGrid設定ガイドを表示"""
    print("\n📚 SendGrid設定ガイド（桜サーバー完全回避）")
    print("=" * 60)
    
    print("🚀 ステップ1: SendGridアカウント作成")
    print("  1. https://sendgrid.com/ にアクセス")
    print("  2. 無料アカウントを作成（月100通無料）")
    print("  3. メールアドレス認証を完了")
    
    print("\n🔑 ステップ2: APIキー取得")
    print("  1. SendGridダッシュボードにログイン")
    print("  2. Settings > API Keys を選択")
    print("  3. 'Create API Key' をクリック")
    print("  4. 'Full Access' を選択")
    print("  5. APIキーをコピー")
    
    print("\n🌐 ステップ3: ドメイン認証")
    print("  1. Settings > Sender Authentication を選択")
    print("  2. 'Authenticate Your Domain' をクリック")
    print("  3. huganjob.jp を入力")
    print("  4. 提供されたDNSレコードを設定")
    
    print("\n⚙️ ステップ4: 設定ファイル更新")
    print("  1. config/sendgrid_independent_config.ini を編集")
    print("  2. password = [APIキー] に設定")
    print("  3. 設定を保存")
    
    print("\n✅ ステップ5: テスト送信")
    print("  1. python huganjob_sendgrid_independent.py を実行")
    print("  2. 送信結果を確認")
    
    print("\n🎯 期待される効果:")
    print("  • 桜サーバー経由: 完全回避")
    print("  • 配信率: 95%以上")
    print("  • 迷惑メール判定: 大幅改善")
    print("  • 送信者表示: huganjob.jpのみ")

def main():
    """メイン処理"""
    print("=" * 60)
    print("📧 HUGAN JOB SendGrid完全独立送信システム")
    print("桜サーバー完全回避 - SendGrid経由送信")
    print("=" * 60)
    
    print("\n🎯 SendGrid完全独立の特徴:")
    print("✓ 桜サーバー経由の完全回避")
    print("✓ smtp.sendgrid.net 経由送信")
    print("✓ 高い配信率（95%以上）")
    print("✓ 詳細な配信統計")
    print("✓ 迷惑メール対策強化")
    print("✓ DNS設定に依存しない独立性")
    
    # 設定読み込み
    config = read_sendgrid_config()
    if not config:
        show_sendgrid_setup_guide()
        return False
    
    # SendGrid接続確認
    if not verify_sendgrid_connection(config):
        print("\n❌ SendGrid接続に失敗しました。")
        print("🔧 APIキーと設定を確認してください。")
        show_sendgrid_setup_guide()
        return False
    
    # HTMLテンプレート読み込み
    html_content = read_html_template()
    if not html_content:
        return False
    
    print("\n✅ HTMLテンプレートを読み込みました")
    
    # 設定確認
    print("\n📋 SendGrid独立送信設定:")
    print(f"  SMTPサーバー: {config.get('SMTP', 'server')}")
    print(f"  認証方式: APIキー認証")
    print(f"  送信者表示: {config.get('SMTP', 'sender_name')} <{config.get('SMTP', 'from_email')}>")
    print(f"  送信方式: SendGrid完全独立")
    print(f"  桜サーバー経由: 完全回避")
    
    # 送信先リスト
    recipients = [
        ("naoki_yamashita@fortyfive.co.jp", "山下様"),
        ("n.yamashita@raxus.inc", "山下様"),
        ("raxus.yamashita@gmail.com", "山下様")
    ]
    
    print("\n📋 送信先:")
    for email, name in recipients:
        print(f"  • {email} ({name})")
    
    # SendGrid独立送信開始
    print("\n📤 SendGrid独立送信開始...")
    print("-" * 40)
    
    success_count = 0
    total_count = len(recipients)
    
    for email, name in recipients:
        if send_sendgrid_email(config, email, name, html_content):
            success_count += 1
        
        # 送信間隔を設ける
        if email != recipients[-1][0]:  # 最後のメール以外
            interval = int(config.get('SENDING', 'interval'))
            print(f"   ⏳ 送信間隔待機中（{interval}秒）...")
            time.sleep(interval)
    
    # 結果表示
    print("\n" + "=" * 60)
    print("📊 SendGrid独立送信結果")
    print("=" * 60)
    print(f"✅ 成功: {success_count}/{total_count}")
    print(f"❌ 失敗: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 全てのSendGrid独立送信が完了しました！")
        print("📧 受信ボックスを確認してください")
        
        print("\n📋 確認ポイント:")
        print("  • from: HUGAN採用事務局 <contact@huganjob.jp>")
        print("  • mailed-by: sendgrid.net")
        print("  • 桜サーバー表示: 一切なし")
        print("  • SendGrid経由での送信")
        print("  • 高い配信率")
        
        print("\n🔧 実装された対策:")
        print("  • 桜サーバー完全回避")
        print("  • SendGrid独立SMTP使用")
        print("  • DNS設定に依存しない独立性")
        print("  • 高品質メール配信")
        
        return True
    else:
        print("\n⚠️  一部の送信に失敗しました")
        print("🔧 SendGrid設定を確認してください")
        show_sendgrid_setup_guide()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
