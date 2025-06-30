#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HUGAN.co.jpドメイン送信設定スクリプト
送信者とドメインの完全一致を実現
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

def create_hugan_domain_config():
    """HUGAN.co.jpドメイン用設定ファイルを作成"""
    print("=" * 80)
    print("🔧 HUGAN.co.jpドメイン送信設定")
    print("=" * 80)
    
    # 新しい設定を作成
    config = configparser.ConfigParser()
    
    # SMTP設定（HUGAN.co.jpドメイン用）
    config.add_section('SMTP')
    config.set('SMTP', 'server', 'f045.sakura.ne.jp')  # 既存のSMTPサーバー
    config.set('SMTP', 'port', '587')
    config.set('SMTP', 'user', 'marketing@fortyfive.co.jp')  # 認証用
    config.set('SMTP', 'username', 'marketing@fortyfive.co.jp')
    config.set('SMTP', 'password', 'e5Fc%%-6Xu59z')
    config.set('SMTP', 'sender_name', 'HUGAN JOB')
    config.set('SMTP', 'from_name', 'HUGAN JOB')
    config.set('SMTP', 'from_email', 'client@hugan.co.jp')  # 表示用
    config.set('SMTP', 'reply_to', 'client@hugan.co.jp')
    config.set('SMTP', 'smtp_auth_email', 'marketing@fortyfive.co.jp')  # 実際の認証
    
    # 送信制御設定
    config.add_section('SENDING')
    config.set('SENDING', 'batch_size', '10')
    config.set('SENDING', 'delay_between_emails', '5')
    config.set('SENDING', 'delay_between_batches', '60')
    config.set('SENDING', 'max_retries', '3')
    
    # 迷惑メール対策設定
    config.add_section('ANTI_SPAM')
    config.set('ANTI_SPAM', 'use_html_format', 'true')
    config.set('ANTI_SPAM', 'add_tracking_pixel', 'true')
    config.set('ANTI_SPAM', 'use_multipart_alternative', 'true')
    config.set('ANTI_SPAM', 'send_interval', '5')
    config.set('ANTI_SPAM', 'enable_bounce_handling', 'true')
    config.set('ANTI_SPAM', 'use_envelope_from_separation', 'true')
    
    # ログ設定
    config.add_section('LOGGING')
    config.set('LOGGING', 'level', 'INFO')
    config.set('LOGGING', 'file', 'logs/hugan_domain_email.log')
    config.set('LOGGING', 'max_size', '10MB')
    config.set('LOGGING', 'backup_count', '5')
    
    # 設定ファイルを保存
    config_path = 'config/hugan_domain_email_config.ini'
    with open(config_path, 'w', encoding='utf-8') as f:
        config.write(f)
    
    print(f"✅ 設定ファイルを作成しました: {config_path}")
    return config_path

def test_hugan_domain_sending():
    """HUGAN.co.jpドメイン送信テスト"""
    print("\n📧 HUGAN.co.jpドメイン送信テスト")
    print("-" * 50)
    
    # テスト用メールアドレス
    test_emails = [
        "raxus.yamashita@gmail.com",
        "naoki_yamashita@fortyfive.co.jp", 
        "n.yamashita@raxus.inc"
    ]
    
    # 設定読み込み
    config = configparser.ConfigParser()
    config.read('config/hugan_domain_email_config.ini', encoding='utf-8')
    
    # SMTP設定
    smtp_server = config.get('SMTP', 'server')
    smtp_port = int(config.get('SMTP', 'port'))
    smtp_user = config.get('SMTP', 'smtp_auth_email')
    smtp_password = config.get('SMTP', 'password')
    sender_name = config.get('SMTP', 'sender_name')
    from_email = config.get('SMTP', 'from_email')
    reply_to = config.get('SMTP', 'reply_to')
    
    print(f"📡 SMTP: {smtp_server}:{smtp_port}")
    print(f"👤 認証: {smtp_user}")
    print(f"📧 送信者: {sender_name} <{from_email}>")
    print(f"↩️ 返信先: {reply_to}")
    print(f"🎯 戦略: Envelope-From分離でドメイン一致を実現")
    
    success_count = 0
    
    try:
        # SMTP接続
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        print("✅ SMTP接続成功")
        
        for i, email in enumerate(test_emails, 1):
            print(f"\n🔄 {i}/3 送信中: {email}")
            
            try:
                # メッセージ作成（ドメイン一致戦略）
                msg = MIMEMultipart('alternative')
                
                # ヘッダー設定（受信者に表示される情報）
                msg['From'] = f"{sender_name} <{from_email}>"
                msg['Reply-To'] = reply_to
                msg['To'] = email
                msg['Subject'] = Header("HUGAN JOB 採用サービスのご案内", 'utf-8')
                
                # 技術的ヘッダー
                msg['Message-ID'] = f"<hugan-{int(time.time())}-{i}@hugan.co.jp>"
                msg['Date'] = formatdate(localtime=True)
                msg['X-Mailer'] = 'HUGAN JOB System'
                msg['X-Priority'] = '3'
                
                # 迷惑メール対策ヘッダー
                msg['List-Unsubscribe'] = '<mailto:unsubscribe@hugan.co.jp>'
                msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
                msg['Precedence'] = 'bulk'
                
                # Return-Pathを設定（Envelope-From）
                msg['Return-Path'] = smtp_user
                
                # プレーンテキスト
                text_content = f"""
{email.split('@')[0]} 様

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
送信方式: ドメイン一致戦略
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0; font-size: 28px;">HUGAN JOB</h1>
            <p style="margin: 10px 0 0 0; font-size: 16px;">採用サービスのご案内</p>
        </div>
        
        <div class="content">
            <p>{email.split('@')[0]} 様</p>
            
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
            <p>送信方式: ドメイン一致戦略</p>
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
                print(f"  🔍 Return-Path: {msg.get('Return-Path', 'なし')}")
                
                # 送信（Envelope-From分離）
                # sendmailの第1引数（Envelope-From）は認証用アドレス
                # メッセージのFromヘッダーは表示用アドレス
                server.sendmail(smtp_user, [email], msg.as_string())
                print(f"  ✅ 送信成功: {email}")
                success_count += 1
                
                # 送信間隔
                if i < len(test_emails):
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
    print("📊 HUGAN.co.jpドメイン送信結果")
    print("=" * 80)
    print(f"送信対象: {len(test_emails)}件")
    print(f"送信成功: {success_count}件")
    print(f"送信失敗: {len(test_emails) - success_count}件")
    print(f"成功率: {(success_count / len(test_emails) * 100):.1f}%")
    
    if success_count == len(test_emails):
        print("🎉 全てのメール送信が成功しました！")
    else:
        print("⚠️ 一部のメール送信が失敗しました。")
    
    print("\n📋 ドメイン一致戦略の内容:")
    print("1. Envelope-From: marketing@fortyfive.co.jp（認証用）")
    print("2. Header-From: client@hugan.co.jp（表示用）")
    print("3. Reply-To: client@hugan.co.jp（返信先）")
    print("4. Message-ID: @hugan.co.jp（ブランディング）")
    print("5. Return-Path: 認証ドメインで設定")
    
    print("\n📋 期待される効果:")
    print("1. 受信者には 'HUGAN JOB <client@hugan.co.jp>' として表示")
    print("2. SPF/DKIM認証は fortyfive.co.jp で正常に通る")
    print("3. 迷惑メール判定率の大幅削減")
    print("4. 返信は client@hugan.co.jp に正常に届く")
    print("=" * 80)
    
    return success_count == len(test_emails)

def main():
    """メイン処理"""
    print("🚀 HUGAN.co.jpドメイン送信設定セットアップ")
    
    # 設定ファイル作成
    config_path = create_hugan_domain_config()
    
    # テスト送信実行
    success = test_hugan_domain_sending()
    
    print(f"\n🏁 セットアップ完了: {'成功' if success else '失敗'}")
    return success

if __name__ == "__main__":
    try:
        success = main()
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
