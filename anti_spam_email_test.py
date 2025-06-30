#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
迷惑メール対策強化版テストメール送信スクリプト
SPF/DKIM認証問題を解決したバージョン
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

def send_anti_spam_test():
    """迷惑メール対策強化版テストメール送信"""
    print("=" * 80)
    print("📧 HUGAN JOB 迷惑メール対策強化版テストメール送信")
    print("=" * 80)
    
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
    print(f"🛡️ 迷惑メール対策: ドメイン統一、件名簡素化、内容最適化")
    
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
                # メッセージ作成（迷惑メール対策強化）
                msg = MIMEMultipart('alternative')
                
                # 送信者とドメインを統一（SPF/DKIM認証対策）
                msg['From'] = f"{sender_name} <{from_email}>"
                msg['Reply-To'] = reply_to
                msg['To'] = email
                
                # 件名を簡素化（迷惑メール判定回避）
                msg['Subject'] = Header("HUGAN JOB 採用サービスのご案内", 'utf-8')
                
                # 迷惑メール対策ヘッダー
                msg['Message-ID'] = f"<hugan-{int(time.time())}-{i}@fortyfive.co.jp>"
                msg['Date'] = formatdate(localtime=True)
                msg['X-Mailer'] = 'HUGAN JOB System'
                msg['X-Priority'] = '3'
                msg['Precedence'] = 'bulk'
                
                # List-Unsubscribe ヘッダー（迷惑メール対策）
                msg['List-Unsubscribe'] = '<mailto:unsubscribe@fortyfive.co.jp>'
                msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
                
                # プレーンテキスト（控えめな内容）
                text_content = f"""
{email.split('@')[0]} 様

お世話になっております。
HUGAN JOBです。

採用でお困りのことはございませんか？

HUGAN JOBでは採用活動をサポートしております。

■ サービス内容
・人材紹介
・採用支援
・効率化サポート

ご興味がございましたら、お気軽にお問い合わせください。

---
HUGAN JOB
Email: {reply_to}
Web: https://hugan.co.jp

※配信停止をご希望の場合は、返信にてお知らせください。

送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                
                text_part = MIMEText(text_content.strip(), 'plain', 'utf-8')
                msg.attach(text_part)
                
                # HTMLテンプレート（簡素版）
                html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HUGAN JOB 採用サービス</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .footer {{ background-color: #f8f9fa; padding: 15px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>HUGAN JOB</h1>
            <p>採用サービスのご案内</p>
        </div>
        
        <div class="content">
            <p>{email.split('@')[0]} 様</p>
            
            <p>お世話になっております。<br>
            HUGAN JOBです。</p>
            
            <p>採用でお困りのことはございませんか？</p>
            
            <p>HUGAN JOBでは採用活動をサポートしております。</p>
            
            <h3>サービス内容</h3>
            <ul>
                <li>人材紹介</li>
                <li>採用支援</li>
                <li>効率化サポート</li>
            </ul>
            
            <p>ご興味がございましたら、お気軽にお問い合わせください。</p>
        </div>
        
        <div class="footer">
            <p><strong>HUGAN JOB</strong><br>
            Email: {reply_to}<br>
            Web: https://hugan.co.jp</p>
            
            <p>※配信停止をご希望の場合は、返信にてお知らせください。</p>
        </div>
    </div>
</body>
</html>
"""
                
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
                
                # デバッグ情報
                print(f"  🔍 From: {msg['From']}")
                print(f"  🔍 Reply-To: {msg['Reply-To']}")
                print(f"  🔍 Subject: {msg['Subject']}")
                print(f"  🔍 Message-ID: {msg['Message-ID']}")
                
                # 送信
                server.sendmail(smtp_user, [email], msg.as_string())
                print(f"  ✅ 送信成功: {email}")
                success_count += 1
                
                # 送信間隔を延長（迷惑メール対策）
                if i < len(emails):
                    print("  ⏳ 5秒待機...")
                    time.sleep(5)
                    
            except Exception as e:
                print(f"  ❌ 送信失敗: {email} - {e}")
        
        server.quit()
        print("\n✅ SMTP接続終了")
        
    except Exception as e:
        print(f"❌ SMTP接続エラー: {e}")
        return False
    
    # 結果表示
    print("\n" + "=" * 80)
    print("📊 迷惑メール対策強化版送信結果")
    print("=" * 80)
    print(f"送信対象: {len(emails)}件")
    print(f"送信成功: {success_count}件")
    print(f"送信失敗: {len(emails) - success_count}件")
    print(f"成功率: {(success_count / len(emails) * 100):.1f}%")
    
    if success_count == len(emails):
        print("🎉 全てのメール送信が成功しました！")
    else:
        print("⚠️ 一部のメール送信が失敗しました。")
    
    print("\n📋 迷惑メール対策内容:")
    print("1. 送信者ドメインと認証ドメインを統一（fortyfive.co.jp）")
    print("2. 件名を簡素化（営業色を削除）")
    print("3. 内容を控えめに調整")
    print("4. List-Unsubscribeヘッダーを追加")
    print("5. 送信間隔を5秒に延長")
    print("6. Message-IDをfortyfive.co.jpドメインに統一")
    
    print("\n📋 受信確認:")
    print("1. 受信トレイに正常に届くか（迷惑メールフォルダではなく）")
    print("2. 送信者が正しく表示されるか")
    print("3. HTMLメールが正しく表示されるか")
    print("4. 返信先がclient@hugan.co.jpになっているか")
    print("=" * 80)
    
    return success_count == len(emails)

if __name__ == "__main__":
    try:
        success = send_anti_spam_test()
        print(f"\n🏁 迷惑メール対策テスト完了: {'成功' if success else '失敗'}")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
