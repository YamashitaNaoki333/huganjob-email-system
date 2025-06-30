#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
実際のバウンスメール分析
48件のバウンスメールから企業を特定し、CSVとの整合性を確認
"""

import json
import pandas as pd
import datetime

def analyze_actual_bounces():
    """実際のバウンスメールを分析"""
    
    print('=== 実際のバウンスメール分析 ===')
    
    # バウンスレポートを読み込み
    with open('huganjob_bounce_report_20250623_154449.json', 'r', encoding='utf-8') as f:
        bounce_report = json.load(f)
    
    print(f'📧 総バウンスメール数: {bounce_report["total_bounce_emails"]}件')
    print(f'📊 永続的バウンス: {bounce_report["summary"]["permanent_bounces"]}件')
    print(f'📊 不明バウンス: {bounce_report["summary"]["unknown_bounces"]}件')
    
    # 企業データを読み込み
    df_companies = pd.read_csv('data/new_input_test.csv')
    df_results = pd.read_csv('new_email_sending_results.csv')
    
    # バウンスしたメールアドレスを抽出
    bounced_addresses = []
    for bounce in bounce_report['bounce_details']:
        for addr in bounce['bounced_addresses']:
            # HUGANJOBから送信されたアドレスのみを対象
            if not any(exclude in addr for exclude in ['kagoya.net', 'xserver.jp', 'sakura.ne.jp']):
                bounced_addresses.append({
                    'email': addr,
                    'bounce_type': bounce['bounce_type'],
                    'date': bounce['date']
                })
    
    print(f'\n🔍 実際のバウンスアドレス: {len(bounced_addresses)}件')
    
    # 企業IDとマッチング
    matched_companies = []
    unmatched_addresses = []
    
    for bounce in bounced_addresses:
        email = bounce['email']
        
        # 送信結果から企業IDを特定
        matching_results = df_results[df_results['メールアドレス'] == email]
        
        if len(matching_results) > 0:
            company_id = matching_results.iloc[0]['企業ID']
            company_name = matching_results.iloc[0]['企業名']
            
            # 企業データからバウンス状態を確認
            company_data = df_companies[df_companies['ID'] == company_id]
            if len(company_data) > 0:
                csv_bounce_status = company_data.iloc[0].get('バウンス状態', '')
                
                matched_companies.append({
                    'company_id': company_id,
                    'company_name': company_name,
                    'email': email,
                    'actual_bounce_type': bounce['bounce_type'],
                    'csv_bounce_status': csv_bounce_status,
                    'status_match': csv_bounce_status == 'permanent',
                    'bounce_date': bounce['date']
                })
            else:
                unmatched_addresses.append(email)
        else:
            unmatched_addresses.append(email)
    
    print(f'✅ マッチした企業: {len(matched_companies)}社')
    print(f'❌ マッチしなかった: {len(unmatched_addresses)}件')
    
    # 詳細表示
    print(f'\n📋 実際のバウンス企業詳細:')
    status_match_count = 0
    
    for i, company in enumerate(matched_companies, 1):
        status_icon = '✅' if company['status_match'] else '❌'
        print(f'{i:2d}. {status_icon} ID {company["company_id"]}: {company["company_name"]}')
        print(f'     メール: {company["email"]}')
        print(f'     実際: {company["actual_bounce_type"]} | CSV: {company["csv_bounce_status"]}')
        
        if company['status_match']:
            status_match_count += 1
        print()
    
    if unmatched_addresses:
        print(f'\n⚠️ マッチしなかったアドレス:')
        for addr in unmatched_addresses:
            print(f'  {addr}')
    
    # 統計サマリー
    print(f'\n' + '=' * 60)
    print(f'📊 バウンス分析結果サマリー')
    print(f'=' * 60)
    print(f'受信ボックスのバウンスメール: {bounce_report["total_bounce_emails"]}件')
    print(f'実際のバウンスアドレス: {len(bounced_addresses)}件')
    print(f'企業とマッチした数: {len(matched_companies)}社')
    print(f'CSVステータス一致: {status_match_count}社 ({status_match_count/len(matched_companies)*100:.1f}%)')
    print(f'CSVステータス不一致: {len(matched_companies)-status_match_count}社')
    
    # CSVに記録されているバウンス企業数
    csv_bounce_companies = len(df_companies[df_companies['バウンス状態'] == 'permanent'])
    print(f'CSVバウンス企業総数: {csv_bounce_companies}社')
    
    print(f'\n🔍 数字の整合性:')
    print(f'  受信ボックス検出: {len(matched_companies)}社')
    print(f'  CSV記録済み: {csv_bounce_companies}社')
    print(f'  差分: {csv_bounce_companies - len(matched_companies)}社')
    
    if csv_bounce_companies > len(matched_companies):
        print(f'\n💡 差分の理由:')
        print(f'  - 手動分析で追加されたバウンス企業')
        print(f'  - www.プレフィックス等の予防的バウンス判定')
        print(f'  - 大企業の一般的なinfoアドレス等')
    
    return matched_companies, bounced_addresses

def update_missing_bounces():
    """実際のバウンスで漏れている企業をCSVに追加"""
    
    matched_companies, _ = analyze_actual_bounces()
    
    print(f'\n📝 CSVバウンス状態更新チェック...')
    
    # 企業データを読み込み
    df_companies = pd.read_csv('data/new_input_test.csv')
    
    updated_count = 0
    for company in matched_companies:
        if not company['status_match']:
            company_id = company['company_id']
            
            # バウンス状態を更新
            company_mask = df_companies['ID'] == company_id
            if company_mask.any():
                df_companies.loc[company_mask, 'バウンス状態'] = 'permanent'
                df_companies.loc[company_mask, 'バウンス日時'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                df_companies.loc[company_mask, 'バウンス理由'] = f'Actual bounce detected: {company["actual_bounce_type"]}'
                
                print(f'  ✅ ID {company_id}: {company["company_name"]} - バウンス状態更新')
                updated_count += 1
    
    if updated_count > 0:
        # バックアップを作成
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'data/new_input_test_backup_actual_bounce_{timestamp}.csv'
        df_companies.to_csv(backup_filename, index=False, encoding='utf-8-sig')
        print(f'📁 バックアップ作成: {backup_filename}')
        
        # 更新されたデータを保存
        df_companies.to_csv('data/new_input_test.csv', index=False, encoding='utf-8-sig')
        print(f'💾 企業データベース更新完了: {updated_count}社')
    else:
        print(f'✅ 全ての実際のバウンス企業が既にCSVに記録済みです')
    
    return updated_count

def main():
    print('HUGANJOB 実際のバウンスメール分析')
    print('=' * 50)
    
    # 実際のバウンス分析
    matched_companies, bounced_addresses = analyze_actual_bounces()
    
    # 漏れているバウンス企業をCSVに追加
    updated_count = update_missing_bounces()
    
    print(f'\n🎯 分析完了')
    print(f'実際のバウンス企業: {len(matched_companies)}社')
    print(f'CSV更新: {updated_count}社')

if __name__ == "__main__":
    main()
