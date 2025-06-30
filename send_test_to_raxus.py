#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB テストメール送信 - n.yamashita@raxus.inc宛て
DMARC対応版迷惑メール対策テスト

作成日時: 2025年06月26日 20:10:00
宛先: n.yamashita@raxus.inc
"""

import smtplib
import configparser
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid

def load_config():
    """設定ファイル読み込み"""
    try:
        config = configparser.ConfigParser()
        config.read('config/huganjob_email_config.ini', encoding='utf-8')
        print("✅ 設定ファイル読み込み完了")
        return config
    except Exception as e:
        print(f"❌ 設定ファイル読み込みエラー: {e}")
        return None

def create_test_email(config, recipient_email="n.yamashita@raxus.inc"):
    """DMARC対応テストメール作成"""
    try:
        msg = MIMEMultipart('alternative')
        
        # 件名（改善版）
        subject = "システムエンジニア採用のご相談 - HUGAN JOB"
        msg['Subject'] = Header(subject, 'utf-8')
        
        # 送信者情報（DMARC対応）
        sender_name = config.get('SMTP', 'sender_name')
        from_email = config.get('SMTP', 'from_email')
        msg['From'] = formataddr((sender_name, from_email))
        msg['To'] = recipient_email
        msg['Reply-To'] = config.get('SMTP', 'reply_to')
        
        # DMARC対応ヘッダー
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid(domain='huganjob.jp')
        msg['X-Mailer'] = 'HUGAN JOB System v2.0'
        msg['X-Priority'] = '3'
        # 🚨 認証結果偽装ヘッダーを削除（迷惑メール判定の主要因）
        # ❌ msg['Authentication-Results'] = 削除済み（偽装ヘッダーは迷惑メール判定要因）
        
        # 配信停止ヘッダー（RFC準拠）
        unsubscribe_url = config.get('EMAIL_CONTENT', 'unsubscribe_url')
        msg['List-Unsubscribe'] = f'<{unsubscribe_url}>'
        msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
        
        # HTMLコンテンツ（営業色を薄めた版）
        html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>システムエンジニア採用のご相談</title>
</head>
<body style="font-family: 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', sans-serif; line-height: 1.6; color: #2c3e50; margin: 0; padding: 0; background-color: #f5f7fa;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        
        <!-- ヘッダー -->
        <div style="background: linear-gradient(135deg, #3498db 0%, #1abc9c 100%); padding: 20px; text-align: center;">
            <div style="font-size: 28px; font-weight: 900; color: #ffffff; margin-bottom: 8px;">
                HUGAN<span style="color: #fff200;">JOB</span>
            </div>
            <div style="color: rgba(255,255,255,0.9); font-size: 14px; font-weight: 500;">採用サポートサービス</div>
        </div>
        
        <!-- メイン内容 -->
        <div style="padding: 30px 20px;">
            <p style="font-size: 14px; margin-bottom: 1em;">
                株式会社Raxus<br>
                採用ご担当者様
            </p>
            <p style="font-size: 14px; margin-bottom: 1em;">
                いつもお疲れ様です。<br>
                HUGAN JOB採用サポートチームです。
            </p>
            <p style="font-size: 14px; margin-bottom: 1em;">
                株式会社Raxus様のシステムエンジニアの採用について、弊社の人材紹介サービスでお手伝いできることがございます。
            </p>
            <p style="font-size: 14px; margin-bottom: 0;">
                HUGAN JOBの特徴をご紹介いたします。
            </p>
        </div>
        
        <!-- 特徴セクション -->
        <div style="background-color: #f8f9fa; padding: 30px 20px;">
            <h2 style="font-size: 20px; font-weight: 700; color: #2c3e50; margin-bottom: 15px; text-align: center;">HUGAN JOBの特徴</h2>
            
            <div style="margin-bottom: 20px; padding: 20px; background-color: white; border-radius: 8px; border-left: 4px solid #3498db;">
                <div style="font-size: 16px; font-weight: 700; color: #2c3e50; margin-bottom: 8px;">
                    <span style="color: #3498db;">1.</span> 採用工数の削減
                </div>
                <p style="font-size: 14px; color: #7f8c8d; line-height: 1.6; margin: 0;">
                    人材の選定から面接調整まで、採用プロセスをトータルサポートいたします。
                </p>
            </div>
            
            <div style="margin-bottom: 20px; padding: 20px; background-color: white; border-radius: 8px; border-left: 4px solid #1abc9c;">
                <div style="font-size: 16px; font-weight: 700; color: #2c3e50; margin-bottom: 8px;">
                    <span style="color: #1abc9c;">2.</span> ミスマッチの防止
                </div>
                <p style="font-size: 14px; color: #7f8c8d; line-height: 1.6; margin: 0;">
                    詳細なヒアリングにより、企業様のニーズに最適な人材をご紹介いたします。
                </p>
            </div>
            
            <div style="margin-bottom: 0; padding: 20px; background-color: white; border-radius: 8px; border-left: 4px solid #e74c3c;">
                <div style="font-size: 16px; font-weight: 700; color: #2c3e50; margin-bottom: 8px;">
                    <span style="color: #e74c3c;">3.</span> 専門性の高いサポート
                </div>
                <p style="font-size: 14px; color: #7f8c8d; line-height: 1.6; margin: 0;">
                    IT業界に精通したコンサルタントが、専門的な観点からサポートいたします。
                </p>
            </div>
        </div>
        
        <!-- お問い合わせ -->
        <div style="padding: 30px 20px; text-align: center;">
            <p style="font-size: 14px; color: #2c3e50; margin-bottom: 20px;">
                詳細については、お気軽にお問い合わせください。
            </p>
            <a href="mailto:contact@huganjob.jp" style="display: inline-block; background-color: #3498db; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600;">
                お問い合わせ
            </a>
        </div>
        
        <!-- フッター -->
        <div style="padding: 20px; text-align: center; background-color: #2c3e50; color: white;">
            <p style="margin: 0; font-size: 14px;">
                HUGAN JOB採用サポート<br>
                Email: contact@huganjob.jp<br>
                配信停止: <a href="{unsubscribe_url}" style="color: #3498db;">こちら</a>
            </p>
        </div>
        
    </div>
</body>
</html>
        """
        
        # プレーンテキスト版
        text_content = f"""
株式会社Raxus
採用ご担当者様

いつもお疲れ様です。
HUGAN JOB採用サポートチームです。

株式会社Raxus様のシステムエンジニアの採用について、
弊社の人材紹介サービスでお手伝いできることがございます。

【HUGAN JOBの特徴】

1. 採用工数の削減
   人材の選定から面接調整まで、採用プロセスをトータルサポートいたします。

2. ミスマッチの防止
   詳細なヒアリングにより、企業様のニーズに最適な人材をご紹介いたします。

3. 専門性の高いサポート
   IT業界に精通したコンサルタントが、専門的な観点からサポートいたします。

詳細については、お気軽にお問い合わせください。

---
HUGAN JOB採用サポート
Email: contact@huganjob.jp
配信停止: {unsubscribe_url}
        """
        
        # パート追加
        text_part = MIMEText(text_content.strip(), 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(text_part)
        msg.attach(html_part)
        
        return msg
        
    except Exception as e:
        print(f"❌ メール作成エラー: {e}")
        return None

def send_test_email(config, recipient_email="n.yamashita@raxus.inc"):
    """テストメール送信"""
    try:
        print(f"\n📧 DMARC対応テストメール送信")
        print(f"   宛先: {recipient_email}")
        print(f"   企業名: 株式会社Raxus")
        print(f"   職種: システムエンジニア")
        
        # メール作成
        msg = create_test_email(config, recipient_email)
        if not msg:
            return False
        
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
        
        print(f"   ✅ 送信成功: {recipient_email}")
        print(f"   📧 件名: {msg['Subject']}")
        print(f"   👤 送信者: {msg['From']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 送信失敗: {e}")
        return False

def main():
    """メイン処理"""
    print("="*60)
    print("📧 HUGANJOB テストメール送信")
    print("宛先: n.yamashita@raxus.inc")
    print("DMARC対応・迷惑メール対策版")
    print("="*60)
    
    # 設定読み込み
    config = load_config()
    if not config:
        return False
    
    # テストメール送信
    success = send_test_email(config, "n.yamashita@raxus.inc")
    
    if success:
        print(f"\n🏁 テストメール送信完了")
        print(f"📬 受信確認のお願い:")
        print(f"   - 受信トレイに到達しているか")
        print(f"   - 迷惑メールフォルダに分類されていないか")
        print(f"   - 送信者認証が正常に表示されているか")
        print(f"   - メール内容が正常に表示されているか")
        
        print(f"\n📊 改善内容:")
        print(f"   ✅ 件名の簡素化")
        print(f"   ✅ 送信者名の最適化")
        print(f"   ✅ DMARC対応ヘッダー追加")
        print(f"   ✅ 営業色の削減")
        print(f"   ✅ RFC準拠の配信停止ヘッダー")
    else:
        print(f"\n❌ テストメール送信失敗")
    
    return success

if __name__ == "__main__":
    main()
