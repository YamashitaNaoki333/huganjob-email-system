#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Microsoft 365対応メール送信システム
OAuth2認証を使用したclient@hugan.co.jp送信
"""

import os
import configparser
import smtplib
import time
import base64
import json
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formatdate

class Microsoft365EmailSender:
    def __init__(self):
        self.config = None
        self.access_token = None
        self.smtp_server = None
        
    def load_config(self):
        """Microsoft 365用設定の読み込み"""
        config_path = 'config/microsoft365_email_config.ini'
        
        if not os.path.exists(config_path):
            print(f"❌ Microsoft 365設定ファイルが見つかりません: {config_path}")
            print("📝 先に create_microsoft365_config.py を実行してください")
            return False
        
        try:
            self.config = configparser.ConfigParser()
            self.config.read(config_path, encoding='utf-8')
            print(f"✅ Microsoft 365設定ファイルを読み込みました")
            return True
        except Exception as e:
            print(f"❌ 設定ファイル読み込みエラー: {e}")
            return False
    
    def get_oauth2_token(self):
        """OAuth2トークンの取得"""
        print("\n🔐 OAuth2認証処理")
        print("-" * 40)
        
        try:
            tenant_id = self.config.get('OAUTH2', 'tenant_id')
            client_id = self.config.get('OAUTH2', 'client_id')
            client_secret = self.config.get('OAUTH2', 'client_secret')
            
            # Microsoft Graph API エンドポイント
            token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
            
            # トークン取得用のデータ
            token_data = {
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret,
                'scope': 'https://graph.microsoft.com/.default'
            }
            
            # トークン取得リクエスト
            response = requests.post(token_url, data=token_data)
            
            if response.status_code == 200:
                token_info = response.json()
                self.access_token = token_info.get('access_token')
                print("✅ OAuth2トークン取得成功")
                return True
            else:
                print(f"❌ OAuth2トークン取得失敗: {response.status_code}")
                print(f"エラー詳細: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ OAuth2認証エラー: {e}")
            return False
    
    def connect_smtp_oauth2(self):
        """OAuth2を使用したSMTP接続"""
        print("\n🔗 Microsoft 365 SMTP接続（OAuth2）")
        print("-" * 50)
        
        try:
            smtp_server = self.config.get('SMTP', 'server')
            smtp_port = int(self.config.get('SMTP', 'port'))
            username = self.config.get('SMTP', 'username')
            
            print(f"📡 接続先: {smtp_server}:{smtp_port}")
            print(f"👤 ユーザー: {username}")
            
            # SMTP接続
            self.smtp_server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            print("✅ SMTP接続成功")
            
            # STARTTLS
            self.smtp_server.starttls()
            print("✅ STARTTLS成功")
            
            # OAuth2認証文字列の作成
            auth_string = f"user={username}\x01auth=Bearer {self.access_token}\x01\x01"
            auth_string_b64 = base64.b64encode(auth_string.encode()).decode()
            
            # OAuth2認証
            self.smtp_server.docmd("AUTH", f"XOAUTH2 {auth_string_b64}")
            print("✅ OAuth2認証成功")
            
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ OAuth2認証失敗: {e}")
            print("📝 Azure AD設定を確認してください")
            return False
        except Exception as e:
            print(f"❌ SMTP接続エラー: {e}")
            return False
    
    def send_email_microsoft365(self, to_email, company_name="テスト企業"):
        """Microsoft 365経由でのメール送信"""
        print(f"\n📧 Microsoft 365メール送信: {to_email}")
        print("-" * 50)
        
        try:
            sender_name = self.config.get('SMTP', 'sender_name')
            from_email = self.config.get('SMTP', 'from_email')
            reply_to = self.config.get('SMTP', 'reply_to')
            
            # メッセージ作成
            msg = MIMEMultipart('alternative')
            
            # ヘッダー設定（Microsoft 365完全対応）
            msg['From'] = f"{sender_name} <{from_email}>"
            msg['Reply-To'] = reply_to
            msg['To'] = to_email
            msg['Subject'] = Header("HUGAN JOB 採用サービスのご案内", 'utf-8')
            
            # Microsoft 365推奨ヘッダー
            msg['Message-ID'] = f"<hugan-m365-{int(time.time())}@hugan.co.jp>"
            msg['Date'] = formatdate(localtime=True)
            msg['X-Mailer'] = 'HUGAN JOB Microsoft 365 System'
            msg['X-Priority'] = '3'
            
            # Microsoft 365迷惑メール対策ヘッダー
            msg['List-Unsubscribe'] = '<mailto:unsubscribe@hugan.co.jp>'
            msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
            
            # プレーンテキスト
            text_content = f"""
{company_name} 採用ご担当者様

お世話になっております。
HUGAN JOBです。

採用でお困りのことはございませんか？

HUGAN JOBでは採用活動をサポートしております。

■ サービス内容
・人材紹介サービス
・採用プロセス支援
・効率化コンサルティング

ご興味がございましたら、お気軽にお問い合わせください。

---
HUGAN JOB
Email: {reply_to}
Web: https://hugan.co.jp

※配信停止をご希望の場合は、返信にてお知らせください。

送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
送信方式: Microsoft 365 OAuth2認証
"""
            
            text_part = MIMEText(text_content.strip(), 'plain', 'utf-8')
            msg.attach(text_part)
            
            # HTMLコンテンツ
            html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HUGAN JOB 採用サービス</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; }}
        .header {{ background: linear-gradient(135deg, #0078d4 0%, #106ebe 100%); color: white; padding: 30px 20px; text-align: center; }}
        .content {{ padding: 30px 20px; }}
        .service-item {{ background-color: #f3f2f1; padding: 15px; margin: 10px 0; border-left: 4px solid #0078d4; }}
        .footer {{ background-color: #f3f2f1; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
        .cta-button {{ display: inline-block; background-color: #0078d4; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .m365-badge {{ background-color: #0078d4; color: white; padding: 5px 10px; border-radius: 3px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0; font-size: 28px;">HUGAN JOB</h1>
            <p style="margin: 10px 0 0 0; font-size: 16px;">採用サービスのご案内</p>
            <span class="m365-badge">Microsoft 365</span>
        </div>
        
        <div class="content">
            <p>{company_name} 採用ご担当者様</p>
            
            <p>お世話になっております。<br>
            HUGAN JOBです。</p>
            
            <p>採用でお困りのことはございませんか？</p>
            
            <p>HUGAN JOBでは採用活動をサポートしております。</p>
            
            <h3 style="color: #0078d4;">サービス内容</h3>
            
            <div class="service-item">
                <strong>人材紹介サービス</strong><br>
                優秀な人材をご紹介いたします
            </div>
            
            <div class="service-item">
                <strong>採用プロセス支援</strong><br>
                効率的な採用フローを構築します
            </div>
            
            <div class="service-item">
                <strong>効率化コンサルティング</strong><br>
                採用業務の最適化をサポートします
            </div>
            
            <p>ご興味がございましたら、お気軽にお問い合わせください。</p>
            
            <div style="text-align: center;">
                <a href="mailto:{reply_to}" class="cta-button">お問い合わせ</a>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>HUGAN JOB</strong><br>
            Email: {reply_to}<br>
            Web: https://hugan.co.jp</p>
            
            <p>※配信停止をご希望の場合は、返信にてお知らせください。</p>
            <p><strong>送信方式:</strong> Microsoft 365 OAuth2認証</p>
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
            print(f"  🔍 Message-ID: {msg['Message-ID']}")
            print(f"  🔍 認証方式: OAuth2")
            
            # 送信（Microsoft 365）
            username = self.config.get('SMTP', 'username')
            self.smtp_server.sendmail(username, [to_email], msg.as_string())
            
            print(f"  ✅ 送信成功: {to_email}")
            return True
            
        except Exception as e:
            print(f"  ❌ 送信失敗: {e}")
            return False
    
    def run_microsoft365_test(self):
        """Microsoft 365包括テスト"""
        print("=" * 80)
        print("🚀 Microsoft 365 OAuth2メール送信テスト")
        print("=" * 80)
        
        # 設定読み込み
        if not self.load_config():
            return False
        
        # OAuth2トークン取得
        if not self.get_oauth2_token():
            return False
        
        # SMTP接続
        if not self.connect_smtp_oauth2():
            return False
        
        # テスト送信
        test_emails = [
            ("raxus.yamashita@gmail.com", "司法書士法人中央ライズアクロス"),
            ("naoki_yamashita@fortyfive.co.jp", "おばた司法書士事務所"),
            ("n.yamashita@raxus.inc", "司法書士法人テスト")
        ]
        
        success_count = 0
        
        for i, (email, company) in enumerate(test_emails, 1):
            print(f"\n🔄 {i}/3 送信処理中...")
            
            if self.send_email_microsoft365(email, company):
                success_count += 1
            
            # 送信間隔
            if i < len(test_emails):
                print("  ⏳ 3秒待機...")
                time.sleep(3)
        
        # SMTP接続終了
        if self.smtp_server:
            self.smtp_server.quit()
            print("\n✅ SMTP接続終了")
        
        # 結果表示
        print("\n" + "=" * 80)
        print("📊 Microsoft 365送信結果")
        print("=" * 80)
        print(f"送信対象: {len(test_emails)}件")
        print(f"送信成功: {success_count}件")
        print(f"送信失敗: {len(test_emails) - success_count}件")
        print(f"成功率: {(success_count / len(test_emails) * 100):.1f}%")
        
        if success_count == len(test_emails):
            print("🎉 全てのメール送信が成功しました！")
        else:
            print("⚠️ 一部のメール送信が失敗しました。")
        
        print("\n📋 Microsoft 365の利点:")
        print("1. 企業レベルのセキュリティ")
        print("2. OAuth2による安全な認証")
        print("3. 高い配信率")
        print("4. Microsoft製品との統合")
        print("5. 詳細な送信ログ")
        
        print("\n📋 受信確認ポイント:")
        print("1. 送信者表示: 'HUGAN JOB <client@hugan.co.jp>'")
        print("2. 迷惑メール判定: Microsoft 365の高い信頼性")
        print("3. HTMLメール: 正常表示")
        print("4. 返信機能: client@hugan.co.jpに正常返信")
        print("=" * 80)
        
        return success_count == len(test_emails)

def main():
    """メイン処理"""
    sender = Microsoft365EmailSender()
    
    try:
        success = sender.run_microsoft365_test()
        print(f"\n🏁 Microsoft 365テスト完了: {'成功' if success else '失敗'}")
        return success
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
