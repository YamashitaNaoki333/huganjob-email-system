#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB メールアドレス検証テスト
画像ファイル名誤抽出問題の修正確認
"""

import sys
import os
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# huganjob_email_address_resolverをインポート
try:
    from huganjob_email_address_resolver import HuganJobEmailResolver
except ImportError as e:
    logger.error(f"インポートエラー: {e}")
    sys.exit(1)

def test_email_validation():
    """メールアドレス検証テスト"""
    
    print("=" * 60)
    print("📧 HUGAN JOB メールアドレス検証テスト")
    print("=" * 60)
    
    # テスト用のメールアドレス
    test_emails = [
        # 画像ファイル名（無効であるべき）
        'naritai_01@2x.png',
        'banner-premium@series.jpg', 
        'logo@lightblue.svg',
        'hero_slider@airline.jpg',
        'banner-floor@03r4-1080x360.jpg',
        'campus_life@sp.jpg',
        'icon@opencampus.svg',
        
        # CSS/JSファイル名（無効であるべき）
        'window._se@plugin.version',
        'gtm4wp@datalayer.name',
        'summary@large.image',
        'search@term.string',
        'my@jquery.easing',
        
        # レスポンシブ画像（無効であるべき）
        'logo@2x.png',
        'banner@3x.jpg',
        'hero@retina.png',
        
        # 有効なメールアドレス（有効であるべき）
        'info@company.com',
        'contact@example.co.jp',
        'support@test-company.org',
        'sales@my-business.net',
        'admin@sk-kaken.co.jp',
        
        # 無効なメールアドレス（無効であるべき）
        'invalid-email',
        '@company.com',
        'test@',
        'test@.com',
        '',
        '‐',
        '-',
        None
    ]
    
    try:
        resolver = HuganJobEmailResolver()
        
        print("\n🔍 メールアドレス検証結果:")
        print("-" * 60)
        
        valid_count = 0
        invalid_count = 0
        
        for email in test_emails:
            try:
                is_valid = resolver.is_valid_email(email)
                status = '✅ 有効' if is_valid else '❌ 無効'
                email_display = str(email) if email is not None else 'None'
                print(f'{status}: {email_display}')
                
                if is_valid:
                    valid_count += 1
                else:
                    invalid_count += 1
                    
            except Exception as e:
                print(f'⚠️  エラー: {email} - {e}')
                invalid_count += 1
        
        print("-" * 60)
        print(f"📊 検証結果サマリー:")
        print(f"   有効: {valid_count}件")
        print(f"   無効: {invalid_count}件")
        print(f"   合計: {valid_count + invalid_count}件")
        
        # 期待される結果の確認
        expected_valid = [
            'info@company.com',
            'contact@example.co.jp',
            'support@test-company.org',
            'sales@my-business.net',
            'admin@sk-kaken.co.jp'
        ]
        
        print(f"\n🎯 期待される有効メール数: {len(expected_valid)}件")
        
        if valid_count == len(expected_valid):
            print("✅ テスト成功: 画像ファイル名が正しく除外されています！")
        else:
            print("❌ テスト失敗: 予期しない結果です")
            
    except Exception as e:
        logger.error(f"テスト実行エラー: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_email_validation()
