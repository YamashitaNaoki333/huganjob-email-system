#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
株式会社ワーキテクノ重複データ統合処理
wa-ki.jpを基準に4社のデータを1社に統合する
"""

import pandas as pd
import datetime

def consolidate_workitechno():
    """株式会社ワーキテクノの重複データをwa-ki.jpを基準に統合する"""
    
    try:
        df = pd.read_csv('data/new_input_test.csv')
        print('=== 株式会社ワーキテクノ 重複データ統合処理 ===')
        print()
        
        # ワーキテクノの全データを取得
        workitechno_mask = df['企業名'] == '株式会社ワーキテクノ'
        workitechno_companies = df[workitechno_mask].copy()
        
        print('統合前のワーキテクノデータ:')
        for _, company in workitechno_companies.iterrows():
            print(f'  ID {company["ID"]}: {company["企業ホームページ"]} | {company["募集職種"]}')
        print()
        
        if len(workitechno_companies) <= 1:
            print('✅ 統合対象のデータが見つかりません')
            return df
        
        # wa-ki.jpを基準企業として特定
        base_company_mask = workitechno_companies['企業ホームページ'] == 'https://wa-ki.jp/'
        if not base_company_mask.any():
            print('❌ エラー: wa-ki.jpのデータが見つかりません')
            return df
            
        base_company = workitechno_companies[base_company_mask].iloc[0]
        other_companies = workitechno_companies[~base_company_mask]
        
        print(f'📌 基準企業: ID {base_company["ID"]} - {base_company["企業ホームページ"]}')
        print('📌 統合対象企業:')
        for _, company in other_companies.iterrows():
            print(f'  ID {company["ID"]}: {company["企業ホームページ"]} | {company["募集職種"]}')
        print()
        
        # 募集職種を統合
        all_positions = [base_company['募集職種']]
        for _, company in other_companies.iterrows():
            if pd.notna(company['募集職種']) and company['募集職種'] not in all_positions:
                all_positions.append(company['募集職種'])
        
        consolidated_position = '・'.join(all_positions)
        
        # メールアドレスの統合（有効なものがあれば採用）
        consolidated_email = base_company['担当者メールアドレス']
        for _, company in other_companies.iterrows():
            if pd.notna(company['担当者メールアドレス']) and company['担当者メールアドレス'] != '‐':
                consolidated_email = company['担当者メールアドレス']
                break
        
        print('統合結果:')
        print(f'  企業名: {base_company["企業名"]}')
        print(f'  ホームページ: {base_company["企業ホームページ"]}')
        print(f'  統合前募集職種: {base_company["募集職種"]}')
        print(f'  統合後募集職種: {consolidated_position}')
        print(f'  メールアドレス: {consolidated_email}')
        print()
        
        # データフレームを更新
        df_updated = df.copy()
        
        # 基準企業のデータを更新
        base_index = df_updated[df_updated['ID'] == base_company['ID']].index[0]
        df_updated.loc[base_index, '募集職種'] = consolidated_position
        if pd.notna(consolidated_email) and consolidated_email != '‐':
            df_updated.loc[base_index, '担当者メールアドレス'] = consolidated_email
        
        # 他の企業データを削除
        other_ids = other_companies['ID'].tolist()
        df_updated = df_updated[~df_updated['ID'].isin(other_ids)]
        
        print(f'✅ 統合完了: {len(other_companies)}社を削除し、1社に統合しました')
        print(f'📊 統合前: {len(df)}社 → 統合後: {len(df_updated)}社')
        
        return df_updated
        
    except Exception as e:
        print(f'❌ エラー: 統合処理に失敗しました: {e}')
        return None

def save_consolidated_data(df_updated):
    """統合後のデータを保存する"""
    
    if df_updated is None:
        print('❌ 保存対象のデータがありません')
        return False
    
    try:
        # バックアップファイルを作成
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'data/new_input_test_backup_{timestamp}.csv'
        
        # 元ファイルをバックアップ
        original_df = pd.read_csv('data/new_input_test.csv')
        original_df.to_csv(backup_filename, index=False, encoding='utf-8-sig')
        print(f'📁 バックアップファイル作成: {backup_filename}')
        
        # 統合後データを保存
        df_updated.to_csv('data/new_input_test.csv', index=False, encoding='utf-8-sig')
        print('💾 統合後データを保存しました: data/new_input_test.csv')
        
        # 統合結果の確認
        print()
        print('=== 統合結果確認 ===')
        workitechno_after = df_updated[df_updated['企業名'] == '株式会社ワーキテクノ']
        if len(workitechno_after) == 1:
            company = workitechno_after.iloc[0]
            print(f'✅ 統合後のワーキテクノデータ:')
            print(f'  ID {company["ID"]}: {company["企業名"]}')
            print(f'  ホームページ: {company["企業ホームページ"]}')
            print(f'  募集職種: {company["募集職種"]}')
            print(f'  メールアドレス: {company["担当者メールアドレス"]}')
        else:
            print(f'⚠️ 警告: 統合後のワーキテクノデータが{len(workitechno_after)}件見つかりました')
        
        return True
        
    except Exception as e:
        print(f'❌ エラー: データ保存に失敗しました: {e}')
        return False

if __name__ == "__main__":
    # ワーキテクノの統合処理を実行
    df_updated = consolidate_workitechno()
    
    if df_updated is not None:
        # 統合後データを保存
        if save_consolidated_data(df_updated):
            print()
            print('🎯 株式会社ワーキテクノの統合処理が完了しました')
            print('📈 ダッシュボードで結果を確認してください: http://127.0.0.1:5002/companies')
        else:
            print('❌ データ保存に失敗しました')
    else:
        print('❌ 統合処理に失敗しました')
