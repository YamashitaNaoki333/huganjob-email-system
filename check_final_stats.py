#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正後の送信統計確認
"""

import pandas as pd
import json

def main():
    print("📊 修正後の送信統計確認")
    print("=" * 50)

    # 送信結果ファイル
    df_results = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
    print(f"送信結果ファイル:")
    print(f"  総記録数: {len(df_results)}件")
    print(f"  ユニーク企業数: {df_results['企業ID'].nunique()}社")

    # 送信結果の内訳
    result_counts = df_results['送信結果'].value_counts()
    print(f"  送信結果内訳:")
    for result, count in result_counts.items():
        print(f"    {result}: {count}件")

    # 送信履歴
    with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
        history = json.load(f)

    print(f"\n送信履歴:")
    print(f"  総記録数: {len(history['sending_records'])}件")

    # 企業データベース
    df_companies = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
    print(f"\n企業データベース:")
    print(f"  総企業数: {len(df_companies)}社")

    # 配信停止
    try:
        df_unsubscribe = pd.read_csv('data/huganjob_unsubscribe_log.csv', encoding='utf-8-sig')
        print(f"\n配信停止:")
        print(f"  配信停止企業数: {len(df_unsubscribe)}社")
        unsubscribed_count = len(df_unsubscribe)
    except:
        print(f"\n配信停止: 0社")
        unsubscribed_count = 0

    # カバレッジ計算
    unique_sent = df_results['企業ID'].nunique()
    total_companies = len(df_companies)
    coverage = (unique_sent / total_companies) * 100

    print(f"\n📈 最終統計:")
    print(f"  総企業数: {total_companies}社")
    print(f"  送信済み企業数: {unique_sent}社")
    print(f"  カバレッジ: {coverage:.2f}%")
    
    # 実質的なカバレッジ（配信停止除外）
    effective_total = total_companies - unsubscribed_count
    effective_coverage = (unique_sent / effective_total) * 100
    print(f"  実質対象企業数: {effective_total}社")
    print(f"  実質カバレッジ: {effective_coverage:.2f}%")
    
    # 欠落企業の確認
    sent_ids = set(df_results['企業ID'].tolist())
    all_ids = set(df_companies['ID'].tolist())
    missing_ids = all_ids - sent_ids
    
    print(f"\n🔍 欠落分析:")
    print(f"  送信記録にない企業数: {len(missing_ids)}社")
    
    if missing_ids:
        missing_list = sorted(missing_ids)
        print(f"  欠落企業ID: {missing_list}")
    else:
        print(f"  ✅ 全企業に送信記録あり")

if __name__ == "__main__":
    main()
