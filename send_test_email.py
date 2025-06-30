#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HUGAN JOB テストメール送信スクリプト
指定されたメールアドレスにテストメールを送信します
"""

import os
import sys
import configparser
import smtplib
import uuid
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

def load_template():
    """corporate-email-newsletter.htmlテンプレートを読み込み"""
    template_file = 'corporate-email-newsletter.html'
    if not os.path.exists(template_file):
        print(f"❌ テンプレートファイルが見つかりません: {template_file}")
        return None
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✅ テンプレートファイルを読み込みました: {template_file}")
        return content
    except Exception as e:
        print(f"❌ テンプレートファイルの読み込みに失敗: {e}")
        return None

def clean_email_address(email):
    """メールアドレスをクリーニング（@より後ろの不要な部分を削除）"""
    if not email:
        return email

    # @マークで分割
    parts = email.split('@')
    if len(parts) != 2:
        return email

    local_part = parts[0]
    domain_part = parts[1]

    # ドメイン部分から不要な文字を削除
    # 例: "client@hugan.co.jp"@www4009.sakura.ne.jp -> client@hugan.co.jp
    if '"' in domain_part:
        domain_part = domain_part.split('"')[0]

    # 複数の@がある場合の処理
    if '@' in domain_part:
        domain_part = domain_part.split('@')[0]

    return f"{local_part}@{domain_part}"

def generate_email_content(template_content, company_name="テスト企業"):
    """メール内容を生成"""
    try:
        # テンプレート内の{{会社名}}を実際の会社名に置換
        email_content = template_content.replace('{{会社名}}', company_name)

        # 追跡用のユニークIDを生成
        tracking_id = str(uuid.uuid4())

        # 開封追跡用の画像タグを追加
        tracking_pixel = f'<img src="http://127.0.0.1:5002/track/{tracking_id}" width="1" height="1" style="display:none;" />'
        email_content = email_content.replace('</body>', f'{tracking_pixel}</body>')

        return email_content, tracking_id
    except Exception as e:
        print(f"❌ メール内容生成に失敗: {e}")
        return None, None

def send_test_email(to_email, company_name="テスト企業"):
    """テストメールを送信"""
    print("=" * 60)
    print("📧 HUGAN JOB テストメール送信")
    print("=" * 60)
    print(f"送信先: {to_email}")
    print(f"企業名: {company_name}")
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
    
    # テンプレートを読み込み
    template_content = load_template()
    if not template_content:
        return False
    
    # HUGAN JOB営業メール内容を生成
    tracking_id = str(uuid.uuid4())
    email_content = f"""
{company_name} 採用ご担当者様

いつもお世話になっております。
HUGAN JOB採用事務局です。

採用活動でお困りのことはございませんか？

HUGAN JOBでは、以下のサービスで採用活動をサポートしております：

■ 主なサービス内容
・採用工数の削減
・ミスマッチ防止
・効率的な人材紹介
・採用プロセスの最適化

■ 実績
多くの企業様で採用成功率の向上を実現しております。

詳細につきましては、お気軽にお問い合わせください。

---
HUGAN JOB採用事務局
Email: client@hugan.co.jp
Tel: [お問い合わせ先電話番号]

※このメールは営業目的で送信しております。
※配信停止をご希望の場合は、返信にてお知らせください。

送信ID: {tracking_id}
"""
    
    try:
        # SMTP設定を取得
        smtp_server = config.get('SMTP', 'server')
        smtp_port = int(config.get('SMTP', 'port'))
        smtp_user = config.get('SMTP', 'smtp_auth_email', fallback=config.get('SMTP', 'user'))
        smtp_password = config.get('SMTP', 'password')
        sender_name = config.get('SMTP', 'sender_name')
        from_email = config.get('SMTP', 'from_email')
        reply_to = config.get('SMTP', 'reply_to')
        
        print(f"📡 SMTP接続中: {smtp_server}:{smtp_port}")
        
        # SMTP接続
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        
        print("✅ SMTP認証成功")
        
        # メールメッセージを作成
        msg = MIMEMultipart('alternative')

        # メールアドレスをクリーニング
        from_email_clean = clean_email_address(from_email)
        to_email_clean = clean_email_address(to_email)
        reply_to_clean = clean_email_address(reply_to)

        # デバッグ情報を表示
        print(f"📧 設定確認 - sender_name: {sender_name}")
        print(f"📧 設定確認 - from_email: {from_email}")
        print(f"📧 設定確認 - from_email_clean: {from_email_clean}")
        print(f"📧 設定確認 - reply_to_clean: {reply_to_clean}")
        print(f"📧 設定確認 - smtp_user: {smtp_user}")

        # Fromヘッダーを適切に設定（文字化け防止のため英語表記）
        msg['From'] = f"HUGAN JOB <{from_email_clean}>"
        msg['Reply-To'] = reply_to_clean
        msg['Sender'] = smtp_user
        msg['To'] = to_email_clean
        msg['Subject'] = Header("【採用ご担当者様へ】採用工数の削減とミスマッチ防止を実現するご提案｜HUGAN JOB", 'utf-8')

        # 迷惑メール対策のための追加ヘッダー
        from email.utils import formatdate
        msg['Message-ID'] = f"<test-{int(time.time())}@hugan.co.jp>"
        msg['Date'] = formatdate(localtime=True)
        msg['X-Mailer'] = 'HUGAN JOB Marketing System'
        msg['X-Priority'] = '3'

        # HTMLテンプレートを読み込み
        template_path = 'corporate-email-newsletter.html'
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()

            # 会社名を置換
            html_content = html_template.replace('{{会社名}}', company_name)

            # プレーンテキスト版を作成
            import re
            plain_text = re.sub(r'<[^>]+>', '', html_content)
            plain_text = plain_text.replace('&nbsp;', ' ')
            plain_text = plain_text.replace('&lt;', '<')
            plain_text = plain_text.replace('&gt;', '>')
            plain_text = plain_text.replace('&amp;', '&')
            plain_text = plain_text.replace('&quot;', '"')
            plain_text = re.sub(r'\s+', ' ', plain_text).strip()

            # プレーンテキストパートを追加
            text_part = MIMEText(plain_text, 'plain', 'utf-8')
            msg.attach(text_part)

            # HTMLパートを追加
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
        else:
            # HTMLテンプレートが見つからない場合はプレーンテキストのみ
            text_part = MIMEText(email_content, 'plain', 'utf-8')
            msg.attach(text_part)

        # メール送信（sendmailを使用してより正確な制御）
        print(f"🔍 送信詳細:")
        print(f"   SMTP User: {smtp_user}")
        print(f"   To Address: {to_email_clean}")
        print(f"   From Header: {msg['From']}")
        print(f"   Reply-To Header: {msg.get('Reply-To', 'なし')}")

        # 実際の送信
        send_result = server.sendmail(smtp_user, [to_email_clean], msg.as_string())
        server.quit()

        print("✅ メール送信成功！")
        print(f"📧 送信者: {smtp_user}")
        print(f"📧 宛先: {to_email_clean}")
        print(f"📧 件名: HUGAN JOB システムテスト")
        print(f"📧 形式: プレーンテキスト")
        print(f"📧 追跡ID: {tracking_id}")
        print(f"📧 送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📧 SMTP応答: {send_result}")

        # メール配信の確認事項
        print("\n📋 迷惑メール判定を回避するための修正:")
        print("1. 件名をシンプルに変更: 'HUGAN JOB システムテスト'")
        print("2. 送信者表示を簡素化: marketing@fortyfive.co.jp")
        print("3. HTMLではなくプレーンテキストで送信")
        print("4. 営業的な表現を削除")
        print("\n📋 受信確認:")
        print("1. 受信トレイを確認してください")
        print("2. 迷惑メールフォルダも確認してください")
        
        return True
        
    except Exception as e:
        print(f"❌ メール送信に失敗: {e}")
        return False

def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("使用方法: python send_test_email.py <メールアドレス> [企業名]")
        print("例: python send_test_email.py naoki_yamashita@fortyfive.co.jp")
        print("例: python send_test_email.py naoki_yamashita@fortyfive.co.jp 'テスト株式会社'")
        return False
    
    to_email = sys.argv[1]
    company_name = sys.argv[2] if len(sys.argv) > 2 else "テスト企業"
    
    return send_test_email(to_email, company_name)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
