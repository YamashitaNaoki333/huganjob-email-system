#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
クイックメール送信テスト
3つのメールアドレスに直接テストメールを送信
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

def send_quick_test():
    """クイックテストメール送信"""
    print("=" * 60)
    print("📧 HUGAN JOB クイックテストメール送信")
    print("=" * 60)
    
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
    
    print(f"📡 SMTP: {smtp_server}:{smtp_port}")
    print(f"👤 認証: {smtp_user}")
    print(f"📧 送信者: {sender_name} <{from_email}>")
    print(f"↩️ 返信先: {reply_to}")
    
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
                msg['From'] = f"HUGAN JOB <{from_email}>"
                msg['Reply-To'] = reply_to
                msg['To'] = email
                msg['Subject'] = Header("【採用ご担当者様へ】採用工数の削減とミスマッチ防止を実現するご提案｜HUGAN JOB", 'utf-8')
                msg['Message-ID'] = f"<test-{int(time.time())}-{i}@hugan.co.jp>"
                msg['Date'] = formatdate(localtime=True)
                msg['X-Mailer'] = 'HUGAN JOB Marketing System'
                
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

詳細につきましては、お気軽にお問い合わせください。

---
HUGAN JOB採用事務局
Email: client@hugan.co.jp

※このメールは営業目的で送信しております。
※配信停止をご希望の場合は、返信にてお知らせください。

送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
送信先: {email}
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
    print("\n" + "=" * 60)
    print("📊 送信結果")
    print("=" * 60)
    print(f"送信対象: {len(emails)}件")
    print(f"送信成功: {success_count}件")
    print(f"送信失敗: {len(emails) - success_count}件")
    print(f"成功率: {(success_count / len(emails) * 100):.1f}%")
    
    if success_count == len(emails):
        print("🎉 全てのメール送信が成功しました！")
    else:
        print("⚠️ 一部のメール送信が失敗しました。")
    
    print("\n📋 受信確認:")
    print("1. 各メールアドレスの受信トレイを確認してください")
    print("2. 迷惑メールフォルダも確認してください")
    print("3. HTMLメールが正しく表示されるか確認してください")
    print("4. 送信者が 'HUGAN採用事務局 <client@hugan.co.jp>' として表示されるか確認してください")
    print("=" * 60)
    
    return success_count == len(emails)

if __name__ == "__main__":
    try:
        success = send_quick_test()
        print(f"\n🏁 テスト完了: {'成功' if success else '失敗'}")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
