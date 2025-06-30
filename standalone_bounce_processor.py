#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB 独立バウンス処理システム
制御パネルから実行可能なバウンス処理スクリプト
"""

import sys
import argparse
import datetime
from huganjob_bounce_processor import HuganjobBounceProcessor

def print_flush(message):
    """出力をフラッシュして即座に表示"""
    print(message)
    sys.stdout.flush()

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='HUGANJOB バウンス処理システム')
    parser.add_argument('--days', type=int, default=7, help='検索期間（日数）')
    parser.add_argument('--test-mode', action='store_true', help='テストモード（移動なし）')
    parser.add_argument('--force-reprocess', action='store_true', help='強制再処理（処理済み追跡を無視）')
    parser.add_argument('--reset-tracking', action='store_true', help='処理済み追跡をリセット')

    args = parser.parse_args()

    print_flush(f"🚀 HUGANJOB バウンス処理開始")
    print_flush(f"   検索期間: {args.days}日")
    print_flush(f"   テストモード: {'有効' if args.test_mode else '無効'}")
    print_flush(f"   強制再処理: {'有効' if args.force_reprocess else '無効'}")
    print_flush(f"   追跡リセット: {'有効' if args.reset_tracking else '無効'}")
    print_flush(f"   開始時刻: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_flush(f"   実行ファイル: standalone_bounce_processor.py")
    print_flush(f"   作業ディレクトリ: {sys.path[0] if sys.path else 'unknown'}")

    try:
        print_flush("\n📧 バウンス処理システムを初期化中...")
        # バウンス処理システムを初期化
        processor = HuganjobBounceProcessor()

        # 処理済み追跡をリセット
        if args.reset_tracking:
            print_flush("🔄 処理済み追跡をリセット中...")
            processor.processed_message_ids = set()
            processor.save_processed_tracking()
            print_flush("✅ 処理済み追跡をリセットしました")

        # 強制再処理モードの設定
        if args.force_reprocess:
            print_flush("⚡ 強制再処理モード: 処理済み追跡を無視します")
            processor.force_reprocess = True

        print_flush("✅ バウンス処理システム初期化完了")

        print_flush("\n📡 メールボックスに接続中...")
        # メールボックスに接続
        if not processor.connect_to_mailbox():
            print_flush("❌ メールボックス接続に失敗しました")
            return False
        print_flush("✅ メールボックス接続成功")

        print_flush("\n🔍 バウンスメールを特定中...")
        # バウンスメールを特定
        if not processor.identify_bounce_emails():
            print_flush("❌ バウンスメール特定に失敗しました")
            return False
        print_flush(f"✅ バウンスメール特定完了: {len(processor.bounce_emails)}件")

        # テストモードでない場合のみ移動処理を実行
        if not args.test_mode:
            print_flush("\n📁 バウンスメールを整理中...")
            # バウンスメールを整理（bounceフォルダに移動）
            if not processor.organize_bounce_emails():
                print_flush("❌ バウンスメール整理に失敗しました")
                return False
            print_flush("✅ バウンスメール整理完了")

            print_flush("\n💾 企業データベースを更新中...")
            # 企業データベースを更新
            if not processor.update_company_database():
                print_flush("❌ 企業データベース更新に失敗しました")
                return False
            print_flush("✅ 企業データベース更新完了")
        else:
            print_flush("⚠️ テストモード: メール移動とデータベース更新をスキップしました")

        print_flush("\n📝 処理済み追跡を更新中...")
        # 処理済み追跡を更新
        processor.save_processed_tracking()
        print_flush("✅ 処理済み追跡更新完了")

        print_flush("\n📄 レポートを生成中...")
        # レポートを生成
        report_file = processor.generate_bounce_report()
        print_flush(f"✅ レポート生成完了: {report_file}")

        print_flush("\n🔌 メールボックス接続を終了中...")
        # 接続を閉じる
        try:
            processor.mail.close()
            processor.mail.logout()
            print_flush("✅ メールボックス接続終了完了")
        except Exception as e:
            print_flush(f"⚠️ メールボックス接続終了時にエラー: {e}")

        print_flush(f"\n🎉 バウンス処理完了")
        print_flush(f"   処理件数: {len(processor.bounce_emails)}件")
        print_flush(f"   レポートファイル: {report_file}")
        print_flush(f"   完了時刻: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if len(processor.bounce_emails) > 0:
            print_flush(f"\n📊 バウンス詳細:")
            for i, bounce in enumerate(processor.bounce_emails, 1):
                print_flush(f"   {i}. {bounce['bounce_type']}: {', '.join(bounce['bounced_addresses'])}")
        else:
            print_flush(f"\n📊 新規バウンスメールはありませんでした")

        return True

    except Exception as e:
        print_flush(f"❌ バウンス処理中にエラーが発生しました: {e}")
        import traceback
        print_flush(f"❌ エラー詳細: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
