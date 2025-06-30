#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Microsoft 365用設定ファイル作成スクリプト
OAuth2認証設定を含む
"""

import configparser
import os
from datetime import datetime

def create_microsoft365_config():
    """Microsoft 365用の設定ファイルを作成"""
    print("🔧 Microsoft 365用設定ファイル作成")
    print("=" * 60)
    
    print("📝 Azure AD アプリケーション情報を入力してください:")
    print("（Azure Portal > Azure Active Directory > アプリの登録 で確認）")
    
    # Azure AD情報の入力
    tenant_id = input("テナントID (Directory ID): ").strip()
    client_id = input("クライアントID (Application ID): ").strip()
    client_secret = input("クライアントシークレット: ").strip()
    
    if not all([tenant_id, client_id, client_secret]):
        print("❌ 必要な情報が入力されていません")
        return False
    
    # メールアドレス確認
    email_address = input("メールアドレス [client@hugan.co.jp]: ").strip()
    if not email_address:
        email_address = "client@hugan.co.jp"
    
    # 設定ファイル作成
    config = configparser.ConfigParser()
    
    # SMTP設定
    config.add_section('SMTP')
    config.set('SMTP', 'server', 'smtp.office365.com')
    config.set('SMTP', 'port', '587')
    config.set('SMTP', 'username', email_address)
    config.set('SMTP', 'sender_name', 'HUGAN JOB')
    config.set('SMTP', 'from_name', 'HUGAN JOB')
    config.set('SMTP', 'from_email', email_address)
    config.set('SMTP', 'reply_to', email_address)
    config.set('SMTP', 'auth_method', 'oauth2')
    
    # OAuth2設定
    config.add_section('OAUTH2')
    config.set('OAUTH2', 'tenant_id', tenant_id)
    config.set('OAUTH2', 'client_id', client_id)
    config.set('OAUTH2', 'client_secret', client_secret)
    config.set('OAUTH2', 'scope', 'https://graph.microsoft.com/.default')
    config.set('OAUTH2', 'grant_type', 'client_credentials')
    
    # 送信制御設定
    config.add_section('SENDING')
    config.set('SENDING', 'batch_size', '10')
    config.set('SENDING', 'delay_between_emails', '3')
    config.set('SENDING', 'delay_between_batches', '60')
    config.set('SENDING', 'max_retries', '3')
    
    # 迷惑メール対策設定
    config.add_section('ANTI_SPAM')
    config.set('ANTI_SPAM', 'use_html_format', 'true')
    config.set('ANTI_SPAM', 'add_tracking_pixel', 'true')
    config.set('ANTI_SPAM', 'use_multipart_alternative', 'true')
    config.set('ANTI_SPAM', 'send_interval', '3')
    config.set('ANTI_SPAM', 'enable_bounce_handling', 'true')
    config.set('ANTI_SPAM', 'use_microsoft365_features', 'true')
    
    # ログ設定
    config.add_section('LOGGING')
    config.set('LOGGING', 'level', 'INFO')
    config.set('LOGGING', 'file', 'logs/microsoft365_email.log')
    config.set('LOGGING', 'max_size', '10MB')
    config.set('LOGGING', 'backup_count', '5')
    
    # リトライ設定
    config.add_section('RETRY')
    config.set('RETRY', 'retry_count', '3')
    config.set('RETRY', 'retry_delay', '5')
    
    # ファイル保存
    config_path = 'config/microsoft365_email_config.ini'
    os.makedirs('config', exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        config.write(f)
    
    print(f"✅ 設定ファイルを作成しました: {config_path}")
    
    # 設定内容の表示
    print("\n📋 作成された設定:")
    print(f"  SMTP サーバー: smtp.office365.com:587")
    print(f"  認証方式: OAuth2")
    print(f"  メールアドレス: {email_address}")
    print(f"  テナントID: {tenant_id}")
    print(f"  クライアントID: {client_id}")
    
    # Azure AD設定確認事項
    print("\n📝 Azure AD設定確認事項:")
    print("1. アプリケーションの登録が完了していること")
    print("2. 以下のAPIアクセス許可が設定されていること:")
    print("   - Microsoft Graph > Mail.Send (Application)")
    print("   - Microsoft Graph > User.Read (Application)")
    print("3. 管理者の同意が与えられていること")
    print("4. クライアントシークレットが有効であること")
    
    # 次のステップ
    print("\n🚀 次のステップ:")
    print("1. Azure AD設定の確認")
    print("2. python microsoft365_email_sender.py でテスト実行")
    print("3. 送信結果の確認")
    
    return True

def show_azure_setup_guide():
    """Azure AD設定ガイドの表示"""
    print("\n" + "=" * 80)
    print("📚 Azure AD アプリケーション設定ガイド")
    print("=" * 80)
    
    print("\n🔧 Azure Portal での設定手順:")
    print("1. Azure Portal (https://portal.azure.com) にログイン")
    print("2. 'Azure Active Directory' を選択")
    print("3. 'アプリの登録' を選択")
    print("4. '新規登録' をクリック")
    print("5. アプリケーション名: 'HUGAN JOB Mail System'")
    print("6. サポートされているアカウントの種類: '単一テナント'")
    print("7. '登録' をクリック")
    
    print("\n🔐 APIアクセス許可の設定:")
    print("1. 作成したアプリを選択")
    print("2. 'APIのアクセス許可' を選択")
    print("3. 'アクセス許可の追加' をクリック")
    print("4. 'Microsoft Graph' を選択")
    print("5. 'アプリケーションのアクセス許可' を選択")
    print("6. 以下のアクセス許可を追加:")
    print("   - Mail.Send")
    print("   - User.Read")
    print("7. '管理者の同意を与える' をクリック")
    
    print("\n🔑 クライアントシークレットの作成:")
    print("1. '証明書とシークレット' を選択")
    print("2. '新しいクライアントシークレット' をクリック")
    print("3. 説明: 'HUGAN JOB Mail Secret'")
    print("4. 有効期限: '24か月'")
    print("5. '追加' をクリック")
    print("6. 生成された値をコピー（一度しか表示されません）")
    
    print("\n📋 必要な情報の取得:")
    print("1. テナントID: '概要' ページの 'ディレクトリ (テナント) ID'")
    print("2. クライアントID: '概要' ページの 'アプリケーション (クライアント) ID'")
    print("3. クライアントシークレット: 上記で作成した値")

if __name__ == "__main__":
    try:
        # Azure AD設定ガイドの表示
        show_azure_setup_guide()
        
        print("\n" + "=" * 80)
        input("Azure AD設定が完了したら Enter キーを押してください...")
        
        # 設定ファイル作成
        success = create_microsoft365_config()
        
        if success:
            print("\n🎉 Microsoft 365設定ファイル作成完了")
            print("次のステップ: python microsoft365_email_sender.py")
        else:
            print("\n❌ 設定ファイル作成失敗")
            
    except KeyboardInterrupt:
        print("\n\n❌ 設定作成がキャンセルされました")
    except Exception as e:
        print(f"❌ エラーが発生: {e}")
        import traceback
        traceback.print_exc()
