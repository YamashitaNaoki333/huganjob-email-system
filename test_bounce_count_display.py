#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
バウンス数表示テストスクリプト
ダッシュボードでのバウンス数表示問題を調査・修正

作成日時: 2025年06月24日
目的: CSVファイルからの正確なバウンス数取得とダッシュボード表示の確認
"""

import csv
import os
import pandas as pd
from datetime import datetime

def test_csv_bounce_count():
    """CSVファイルから直接バウンス数を取得してテスト"""
    print("🔍 CSVファイルからのバウンス数取得テスト")
    print("=" * 60)
    
    csv_file = 'data/new_input_test.csv'
    
    if not os.path.exists(csv_file):
        print(f"❌ CSVファイルが見つかりません: {csv_file}")
        return 0
    
    try:
        # 方法1: csv.DictReaderを使用
        bounce_count_dict = 0
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                bounce_status = row.get('バウンス状態', '').strip()
                if bounce_status and bounce_status.lower() in ['permanent', 'temporary', 'unknown']:
                    bounce_count_dict += 1
        
        print(f"📊 方法1 (csv.DictReader): {bounce_count_dict}件")
        
        # 方法2: pandasを使用
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
        bounce_count_pandas = len(df[df['バウンス状態'].notna() & 
                                    df['バウンス状態'].str.strip().str.lower().isin(['permanent', 'temporary', 'unknown'])])
        
        print(f"📊 方法2 (pandas): {bounce_count_pandas}件")
        
        # 詳細分析
        print(f"\n📋 バウンス状態詳細分析:")
        bounce_status_counts = df['バウンス状態'].value_counts()
        for status, count in bounce_status_counts.items():
            if pd.notna(status) and str(status).strip():
                print(f"   {status}: {count}件")
        
        # 空の値の確認
        empty_count = len(df[df['バウンス状態'].isna() | (df['バウンス状態'].str.strip() == '')])
        print(f"   空/未設定: {empty_count}件")
        
        # 総企業数
        total_companies = len(df)
        print(f"\n📈 統計:")
        print(f"   総企業数: {total_companies}社")
        print(f"   バウンス企業数: {bounce_count_pandas}社")
        print(f"   正常企業数: {total_companies - bounce_count_pandas}社")
        print(f"   バウンス率: {bounce_count_pandas / total_companies * 100:.2f}%")
        
        return bounce_count_pandas
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return 0

def test_dashboard_bounce_function():
    """ダッシュボードのバウンス取得関数をテスト"""
    print(f"\n🌐 ダッシュボードバウンス取得関数テスト")
    print("=" * 60)
    
    try:
        # ダッシュボードの関数をインポート
        import sys
        sys.path.append('dashboard')
        from derivative_dashboard import get_csv_bounce_count, check_bounce_status
        
        # CSVバウンス数取得テスト
        dashboard_bounce_count = get_csv_bounce_count()
        print(f"📊 ダッシュボード関数結果: {dashboard_bounce_count}件")
        
        # 特定企業のバウンス状態テスト
        test_company_ids = [6, 7, 8, 9, 10]  # バウンス企業として知られているID
        print(f"\n🏢 特定企業バウンス状態テスト:")
        
        for company_id in test_company_ids:
            bounce_status = check_bounce_status(company_id)
            status_text = "バウンス" if bounce_status['is_bounced'] else "正常"
            print(f"   企業ID {company_id}: {status_text}")
            if bounce_status['is_bounced']:
                print(f"      理由: {bounce_status.get('reason', 'N/A')}")
                print(f"      タイプ: {bounce_status.get('bounce_type', 'N/A')}")
        
        return dashboard_bounce_count
        
    except Exception as e:
        print(f"❌ ダッシュボード関数テストエラー: {e}")
        return 0

def test_sending_results_bounce_count():
    """送信結果ファイルからのバウンス数確認"""
    print(f"\n📤 送信結果ファイルからのバウンス数確認")
    print("=" * 60)
    
    sending_files = [
        'new_email_sending_results.csv',
        'huganjob_sending_results_20250624_141526.csv'
    ]
    
    total_bounce_from_sending = 0
    
    for file_name in sending_files:
        if os.path.exists(file_name):
            try:
                with open(file_name, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    bounce_count = 0
                    
                    for row in reader:
                        send_result = row.get('送信結果', '').strip()
                        error_message = row.get('エラーメッセージ', '').strip()
                        
                        # バウンスの判定
                        if (send_result == 'failed' or 
                            send_result == 'bounced' or 
                            (error_message and error_message != '')):
                            bounce_count += 1
                    
                    print(f"📄 {file_name}: {bounce_count}件のバウンス")
                    total_bounce_from_sending += bounce_count
                    
            except Exception as e:
                print(f"❌ {file_name} 読み込みエラー: {e}")
        else:
            print(f"⚠️ {file_name}: ファイルが見つかりません")
    
    print(f"📊 送信結果ファイル合計バウンス数: {total_bounce_from_sending}件")
    return total_bounce_from_sending

def compare_bounce_counts():
    """各方法でのバウンス数を比較"""
    print(f"\n🔄 バウンス数比較分析")
    print("=" * 60)
    
    # 各方法でバウンス数を取得
    csv_bounce_count = test_csv_bounce_count()
    dashboard_bounce_count = test_dashboard_bounce_function()
    sending_bounce_count = test_sending_results_bounce_count()
    
    print(f"\n📊 バウンス数比較結果:")
    print(f"   CSVファイル直接: {csv_bounce_count}件")
    print(f"   ダッシュボード関数: {dashboard_bounce_count}件")
    print(f"   送信結果ファイル: {sending_bounce_count}件")
    
    # 一致性チェック
    if csv_bounce_count == dashboard_bounce_count:
        print(f"✅ CSVとダッシュボード関数の結果が一致")
    else:
        print(f"❌ CSVとダッシュボード関数の結果が不一致")
        print(f"   差分: {abs(csv_bounce_count - dashboard_bounce_count)}件")
    
    # 推奨値の決定
    recommended_count = max(csv_bounce_count, dashboard_bounce_count, sending_bounce_count)
    print(f"\n💡 推奨バウンス数: {recommended_count}件")
    print(f"   理由: 最も高い値を採用（データの完全性を重視）")
    
    return {
        'csv_count': csv_bounce_count,
        'dashboard_count': dashboard_bounce_count,
        'sending_count': sending_bounce_count,
        'recommended_count': recommended_count
    }

def generate_bounce_fix_recommendations(comparison_results):
    """バウンス数修正の推奨事項を生成"""
    print(f"\n💡 バウンス数表示修正の推奨事項")
    print("=" * 60)
    
    csv_count = comparison_results['csv_count']
    dashboard_count = comparison_results['dashboard_count']
    recommended_count = comparison_results['recommended_count']
    
    if csv_count == 0 and dashboard_count == 0:
        print("⚠️ 問題: すべての方法でバウンス数が0件")
        print("📋 推奨対応:")
        print("   1. バウンス処理スクリプトの実行確認")
        print("   2. メールボックスのバウンスメール確認")
        print("   3. CSVファイルのバウンス状態列の手動確認")
    
    elif csv_count != dashboard_count:
        print("⚠️ 問題: CSVとダッシュボードの結果が不一致")
        print("📋 推奨対応:")
        print("   1. ダッシュボードのget_csv_bounce_count()関数の修正")
        print("   2. CSVファイルの読み込み処理の見直し")
        print("   3. バウンス状態の判定条件の統一")
    
    else:
        print("✅ 状況: バウンス数の取得は正常に動作")
        print("📋 確認事項:")
        print("   1. ダッシュボードでの表示が正しく反映されているか")
        print("   2. リアルタイム更新が機能しているか")
    
    print(f"\n🎯 最終推奨:")
    print(f"   ダッシュボードで表示すべきバウンス数: {recommended_count}件")
    print(f"   この値がhttp://127.0.0.1:5002/open-rate-analyticsで表示されることを確認")

def main():
    """メイン実行関数"""
    print("🔍 バウンス数表示問題の包括的調査")
    print("=" * 80)
    print(f"📅 実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 比較分析実行
    comparison_results = compare_bounce_counts()
    
    # 修正推奨事項生成
    generate_bounce_fix_recommendations(comparison_results)
    
    print(f"\n🎉 調査完了")
    print("=" * 80)
    print("次のステップ:")
    print("1. ダッシュボードを再起動")
    print("2. http://127.0.0.1:5002/open-rate-analytics にアクセス")
    print("3. バウンス数の表示を確認")
    print("4. 必要に応じてページを更新")

if __name__ == "__main__":
    main()
