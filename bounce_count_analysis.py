#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
バウンス数の詳細分析
48件のバウンスメールと51社のCSVバウンス企業の整合性確認
"""

import json
import pandas as pd

def analyze_bounce_counts():
    """バウンス数の詳細分析"""
    
    print('=== バウンス数詳細分析 ===')
    
    # 1. バウンスレポートから実際のバウンス数を確認
    with open('huganjob_bounce_report_20250623_154449.json', 'r', encoding='utf-8') as f:
        bounce_report = json.load(f)
    
    print(f'📧 受信ボックスのバウンスメール: {bounce_report["total_bounce_emails"]}件')
    
    # 2. CSVファイルからバウンス企業数を確認
    df_companies = pd.read_csv('data/new_input_test.csv')
    csv_bounce_companies = df_companies[df_companies['バウンス状態'] == 'permanent']
    
    print(f'📊 CSVファイルのバウンス企業: {len(csv_bounce_companies)}社')
    
    # 3. バウンス理由別の分類
    bounce_reasons = csv_bounce_companies['バウンス理由'].value_counts()
    print(f'\n📋 バウンス理由別分類:')
    for reason, count in bounce_reasons.items():
        print(f'  {reason}: {count}社')
    
    # 4. 実際のバウンスメールから企業を特定
    df_results = pd.read_csv('new_email_sending_results.csv')
    
    actual_bounce_companies = []
    for bounce in bounce_report['bounce_details']:
        for addr in bounce['bounced_addresses']:
            # HUGANJOBから送信されたアドレスのみを対象
            if not any(exclude in addr for exclude in ['kagoya.net', 'xserver.jp', 'sakura.ne.jp']):
                # 送信結果から企業IDを特定
                matching_results = df_results[df_results['メールアドレス'] == addr]
                if len(matching_results) > 0:
                    company_id = matching_results.iloc[0]['企業ID']
                    company_name = matching_results.iloc[0]['企業名']
                    actual_bounce_companies.append({
                        'company_id': company_id,
                        'company_name': company_name,
                        'email': addr,
                        'bounce_type': bounce['bounce_type']
                    })
    
    # 重複を除去
    unique_actual_bounces = []
    seen_ids = set()
    for company in actual_bounce_companies:
        if company['company_id'] not in seen_ids:
            unique_actual_bounces.append(company)
            seen_ids.add(company['company_id'])
    
    print(f'\n🔍 実際にバウンスした企業: {len(unique_actual_bounces)}社')
    
    # 5. 数字の整合性確認
    print(f'\n' + '=' * 60)
    print(f'📊 バウンス数整合性分析')
    print(f'=' * 60)
    print(f'受信ボックスのバウンスメール: {bounce_report["total_bounce_emails"]}件')
    print(f'実際にバウンスした企業: {len(unique_actual_bounces)}社')
    print(f'CSVに記録されたバウンス企業: {len(csv_bounce_companies)}社')
    
    # 6. 差分の詳細分析
    actual_bounce_ids = {c['company_id'] for c in unique_actual_bounces}
    csv_bounce_ids = set(csv_bounce_companies['ID'].tolist())
    
    # 実際のバウンスだがCSVに記録されていない企業
    missing_in_csv = actual_bounce_ids - csv_bounce_ids
    # CSVに記録されているが実際のバウンスではない企業
    extra_in_csv = csv_bounce_ids - actual_bounce_ids
    
    print(f'\n🔍 詳細分析:')
    print(f'実際のバウンス ∩ CSV記録: {len(actual_bounce_ids & csv_bounce_ids)}社')
    print(f'実際のバウンス - CSV記録: {len(missing_in_csv)}社')
    print(f'CSV記録 - 実際のバウンス: {len(extra_in_csv)}社')
    
    if missing_in_csv:
        print(f'\n❌ 実際にバウンスしたがCSVに記録されていない企業:')
        for company_id in missing_in_csv:
            company = next(c for c in unique_actual_bounces if c['company_id'] == company_id)
            print(f'  ID {company_id}: {company["company_name"]} ({company["email"]})')
    
    if extra_in_csv:
        print(f'\n💡 CSVに記録されているが実際のバウンスではない企業 (予防的判定):')
        extra_companies = csv_bounce_companies[csv_bounce_companies['ID'].isin(extra_in_csv)]
        
        # 理由別に分類
        manual_analysis = extra_companies[extra_companies['バウンス理由'].str.contains('Manual analysis', na=False)]
        invalid_format = extra_companies[extra_companies['バウンス理由'].str.contains('Invalid email format', na=False)]
        other_reasons = extra_companies[~extra_companies['バウンス理由'].str.contains('Manual analysis|Invalid email format', na=False)]
        
        print(f'  手動分析による予防的判定: {len(manual_analysis)}社')
        print(f'  無効なメール形式: {len(invalid_format)}社')
        print(f'  その他の理由: {len(other_reasons)}社')
        
        # 手動分析の詳細
        if len(manual_analysis) > 0:
            print(f'\n  手動分析による予防的判定の詳細:')
            for _, row in manual_analysis.iterrows():
                print(f'    ID {row["ID"]}: {row["企業名"]} - {row["バウンス理由"]}')
    
    # 7. 結論
    print(f'\n' + '=' * 60)
    print(f'🎯 結論')
    print(f'=' * 60)
    print(f'受信ボックスで確認された実際のバウンス: {len(unique_actual_bounces)}社')
    print(f'予防的に判定されたバウンス: {len(extra_in_csv)}社')
    print(f'総バウンス企業 (CSV記録): {len(csv_bounce_companies)}社')
    print(f'')
    print(f'48件のバウンスメールは複数の同一企業への再送信や')
    print(f'システムメールを含むため、実際のバウンス企業数は{len(unique_actual_bounces)}社です。')
    print(f'')
    print(f'CSVの{len(csv_bounce_companies)}社には実際のバウンス{len(unique_actual_bounces)}社に加えて、')
    print(f'www.プレフィックスや大企業infoアドレス等の予防的判定{len(extra_in_csv)}社が含まれています。')
    
    return unique_actual_bounces, csv_bounce_companies

def main():
    print('HUGANJOB バウンス数詳細分析')
    print('=' * 50)
    
    unique_actual_bounces, csv_bounce_companies = analyze_bounce_counts()
    
    print(f'\n✅ 分析完了')

if __name__ == "__main__":
    main()
