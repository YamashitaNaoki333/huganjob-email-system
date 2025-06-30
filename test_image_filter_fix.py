#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
画像ファイル名フィルタリング機能のテスト
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'core_scripts'))

from derivative_email_extractor import PrioritizedEmailExtractor

def test_image_filtering():
    """画像ファイル名フィルタリング機能をテスト"""
    
    print("=" * 60)
    print("🖼️ 画像ファイル名フィルタリング機能テスト")
    print("=" * 60)
    
    # テスト用のメールアドレス候補
    test_emails = [
        # 有効なメールアドレス
        "info@example.com",
        "contact@company.co.jp",
        "support@test.org",
        
        # 画像ファイル名（除外されるべき）
        "main_01@sp.jpg",
        "header@logo.png",
        "banner@top.gif",
        "icon@menu.svg",
        "thumb@gallery.webp",
        "hero@main.bmp",
        "footer@banner01.png",
        "logo@plus.png",
        "top@main04.jpg",
        "home@slidethum2.jpg",
        
        # レスポンシブ画像（除外されるべき）
        "image@2x.png",
        "logo@3x.jpg",
        "icon@retina.png",
        "banner@mobile.gif",
        "header@tablet.svg",
        
        # CSS/JSファイル（除外されるべき）
        "style@main.css",
        "script@app.js",
        "font@custom.woff",
        "config@settings.json",
        
        # JavaScript変数パターン（除外されるべき）
        "window@version.js",
        "jquery@plugin.js",
        "gtm4wp@config.js",
        "summary@data.js",
        
        # 無効ドメインパターン（除外されるべき）
        "test@example.image",
        "user@config.settings",
        "admin@data.params",
    ]
    
    # PrioritizedEmailExtractorのインスタンスを作成
    extractor = PrioritizedEmailExtractor()
    
    print("📋 テスト結果:")
    print()
    
    valid_count = 0
    invalid_count = 0
    
    for email in test_emails:
        is_valid = extractor.is_valid_email_format(email)
        status = "✅ 有効" if is_valid else "❌ 無効"
        
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
        
        print(f"  {status}: {email}")
    
    print()
    print("📊 統計:")
    print(f"  有効なメールアドレス: {valid_count}件")
    print(f"  無効なメールアドレス: {invalid_count}件")
    print(f"  総テスト件数: {len(test_emails)}件")
    
    # 期待される結果の検証
    expected_valid = 3  # info@example.com, contact@company.co.jp, support@test.org
    expected_invalid = len(test_emails) - expected_valid
    
    print()
    print("🔍 検証結果:")
    if valid_count == expected_valid and invalid_count == expected_invalid:
        print("✅ すべてのテストが正常に通過しました！")
        print("   画像ファイル名フィルタリング機能が正常に動作しています。")
        return True
    else:
        print("❌ テストに失敗しました。")
        print(f"   期待値: 有効{expected_valid}件、無効{expected_invalid}件")
        print(f"   実際値: 有効{valid_count}件、無効{invalid_count}件")
        return False

if __name__ == "__main__":
    print("🧪 HUGAN JOB 画像ファイル名フィルタリング機能テスト")
    print()
    
    # テスト実行
    test_result = test_image_filtering()
    
    print("\n" + "=" * 60)
    print("📋 総合結果")
    print("=" * 60)
    
    if test_result:
        print("🎉 テストが成功しました！")
        print("   画像ファイル名フィルタリング機能が正常に実装されています。")
        print()
        print("✅ 期待される効果:")
        print("   - 画像ファイル名の誤抽出が完全に停止")
        print("   - メールアドレス抽出処理の高速化")
        print("   - ログの無関係な出力が削減")
        print("   - 実際の有効なメールアドレスのみが抽出対象")
    else:
        print("❌ テストが失敗しました。")
        print("   修正が必要です。")
