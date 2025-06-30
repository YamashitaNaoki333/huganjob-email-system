#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB SMTP設定スクリプト
contact@huganjob.jp用のSMTP設定を安全に設定
"""

import os
import configparser
import getpass
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formatdate

def setup_huganjob_smtp():
    """HUGAN JOB SMTP設定の更新"""
    print("=" * 60)
    print("📧 HUGAN JOB SMTP設定")
    print("=" * 60)

    config_file = 'config/derivative_email_config.ini'

    if not os.path.exists(config_file):
        print(f"❌ 設定ファイルが見つかりません: {config_file}")
        return False

    print("🔐 contact@huganjob.jp のパスワードを入力してください:")
    password = getpass.getpass("パスワード: ")

    if not password:
        print("❌ パスワードが入力されませんでした。")
        return False

    # 設定ファイルを更新
    print("\n💾 設定ファイルを更新中...")

    config = configparser.ConfigParser()
    config.read(config_file, encoding='utf-8')

    # SMTP設定を更新
    config.set('SMTP', 'password', password)

    # email設定を更新
    config.set('email', 'password', password)

    # ファイルに保存
    with open(config_file, 'w', encoding='utf-8') as f:
        config.write(f)

    print("✅ 設定ファイルが更新されました。")

    # 接続テスト
    print("\n🔍 SMTP接続テスト中...")

    try:
        # SMTP接続テスト
        server = smtplib.SMTP('smtp.huganjob.jp', 587, timeout=10)
        server.starttls()
        server.login('contact@huganjob.jp', password)
        server.quit()

        print("✅ SMTP接続テスト成功！")

        # テストメール送信の確認
        print("\n📧 テストメール送信")
        send_test = input("テストメールを送信しますか？ (y/N): ").strip().lower()

        if send_test == 'y':
            test_email = input("テスト送信先メールアドレス: ").strip()
            if test_email:
                send_test_email(password, test_email)

        return True

    except Exception as e:
        print(f"❌ SMTP接続失敗: {e}")
        print("\n🔧 確認事項:")
        print("1. パスワードが正しいか確認してください")
        print("2. smtp.huganjob.jp サーバーが稼働しているか確認してください")
        print("3. ファイアウォール設定を確認してください")
        return False

def send_test_email(password, test_email):
    """テストメール送信"""
    try:
        print(f"\n📤 テストメール送信中: {test_email}")

        # メール作成
        msg = MIMEMultipart('alternative')
        msg['From'] = Header('HUGAN採用事務局 <contact@huganjob.jp>', 'utf-8')
        msg['To'] = test_email
        msg['Subject'] = Header('HUGAN JOB システム接続テスト', 'utf-8')
        msg['Date'] = formatdate(localtime=True)
        msg['Reply-To'] = 'contact@huganjob.jp'

        # テキスト版
        text_content = """
HUGAN JOB システム接続テスト

このメールは、HUGAN JOBメールシステムの接続テストです。
正常に受信できている場合、システムが正しく設定されています。

--
HUGAN採用事務局
contact@huganjob.jp
        """.strip()

        # HTML版
        html_content = """
        <html>
        <body>
        <h2>HUGAN JOB システム接続テスト</h2>
        <p>このメールは、HUGAN JOBメールシステムの接続テストです。</p>
        <p>正常に受信できている場合、システムが正しく設定されています。</p>
        <hr>
        <p><strong>HUGAN採用事務局</strong><br>
        contact@huganjob.jp</p>
        </body>
        </html>
        """

        # メール本文を追加
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')

        msg.attach(text_part)
        msg.attach(html_part)

        # SMTP送信
        server = smtplib.SMTP('smtp.huganjob.jp', 587, timeout=10)
        server.starttls()
        server.login('contact@huganjob.jp', password)
        server.send_message(msg)
        server.quit()

        print("✅ テストメール送信成功！")
        print(f"📧 送信先: {test_email}")
        print("📬 受信ボックスを確認してください")

    except Exception as e:
        print(f"❌ テストメール送信失敗: {e}")

def show_current_config():
    """現在の設定を表示"""
    print("\n📋 現在のSMTP設定:")
    print("-" * 40)

    config_file = 'config/derivative_email_config.ini'

    if not os.path.exists(config_file):
        print(f"❌ 設定ファイルが見つかりません: {config_file}")
        return

    config = configparser.ConfigParser()
    config.read(config_file, encoding='utf-8')

    print(f"  サーバー: {config.get('SMTP', 'server')}")
    print(f"  ポート: {config.get('SMTP', 'port')}")
    print(f"  ユーザー名: {config.get('SMTP', 'user')}")
    print(f"  送信者名: {config.get('SMTP', 'sender_name')}")
    print(f"  送信者アドレス: {config.get('SMTP', 'from_email')}")
    print(f"  返信先: {config.get('SMTP', 'reply_to')}")
    print(f"  認証方式: 通常のパスワード認証")
    print(f"  接続の保護: STARTTLS")

def main():
    """メイン処理"""
    print("🚀 HUGAN JOB メールシステム設定")
    print("=" * 60)

    # 現在の設定を表示
    show_current_config()

    print("\n📝 新しいSMTP設定:")
    print("  サーバー名: smtp.huganjob.jp")
    print("  ポート: 587")
    print("  ユーザー名: contact@huganjob.jp")
    print("  認証方式: 通常のパスワード認証")
    print("  接続の保護: STARTTLS")
    print("  送信者名: HUGAN採用事務局")

    print("\n" + "=" * 60)

    # 設定実行の確認
    proceed = input("この設定でSMTP設定を更新しますか？ (y/N): ").strip().lower()

    if proceed != 'y':
        print("❌ 設定更新がキャンセルされました。")
        return False

    # SMTP設定実行
    success = setup_huganjob_smtp()

    if success:
        print("\n🎉 HUGAN JOB SMTP設定完了！")
        print("📧 メールシステムは新しい設定で動作します")
        print("\n📋 設定内容:")
        print("  送信者: HUGAN採用事務局 <contact@huganjob.jp>")
        print("  返信先: contact@huganjob.jp")
        print("  SMTP: smtp.huganjob.jp:587 (STARTTLS)")
    else:
        print("\n❌ SMTP設定に失敗しました")
        print("🔧 設定を確認して再度実行してください")

    return success

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ 設定がキャンセルされました")
        exit(1)
    except Exception as e:
        print(f"\n❌ エラーが発生: {e}")
        import traceback
        traceback.print_exc()
        exit(1)