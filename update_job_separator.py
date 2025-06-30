#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB職種区切り文字変更ツール
統合済み企業の職種区切り文字を「・」から「/」に変更する
"""

import pandas as pd
import datetime
import re

def identify_consolidated_companies():
    """統合済み企業を特定する"""
    
    try:
        df = pd.read_csv('data/new_input_test.csv')
        
        # 統合済み企業の特定（複数の「・」を含む職種）
        # 単一職種の「・」（例: 点検・取付スタッフ）と区別するため、
        # 2つ以上の「・」を含む、または明らかに異なる職種が結合されているものを対象
        consolidated_companies = []
        
        for _, row in df.iterrows():
            job_position = str(row['募集職種'])
            
            # 複数の「・」を含む場合（統合済みの可能性が高い）
            if job_position.count('・') >= 2:
                consolidated_companies.append({
                    'id': row['ID'],
                    'name': row['企業名'],
                    'original_job': job_position,
                    'reason': '複数の・を含む'
                })
            # 明らかに異なる職種が結合されているパターンを検出
            elif '・' in job_position:
                # 統合済みと思われるキーワードパターン
                integration_patterns = [
                    r'スタッフ・.*職',  # 「スタッフ・営業職」など
                    r'職・.*スタッフ',  # 「営業職・製造スタッフ」など
                    r'エンジニア・.*',  # 「ITエンジニア・人事」など
                    r'.*・エンジニア',  # 「製造・ITエンジニア」など
                    r'営業・.*管理',    # 「営業・生産管理」など
                    r'管理・.*営業',    # 「生産管理・営業」など
                ]
                
                for pattern in integration_patterns:
                    if re.search(pattern, job_position):
                        consolidated_companies.append({
                            'id': row['ID'],
                            'name': row['企業名'],
                            'original_job': job_position,
                            'reason': f'統合パターン検出: {pattern}'
                        })
                        break
        
        return consolidated_companies
        
    except Exception as e:
        print(f"❌ エラー: 統合済み企業の特定に失敗しました: {e}")
        return []

def update_job_separators():
    """職種区切り文字を「・」から「/」に変更"""
    
    try:
        # バックアップファイルを作成
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'data/new_input_test_backup_separator_{timestamp}.csv'
        
        df = pd.read_csv('data/new_input_test.csv')
        df.to_csv(backup_filename, index=False, encoding='utf-8-sig')
        print(f'📁 バックアップファイル作成: {backup_filename}')
        print()
        
        # 統合済み企業を特定
        consolidated_companies = identify_consolidated_companies()
        
        if not consolidated_companies:
            print('✅ 統合済み企業が見つかりませんでした')
            return False
        
        print(f'🔍 統合済み企業を{len(consolidated_companies)}社検出しました:')
        for company in consolidated_companies:
            print(f"  ID {company['id']}: {company['name']}")
            print(f"    変更前: {company['original_job']}")
            print(f"    理由: {company['reason']}")
        print()
        
        # 確認済みの統合企業リスト（手動で指定）
        confirmed_consolidated_ids = [
            175,  # 株式会社ワーキテクノ
            215,  # 株式会社フジワーク  
            141,  # 株式会社サカイ引越センター
        ]
        
        # データフレームを更新
        df_updated = df.copy()
        updated_count = 0
        
        for _, row in df_updated.iterrows():
            company_id = row['ID']
            job_position = str(row['募集職種'])
            
            # 確認済み統合企業または検出された統合企業の場合
            if (company_id in confirmed_consolidated_ids or 
                any(c['id'] == company_id for c in consolidated_companies)):
                
                # 「・」を「/」に置換（ただし、明らかに単一職種の場合は除外）
                if '・' in job_position:
                    # 単一職種の「・」を保護するパターン
                    single_job_patterns = [
                        r'^[^・]*・[^・]*$',  # 1つの「・」のみ含む
                        r'^点検・取付',       # 点検・取付スタッフ
                        r'^設備・',          # 設備・メンテナンス
                        r'^営業・事務$',      # 営業・事務（単一職種）
                    ]
                    
                    is_single_job = False
                    for pattern in single_job_patterns:
                        if re.match(pattern, job_position) and job_position.count('・') == 1:
                            # 明らかに単一職種の場合はスキップ
                            is_single_job = True
                            break
                    
                    if not is_single_job:
                        new_job_position = job_position.replace('・', '/')
                        df_updated.loc[df_updated['ID'] == company_id, '募集職種'] = new_job_position
                        updated_count += 1
                        
                        print(f"✅ ID {company_id}: {row['企業名']}")
                        print(f"    変更前: {job_position}")
                        print(f"    変更後: {new_job_position}")
                        print()
        
        # 更新されたデータを保存
        df_updated.to_csv('data/new_input_test.csv', index=False, encoding='utf-8-sig')
        
        print(f'📊 職種区切り文字変更完了:')
        print(f'  更新企業数: {updated_count}社')
        print(f'  総企業数: {len(df_updated)}社')
        print('💾 更新データを保存しました: data/new_input_test.csv')
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: 職種区切り文字の変更に失敗しました: {e}")
        return False

def verify_changes():
    """変更結果を検証"""
    
    try:
        df = pd.read_csv('data/new_input_test.csv')
        
        print('\n=== 変更結果検証 ===')
        
        # 「/」を含む職種を検索
        slash_jobs = df[df['募集職種'].str.contains('/', na=False)]
        print(f'📊 「/」区切り職種: {len(slash_jobs)}社')
        
        if len(slash_jobs) > 0:
            print('変更された職種の例:')
            for _, row in slash_jobs.head(5).iterrows():
                print(f"  ID {row['ID']}: {row['企業名']} - {row['募集職種']}")
        
        # 残存する「・」を含む職種を確認
        dot_jobs = df[df['募集職種'].str.contains('・', na=False)]
        print(f'\n📊 「・」を含む職種（残存）: {len(dot_jobs)}社')
        
        if len(dot_jobs) > 0:
            print('残存する「・」職種の例（単一職種）:')
            for _, row in dot_jobs.head(5).iterrows():
                print(f"  ID {row['ID']}: {row['企業名']} - {row['募集職種']}")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: 検証に失敗しました: {e}")
        return False

if __name__ == "__main__":
    print('=== HUGANJOB職種区切り文字変更処理 ===')
    print('統合済み企業の職種区切り文字を「・」から「/」に変更します')
    print()
    
    # 職種区切り文字を変更
    if update_job_separators():
        # 変更結果を検証
        verify_changes()
        print('\n🎯 職種区切り文字の変更が完了しました')
        print('📈 ダッシュボードで結果を確認してください: http://127.0.0.1:5002/companies')
    else:
        print('\n❌ 職種区切り文字の変更に失敗しました')
