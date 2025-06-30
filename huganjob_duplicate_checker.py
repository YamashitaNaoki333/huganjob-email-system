#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB企業データ重複チェックツール
企業ホームページURLを基準として重複企業を検出・分析する
"""

import pandas as pd
import datetime

def check_duplicates():
    """企業データの重複をチェックする"""
    
    # CSVファイルを読み込み
    try:
        df = pd.read_csv('data/new_input_test.csv')
        print('=== HUGANJOB企業データ重複チェック ===')
        print(f'総企業数: {len(df)}社')
        print()
    except FileNotFoundError:
        print("❌ エラー: data/new_input_test.csv が見つかりません")
        return
    except Exception as e:
        print(f"❌ エラー: CSVファイルの読み込みに失敗しました: {e}")
        return

    # 1. 企業ホームページURLによる重複チェック
    print('1. 企業ホームページURLによる重複チェック')
    print('-' * 50)

    # 空白やNaN値を除外してホームページURLの重複をチェック
    valid_homepage_mask = df['企業ホームページ'].notna() & (df['企業ホームページ'] != '‐')
    homepage_counts = df[valid_homepage_mask]['企業ホームページ'].value_counts()
    duplicates = homepage_counts[homepage_counts > 1]

    if len(duplicates) > 0:
        print(f'🔍 重複ホームページURL数: {len(duplicates)}件')
        print(f'🔍 重複企業総数: {duplicates.sum()}社')
        print()
        
        print('重複しているホームページURL一覧:')
        for url, count in duplicates.items():
            print(f'  📌 {url} -> {count}社')
            # 該当企業の詳細を表示
            duplicate_companies = df[df['企業ホームページ'] == url]
            for _, company in duplicate_companies.iterrows():
                email = company['担当者メールアドレス'] if pd.notna(company['担当者メールアドレス']) and company['担当者メールアドレス'] != '‐' else '未登録'
                print(f'    ID {company["ID"]}: {company["企業名"]} | {company["募集職種"]} | {email}')
            print()
    else:
        print('✅ 企業ホームページURLに重複は見つかりませんでした')

    print()

    # 2. 企業名による重複チェック（参考情報）
    print('2. 企業名による重複チェック（参考）')
    print('-' * 50)

    company_name_counts = df['企業名'].value_counts()
    name_duplicates = company_name_counts[company_name_counts > 1]

    if len(name_duplicates) > 0:
        print(f'🔍 重複企業名数: {len(name_duplicates)}件')
        print(f'🔍 重複企業総数: {name_duplicates.sum()}社')
        print()
        
        print('重複している企業名一覧（上位10件）:')
        for name, count in name_duplicates.head(10).items():
            print(f'  📌 {name} -> {count}社')
            # 該当企業の詳細を表示
            duplicate_companies = df[df['企業名'] == name]
            for _, company in duplicate_companies.iterrows():
                homepage = company['企業ホームページ'] if pd.notna(company['企業ホームページ']) and company['企業ホームページ'] != '‐' else '未登録'
                email = company['担当者メールアドレス'] if pd.notna(company['担当者メールアドレス']) and company['担当者メールアドレス'] != '‐' else '未登録'
                print(f'    ID {company["ID"]}: {homepage} | {company["募集職種"]} | {email}')
            print()
    else:
        print('✅ 企業名に重複は見つかりませんでした')

    print()

    # 3. 統計情報
    print('3. 統計情報')
    print('-' * 50)
    
    homepage_valid = len(df[df['企業ホームページ'].notna() & (df['企業ホームページ'] != '‐')])
    homepage_invalid = len(df[(df['企業ホームページ'].isna()) | (df['企業ホームページ'] == '‐')])
    email_valid = len(df[df['担当者メールアドレス'].notna() & (df['担当者メールアドレス'] != '‐')])
    email_invalid = len(df[(df['担当者メールアドレス'].isna()) | (df['担当者メールアドレス'] == '‐')])
    
    print(f'📊 総企業数: {len(df)}社')
    print(f'📊 ホームページURL有り: {homepage_valid}社 ({homepage_valid/len(df)*100:.1f}%)')
    print(f'📊 ホームページURL無し: {homepage_invalid}社 ({homepage_invalid/len(df)*100:.1f}%)')
    print(f'📊 メールアドレス有り: {email_valid}社 ({email_valid/len(df)*100:.1f}%)')
    print(f'📊 メールアドレス無し: {email_invalid}社 ({email_invalid/len(df)*100:.1f}%)')

    # 4. 重複データ処理方針の提案
    print()
    print('4. 重複データ処理方針の提案')
    print('-' * 50)
    
    if len(duplicates) > 0:
        print('🔧 重複データが発見されました。以下の処理方針を推奨します:')
        print()
        print('【推奨処理方針】')
        print('1. 統合処理: 同一ホームページURLの企業を1つに統合')
        print('   - メールアドレス: 有効なものを優先')
        print('   - 募集職種: 複数ある場合は結合または最新を採用')
        print('   - ID: 最小IDを採用')
        print()
        print('2. 削除処理: 重複企業の中で情報が少ないものを削除')
        print('   - メールアドレス未登録の企業を削除')
        print('   - より詳細な募集職種情報を持つ企業を残す')
        print()
        print('3. 手動確認: 企業名が異なる場合は手動で確認')
        print('   - 同一企業の異なる部門の可能性')
        print('   - 企業統合・分社化の可能性')
    else:
        print('✅ 重複データは見つかりませんでした。')
        print('📈 データ品質は良好です。追加の処理は不要です。')

    return duplicates, name_duplicates

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
    # 重複チェックを実行
    duplicates, name_duplicates = check_duplicates()

    print()
    print('=' * 60)

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
