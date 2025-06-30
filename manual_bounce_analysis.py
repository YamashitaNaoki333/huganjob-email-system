#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手動バウンス分析 - ID 30-150の企業
"""

import pandas as pd
import datetime

def analyze_suspicious_patterns():
    """疑わしいメールアドレスパターンを分析"""
    
    print('=== ID 30-150 手動バウンス分析 ===')
    
    # 送信結果を読み込み
    df_results = pd.read_csv('new_email_sending_results.csv')
    
    # ID 30-150の企業を抽出
    target_results = df_results[(df_results['企業ID'] >= 30) & (df_results['企業ID'] <= 150)]
    
    print(f'📊 分析対象: {len(target_results)}社 (ID 30-150)')
    
    # 疑わしいパターンを検出
    suspicious_companies = []
    
    for _, row in target_results.iterrows():
        company_id = row['企業ID']
        company_name = row['企業名']
        email_address = row['メールアドレス']
        send_result = row['送信結果']
        
        suspicious_flags = []
        risk_score = 0
        
        # 1. www.プレフィックス付きメールアドレス（高リスク）
        if 'info@www.' in email_address:
            suspicious_flags.append('www_prefix')
            risk_score += 3
        
        # 2. 大企業の一般的なinfoアドレス（中リスク）
        if email_address.startswith('info@'):
            # 大企業キーワード
            if any(keyword in company_name for keyword in ['株式会社', '大学', '学校法人', '財団法人', '一般財団法人']):
                suspicious_flags.append('generic_info_large_company')
                risk_score += 2
        
        # 3. 教育機関・公的機関ドメイン（中リスク）
        domain = email_address.split('@')[1] if '@' in email_address else ''
        if any(pattern in domain for pattern in ['.ac.jp', '.or.jp', '.go.jp']):
            suspicious_flags.append('institutional_domain')
            risk_score += 2
        
        # 4. 特定の大企業ドメイン（高リスク）
        high_risk_domains = [
            'toray.co.jp',           # 東レ株式会社
            'sumitomo-chem.co.jp',   # 住友化学株式会社
            'nissin.com',            # 日清食品株式会社
            'ytv.co.jp',             # 読売テレビ放送株式会社
            'hankyu-hanshin-dept.co.jp', # 株式会社阪急阪神百貨店
            'miyakohotels.ne.jp'     # 株式会社近鉄・都ホテルズ
        ]
        
        if any(high_domain in domain for high_domain in high_risk_domains):
            suspicious_flags.append('major_corporation')
            risk_score += 4
        
        # 5. 送信結果がsuccessでもリスクが高い場合
        if send_result == 'success' and risk_score >= 3:
            suspicious_companies.append({
                'company_id': company_id,
                'company_name': company_name,
                'email_address': email_address,
                'send_result': send_result,
                'suspicious_flags': suspicious_flags,
                'risk_score': risk_score,
                'likely_bounce': risk_score >= 5
            })
    
    # リスクレベル別に分類
    high_risk = [c for c in suspicious_companies if c['risk_score'] >= 5]
    medium_risk = [c for c in suspicious_companies if 3 <= c['risk_score'] < 5]
    
    print(f'\n🔍 疑わしい企業検出結果:')
    print(f'  高リスク (5+点): {len(high_risk)}社')
    print(f'  中リスク (3-4点): {len(medium_risk)}社')
    print(f'  総疑わしい企業: {len(suspicious_companies)}社')
    
    # 高リスク企業を詳細表示
    if high_risk:
        print(f'\n🚨 高リスク企業 (バウンスの可能性が高い):')
        for company in high_risk:
            print(f'  ID {company["company_id"]}: {company["company_name"]}')
            print(f'    メール: {company["email_address"]}')
            print(f'    リスク要因: {", ".join(company["suspicious_flags"])}')
            print(f'    リスクスコア: {company["risk_score"]}点')
            print()
    
    # 中リスク企業を表示
    if medium_risk:
        print(f'\n⚠️ 中リスク企業 (要注意):')
        for company in medium_risk[:10]:  # 最初の10社
            print(f'  ID {company["company_id"]}: {company["company_name"]}')
            print(f'    メール: {company["email_address"]}')
            print(f'    リスク要因: {", ".join(company["suspicious_flags"])}')
            print()
    
    return suspicious_companies

def generate_bounce_candidates():
    """バウンス候補企業リストを生成"""
    
    # 手動で特定された追加のバウンス候補
    manual_bounce_candidates = [
        # www.プレフィックス付きアドレス（高確率でバウンス）
        {'id': 35, 'email': 'info@www.tenmasamatsushita.co.jp', 'reason': 'www prefix'},
        {'id': 36, 'email': 'info@www.toray.co.jp', 'reason': 'www prefix + major corp'},
        {'id': 37, 'email': 'info@www.artner.co.jp', 'reason': 'www prefix'},
        {'id': 39, 'email': 'info@www.ytv.co.jp', 'reason': 'www prefix + major corp'},
        {'id': 41, 'email': 'info@www.lighting-daiko.co.jp', 'reason': 'www prefix'},
        {'id': 42, 'email': 'info@www.ksdh.or.jp', 'reason': 'www prefix + institutional'},
        {'id': 43, 'email': 'info@www.kinryu-foods.co.jp', 'reason': 'www prefix'},
        {'id': 45, 'email': 'info@www.sanei-yakuhin.co.jp', 'reason': 'www prefix'},
        {'id': 46, 'email': 'info@www.nissin.com', 'reason': 'www prefix + major corp'},
        {'id': 47, 'email': 'info@www.rex.co.jp', 'reason': 'www prefix'},
        {'id': 48, 'email': 'info@www.kk-maekawa.co.jp', 'reason': 'www prefix'},
        {'id': 50, 'email': 'info@www.askme.co.jp', 'reason': 'www prefix'},
        
        # 大企業の一般的なinfoアドレス（バウンスしやすい）
        {'id': 36, 'email': 'info@sumitomo-chem.co.jp', 'reason': 'major corporation'},
        {'id': 80, 'email': 'info@miyakohotels.ne.jp', 'reason': 'major corporation'},
        {'id': 81, 'email': 'info@hankyu-hanshin-dept.co.jp', 'reason': 'major corporation'},
        
        # 教育機関・公的機関
        {'id': 56, 'email': 'info@syusei.ac.jp', 'reason': 'educational institution'},
    ]
    
    print(f'\n📋 手動特定バウンス候補: {len(manual_bounce_candidates)}社')
    
    for candidate in manual_bounce_candidates:
        print(f'  ID {candidate["id"]}: {candidate["email"]} ({candidate["reason"]})')
    
    return manual_bounce_candidates

def update_csv_with_bounces():
    """CSVファイルにバウンス情報を更新"""
    
    print(f'\n📝 CSVファイル更新処理...')
    
    # バウンス候補を取得
    bounce_candidates = generate_bounce_candidates()
    
    # 企業データを読み込み
    df_companies = pd.read_csv('data/new_input_test.csv')
    
    # バックアップを作成
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'data/new_input_test_backup_manual_bounce_{timestamp}.csv'
    df_companies.to_csv(backup_filename, index=False, encoding='utf-8-sig')
    print(f'📁 バックアップ作成: {backup_filename}')
    
    # バウンス状態列を確認・追加
    if 'バウンス状態' not in df_companies.columns:
        df_companies['バウンス状態'] = ''
    if 'バウンス日時' not in df_companies.columns:
        df_companies['バウンス日時'] = ''
    if 'バウンス理由' not in df_companies.columns:
        df_companies['バウンス理由'] = ''
    
    # バウンス候補を更新
    updated_count = 0
    for candidate in bounce_candidates:
        company_id = candidate['id']
        
        # 該当企業を特定
        company_mask = df_companies['ID'] == company_id
        if company_mask.any():
            # 既にバウンス状態が設定されていない場合のみ更新
            current_bounce_status = df_companies.loc[company_mask, 'バウンス状態'].iloc[0]
            if pd.isna(current_bounce_status) or current_bounce_status == '':
                df_companies.loc[company_mask, 'バウンス状態'] = 'permanent'
                df_companies.loc[company_mask, 'バウンス日時'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                df_companies.loc[company_mask, 'バウンス理由'] = f'Manual analysis: {candidate["reason"]}'
                
                company_name = df_companies.loc[company_mask, '企業名'].iloc[0]
                print(f'  ✅ ID {company_id}: {company_name} - バウンス状態更新')
                updated_count += 1
    
    # 更新されたデータを保存
    df_companies.to_csv('data/new_input_test.csv', index=False, encoding='utf-8-sig')
    print(f'💾 企業データベース更新完了: {updated_count}社')
    
    return updated_count

def main():
    print('HUGANJOB ID 30-150 手動バウンス分析')
    print('=' * 50)
    
    # 疑わしいパターンを分析
    suspicious_companies = analyze_suspicious_patterns()
    
    # バウンス候補を生成
    bounce_candidates = generate_bounce_candidates()
    
    # CSVファイルを更新
    updated_count = update_csv_with_bounces()
    
    print('\n' + '=' * 50)
    print('📊 手動バウンス分析結果サマリー')
    print('=' * 50)
    print(f'疑わしい企業検出: {len(suspicious_companies)}社')
    print(f'バウンス候補特定: {len(bounce_candidates)}社')
    print(f'CSVファイル更新: {updated_count}社')
    
    print('\n推奨アクション:')
    print('1. ダッシュボードを再起動して更新を確認')
    print('2. 送信システムのバウンスリストを更新')
    print('3. 実際のバウンスメール受信を監視')
    print('4. 代替メールアドレスの調査を検討')

if __name__ == "__main__":
    main()
