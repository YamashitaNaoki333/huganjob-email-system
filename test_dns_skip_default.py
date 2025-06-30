#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNS検証スキップがデフォルトになったことのテスト
"""

from datetime import datetime

def test_dns_skip_default():
    """DNS検証スキップデフォルト設定のテスト"""
    
    print("🧪 DNS検証スキップ デフォルト設定テスト")
    print("=" * 60)
    print(f"テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # huganjob_unified_senderをインポート
        from huganjob_unified_sender import UnifiedEmailSender
        
        print("📋 1. デフォルト設定テスト:")
        print("-" * 40)
        
        # デフォルト設定でインスタンス作成
        sender_default = UnifiedEmailSender()
        print(f"  デフォルト設定: skip_dns_validation = {sender_default.skip_dns_validation}")
        
        if sender_default.skip_dns_validation:
            print("  ✅ DNS検証スキップがデフォルトで有効")
        else:
            print("  ❌ DNS検証スキップがデフォルトで無効")
        
        print()
        
        print("📋 2. 明示的設定テスト:")
        print("-" * 40)
        
        # 明示的にDNS検証を有効にする
        sender_dns_enabled = UnifiedEmailSender(skip_dns_validation=False)
        print(f"  DNS検証有効設定: skip_dns_validation = {sender_dns_enabled.skip_dns_validation}")
        
        # 明示的にDNS検証をスキップする
        sender_dns_skipped = UnifiedEmailSender(skip_dns_validation=True)
        print(f"  DNS検証スキップ設定: skip_dns_validation = {sender_dns_skipped.skip_dns_validation}")
        
        print()
        
        print("📋 3. 設定確認:")
        print("-" * 40)
        
        if (sender_default.skip_dns_validation and 
            not sender_dns_enabled.skip_dns_validation and 
            sender_dns_skipped.skip_dns_validation):
            print("  ✅ 全ての設定が正常に動作しています")
            print("  ✅ デフォルトでDNS検証がスキップされます")
            print("  ✅ 明示的な設定も正常に反映されます")
            return True
        else:
            print("  ❌ 設定に問題があります")
            return False
            
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False

def show_usage_examples():
    """使用例の表示"""
    
    print("\n📚 使用例:")
    print("=" * 40)
    
    print("""
🚀 基本的な送信（DNS検証スキップ - デフォルト）:
  python huganjob_unified_sender.py --start-id 1971 --end-id 1980

⚡ 機械的送信（明示的にDNS検証スキップ）:
  python huganjob_unified_sender.py --start-id 1971 --end-id 1980

🌍 DNS検証を有効にする場合:
  python huganjob_unified_sender.py --start-id 1971 --end-id 1980 --enable-dns

💡 変更点:
  - デフォルトでDNS検証をスキップ
  - --skip-dns オプションは不要
  - DNS検証が必要な場合のみ --enable-dns を使用
  - プロセスがDNS問題で停止することがなくなりました

⚠️ 注意事項:
  - 無効なドメインへの送信でバウンス率が増加する可能性
  - SMTPサーバーが最終的な配信可否を判定
  - バウンスメールの処理が重要
""")

def test_problematic_domains():
    """問題のあったドメインのリスト"""
    
    print("\n📋 DNS問題が確認された企業:")
    print("=" * 50)
    
    problematic_companies = [
        {
            "id": 1957,
            "company": "アイリスオーヤマ株式会社",
            "email": "iriscareer@irisohyama.co.jp",
            "domain": "irisohyama.co.jp",
            "status": "DNS解決失敗"
        },
        {
            "id": 1965,
            "company": "日新薬品株式会社",
            "email": "info@yg-nissin.co.jp",
            "domain": "yg-nissin.co.jp",
            "status": "DNS解決失敗 → 送信成功（スキップ後）"
        },
        {
            "id": 1967,
            "company": "安田倉庫株式会社",
            "email": "info@yasuda-soko.co.jp",
            "domain": "yasuda-soko.co.jp",
            "status": "DNS解決失敗"
        },
        {
            "id": 1969,
            "company": "株式会社ヤナセ",
            "email": "info@yanase.co.jp",
            "domain": "yanase.co.jp",
            "status": "DNS解決失敗"
        }
    ]
    
    for company in problematic_companies:
        print(f"  ID {company['id']}: {company['company']}")
        print(f"    メール: {company['email']}")
        print(f"    ドメイン: {company['domain']}")
        print(f"    状況: {company['status']}")
        print()
    
    print("💡 これらの企業は現在DNS検証スキップで送信可能です")

if __name__ == "__main__":
    # デフォルト設定テスト
    success = test_dns_skip_default()
    
    # 使用例表示
    show_usage_examples()
    
    # 問題ドメインリスト
    test_problematic_domains()
    
    print(f"\nテスト終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success:
        print("🎉 DNS検証スキップがデフォルトで有効になりました！")
        print("🚀 今後のすべての送信でDNS問題による停止が回避されます")
    else:
        print("❌ 設定に問題があります。確認が必要です。")
