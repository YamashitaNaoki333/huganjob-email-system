#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB送信システムテスト
"""

import sys
import os

def test_imports():
    """インポートテスト"""
    print("📦 インポートテスト開始...")
    
    try:
        import smtplib
        print("✅ smtplib: OK")
    except Exception as e:
        print(f"❌ smtplib: {e}")
        return False
    
    try:
        import configparser
        print("✅ configparser: OK")
    except Exception as e:
        print(f"❌ configparser: {e}")
        return False
    
    try:
        from huganjob_duplicate_prevention import DuplicatePreventionManager
        print("✅ huganjob_duplicate_prevention: OK")
    except Exception as e:
        print(f"❌ huganjob_duplicate_prevention: {e}")
        return False
    
    try:
        from huganjob_unified_sender import UnifiedEmailSender
        print("✅ huganjob_unified_sender: OK")
    except Exception as e:
        print(f"❌ huganjob_unified_sender: {e}")
        return False
    
    return True

def test_config():
    """設定ファイルテスト"""
    print("\n⚙️ 設定ファイルテスト開始...")
    
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read('config/huganjob_email_config.ini', encoding='utf-8')
        
        # 必要なセクションの確認
        required_sections = ['SMTP', 'EMAIL_CONTENT', 'SENDING']
        for section in required_sections:
            if section in config:
                print(f"✅ セクション {section}: OK")
            else:
                print(f"❌ セクション {section}: 見つかりません")
                return False
        
        # SMTP設定の確認
        smtp_config = config['SMTP']
        required_keys = ['server', 'port', 'user', 'password']
        for key in required_keys:
            if key in smtp_config:
                print(f"✅ SMTP.{key}: OK")
            else:
                print(f"❌ SMTP.{key}: 見つかりません")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 設定ファイルエラー: {e}")
        return False

def test_templates():
    """テンプレートファイルテスト"""
    print("\n📄 テンプレートファイルテスト開始...")
    
    # HTMLテンプレート
    html_template = 'corporate-email-newsletter.html'
    if os.path.exists(html_template):
        print(f"✅ HTMLテンプレート: {html_template}")
    else:
        print(f"❌ HTMLテンプレート: {html_template} が見つかりません")
        return False
    
    # テキストテンプレート
    text_template = 'templates/corporate-email-newsletter-text.txt'
    if os.path.exists(text_template):
        print(f"✅ テキストテンプレート: {text_template}")
    else:
        print(f"⚠️ テキストテンプレート: {text_template} が見つかりません（オプション）")
    
    return True

def test_data_files():
    """データファイルテスト"""
    print("\n📊 データファイルテスト開始...")
    
    # 企業データファイル
    data_file = 'data/new_input_test.csv'
    if os.path.exists(data_file):
        print(f"✅ 企業データ: {data_file}")
        
        # ファイルサイズ確認
        size = os.path.getsize(data_file)
        print(f"   ファイルサイズ: {size:,} bytes")
        
        # 行数確認
        try:
            with open(data_file, 'r', encoding='utf-8-sig') as f:
                line_count = sum(1 for line in f)
            print(f"   行数: {line_count:,} 行")
        except Exception as e:
            print(f"   ⚠️ 行数確認エラー: {e}")
    else:
        print(f"❌ 企業データ: {data_file} が見つかりません")
        return False
    
    return True

def test_simple_sender():
    """簡単な送信テスト"""
    print("\n🧪 簡単な送信テスト開始...")
    
    try:
        from huganjob_unified_sender import UnifiedEmailSender
        
        # 送信システム初期化
        sender = UnifiedEmailSender()
        print("✅ 送信システム初期化: OK")
        
        # 設定読み込み
        if sender.load_config():
            print("✅ 設定読み込み: OK")
        else:
            print("❌ 設定読み込み: 失敗")
            return False
        
        # HTMLテンプレート読み込み
        if sender.load_html_template():
            print("✅ HTMLテンプレート読み込み: OK")
        else:
            print("❌ HTMLテンプレート読み込み: 失敗")
            return False
        
        print("✅ 送信システム準備完了")
        return True
        
    except Exception as e:
        print(f"❌ 送信テストエラー: {e}")
        import traceback
        print(f"   詳細: {traceback.format_exc()}")
        return False

def main():
    print("🔍 HUGANJOB送信システム診断テスト")
    print("=" * 60)
    
    tests = [
        ("インポート", test_imports),
        ("設定ファイル", test_config),
        ("テンプレート", test_templates),
        ("データファイル", test_data_files),
        ("送信システム", test_simple_sender)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}テスト実行中...")
        result = test_func()
        results.append((test_name, result))
        
        if result:
            print(f"✅ {test_name}テスト: 成功")
        else:
            print(f"❌ {test_name}テスト: 失敗")
    
    print("\n" + "=" * 60)
    print("📋 テスト結果サマリー")
    print("=" * 60)
    
    success_count = 0
    for test_name, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n🎯 総合結果: {success_count}/{len(tests)} テスト成功")
    
    if success_count == len(tests):
        print("🎉 すべてのテストが成功しました！送信システムは正常です。")
        return True
    else:
        print("⚠️ 一部のテストが失敗しました。問題を修正してください。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
