#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Microsoft 365基本認証テストツール
OAuth2が設定できない場合の代替手段
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

def test_microsoft365_basic_auth():
    """Microsoft 365基本認証テスト"""
    print("=" * 80)
    print("🔐 Microsoft 365 基本認証テスト")
    print("=" * 80)
    
    # 認証情報の入力
    print("📝 Microsoft 365認証情報を入力してください:")
    username = input("ユーザー名 [client@hugan.co.jp]: ").strip()
    if not username:
        username = "client@hugan.co.jp"
    
    password = input("パスワード: ").strip()
    if not password:
        print("❌ パスワードが入力されていません")
        return False
    
    # テスト送信先
    test_emails = [
        ("raxus.yamashita@gmail.com", "司法書士法人中央ライズアクロス"),
        ("naoki_yamashita@fortyfive.co.jp", "おばた司法書士事務所"),
        ("n.yamashita@raxus.inc", "司法書士法人テスト")
    ]
    
    success_count = 0
    
    try:
        print(f"\n🔗 SMTP接続テスト")
        print("-" * 50)
        print(f"📡 サーバー: smtp.office365.com:587")
        print(f"👤 ユーザー: {username}")
        
        # SMTP接続
        server = smtplib.SMTP('smtp.office365.com', 587, timeout=30)
        print("✅ SMTP接続成功")
        
        # STARTTLS
        server.starttls()
        print("✅ STARTTLS成功")
        
        # 基本認証
        server.login(username, password)
        print("✅ 基本認証成功")
        
        # 認証方法確認
        auth_methods = server.esmtp_features.get('auth', '')
        print(f"🔐 認証方法: {auth_methods}")
        
        # テスト送信
        for i, (email, company) in enumerate(test_emails, 1):
            print(f"\n🔄 {i}/3 送信処理中: {email}")
            
            try:
                # メッセージ作成
                msg = MIMEMultipart('alternative')
                
                # ヘッダー設定
                msg['From'] = f"HUGAN JOB <{username}>"
                msg['Reply-To'] = username
                msg['To'] = email
                msg['Subject'] = Header("HUGAN JOB 採用サービスのご案内", 'utf-8')
                
                # Microsoft 365推奨ヘッダー
                msg['Message-ID'] = f"<hugan-m365-basic-{int(time.time())}-{i}@hugan.co.jp>"
                msg['Date'] = formatdate(localtime=True)
                msg['X-Mailer'] = 'HUGAN JOB Microsoft 365 Basic Auth'
                msg['X-Priority'] = '3'
                
                # プレーンテキスト
                text_content = f"""
{company} 採用ご担当者様

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
Email: {username}
Web: https://hugan.co.jp

※配信停止をご希望の場合は、返信にてお知らせください。

送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
送信方式: Microsoft 365 基本認証
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
        .auth-badge {{ background-color: #107c10; color: white; padding: 5px 10px; border-radius: 3px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0; font-size: 28px;">HUGAN JOB</h1>
            <p style="margin: 10px 0 0 0; font-size: 16px;">採用サービスのご案内</p>
            <span class="auth-badge">Microsoft 365 Basic Auth</span>
        </div>
        
        <div class="content">
            <p>{company} 採用ご担当者様</p>
            
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
                <a href="mailto:{username}" class="cta-button">お問い合わせ</a>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>HUGAN JOB</strong><br>
            Email: {username}<br>
            Web: https://hugan.co.jp</p>
            
            <p>※配信停止をご希望の場合は、返信にてお知らせください。</p>
            <p><strong>送信方式:</strong> Microsoft 365 基本認証</p>
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
                
                # 送信
                server.sendmail(username, [email], msg.as_string())
                print(f"  ✅ 送信成功: {email}")
                success_count += 1
                
                # 送信間隔
                if i < len(test_emails):
                    print("  ⏳ 3秒待機...")
                    time.sleep(3)
                    
            except Exception as e:
                print(f"  ❌ 送信失敗: {email} - {e}")
        
        # SMTP接続終了
        server.quit()
        print("\n✅ SMTP接続終了")
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ 認証失敗: {e}")
        print("\n📝 考えられる原因:")
        print("1. パスワードが間違っている")
        print("2. 多要素認証が有効になっている")
        print("3. 基本認証が無効になっている")
        print("4. アプリパスワードが必要")
        return False
    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        return False
    
    # 結果表示
    print("\n" + "=" * 80)
    print("📊 Microsoft 365基本認証テスト結果")
    print("=" * 80)
    print(f"送信対象: {len(test_emails)}件")
    print(f"送信成功: {success_count}件")
    print(f"送信失敗: {len(test_emails) - success_count}件")
    print(f"成功率: {(success_count / len(test_emails) * 100):.1f}%")
    
    if success_count == len(test_emails):
        print("🎉 全てのメール送信が成功しました！")
        print("\n📋 次のステップ:")
        print("1. 受信確認（迷惑メールフォルダも確認）")
        print("2. 本格運用への設定変更")
        print("3. OAuth2認証への移行検討")
    else:
        print("⚠️ 一部のメール送信が失敗しました。")
        print("\n📋 対策:")
        print("1. OAuth2認証の設定")
        print("2. アプリパスワードの使用")
        print("3. Microsoft 365管理者への相談")
    
    print("\n📋 Microsoft 365基本認証の制限:")
    print("1. 2022年10月以降、基本認証は段階的に廃止")
    print("2. OAuth2認証への移行が強く推奨")
    print("3. セキュリティポリシーにより制限される場合あり")
    print("=" * 80)
    
    return success_count == len(test_emails)

if __name__ == "__main__":
    try:
        success = test_microsoft365_basic_auth()
        print(f"\n🏁 テスト完了: {'成功' if success else '失敗'}")
    except KeyboardInterrupt:
        print("\n\n❌ テストがキャンセルされました")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
