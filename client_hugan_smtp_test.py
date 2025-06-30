#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
client@hugan.co.jp SMTP接続・送信テストスクリプト
完全なドメイン一致での送信テスト
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

class ClientHuganSMTPTester:
    def __init__(self):
        self.config = None
        self.smtp_server = None
        
    def load_config(self):
        """設定ファイルの読み込み"""
        config_path = 'config/client_hugan_email_config.ini'
        
        if not os.path.exists(config_path):
            print(f"❌ 設定ファイルが見つかりません: {config_path}")
            print("📝 先に create_client_hugan_config.py を実行してください")
            return False
        
        try:
            self.config = configparser.ConfigParser()
            self.config.read(config_path, encoding='utf-8')
            print(f"✅ 設定ファイルを読み込みました: {config_path}")
            return True
        except Exception as e:
            print(f"❌ 設定ファイル読み込みエラー: {e}")
            return False
    
    def test_smtp_connection(self):
        """SMTP接続テスト"""
        print("\n🔗 SMTP接続テスト")
        print("-" * 50)
        
        try:
            smtp_server = self.config.get('SMTP', 'server')
            smtp_port = int(self.config.get('SMTP', 'port'))
            smtp_user = self.config.get('SMTP', 'user')
            smtp_password = self.config.get('SMTP', 'password')
            
            print(f"📡 接続先: {smtp_server}:{smtp_port}")
            print(f"👤 認証ユーザー: {smtp_user}")
            
            # SMTP接続
            self.smtp_server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            print("✅ SMTP接続成功")
            
            # STARTTLS
            self.smtp_server.starttls()
            print("✅ STARTTLS成功")
            
            # 認証
            self.smtp_server.login(smtp_user, smtp_password)
            print("✅ SMTP認証成功")
            
            # 認証方法確認
            auth_methods = self.smtp_server.esmtp_features.get('auth', '')
            print(f"🔐 認証方法: {auth_methods}")
            
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP認証失敗: {e}")
            print("📝 client@hugan.co.jpアカウントが作成されているか確認してください")
            return False
        except Exception as e:
            print(f"❌ SMTP接続エラー: {e}")
            return False
    
    def send_test_email(self, to_email, company_name="テスト企業"):
        """テストメール送信"""
        print(f"\n📧 テストメール送信: {to_email}")
        print("-" * 50)
        
        try:
            sender_name = self.config.get('SMTP', 'sender_name')
            from_email = self.config.get('SMTP', 'from_email')
            reply_to = self.config.get('SMTP', 'reply_to')
            
            # メッセージ作成
            msg = MIMEMultipart('alternative')
            
            # ヘッダー設定（完全なドメイン一致）
            msg['From'] = f"{sender_name} <{from_email}>"
            msg['Reply-To'] = reply_to
            msg['To'] = to_email
            msg['Subject'] = Header("HUGAN JOB 採用サービスのご案内", 'utf-8')
            
            # 技術的ヘッダー
            msg['Message-ID'] = f"<hugan-direct-{int(time.time())}@hugan.co.jp>"
            msg['Date'] = formatdate(localtime=True)
            msg['X-Mailer'] = 'HUGAN JOB Direct System'
            msg['X-Priority'] = '3'
            
            # 迷惑メール対策ヘッダー
            msg['List-Unsubscribe'] = '<mailto:unsubscribe@hugan.co.jp>'
            msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
            msg['Precedence'] = 'bulk'
            
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
送信方式: client@hugan.co.jp直接送信
ドメイン統一: 完全一致
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
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }}
        .content {{ padding: 30px 20px; }}
        .service-item {{ background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #667eea; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
        .cta-button {{ display: inline-block; background-color: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .direct-badge {{ background-color: #28a745; color: white; padding: 5px 10px; border-radius: 3px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0; font-size: 28px;">HUGAN JOB</h1>
            <p style="margin: 10px 0 0 0; font-size: 16px;">採用サービスのご案内</p>
            <span class="direct-badge">Direct Sending</span>
        </div>
        
        <div class="content">
            <p>{company_name} 採用ご担当者様</p>
            
            <p>お世話になっております。<br>
            HUGAN JOBです。</p>
            
            <p>採用でお困りのことはございませんか？</p>
            
            <p>HUGAN JOBでは採用活動をサポートしております。</p>
            
            <h3 style="color: #667eea;">サービス内容</h3>
            
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
            <p><strong>送信方式:</strong> client@hugan.co.jp直接送信<br>
            <strong>ドメイン統一:</strong> 完全一致</p>
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
            print(f"  🔍 Subject: {msg['Subject']}")
            
            # 送信（完全なドメイン一致）
            smtp_user = self.config.get('SMTP', 'user')
            self.smtp_server.sendmail(smtp_user, [to_email], msg.as_string())
            
            print(f"  ✅ 送信成功: {to_email}")
            return True
            
        except Exception as e:
            print(f"  ❌ 送信失敗: {e}")
            return False
    
    def run_comprehensive_test(self):
        """包括的なテスト実行"""
        print("=" * 80)
        print("🚀 client@hugan.co.jp 包括的送信テスト")
        print("=" * 80)
        
        # 設定読み込み
        if not self.load_config():
            return False
        
        # SMTP接続テスト
        if not self.test_smtp_connection():
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
            
            if self.send_test_email(email, company):
                success_count += 1
            
            # 送信間隔
            if i < len(test_emails):
                print("  ⏳ 5秒待機...")
                time.sleep(5)
        
        # SMTP接続終了
        if self.smtp_server:
            self.smtp_server.quit()
            print("\n✅ SMTP接続終了")
        
        # 結果表示
        print("\n" + "=" * 80)
        print("📊 client@hugan.co.jp直接送信結果")
        print("=" * 80)
        print(f"送信対象: {len(test_emails)}件")
        print(f"送信成功: {success_count}件")
        print(f"送信失敗: {len(test_emails) - success_count}件")
        print(f"成功率: {(success_count / len(test_emails) * 100):.1f}%")
        
        if success_count == len(test_emails):
            print("🎉 全てのメール送信が成功しました！")
        else:
            print("⚠️ 一部のメール送信が失敗しました。")
        
        print("\n📋 完全ドメイン一致の効果:")
        print("1. 送信者: HUGAN JOB <client@hugan.co.jp>")
        print("2. 認証: client@hugan.co.jp（完全一致）")
        print("3. SPF/DKIM: hugan.co.jpドメインで認証")
        print("4. 迷惑メール判定: 最大限回避")
        print("5. ブランド統一: 完全なHUGAN JOBブランド")
        
        print("\n📋 受信確認ポイント:")
        print("1. 送信者表示: 'HUGAN JOB <client@hugan.co.jp>'")
        print("2. 迷惑メール判定: 受信トレイに正常配信")
        print("3. 認証表示: 'via'表示なし")
        print("4. HTMLメール: 正常表示")
        print("5. 返信機能: client@hugan.co.jpに正常返信")
        print("=" * 80)
        
        return success_count == len(test_emails)

def main():
    """メイン処理"""
    tester = ClientHuganSMTPTester()
    
    try:
        success = tester.run_comprehensive_test()
        print(f"\n🏁 テスト完了: {'成功' if success else '失敗'}")
        return success
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
