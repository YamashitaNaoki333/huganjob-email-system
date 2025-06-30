#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
シンプルなテストメール送信スクリプト
配信確認用の基本的なメール送信
"""

import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime

def send_simple_test_email(to_email):
    """シンプルなテストメールを送信"""
    print("=" * 60)
    print("📧 シンプルテストメール送信")
    print("=" * 60)
    print(f"送信先: {to_email}")
    print("=" * 60)
    
    # SMTP設定（確実に動作する設定）
    smtp_server = "f045.sakura.ne.jp"
    smtp_port = 587
    smtp_user = "marketing@fortyfive.co.jp"
    smtp_password = "e5Fc%%-6Xu59z"
    
    try:
        # SMTP接続
        print(f"📡 SMTP接続中: {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        print("✅ SMTP認証成功")
        
        # シンプルなメールメッセージを作成
        msg = MIMEMultipart()
        msg['From'] = f"HUGAN採用事務局 <{smtp_user}>"
        msg['To'] = to_email
        msg['Subject'] = Header("【配信テスト】HUGAN JOB メール配信確認", 'utf-8')
        
        # メール本文（シンプルなテキスト）
        body = f"""
HUGAN JOB メール配信テストです。

このメールが正常に受信できている場合、メール配信システムは正常に動作しています。

送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
送信者: HUGAN採用事務局
システム: HUGAN JOB 採用営業システム

※このメールはテスト送信です。

---
HUGAN JOB 採用事務局
Email: marketing@fortyfive.co.jp
"""
        
        text_part = MIMEText(body, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # メール送信
        print("📤 メール送信中...")
        server.sendmail(smtp_user, [to_email], msg.as_string())
        server.quit()
        
        print("✅ メール送信成功！")
        print(f"📧 送信者: HUGAN採用事務局 <{smtp_user}>")
        print(f"📧 宛先: {to_email}")
        print(f"📧 件名: 【配信テスト】HUGAN JOB メール配信確認")
        print(f"📧 送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n📋 受信確認のお願い:")
        print("1. 受信トレイを確認してください")
        print("2. 迷惑メールフォルダを確認してください")
        print("3. プロモーションタブ（Gmail）を確認してください")
        print("4. 5-10分程度お待ちください（配信遅延の可能性）")
        
        return True
        
    except Exception as e:
        print(f"❌ メール送信に失敗: {e}")
        return False

def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("使用方法: python simple_test_email.py <メールアドレス>")
        print("例: python simple_test_email.py raxus.yamashita@gmail.com")
        return False
    
    to_email = sys.argv[1]
    return send_simple_test_email(to_email)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
