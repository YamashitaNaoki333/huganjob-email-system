#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
直接メール送信テストスクリプト
ターミナル問題を回避して直接メール送信を実行
"""

import sys
import os

# パスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core_scripts'))

try:
    from core_scripts.derivative_ad_email_sender import AdEmailSender
    print("✅ AdEmailSenderクラスをインポートしました")
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    sys.exit(1)

def test_email_sending():
    """メール送信テスト"""
    print("=" * 80)
    print("📧 HUGAN JOB 直接メール送信テスト")
    print("=" * 80)
    
    # 送信対象のメールアドレス
    test_emails = [
        ("raxus.yamashita@gmail.com", "司法書士法人中央ライズアクロス"),
        ("naoki_yamashita@fortyfive.co.jp", "おばた司法書士事務所"),
        ("n.yamashita@raxus.inc", "司法書士法人テスト")
    ]
    
    try:
        # メール送信クラスを初期化
        sender = AdEmailSender()
        print("✅ AdEmailSenderを初期化しました")
        
        # 設定を読み込み
        if not sender.load_config():
            print("❌ 設定ファイルの読み込みに失敗")
            return False
        print("✅ 設定ファイルを読み込みました")
        
        # テンプレートを読み込み
        template_content = sender.load_ad_template()
        if not template_content:
            print("❌ テンプレートの読み込みに失敗")
            return False
        print("✅ テンプレートを読み込みました")
        
        # SMTP接続
        if not sender.connect_smtp():
            print("❌ SMTP接続に失敗")
            return False
        print("✅ SMTP接続が確立されました")
        
        success_count = 0
        total_count = len(test_emails)
        
        # 各メールアドレスに送信
        for i, (email, company) in enumerate(test_emails, 1):
            print(f"\n🔄 {i}/{total_count} 送信処理中...")
            print(f"📧 宛先: {email}")
            print(f"🏢 企業名: {company}")
            
            try:
                # メール送信
                success, tracking_id = sender.send_email(email, company, template_content)
                
                if success:
                    success_count += 1
                    print(f"✅ {email} への送信完了")
                    print(f"📋 追跡ID: {tracking_id}")
                else:
                    print(f"❌ {email} への送信失敗")
                
            except Exception as e:
                print(f"❌ {email} への送信中にエラー: {e}")
            
            # 送信間隔（最後以外）
            if i < total_count:
                print("⏳ 送信間隔: 3秒待機中...")
                import time
                time.sleep(3)
        
        # SMTP接続を切断
        sender.disconnect_smtp()
        print("✅ SMTP接続を切断しました")
        
        # 結果表示
        print("\n" + "=" * 80)
        print("📊 送信結果サマリー")
        print("=" * 80)
        print(f"送信対象: {total_count}件")
        print(f"送信成功: {success_count}件")
        print(f"送信失敗: {total_count - success_count}件")
        print(f"成功率: {(success_count / total_count * 100):.1f}%")
        
        if success_count == total_count:
            print("🎉 全てのメール送信が成功しました！")
        else:
            print("⚠️ 一部のメール送信が失敗しました。")
        
        print("\n📋 受信確認:")
        print("1. 各メールアドレスの受信トレイを確認してください")
        print("2. 迷惑メールフォルダも確認してください")
        print("3. HTMLメールが正しく表示されるか確認してください")
        print("4. 送信者が 'HUGAN採用事務局 <client@hugan.co.jp>' として表示されるか確認してください")
        print("=" * 80)
        
        return success_count == total_count
        
    except Exception as e:
        print(f"❌ メール送信処理中にエラー: {e}")
        import traceback
        print(f"詳細エラー: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    try:
        success = test_email_sending()
        print(f"\n🏁 テスト完了: {'成功' if success else '失敗'}")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        print(f"詳細エラー: {traceback.format_exc()}")
        sys.exit(1)
