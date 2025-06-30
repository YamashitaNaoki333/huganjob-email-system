#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修正版テストメール送信スクリプト
文字化け問題を解決したバージョン
"""

import os
import configparser
import smtplib
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formatdate

def clean_email_address(email):
    """メールアドレスをクリーニング（改良版）"""
    if not email:
        return email

    email_str = str(email).strip()
    
    # 引用符で囲まれている場合の処理
    if email_str.startswith('"') and '"' in email_str[1:]:
        quote_end = email_str.find('"', 1)
        if quote_end > 0:
            quoted_part = email_str[1:quote_end]
            if '<' in quoted_part and '>' in quoted_part:
                start = quoted_part.find('<') + 1
                end = quoted_part.find('>')
                if start > 0 and end > start:
                    return quoted_part[start:end]
    
    # @マークで分割
    parts = email_str.split('@')
    if len(parts) < 2:
        return email_str

    local_part = parts[0]
    domain_part = parts[1]

    # ドメイン部分から不要な文字を削除
    if '"' in domain_part:
        domain_part = domain_part.split('"')[0]

    # 複数の@がある場合の処理
    if '@' in domain_part:
        domain_part = domain_part.split('@')[0]
        
    domain_part = domain_part.strip()
    return f"{local_part}@{domain_part}"

def send_fixed_test():
    """修正版テストメール送信"""
    print("=" * 70)
    print("📧 HUGAN JOB 修正版テストメール送信")
    print("=" * 70)
    
    # 送信対象
    emails = [
        "raxus.yamashita@gmail.com",
        "naoki_yamashita@fortyfive.co.jp", 
        "n.yamashita@raxus.inc"
    ]
    
    # 設定読み込み
    config = configparser.ConfigParser()
    config.read('config/derivative_email_config.ini', encoding='utf-8')
    
    # SMTP設定
    smtp_server = config.get('SMTP', 'server')
    smtp_port = int(config.get('SMTP', 'port'))
    smtp_user = config.get('SMTP', 'smtp_auth_email', fallback=config.get('SMTP', 'user'))
    smtp_password = config.get('SMTP', 'password')
    sender_name = config.get('SMTP', 'sender_name')
    from_email = config.get('SMTP', 'from_email')
    reply_to = config.get('SMTP', 'reply_to')
    
    # アドレスをクリーニング
    from_email_clean = clean_email_address(from_email)
    reply_to_clean = clean_email_address(reply_to)
    
    print(f"📡 SMTP: {smtp_server}:{smtp_port}")
    print(f"👤 認証: {smtp_user}")
    print(f"📧 送信者: {sender_name} <{from_email_clean}>")
    print(f"↩️ 返信先: {reply_to_clean}")
    print(f"🔧 修正点: 英語表記で文字化け防止、アドレスクリーニング強化")
    
    success_count = 0
    
    try:
        # SMTP接続
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        print("✅ SMTP接続成功")
        
        for i, email in enumerate(emails, 1):
            print(f"\n🔄 {i}/3 送信中: {email}")
            
            try:
                # メッセージ作成
                msg = MIMEMultipart('alternative')
                
                # 文字化け防止のため英語表記を使用
                msg['From'] = f"HUGAN JOB <{from_email_clean}>"
                msg['Reply-To'] = reply_to_clean
                msg['To'] = email
                msg['Subject'] = Header("【採用ご担当者様へ】採用工数の削減とミスマッチ防止を実現するご提案｜HUGAN JOB", 'utf-8')
                msg['Message-ID'] = f"<test-fixed-{int(time.time())}-{i}@hugan.co.jp>"
                msg['Date'] = formatdate(localtime=True)
                msg['X-Mailer'] = 'HUGAN JOB Marketing System'
                msg['X-Priority'] = '3'
                
                # プレーンテキスト
                text_content = f"""
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

■ 実績
多くの企業様で採用成功率の向上を実現しております。

詳細につきましては、お気軽にお問い合わせください。

---
HUGAN JOB採用事務局
Email: client@hugan.co.jp
Tel: [お問い合わせ先電話番号]

※このメールは営業目的で送信しております。
※配信停止をご希望の場合は、返信にてお知らせください。

送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
送信先: {email}
修正版: 文字化け対策済み
"""
                
                text_part = MIMEText(text_content.strip(), 'plain', 'utf-8')
                msg.attach(text_part)
                
                # HTMLテンプレート読み込み
                if os.path.exists('corporate-email-newsletter.html'):
                    with open('corporate-email-newsletter.html', 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    html_content = html_content.replace('{{会社名}}', 'テスト企業')
                    html_part = MIMEText(html_content, 'html', 'utf-8')
                    msg.attach(html_part)
                    print("  📄 HTMLメール作成")
                else:
                    print("  📄 プレーンテキストのみ")
                
                # デバッグ情報
                print(f"  🔍 From: {msg['From']}")
                print(f"  🔍 Reply-To: {msg['Reply-To']}")
                print(f"  🔍 Message-ID: {msg['Message-ID']}")
                
                # 送信
                server.sendmail(smtp_user, [email], msg.as_string())
                print(f"  ✅ 送信成功: {email}")
                success_count += 1
                
                # 送信間隔
                if i < len(emails):
                    print("  ⏳ 3秒待機...")
                    time.sleep(3)
                    
            except Exception as e:
                print(f"  ❌ 送信失敗: {email} - {e}")
        
        server.quit()
        print("\n✅ SMTP接続終了")
        
    except Exception as e:
        print(f"❌ SMTP接続エラー: {e}")
        return False
    
    # 結果表示
    print("\n" + "=" * 70)
    print("📊 修正版送信結果")
    print("=" * 70)
    print(f"送信対象: {len(emails)}件")
    print(f"送信成功: {success_count}件")
    print(f"送信失敗: {len(emails) - success_count}件")
    print(f"成功率: {(success_count / len(emails) * 100):.1f}%")
    
    if success_count == len(emails):
        print("🎉 全てのメール送信が成功しました！")
    else:
        print("⚠️ 一部のメール送信が失敗しました。")
    
    print("\n📋 修正内容:")
    print("1. 送信者名を英語表記に変更（HUGAN JOB）")
    print("2. メールアドレスクリーニング機能を強化")
    print("3. 文字化け防止対策を実装")
    print("4. 不要なドメイン情報の除去")
    
    print("\n📋 受信確認:")
    print("1. 送信者が 'HUGAN JOB <client@hugan.co.jp>' として正しく表示されるか")
    print("2. 文字化けが発生していないか")
    print("3. HTMLメールが正しく表示されるか")
    print("4. 迷惑メールフォルダに入っていないか")
    print("=" * 70)
    
    return success_count == len(emails)

if __name__ == "__main__":
    try:
        success = send_fixed_test()
        print(f"\n🏁 修正版テスト完了: {'成功' if success else '失敗'}")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
