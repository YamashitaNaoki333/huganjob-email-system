#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB バウンス状態リセットツール

特定の企業またはCSVに有効なメールアドレスがあるバウンス企業の
バウンス状態をリセットして、修正後のプロセスで再送信を可能にします。
"""

import pandas as pd
import argparse
import sys
from datetime import datetime

def reset_bounce_status(company_ids=None, csv_email_only=False, dry_run=False):
    """
    バウンス状態をリセット
    
    Args:
        company_ids (list): リセット対象の企業IDリスト（Noneの場合は条件に基づく）
        csv_email_only (bool): CSVに有効なメールアドレスがある企業のみ対象
        dry_run (bool): 実際の変更を行わず、対象企業のみ表示
    """
    try:
        # CSVファイル読み込み
        df = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
        
        # 対象企業の特定
        if company_ids:
            # 指定されたIDの企業
            target_df = df[df['ID'].isin(company_ids)]
            print(f"📋 指定企業ID: {company_ids}")
        elif csv_email_only:
            # CSVに有効なメールアドレスがあるバウンス企業
            target_df = df[
                (df['バウンス状態'].notna()) &  # バウンス状態がある
                (df['担当者メールアドレス'].notna()) &  # メールアドレスがある
                (df['担当者メールアドレス'].str.strip() != '') &  # 空文字でない
                (df['担当者メールアドレス'].str.strip() != '‐') &  # ハイフンでない
                (df['担当者メールアドレス'].str.contains('@', na=False))  # @を含む
            ]
            print(f"📋 CSVに有効なメールアドレスがあるバウンス企業を対象")
        else:
            # 全バウンス企業
            target_df = df[df['バウンス状態'].notna()]
            print(f"📋 全バウンス企業を対象")
        
        if target_df.empty:
            print("❌ 対象企業が見つかりませんでした")
            return False
        
        print(f"\n🎯 対象企業: {len(target_df)}社")
        print("-" * 80)
        
        # 対象企業の詳細表示
        for _, row in target_df.iterrows():
            company_id = row['ID']
            company_name = row['企業名']
            csv_email = row.get('担当者メールアドレス', '‐')
            bounce_status = row.get('バウンス状態', '')
            bounce_date = row.get('バウンス日時', '')
            bounce_reason = row.get('バウンス理由', '')
            
            print(f"ID {company_id}: {company_name}")
            print(f"  📧 CSVメール: {csv_email}")
            print(f"  🚫 バウンス状態: {bounce_status}")
            print(f"  📅 バウンス日時: {bounce_date}")
            print(f"  💬 バウンス理由: {bounce_reason}")
            print()
        
        if dry_run:
            print("🔍 ドライラン完了 - 実際の変更は行われませんでした")
            return True
        
        # 確認プロンプト
        response = input(f"\n❓ {len(target_df)}社のバウンス状態をリセットしますか？ (y/N): ")
        if response.lower() != 'y':
            print("❌ キャンセルされました")
            return False
        
        # バウンス状態をリセット
        reset_count = 0
        for idx, row in target_df.iterrows():
            company_id = row['ID']
            company_name = row['企業名']
            
            # バウンス関連フィールドをクリア
            df.loc[df['ID'] == company_id, 'バウンス状態'] = ''
            df.loc[df['ID'] == company_id, 'バウンス日時'] = ''
            df.loc[df['ID'] == company_id, 'バウンス理由'] = ''
            
            print(f"✅ リセット完了: ID {company_id} - {company_name}")
            reset_count += 1
        
        # CSVファイルに保存
        df.to_csv('data/new_input_test.csv', index=False, encoding='utf-8-sig')
        
        print(f"\n🎉 バウンス状態リセット完了: {reset_count}社")
        print(f"📁 ファイル更新: data/new_input_test.csv")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='HUGANJOB バウンス状態リセットツール')
    parser.add_argument('--ids', type=str, help='リセット対象の企業ID（カンマ区切り）')
    parser.add_argument('--csv-email-only', action='store_true', 
                       help='CSVに有効なメールアドレスがあるバウンス企業のみ対象')
    parser.add_argument('--dry-run', action='store_true', 
                       help='ドライラン（実際の変更を行わない）')
    
    args = parser.parse_args()
    
    # 企業IDの解析
    company_ids = None
    if args.ids:
        try:
            company_ids = [int(id.strip()) for id in args.ids.split(',')]
        except ValueError:
            print("❌ 企業IDは数値で指定してください（例: --ids 21,37,45）")
            return False
    
    print("=" * 80)
    print("🔄 HUGANJOB バウンス状態リセットツール")
    print("=" * 80)
    
    success = reset_bounce_status(
        company_ids=company_ids,
        csv_email_only=args.csv_email_only,
        dry_run=args.dry_run
    )
    
    if success and not args.dry_run:
        print("\n📋 次のステップ:")
        print("1. huganjob_unified_sender.py で対象企業に再送信")
        print("2. 送信結果とバウンス状況を確認")
        print("3. 必要に応じてバウンス検知を実行")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
