#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB バウンスレポート復元システム

バウンスレポートファイルから企業データベースのバウンス状態を復元
"""

import json
import pandas as pd
import datetime
import sys

def restore_bounce_status_from_report(report_file='huganjob_bounce_report_20250624_090401.json'):
    """バウンスレポートから企業データベースを復元"""
    try:
        print('=== HUGANJOB バウンスレポート復元システム ===')
        print(f'📄 レポートファイル: {report_file}')
        print()
        
        # バウンスレポートを読み込み
        with open(report_file, 'r', encoding='utf-8') as f:
            bounce_report = json.load(f)
        
        print(f'📊 バウンスレポート情報:')
        print(f'   処理日時: {bounce_report["processing_date"]}')
        print(f'   総バウンスメール数: {bounce_report["total_bounce_emails"]}件')
        print()
        
        # 企業データベースを読み込み
        df_companies = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
        print(f'📋 企業データベース読み込み: {len(df_companies)}社')
        
        # 送信結果ファイルを読み込み
        df_results = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
        print(f'📧 送信結果読み込み: {len(df_results)}件')
        
        # バックアップ作成
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'data/new_input_test_backup_report_restore_{timestamp}.csv'
        df_companies.to_csv(backup_filename, index=False, encoding='utf-8-sig')
        print(f'📁 バックアップ作成: {backup_filename}')
        
        # バウンス状態列を確認・追加
        if 'バウンス状態' not in df_companies.columns:
            df_companies['バウンス状態'] = ''
        if 'バウンス日時' not in df_companies.columns:
            df_companies['バウンス日時'] = ''
        if 'バウンス理由' not in df_companies.columns:
            df_companies['バウンス理由'] = ''
        
        print('\n🔄 バウンス状態復元中...')
        print('-' * 80)
        
        updated_count = 0
        not_found_count = 0
        
        # 各バウンスメールを処理
        for bounce_detail in bounce_report['bounce_details']:
            bounced_addresses = bounce_detail['bounced_addresses']
            bounce_type = bounce_detail['bounce_type']
            bounce_subject = bounce_detail['subject']
            bounce_date = bounce_detail['date']
            
            for bounced_email in bounced_addresses:
                # 送信結果から該当企業を検索
                matches = df_results[df_results['メールアドレス'].str.lower() == bounced_email.lower()]
                
                if not matches.empty:
                    for _, match in matches.iterrows():
                        company_id = match['企業ID']
                        company_name = match['企業名']
                        
                        # 企業データベースを更新
                        mask = df_companies['ID'] == company_id
                        if mask.any():
                            df_companies.loc[mask, 'バウンス状態'] = bounce_type
                            df_companies.loc[mask, 'バウンス日時'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            df_companies.loc[mask, 'バウンス理由'] = bounce_subject
                            
                            updated_count += 1
                            print(f'✅ ID {company_id}: {company_name} - {bounce_type}バウンス')
                            print(f'   📧 メール: {bounced_email}')
                            print(f'   📅 バウンス日時: {bounce_date}')
                            print(f'   💬 理由: {bounce_subject[:60]}...')
                            print()
                        else:
                            print(f'⚠️ 企業ID {company_id} が企業データベースに見つかりません')
                            not_found_count += 1
                else:
                    print(f'⚠️ メールアドレス {bounced_email} が送信結果に見つかりません')
                    not_found_count += 1
        
        # 更新されたデータを保存
        df_companies.to_csv('data/new_input_test.csv', index=False, encoding='utf-8-sig')
        
        print('=' * 80)
        print('🎯 バウンス状態復元完了')
        print(f'✅ 更新成功: {updated_count}社')
        if not_found_count > 0:
            print(f'⚠️ 見つからない: {not_found_count}件')
        print(f'💾 企業データベース更新: data/new_input_test.csv')
        print(f'📁 バックアップ: {backup_filename}')
        
        # 復元結果の統計
        bounce_stats = df_companies['バウンス状態'].value_counts()
        print(f'\n📊 復元後のバウンス統計:')
        for status, count in bounce_stats.items():
            if status and status.strip():
                print(f'   {status}: {count}社')
        
        return True
        
    except Exception as e:
        print(f'❌ 復元処理失敗: {e}')
        return False

def verify_restoration():
    """復元結果を検証"""
    try:
        print('\n🔍 復元結果検証中...')
        
        df_companies = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
        
        # バウンス状態の統計
        total_companies = len(df_companies)
        bounce_companies = len(df_companies[df_companies['バウンス状態'].notna() & (df_companies['バウンス状態'] != '')])
        permanent_bounces = len(df_companies[df_companies['バウンス状態'] == 'permanent'])
        temporary_bounces = len(df_companies[df_companies['バウンス状態'] == 'temporary'])
        unknown_bounces = len(df_companies[df_companies['バウンス状態'] == 'unknown'])
        
        print(f'📊 検証結果:')
        print(f'   総企業数: {total_companies}社')
        print(f'   バウンス企業: {bounce_companies}社')
        print(f'   - permanent: {permanent_bounces}社')
        print(f'   - temporary: {temporary_bounces}社')
        print(f'   - unknown: {unknown_bounces}社')
        print(f'   正常企業: {total_companies - bounce_companies}社')
        
        # ID 101以降のバウンス状況確認
        id_101_plus = df_companies[df_companies['ID'] >= 101]
        id_101_plus_bounces = len(id_101_plus[id_101_plus['バウンス状態'].notna() & (id_101_plus['バウンス状態'] != '')])
        
        print(f'\n🎯 ID 101以降の状況:')
        print(f'   総企業数: {len(id_101_plus)}社')
        print(f'   バウンス企業: {id_101_plus_bounces}社')
        print(f'   正常企業: {len(id_101_plus) - id_101_plus_bounces}社')
        
        if id_101_plus_bounces > 0:
            print(f'✅ ID 101以降のバウンス検知が復元されました！')
        else:
            print(f'⚠️ ID 101以降のバウンス検知がまだ不完全です')
        
        return True
        
    except Exception as e:
        print(f'❌ 検証失敗: {e}')
        return False

def main():
    """メイン処理"""
    # バウンス状態を復元
    if restore_bounce_status_from_report():
        # 復元結果を検証
        verify_restoration()
        
        print('\n📋 次のステップ:')
        print('1. ダッシュボードでバウンス状況を確認')
        print('2. 必要に応じて追加のバウンス検知を実行')
        print('3. 正しいメールアドレスでの再送信を検討')
        
        return True
    else:
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
