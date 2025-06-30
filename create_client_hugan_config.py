#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
client@hugan.co.jp用設定ファイル作成スクリプト
"""

import configparser
import os
from datetime import datetime

def create_client_hugan_config():
    """client@hugan.co.jp用の設定ファイルを作成"""
    print("🔧 client@hugan.co.jp用設定ファイル作成")
    print("=" * 60)
    
    # パスワード入力
    print("📝 client@hugan.co.jpのSMTPパスワードを入力してください:")
    password = input("パスワード: ").strip()
    
    if not password:
        print("❌ パスワードが入力されていません")
        return False
    
    # 設定ファイル作成
    config = configparser.ConfigParser()
    
    # SMTP設定
    config.add_section('SMTP')
    config.set('SMTP', 'server', 'f045.sakura.ne.jp')
    config.set('SMTP', 'port', '587')
    config.set('SMTP', 'user', 'client@hugan.co.jp')
    config.set('SMTP', 'username', 'client@hugan.co.jp')
    config.set('SMTP', 'password', password)
    config.set('SMTP', 'sender_name', 'HUGAN JOB')
    config.set('SMTP', 'from_name', 'HUGAN JOB')
    config.set('SMTP', 'from_email', 'client@hugan.co.jp')
    config.set('SMTP', 'reply_to', 'client@hugan.co.jp')
    config.set('SMTP', 'smtp_auth_email', 'client@hugan.co.jp')
    
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
    config.set('ANTI_SPAM', 'use_domain_alignment', 'true')
    
    # ログ設定
    config.add_section('LOGGING')
    config.set('LOGGING', 'level', 'INFO')
    config.set('LOGGING', 'file', 'logs/client_hugan_email.log')
    config.set('LOGGING', 'max_size', '10MB')
    config.set('LOGGING', 'backup_count', '5')
    
    # リトライ設定
    config.add_section('RETRY')
    config.set('RETRY', 'retry_count', '3')
    config.set('RETRY', 'retry_delay', '5')
    
    # ファイル保存
    config_path = 'config/client_hugan_email_config.ini'
    os.makedirs('config', exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        config.write(f)
    
    print(f"✅ 設定ファイルを作成しました: {config_path}")
    
    # 設定内容の表示
    print("\n📋 作成された設定:")
    print(f"  SMTP サーバー: f045.sakura.ne.jp:587")
    print(f"  認証ユーザー: client@hugan.co.jp")
    print(f"  送信者: HUGAN JOB <client@hugan.co.jp>")
    print(f"  返信先: client@hugan.co.jp")
    print(f"  ドメイン統一: 完全一致")
    
    return True

if __name__ == "__main__":
    try:
        success = create_client_hugan_config()
        if success:
            print("\n🎉 設定ファイル作成完了")
            print("次のステップ: python client_hugan_smtp_test.py")
        else:
            print("\n❌ 設定ファイル作成失敗")
    except Exception as e:
        print(f"❌ エラーが発生: {e}")
        import traceback
        traceback.print_exc()
