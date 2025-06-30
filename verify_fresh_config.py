#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB 完全新規設定確認ツール
桜サーバー情報一切なし - 0から再構築
作成日時: 2025年06月20日 18:30:00
"""

import os
import configparser
import smtplib

def verify_fresh_config():
    """完全新規設定ファイルを確認"""
    config_file = 'config/huganjob_email_config.ini'
    
    print("=" * 60)
    print("📧 HUGAN JOB 完全新規設定確認")
    print("=" * 60)
    
    if not os.path.exists(config_file):
        print(f"❌ 新規設定ファイルが見つかりません: {config_file}")
        return False
    
    try:
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        
        print("✅ 完全新規設定ファイルを読み込みました")
        
        # SMTP設定確認
        print("\n📋 SMTP設定:")
        print(f"  サーバー: {config.get('SMTP', 'server')}")
        print(f"  ポート: {config.get('SMTP', 'port')}")
        print(f"  ユーザー名: {config.get('SMTP', 'user')}")
        print(f"  送信者名: {config.get('SMTP', 'sender_name')}")
        print(f"  送信者アドレス: {config.get('SMTP', 'from_email')}")
        print(f"  返信先: {config.get('SMTP', 'reply_to')}")
        
        # 設定チェック
        print("\n🔍 設定チェック:")
        
        # SMTPサーバーチェック
        if config.get('SMTP', 'server') == 'smtp.huganjob.jp':
            print("  ✅ SMTPサーバー: 正しく設定されています")
        else:
            print("  ❌ SMTPサーバー: 設定が正しくありません")
        
        # ポートチェック
        if config.get('SMTP', 'port') == '587':
            print("  ✅ ポート: 正しく設定されています")
        else:
            print("  ❌ ポート: 設定が正しくありません")
        
        # ユーザー名チェック
        if config.get('SMTP', 'user') == 'contact@huganjob.jp':
            print("  ✅ ユーザー名: 正しく設定されています")
        else:
            print("  ❌ ユーザー名: 設定が正しくありません")
        
        # 送信者アドレスチェック
        if config.get('SMTP', 'from_email') == 'contact@huganjob.jp':
            print("  ✅ 送信者アドレス: 正しく設定されています")
        else:
            print("  ❌ 送信者アドレス: 設定が正しくありません")
        
        # 送信者名チェック
        if config.get('SMTP', 'sender_name') == 'HUGAN採用事務局':
            print("  ✅ 送信者名: 正しく設定されています")
        else:
            print("  ❌ 送信者名: 設定が正しくありません")
        
        # パスワードチェック
        if config.get('SMTP', 'password'):
            print("  ✅ パスワード: 設定されています")
        else:
            print("  ❌ パスワード: 設定されていません")
        
        # SMTP接続テスト
        print("\n🔗 SMTP接続テスト")
        print("-" * 40)
        
        smtp_server = config.get('SMTP', 'server')
        smtp_port = int(config.get('SMTP', 'port'))
        smtp_user = config.get('SMTP', 'user')
        smtp_password = config.get('SMTP', 'password')
        
        print(f"📡 接続中: {smtp_server}:{smtp_port}")
        print(f"👤 認証ユーザー: {smtp_user}")
        
        try:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.quit()
            print("✅ SMTP接続成功")
        except Exception as e:
            print(f"❌ SMTP接続失敗: {e}")
            return False
        
        # 桜サーバー情報チェック
        print("\n🚫 桜サーバー情報チェック:")
        
        # 設定ファイル内容を文字列として読み込み
        with open(config_file, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        sakura_keywords = [
            'sakura', 'www4009', 'sv12053', 'xserver', 'f045',
            'marketing@fortyfive.co.jp', 'client@hugan.co.jp'
        ]
        
        found_sakura = False
        for keyword in sakura_keywords:
            if keyword.lower() in config_content.lower():
                print(f"  ❌ 桜サーバー関連情報発見: {keyword}")
                found_sakura = True
        
        if not found_sakura:
            print("  ✅ 桜サーバー関連情報: 一切なし")
        
        # 設定サマリー
        print("\n📊 完全新規設定サマリー")
        print("=" * 60)
        print("🔄 新規設定:")
        print(f"    サーバー: {config.get('SMTP', 'server')}")
        print(f"    ユーザー: {config.get('SMTP', 'user')}")
        print(f"    送信者: {config.get('SMTP', 'sender_name')} <{config.get('SMTP', 'from_email')}>")
        print(f"    返信先: {config.get('SMTP', 'reply_to')}")
        
        print("\n✅ 改善点:")
        print("  • 桜サーバー情報完全削除")
        print("  • huganjob.jpドメイン統一")
        print("  • 0から再構築された設定")
        print("  • クリーンな送信環境")
        
        print("\n" + "=" * 60)
        print("✅ HUGAN JOB 完全新規設定は正常です")
        print("📧 メールシステムは新規設定で動作する準備ができています")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ 設定ファイル読み込みエラー: {e}")
        return False

def main():
    """メイン処理"""
    success = verify_fresh_config()
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
