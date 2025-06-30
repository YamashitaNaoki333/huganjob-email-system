#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テキストメールテンプレート送信テスト
指定されたメールアドレスにテキストメールテンプレートを送信
"""

import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate

def send_text_template_test():
    """テキストメールテンプレートのテスト送信"""
    
    # 送信先メールアドレス
    recipients = [
        "n.yamashita@raxus.inc",
        "naoki_yamashita@fortyfive.co.jp"
    ]
    
    # テンプレート読み込み
    try:
        with open('templates/corporate-email-newsletter-text.txt', 'r', encoding='utf-8') as f:
            template_content = f.read()
        print("✅ テキストテンプレート読み込み完了")
    except Exception as e:
        print(f"❌ テンプレート読み込みエラー: {e}")
        return
    
    # テンプレート変数を置換
    test_company_name = "テスト株式会社"
    test_job_position = "システムエンジニア"
    
    text_content = template_content.replace('{{company_name}}', test_company_name)
    text_content = text_content.replace('{{job_position}}', test_job_position)
    
    # 件名
    subject = f"【{test_job_position}の人材採用を強化しませんか？】株式会社HUGANからのご提案（更新版テキストメールテンプレート確認）"
    
    print(f"\n📧 テキストメールテンプレート送信テスト")
    print("=" * 60)
    print(f"📋 送信先: {len(recipients)}件")
    for email in recipients:
        print(f"  - {email}")
    print(f"📝 件名: {subject}")
    print(f"🏢 テスト企業名: {test_company_name}")
    print(f"💼 テスト職種: {test_job_position}")
    print("=" * 60)
    
    # 各メールアドレスに送信
    success_count = 0
    for recipient_email in recipients:
        try:
            print(f"\n📤 送信中: {recipient_email}")
            
            # メール作成
            msg = MIMEText(text_content, 'plain', 'utf-8')
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = formataddr(('竹下隼平【株式会社HUGAN】', 'contact@huganjob.jp'))
            msg['To'] = recipient_email
            msg['Reply-To'] = 'contact@huganjob.jp'
            msg['Date'] = formatdate(localtime=True)
            
            # SMTP送信
            server = smtplib.SMTP('smtp.huganjob.jp', 587, timeout=30)
            server.starttls()
            server.login('contact@huganjob.jp', 'gD34bEmB')
            server.send_message(msg)
            server.quit()
            
            print(f"   ✅ 送信成功: {recipient_email}")
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ 送信失敗: {recipient_email} - {e}")
    
    # 結果表示
    print(f"\n" + "=" * 60)
    print("📊 テキストメールテンプレート送信結果")
    print("=" * 60)
    print(f"✅ 成功: {success_count}/{len(recipients)}")
    print(f"❌ 失敗: {len(recipients) - success_count}/{len(recipients)}")
    
    if success_count > 0:
        print(f"\n📝 送信内容:")
        print(f"  - 形式: プレーンテキスト")
        print(f"  - 送信者: 竹下隼平【株式会社HUGAN】")
        print(f"  - 送信元: contact@huganjob.jp")
        print(f"  - 目的: テキストメールテンプレート確認")
        print(f"\n💡 受信メールボックスをご確認ください。")

if __name__ == "__main__":
    send_text_template_test()
