#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡単なテストメール送信 - n.yamashita@raxus.inc宛て
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

def send_simple_test():
    """簡単なテストメール送信"""
    try:
        print("📧 テストメール送信開始")
        print("宛先: n.yamashita@raxus.inc")
        
        # メール作成
        msg = MIMEMultipart('alternative')
        msg['Subject'] = Header("システムエンジニア採用のご相談 - HUGAN JOB", 'utf-8')
        msg['From'] = formataddr(("HUGAN JOB採用サポート", "contact@huganjob.jp"))
        msg['To'] = "n.yamashita@raxus.inc"
        msg['Reply-To'] = "contact@huganjob.jp"
        
        # プレーンテキスト
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

詳細については、お気軽にお問い合わせください。

---
HUGAN JOB採用サポート
Email: contact@huganjob.jp
配信停止: https://forms.gle/49BTNfSgUeNkH7rz5
        """.strip()
        
        # HTMLコンテンツ
        html_content = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>システムエンジニア採用のご相談</title>
</head>
<body style="font-family: sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #3498db 0%, #1abc9c 100%); padding: 20px; text-align: center; color: white; border-radius: 8px;">
            <h1 style="margin: 0;">HUGAN JOB</h1>
            <p style="margin: 10px 0 0 0;">採用サポートサービス</p>
        </div>
        
        <div style="padding: 30px 20px;">
            <p>株式会社Raxus<br>採用ご担当者様</p>
            <p>いつもお疲れ様です。<br>HUGAN JOB採用サポートチームです。</p>
            <p>株式会社Raxus様のシステムエンジニアの採用について、弊社の人材紹介サービスでお手伝いできることがございます。</p>
            
            <h3>HUGAN JOBの特徴</h3>
            <ul>
                <li>採用工数の大幅削減</li>
                <li>ミスマッチの防止</li>
                <li>専門性の高い人材紹介</li>
            </ul>
            
            <p>詳細については、お気軽にお問い合わせください。</p>
        </div>
        
        <div style="padding: 20px; text-align: center; background: #f8f9fa; border-radius: 8px;">
            <p style="margin: 0; color: #666; font-size: 14px;">
                HUGAN JOB採用サポート<br>
                Email: contact@huganjob.jp<br>
                配信停止: <a href="https://forms.gle/49BTNfSgUeNkH7rz5">こちら</a>
            </p>
        </div>
    </div>
</body>
</html>
        """
        
        # パート追加
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(text_part)
        msg.attach(html_part)
        
        # SMTP送信
        print("📡 SMTP接続中...")
        server = smtplib.SMTP('smtp.huganjob.jp', 587, timeout=30)
        server.starttls()
        server.login('contact@huganjob.jp', 'gD34bEmB')
        server.send_message(msg)
        server.quit()
        
        print("✅ 送信成功: n.yamashita@raxus.inc")
        print("📧 件名: システムエンジニア採用のご相談 - HUGAN JOB")
        print("👤 送信者: HUGAN JOB採用サポート")
        
        return True
        
    except Exception as e:
        print(f"❌ 送信失敗: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("📧 HUGANJOB テストメール送信")
    print("宛先: n.yamashita@raxus.inc")
    print("="*50)
    
    success = send_simple_test()
    
    if success:
        print("\n🏁 テストメール送信完了")
        print("📬 受信確認をお願いします")
    else:
        print("\n❌ テストメール送信失敗")
