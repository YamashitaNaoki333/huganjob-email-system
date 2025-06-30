#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB重複企業データ統合処理
企業ホームページURLが同一の重複企業を1つのIDに統合する
"""

import pandas as pd
import datetime
import os

def analyze_duplicates():
    """重複企業の詳細分析"""
    
    try:
        df = pd.read_csv('data/new_input_test.csv')
        print('=== HUGANJOB重複企業データ分析 ===')
        print(f'総企業数: {len(df)}社')
        print()
        
        # 企業ホームページURLによる重複チェック
        valid_homepage_mask = df['企業ホームページ'].notna() & (df['企業ホームページ'] != '‐')
        homepage_counts = df[valid_homepage_mask]['企業ホームページ'].value_counts()
        duplicates = homepage_counts[homepage_counts > 1]
        
        print(f'重複ホームページURL数: {len(duplicates)}件')
        print(f'重複企業総数: {duplicates.sum()}社')
        print()
        
        duplicate_groups = []
        for url, count in duplicates.items():
            duplicate_companies = df[df['企業ホームページ'] == url].copy()
            duplicate_groups.append({
                'url': url,
                'count': count,
                'companies': duplicate_companies
            })
        
        return duplicate_groups
        
    except Exception as e:
        print(f'❌ エラー: 重複分析に失敗しました: {e}')
        return []

def consolidate_duplicate_group(group):
    """重複グループを統合する"""
    
    companies = group['companies']
    url = group['url']
    
    # 最小IDを基準企業として選択
    base_company = companies.loc[companies['ID'].idxmin()]
    other_companies = companies[companies['ID'] != base_company['ID']]
    
    print(f'📌 統合グループ: {url}')
    print(f'  基準企業: ID {base_company["ID"]} - {base_company["企業名"]}')
    print(f'  統合対象: {len(other_companies)}社')
    
    # 募集職種を統合
    all_positions = [base_company['募集職種']]
    for _, company in other_companies.iterrows():
        if pd.notna(company['募集職種']) and company['募集職種'] not in all_positions:
            all_positions.append(company['募集職種'])
    
    consolidated_position = '・'.join(all_positions)
    
    # メールアドレスの統合（有効なものを優先）
    consolidated_email = base_company['担当者メールアドレス']
    if pd.isna(consolidated_email) or consolidated_email == '‐':
        for _, company in other_companies.iterrows():
            if pd.notna(company['担当者メールアドレス']) and company['担当者メールアドレス'] != '‐':
                consolidated_email = company['担当者メールアドレス']
                break
    
    print(f'  統合後募集職種: {consolidated_position}')
    print(f'  統合後メールアドレス: {consolidated_email}')
    print()
    
    return {
        'base_id': base_company['ID'],
        'remove_ids': other_companies['ID'].tolist(),
        'consolidated_position': consolidated_position,
        'consolidated_email': consolidated_email
    }

def execute_consolidation():
    """重複企業の統合処理を実行"""
    
    try:
        # 元データを読み込み
        df = pd.read_csv('data/new_input_test.csv')
        original_count = len(df)
        
        print('=== HUGANJOB重複企業統合処理開始 ===')
        print(f'統合前企業数: {original_count}社')
        print()
        
        # バックアップファイルを作成
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'data/new_input_test_backup_consolidation_{timestamp}.csv'
        df.to_csv(backup_filename, index=False, encoding='utf-8-sig')
        print(f'📁 バックアップファイル作成: {backup_filename}')
        print()
        
        # 重複企業を分析
        duplicate_groups = analyze_duplicates()
        
        if not duplicate_groups:
            print('✅ 統合対象の重複企業が見つかりませんでした')
            return df
        
        # 統合処理を実行
        df_updated = df.copy()
        total_removed = 0
        
        for group in duplicate_groups:
            consolidation_result = consolidate_duplicate_group(group)
            
            # 基準企業のデータを更新
            base_index = df_updated[df_updated['ID'] == consolidation_result['base_id']].index[0]
            df_updated.loc[base_index, '募集職種'] = consolidation_result['consolidated_position']
            
            if (pd.notna(consolidation_result['consolidated_email']) and 
                consolidation_result['consolidated_email'] != '‐'):
                df_updated.loc[base_index, '担当者メールアドレス'] = consolidation_result['consolidated_email']
            
            # 重複企業を削除
            df_updated = df_updated[~df_updated['ID'].isin(consolidation_result['remove_ids'])]
            total_removed += len(consolidation_result['remove_ids'])
        
        final_count = len(df_updated)
        
        print('=== 統合処理完了 ===')
        print(f'統合前企業数: {original_count}社')
        print(f'統合後企業数: {final_count}社')
        print(f'削除企業数: {total_removed}社')
        print(f'統合グループ数: {len(duplicate_groups)}件')
        print()
        
        # 統合後データを保存
        df_updated.to_csv('data/new_input_test.csv', index=False, encoding='utf-8-sig')
        print('💾 統合後データを保存しました: data/new_input_test.csv')
        
        return df_updated
        
    except Exception as e:
        print(f'❌ エラー: 統合処理に失敗しました: {e}')
        return None

def verify_consolidation():
    """統合結果を検証"""
    
    try:
        df = pd.read_csv('data/new_input_test.csv')
        
        print('=== 統合結果検証 ===')
        
        # 重複チェック
        valid_homepage_mask = df['企業ホームページ'].notna() & (df['企業ホームページ'] != '‐')
        homepage_counts = df[valid_homepage_mask]['企業ホームページ'].value_counts()
        remaining_duplicates = homepage_counts[homepage_counts > 1]
        
        if len(remaining_duplicates) == 0:
            print('✅ 重複企業の統合が完了しました')
        else:
            print(f'⚠️ 残存重複: {len(remaining_duplicates)}件')
            for url, count in remaining_duplicates.items():
                print(f'  {url}: {count}社')
        
        # 統合された職種の確認
        multi_position_companies = df[df['募集職種'].str.contains('・', na=False)]
        print(f'📊 複数職種統合企業: {len(multi_position_companies)}社')
        
        if len(multi_position_companies) > 0:
            print('統合された職種の例:')
            for _, company in multi_position_companies.head(5).iterrows():
                print(f'  ID {company["ID"]}: {company["企業名"]} - {company["募集職種"]}')
        
        print()
        return True
        
    except Exception as e:
        print(f'❌ エラー: 検証に失敗しました: {e}')
        return False

if __name__ == "__main__":
    # 統合処理を実行
    df_updated = execute_consolidation()
    
    if df_updated is not None:
        # 結果を検証
        if verify_consolidation():
            print('🎯 重複企業統合処理が正常に完了しました')
            print('📈 ダッシュボードで結果を確認してください: http://127.0.0.1:5002/companies')
        else:
            print('❌ 統合結果の検証に失敗しました')
    else:
        print('❌ 統合処理に失敗しました')
