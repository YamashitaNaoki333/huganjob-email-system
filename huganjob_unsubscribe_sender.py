#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB 配信停止リンク付き送信システム
追跡機能完全削除版

作成日時: 2025年06月26日 21:50:00
目的: 配信停止リンクを挿入し、追跡機能を完全削除
"""

import smtplib
import configparser
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid

def send_unsubscribe_email():
    """配信停止リンク付きメール送信"""
    try:
        print("="*60)
        print("📧 HUGANJOB 配信停止リンク付き送信システム")
        print("追跡機能完全削除版")
        print("="*60)
        
        # 設定読み込み
        config = configparser.ConfigParser()
        config.read('config/huganjob_email_config.ini', encoding='utf-8')
        print("✅ 設定ファイル読み込み完了")
        
        # メール作成
        msg = MIMEMultipart('alternative')
        
        # 件名
        subject = "システムエンジニア採用について - HUGAN JOB"
        msg['Subject'] = Header(subject, 'utf-8')
        
        # 送信者情報
        sender_name = config.get('SMTP', 'sender_name')
        from_email = config.get('SMTP', 'from_email')
        msg['From'] = formataddr((sender_name, from_email))
        msg['To'] = "n.yamashita@raxus.inc"
        msg['Reply-To'] = config.get('SMTP', 'reply_to')
        
        # 最小限のヘッダー
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid(domain='huganjob.jp')
        
        # プレーンテキスト版
        text_content = """
株式会社Raxus
採用ご担当者様

いつもお疲れ様です。
HUGAN JOB採用サポートチームです。

株式会社Raxus様のシステムエンジニアの採用について、
弊社の人材紹介サービスでお手伝いできることがございます。

【HUGAN JOBの特徴】
・採用工数の大幅削減
・ミスマッチの防止
・専門性の高い人材紹介

【お問い合わせ】
Email: contact@huganjob.jp
Tel: 0120-917-906

詳細については、お気軽にお問い合わせください。

---
HUGAN JOB採用サポート
Email: contact@huganjob.jp | Tel: 0120-917-906

配信停止: https://forms.gle/49BTNfSgUeNkH7rz5
        """.strip()
        
        # HTMLコンテンツ（配信停止リンク付き・追跡削除）
        html_content = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>システムエンジニア採用について - HUGAN JOB</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto;">
        
        <div style="background-color: #3498db; padding: 20px; text-align: center; color: white; margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 24px;">HUGAN JOB</h1>
            <p style="margin: 5px 0 0 0; font-size: 14px;">採用サポートサービス</p>
        </div>
        
        <div style="padding: 0 10px;">
            <p>株式会社Raxus<br>採用ご担当者様</p>
            <p>いつもお疲れ様です。<br>HUGAN JOB採用サポートチームです。</p>
            <p>株式会社Raxus様のシステムエンジニアの採用について、弊社の人材紹介サービスでお手伝いできることがございます。</p>
            
            <h3>HUGAN JOBの特徴</h3>
            <ul>
                <li>採用工数の大幅削減</li>
                <li>ミスマッチの防止</li>
                <li>専門性の高い人材紹介</li>
            </ul>
            
            <div style="background-color: #3498db; color: white; padding: 20px; text-align: center; margin: 30px 0; border-radius: 8px;">
                <h3 style="margin: 0 0 15px 0;">お問い合わせ・ご相談</h3>
                <p style="margin: 0; font-size: 16px;">
                    📧 <strong>contact@huganjob.jp</strong><br>
                    📞 <strong>0120-917-906</strong>
                </p>
            </div>
            
            <p>詳細については、お気軽にお問い合わせください。</p>
        </div>
        
        <div style="margin-top: 30px; padding: 20px; background-color: #2c3e50; color: white; text-align: center;">
            <h4 style="margin: 0 0 10px 0;">HUGAN JOB採用サポート</h4>
            <p style="margin: 0; font-size: 12px; opacity: 0.8;">
                Email: contact@huganjob.jp | Tel: 0120-917-906
            </p>
            
            <div style="margin-top: 15px; padding: 10px; background-color: rgba(255,255,255,0.1); border-radius: 5px;">
                <p style="margin: 0; font-size: 11px; opacity: 0.7;">
                    配信停止をご希望の場合は<a href="https://forms.gle/49BTNfSgUeNkH7rz5" style="color: #ffffff; text-decoration: underline;">こちら</a>からお手続きください。
                </p>
            </div>
        </div>
        
    </div>
    
    <!-- 🚫 追跡機能を完全削除 -->
    <!-- ❌ 追跡ピクセル削除 -->
    <!-- ❌ JavaScript追跡削除 -->
    
</body>
</html>
        """
        
        # パート追加
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(text_part)
        msg.attach(html_part)
        
        print(f"\n📧 配信停止リンク付きメール送信")
        print(f"   宛先: n.yamashita@raxus.inc")
        print(f"   企業名: 株式会社Raxus")
        print(f"   職種: システムエンジニア")
        print(f"   ✅ 配信停止リンク: https://forms.gle/49BTNfSgUeNkH7rz5")
        print(f"   🚫 追跡機能: 完全削除")
        
        # SMTP送信
        smtp_server = config.get('SMTP', 'server')
        smtp_port = int(config.get('SMTP', 'port'))
        smtp_user = config.get('SMTP', 'user')
        smtp_password = config.get('SMTP', 'password')
        
        print(f"   📡 SMTP接続: {smtp_server}:{smtp_port}")
        
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        print(f"   ✅ 送信成功: n.yamashita@raxus.inc")
        print(f"   📧 件名: {msg['Subject']}")
        print(f"   👤 送信者: {msg['From']}")
        
        print(f"\n🏁 配信停止リンク付きメール送信完了")
        print(f"✅ 配信停止リンク: 挿入済み")
        print(f"🚫 追跡機能: 完全削除")
        print(f"🛡️ 迷惑メール対策: 適用済み")
        print(f"📬 受信確認をお願いします")
        
        return True
        
    except Exception as e:
        print(f"❌ 送信失敗: {e}")
        return False

if __name__ == "__main__":
    send_unsubscribe_email()
