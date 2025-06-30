#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
複数アドレスへのテストメール送信スクリプト
指定された3つのメールアドレスにテストメールを送信します
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
from email.utils import formatdate

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
    if '"' in domain_part:
        domain_part = domain_part.split('"')[0]

    # 複数の@がある場合の処理
    if '@' in domain_part:
        domain_part = domain_part.split('@')[0]

    return f"{local_part}@{domain_part}"

def send_test_email(to_email, company_name="テスト企業"):
    """テストメールを送信"""
    print(f"\n📧 送信中: {to_email} ({company_name})")
    print("-" * 50)
    
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

        # Fromヘッダーを適切に設定（client@hugan.co.jpとして表示）
        msg['From'] = f"{sender_name} <{from_email_clean}>"
        msg['Reply-To'] = reply_to_clean
        msg['Sender'] = smtp_user
        msg['To'] = to_email_clean
        msg['Subject'] = Header("【採用ご担当者様へ】採用工数の削減とミスマッチ防止を実現するご提案｜HUGAN JOB", 'utf-8')
        
        # 迷惑メール対策のための追加ヘッダー
        msg['Message-ID'] = f"<test-{int(time.time())}-{uuid.uuid4().hex[:8]}@hugan.co.jp>"
        msg['Date'] = formatdate(localtime=True)
        msg['X-Mailer'] = 'HUGAN JOB Marketing System'
        msg['X-Priority'] = '3'

        # プレーンテキスト版を作成
        plain_text = f"""
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

送信ID: {msg['Message-ID']}
送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        # プレーンテキストパートを追加
        text_part = MIMEText(plain_text.strip(), 'plain', 'utf-8')
        msg.attach(text_part)

        # HTMLテンプレートを読み込み
        template_path = 'corporate-email-newsletter.html'
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
            
            # 会社名を置換
            html_content = html_template.replace('{{会社名}}', company_name)
            
            # HTMLパートを追加
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            print("✅ HTMLメール作成成功")
        else:
            print("⚠️ HTMLテンプレートが見つかりません（プレーンテキストのみ）")

        # メール送信
        print(f"🔍 送信詳細:")
        print(f"   SMTP User: {smtp_user}")
        print(f"   To Address: {to_email_clean}")
        print(f"   From Header: {msg['From']}")
        print(f"   Reply-To Header: {msg.get('Reply-To', 'なし')}")

        # 実際の送信
        send_result = server.sendmail(smtp_user, [to_email_clean], msg.as_string())
        server.quit()

        print("✅ メール送信成功！")
        print(f"📧 送信者: {msg['From']}")
        print(f"📧 宛先: {to_email_clean}")
        print(f"📧 件名: 【採用ご担当者様へ】採用工数の削減とミスマッチ防止を実現するご提案｜HUGAN JOB")
        print(f"📧 形式: HTMLメール（プレーンテキスト代替付き）")
        print(f"📧 メッセージID: {msg['Message-ID']}")
        print(f"📧 送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ メール送信に失敗: {e}")
        import traceback
        print(f"詳細エラー: {traceback.format_exc()}")
        return False

def main():
    """メイン処理"""
    print("=" * 80)
    print("📧 HUGAN JOB 複数アドレステストメール送信")
    print("=" * 80)
    
    # 送信対象のメールアドレス
    test_emails = [
        ("raxus.yamashita@gmail.com", "司法書士法人中央ライズアクロス"),
        ("naoki_yamashita@fortyfive.co.jp", "おばた司法書士事務所"),
        ("n.yamashita@raxus.inc", "司法書士法人テスト")
    ]
    
    success_count = 0
    total_count = len(test_emails)
    
    for i, (email, company) in enumerate(test_emails, 1):
        print(f"\n🔄 {i}/{total_count} 送信処理中...")
        
        if send_test_email(email, company):
            success_count += 1
            print(f"✅ {email} への送信完了")
        else:
            print(f"❌ {email} への送信失敗")
        
        # 送信間隔（最後以外）
        if i < total_count:
            print("⏳ 送信間隔: 3秒待機中...")
            time.sleep(3)
    
    # 結果表示
    print("\n" + "=" * 80)
    print("📊 送信結果サマリー")
    print("=" * 80)
    print(f"送信対象: {total_count}件")
    print(f"送信成功: {success_count}件")
    print(f"送信失敗: {total_count - success_count}件")
    print(f"成功率: {(success_count / total_count * 100):.1f}%")
    
    if success_count == total_count:
        print("🎉 全てのメール送信が成功しました！")
    else:
        print("⚠️ 一部のメール送信が失敗しました。")
    
    print("\n📋 受信確認:")
    print("1. 各メールアドレスの受信トレイを確認してください")
    print("2. 迷惑メールフォルダも確認してください")
    print("3. HTMLメールが正しく表示されるか確認してください")
    print("4. 送信者が 'HUGAN採用事務局 <client@hugan.co.jp>' として表示されるか確認してください")
    print("=" * 80)
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
