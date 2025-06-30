#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB テスト送信スクリプト
少数企業への安全なテスト送信

作成日時: 2025年06月20日 22:00:00
作成者: AI Assistant
"""

import sys
import os
from huganjob_bulk_email_sender import HuganJobBulkEmailSender

def main():
    """テスト送信メイン処理"""
    print("=" * 60)
    print("🧪 HUGAN JOB テスト送信")
    print("=" * 60)
    
    # テスト送信設定
    test_configs = [
        {
            'name': 'テストモード（送信なし）',
            'params': {
                'start_id': 1,
                'end_id': 5,
                'test_mode': True,
                'max_emails': 5
            }
        },
        {
            'name': '実際のテスト送信（1社のみ）',
            'params': {
                'start_id': 1,
                'end_id': 1,
                'test_mode': False,
                'max_emails': 1
            }
        }
    ]
    
    print("📋 利用可能なテストオプション:")
    for i, config in enumerate(test_configs, 1):
        print(f"  {i}. {config['name']}")
    
    # ユーザー選択
    try:
        choice = input("\n選択してください (1-2): ").strip()
        if choice not in ['1', '2']:
            print("❌ 無効な選択です")
            return False
        
        selected_config = test_configs[int(choice) - 1]
        print(f"\n✅ 選択: {selected_config['name']}")
        
        # 確認
        if not selected_config['params']['test_mode']:
            confirm = input("\n⚠️  実際にメールを送信します。続行しますか？ (y/N): ").strip().lower()
            if confirm != 'y':
                print("❌ キャンセルされました")
                return False
        
        # 送信実行
        sender = HuganJobBulkEmailSender()
        
        # 初期化
        if not sender.load_config():
            print("❌ 設定読み込み失敗")
            return False
        
        if not sender.load_email_template():
            print("❌ テンプレート読み込み失敗")
            return False
        
        if not selected_config['params']['test_mode']:
            if not sender.connect_smtp():
                print("❌ SMTP接続失敗")
                return False
        
        # 送信実行
        stats = sender.bulk_send_emails(**selected_config['params'])
        
        if 'error' in stats:
            print(f"❌ エラー: {stats['error']}")
            return False
        
        # 結果表示
        print("\n" + "=" * 60)
        print("📊 テスト結果")
        print("=" * 60)
        print(f"対象企業数: {stats['total_companies']}")
        print(f"成功: {stats['success_count']}")
        print(f"失敗: {stats['failure_count']}")
        print(f"成功率: {stats['success_rate']:.1f}%")
        
        if stats['test_mode']:
            print("\n🧪 テストモードで実行されました")
            print("💡 実際の送信を行う場合は選択肢2を選んでください")
        else:
            print("\n✅ 実際の送信が完了しました")
            print("📧 受信ボックスを確認してください")
        
        # 結果保存
        sender.save_sending_results()
        sender.cleanup()
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n❌ キャンセルされました")
        return False
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ システムエラー: {e}")
        sys.exit(1)
