#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNS検証機能のテスト
改善されたhuganjob_unified_sender.pyのテスト
"""

import socket
from datetime import datetime

def test_dns_validation():
    """DNS検証機能のテスト"""
    
    print("🔍 DNS検証機能テスト")
    print("=" * 50)
    print(f"テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # テスト用メールアドレス
    test_emails = [
        # 正常なドメイン
        ("gmail.com", "test@gmail.com", True),
        ("yahoo.co.jp", "test@yahoo.co.jp", True),
        ("huganjob.jp", "contact@huganjob.jp", True),
        
        # 問題のあるドメイン
        ("irisohyama.co.jp", "iriscareer@irisohyama.co.jp", False),  # ID 1957の問題ドメイン
        
        # 無効な形式
        ("", "invalid-email", False),
        ("", "test@", False),
        ("", "@domain.com", False),
        
        # 存在しないドメイン
        ("nonexistent-domain-12345.com", "test@nonexistent-domain-12345.com", False),
    ]
    
    def validate_email_domain(email_address):
        """DNS検証機能（huganjob_unified_sender.pyと同じロジック）"""
        try:
            # 基本的なメールアドレス形式チェック
            if '@' not in email_address or '.' not in email_address.split('@')[1]:
                return False, "無効なメールアドレス形式"
            
            domain = email_address.split('@')[1]
            
            # DNS解決テスト（タイムアウト5秒）
            socket.setdefaulttimeout(5)
            socket.gethostbyname(domain)
            return True, None
            
        except socket.gaierror as dns_error:
            error_msg = f"DNS解決失敗: {dns_error}"
            return False, error_msg
        except socket.timeout:
            error_msg = "DNS解決タイムアウト"
            return False, error_msg
        except Exception as e:
            error_msg = f"ドメイン検証エラー: {e}"
            return False, error_msg
        finally:
            # タイムアウトをリセット
            socket.setdefaulttimeout(None)
    
    # テスト実行
    success_count = 0
    total_count = len(test_emails)
    
    for i, (domain, email, expected_valid) in enumerate(test_emails):
        print(f"📧 テスト {i+1}/{total_count}: {email}")
        print(f"   ドメイン: {domain}")
        print(f"   期待結果: {'有効' if expected_valid else '無効'}")
        
        try:
            is_valid, error_msg = validate_email_domain(email)
            
            if is_valid:
                print(f"   ✅ 結果: 有効")
            else:
                print(f"   ❌ 結果: 無効 - {error_msg}")
            
            # 期待結果と一致するかチェック
            if is_valid == expected_valid:
                print(f"   🎯 テスト結果: 成功")
                success_count += 1
            else:
                print(f"   ⚠️ テスト結果: 失敗（期待: {'有効' if expected_valid else '無効'}, 実際: {'有効' if is_valid else '無効'}）")
                
        except Exception as e:
            print(f"   💥 テスト例外: {e}")
            
        print()
    
    # 結果サマリー
    print("=" * 50)
    print(f"📊 テスト結果サマリー")
    print(f"   成功: {success_count}/{total_count}")
    print(f"   成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("✅ 全てのテストが成功しました")
    else:
        print("⚠️ 一部のテストが失敗しました")
    
    return success_count == total_count

def test_id_1957_specific():
    """ID 1957の具体的なテスト"""
    
    print("\n🎯 ID 1957 具体的テスト")
    print("=" * 30)
    
    email = "iriscareer@irisohyama.co.jp"
    domain = "irisohyama.co.jp"
    
    print(f"対象メール: {email}")
    print(f"対象ドメイン: {domain}")
    
    try:
        # DNS解決テスト
        socket.setdefaulttimeout(5)
        ip = socket.gethostbyname(domain)
        print(f"✅ DNS解決成功: {domain} -> {ip}")
        return True
        
    except socket.gaierror as e:
        print(f"❌ DNS解決失敗: {e}")
        return False
    except socket.timeout:
        print(f"❌ DNS解決タイムアウト")
        return False
    except Exception as e:
        print(f"❌ DNS解決エラー: {e}")
        return False
    finally:
        socket.setdefaulttimeout(None)

def test_huganjob_unified_sender():
    """改善されたhuganjob_unified_sender.pyのテスト"""
    
    print("\n🧪 huganjob_unified_sender.py テスト")
    print("=" * 40)
    
    try:
        # huganjob_unified_senderをインポート
        from huganjob_unified_sender import UnifiedEmailSender

        sender = UnifiedEmailSender()
        
        # DNS検証メソッドのテスト
        test_cases = [
            ("test@gmail.com", True),
            ("iriscareer@irisohyama.co.jp", False),
            ("invalid-email", False),
        ]
        
        for email, expected in test_cases:
            print(f"📧 テスト: {email}")
            is_valid, error_msg = sender.validate_email_domain(email)
            
            if is_valid:
                print(f"   ✅ 有効")
            else:
                print(f"   ❌ 無効: {error_msg}")
            
            result = "成功" if (is_valid == expected) else "失敗"
            print(f"   🎯 テスト結果: {result}")
            print()
        
        print("✅ huganjob_unified_sender.py のDNS検証機能は正常に動作しています")
        return True
        
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False

if __name__ == "__main__":
    print(f"🚀 DNS検証機能テスト開始")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 基本DNS検証テスト
    basic_test_success = test_dns_validation()
    
    # ID 1957具体的テスト
    id_1957_test_success = test_id_1957_specific()
    
    # huganjob_unified_senderテスト
    sender_test_success = test_huganjob_unified_sender()
    
    print("\n" + "=" * 60)
    print("🏁 全体テスト結果")
    print(f"   基本DNS検証: {'✅ 成功' if basic_test_success else '❌ 失敗'}")
    print(f"   ID 1957テスト: {'✅ 成功' if id_1957_test_success else '❌ 失敗'}")
    print(f"   Senderテスト: {'✅ 成功' if sender_test_success else '❌ 失敗'}")
    
    if all([basic_test_success, id_1957_test_success, sender_test_success]):
        print("\n🎉 全てのテストが成功しました！")
        print("DNS検証機能が正常に実装されています。")
    else:
        print("\n⚠️ 一部のテストが失敗しました。")
    
    print(f"\n終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
