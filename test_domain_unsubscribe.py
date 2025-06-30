#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ドメインベース配信停止機能テストスクリプト
t-hayakawa@media4u.co.jp の配信停止申請により、
株式会社メディア4u (info@media4u.co.jp) への送信が停止されるかテスト

作成日時: 2025年6月26日
目的: ドメインベース配信停止機能の動作確認
"""

import sys
import os
sys.path.append('.')

from huganjob_unified_sender import HUGANJOBEmailSender

def test_domain_unsubscribe():
    """ドメインベース配信停止機能のテスト"""
    print("=" * 60)
    print("ドメインベース配信停止機能テスト")
    print("=" * 60)
    
    # テスト対象企業データ
    test_company = {
        'id': 2117,
        'name': '株式会社メディア4u',
        'email': 'info@media4u.co.jp',
        'job_position': '法人営業',
        '企業ホームページ': 'https://www.media4u.co.jp/'
    }
    
    print(f"📋 テスト対象企業:")
    print(f"   企業名: {test_company['name']}")
    print(f"   企業ID: {test_company['id']}")
    print(f"   メールアドレス: {test_company['email']}")
    print(f"   ホームページ: {test_company['企業ホームページ']}")
    
    print(f"\n🚫 配信停止申請:")
    print(f"   申請メール: t-hayakawa@media4u.co.jp")
    print(f"   ドメイン: media4u.co.jp")
    print(f"   理由: 個人メールアドレスからの配信停止申請")
    
    # 送信システム初期化
    sender = HUGANJOBEmailSender()
    
    print(f"\n🔍 配信停止チェック実行:")
    
    # 1. 完全一致チェック（期待結果: False）
    is_unsubscribed_exact, reason_exact = sender.check_unsubscribe_status(test_company['email'])
    print(f"   完全一致チェック: {is_unsubscribed_exact}")
    if is_unsubscribed_exact:
        print(f"     理由: {reason_exact}")
    
    # 2. ドメインベースチェック（期待結果: True）
    is_unsubscribed_domain, reason_domain = sender.check_unsubscribe_status(
        test_company['email'], 
        test_company
    )
    print(f"   ドメインベースチェック: {is_unsubscribed_domain}")
    if is_unsubscribed_domain:
        print(f"     理由: {reason_domain}")
    
    print(f"\n📊 テスト結果:")
    if is_unsubscribed_domain:
        print(f"   ✅ ドメインベース配信停止機能が正常に動作しています")
        print(f"   🚫 株式会社メディア4uへの送信は停止されます")
        print(f"   💡 理由: t-hayakawa@media4u.co.jp からの配信停止申請により、")
        print(f"        同一ドメイン（media4u.co.jp）の企業への送信を停止")
    else:
        print(f"   ❌ ドメインベース配信停止機能が動作していません")
        print(f"   ⚠️ 設定を確認してください")
    
    # 3. 実際の送信テスト（ドライラン）
    print(f"\n🧪 送信テスト（ドライラン）:")
    try:
        # 送信前チェックのみ実行（実際には送信しない）
        result = sender.send_email_with_prevention(
            test_company['id'],
            test_company['name'],
            test_company['job_position'],
            test_company['email'],
            test_company
        )
        
        print(f"   送信結果: {result}")
        
        if result == 'unsubscribed':
            print(f"   ✅ 配信停止により送信がスキップされました")
        else:
            print(f"   ⚠️ 予期しない結果: {result}")
            
    except Exception as e:
        print(f"   ❌ 送信テストエラー: {e}")
    
    print(f"\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)

def test_other_domain():
    """他のドメインの企業への影響をテスト"""
    print("\n" + "=" * 60)
    print("他ドメイン企業への影響テスト")
    print("=" * 60)
    
    # 異なるドメインの企業データ
    other_company = {
        'id': 2118,
        'name': '株式会社丸雄組',
        'email': 'info@maruyuugumi.com',
        'job_position': '法人営業',
        '企業ホームページ': 'https://www.maruyuugumi.com/'
    }
    
    print(f"📋 テスト対象企業（異なるドメイン）:")
    print(f"   企業名: {other_company['name']}")
    print(f"   企業ID: {other_company['id']}")
    print(f"   メールアドレス: {other_company['email']}")
    print(f"   ドメイン: maruyuugumi.com")
    
    sender = HUGANJOBEmailSender()
    
    # ドメインベースチェック（期待結果: False）
    is_unsubscribed, reason = sender.check_unsubscribe_status(
        other_company['email'], 
        other_company
    )
    
    print(f"\n🔍 配信停止チェック結果:")
    print(f"   配信停止: {is_unsubscribed}")
    if is_unsubscribed:
        print(f"   理由: {reason}")
    
    if not is_unsubscribed:
        print(f"   ✅ 異なるドメインの企業には影響なし")
        print(f"   📤 正常に送信可能です")
    else:
        print(f"   ❌ 予期しない配信停止検出")
        print(f"   ⚠️ 設定を確認してください")

if __name__ == "__main__":
    test_domain_unsubscribe()
    test_other_domain()
