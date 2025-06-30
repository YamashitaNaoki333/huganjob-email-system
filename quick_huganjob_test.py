#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB クイックテストメール送信
"""

import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formatdate

def create_test_email(recipient_email, recipient_name=""):
    """テストメールを作成"""
    
    # メール作成
    msg = MIMEMultipart('alternative')
    msg['From'] = Header('HUGAN採用事務局 <contact@huganjob.jp>', 'utf-8')
    msg['To'] = recipient_email
    msg['Subject'] = Header('【HUGAN JOB】新SMTP設定テスト - 送信元アドレス変更確認', 'utf-8')
    msg['Date'] = formatdate(localtime=True)
    msg['Reply-To'] = 'contact@huganjob.jp'
    
    # テキスト版
    text_content = f"""
【HUGAN JOB】新SMTP設定テスト

{recipient_name}様

いつもお世話になっております。
HUGAN採用事務局です。

このメールは、HUGAN JOBメールシステムの新しいSMTP設定のテストメールです。

■ 変更内容
・送信元アドレス: contact@huganjob.jp
・送信者名: HUGAN採用事務局
・SMTPサーバー: smtp.huganjob.jp
・認証方式: 通常のパスワード認証 (STARTTLS)

■ 改善点
・送信ドメインと表示ドメインの完全一致
・SPF/DKIM認証の改善
・迷惑メール判定の回避
・ブランド統一

このメールが正常に受信できている場合、新しい設定が正しく動作しています。

何かご不明な点がございましたら、お気軽にお問い合わせください。

--
HUGAN採用事務局
contact@huganjob.jp
https://huganjob.jp/

※このメールはシステムテスト用です。
    """.strip()
    
    # HTML版
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Hiragino Sans', 'Yu Gothic', 'Meiryo', sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background-color: #2c5aa0; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .section {{ margin-bottom: 20px; }}
            .highlight {{ background-color: #f0f8ff; padding: 15px; border-left: 4px solid #2c5aa0; }}
            .footer {{ background-color: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
            ul {{ padding-left: 20px; }}
            li {{ margin-bottom: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>【HUGAN JOB】新SMTP設定テスト</h1>
            <p>送信元アドレス変更確認</p>
        </div>
        
        <div class="content">
            <div class="section">
                <p><strong>{recipient_name}様</strong></p>
                <p>いつもお世話になっております。<br>
                HUGAN採用事務局です。</p>
                <p>このメールは、HUGAN JOBメールシステムの新しいSMTP設定のテストメールです。</p>
            </div>
            
            <div class="section highlight">
                <h3>■ 変更内容</h3>
                <ul>
                    <li><strong>送信元アドレス:</strong> contact@huganjob.jp</li>
                    <li><strong>送信者名:</strong> HUGAN採用事務局</li>
                    <li><strong>SMTPサーバー:</strong> smtp.huganjob.jp</li>
                    <li><strong>認証方式:</strong> 通常のパスワード認証 (STARTTLS)</li>
                </ul>
            </div>
            
            <div class="section">
                <h3>■ 改善点</h3>
                <ul>
                    <li>送信ドメインと表示ドメインの完全一致</li>
                    <li>SPF/DKIM認証の改善</li>
                    <li>迷惑メール判定の回避</li>
                    <li>ブランド統一</li>
                </ul>
            </div>
            
            <div class="section">
                <p><strong>このメールが正常に受信できている場合、新しい設定が正しく動作しています。</strong></p>
                <p>何かご不明な点がございましたら、お気軽にお問い合わせください。</p>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>HUGAN採用事務局</strong><br>
            contact@huganjob.jp<br>
            <a href="https://huganjob.jp/">https://huganjob.jp/</a></p>
            <p style="margin-top: 10px; font-size: 11px;">※このメールはシステムテスト用です。</p>
        </div>
    </body>
    </html>
    """
    
    # メール本文を追加
    text_part = MIMEText(text_content, 'plain', 'utf-8')
    html_part = MIMEText(html_content, 'html', 'utf-8')
    
    msg.attach(text_part)
    msg.attach(html_part)
    
    return msg

def send_test_email(password, recipient_email, recipient_name=""):
    """テストメール送信"""
    try:
        print(f"\n📤 テストメール送信中: {recipient_email}")
        
        # メール作成
        msg = create_test_email(recipient_email, recipient_name)
        
        # SMTP送信
        server = smtplib.SMTP('smtp.huganjob.jp', 587, timeout=30)
        server.starttls()
        server.login('contact@huganjob.jp', password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ 送信成功: {recipient_email}")
        return True
        
    except Exception as e:
        print(f"❌ 送信失敗: {recipient_email} - {e}")
        return False

def main():
    """メイン処理"""
    print("=" * 60)
    print("📧 HUGAN JOB テストメール送信")
    print("=" * 60)
    
    # 送信先リスト
    recipients = [
        ("naoki_yamashita@fortyfive.co.jp", "山下様"),
        ("n.yamashita@raxus.inc", "山下様"),
        ("raxus.yamashita@gmail.com", "山下様")
    ]
    
    print("📋 送信先:")
    for email, name in recipients:
        print(f"  • {email} ({name})")
    
    # パスワード入力
    print("\n🔐 contact@huganjob.jp のパスワードを入力してください:")
    import getpass
    password = getpass.getpass("パスワード: ")
    
    if not password:
        print("❌ パスワードが入力されませんでした。")
        return False
    
    # SMTP接続テスト
    print("\n🔍 SMTP接続テスト中...")
    try:
        server = smtplib.SMTP('smtp.huganjob.jp', 587, timeout=10)
        server.starttls()
        server.login('contact@huganjob.jp', password)
        server.quit()
        print("✅ SMTP接続成功")
    except Exception as e:
        print(f"❌ SMTP接続失敗: {e}")
        return False
    
    # テストメール送信
    print("\n📤 テストメール送信開始...")
    print("-" * 40)
    
    success_count = 0
    total_count = len(recipients)
    
    for email, name in recipients:
        if send_test_email(password, email, name):
            success_count += 1
        
        # 送信間隔を設ける（迷惑メール対策）
        if email != recipients[-1][0]:  # 最後のメール以外
            print("⏳ 送信間隔待機中...")
            time.sleep(2)
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 送信結果サマリー")
    print("=" * 60)
    print(f"✅ 成功: {success_count}/{total_count}")
    print(f"❌ 失敗: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 全てのテストメール送信が完了しました！")
        print("📧 受信ボックスを確認してください")
        print("\n📋 確認ポイント:")
        print("  • 送信者が「HUGAN採用事務局 <contact@huganjob.jp>」と表示されているか")
        print("  • 迷惑メールフォルダに入っていないか")
        print("  • 'via fortyfive.co.jp' などの表示がないか")
    else:
        print("\n⚠️  一部のメール送信に失敗しました")
        print("🔧 設定を確認してください")
    
    return success_count == total_count

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ 送信がキャンセルされました")
        exit(1)
    except Exception as e:
        print(f"\n❌ エラーが発生: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
