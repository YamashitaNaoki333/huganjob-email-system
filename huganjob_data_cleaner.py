#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB企業データクリーナー
テスト関連企業や存在しない企業データを検出・削除するツール
"""

import pandas as pd
import re
import os
import json
import csv
from datetime import datetime

class HuganjobDataCleaner:
    def __init__(self, csv_file='data/new_input_test.csv'):
        self.csv_file = csv_file
        self.backup_file = f"{csv_file}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.email_results_file = 'huganjob_email_resolution_results.csv'
        self.sending_results_file = 'new_email_sending_results.csv'
        self.sending_history_file = 'huganjob_sending_history.json'
        
    def create_backup(self):
        """バックアップファイルを作成"""
        try:
            import shutil
            shutil.copy2(self.csv_file, self.backup_file)
            print(f"✅ バックアップ作成: {self.backup_file}")
            return True
        except Exception as e:
            print(f"❌ バックアップ作成エラー: {e}")
            return False
    
    def load_data(self):
        """CSVデータを読み込み"""
        try:
            df = pd.read_csv(self.csv_file, encoding='utf-8-sig')
            print(f"📊 データ読み込み完了: {len(df)}社")
            return df
        except Exception as e:
            print(f"❌ データ読み込みエラー: {e}")
            return None
    
    def detect_test_companies(self, df):
        """テスト関連企業を検出"""
        test_patterns = [
            # 企業名パターン
            r'テスト',
            r'test',
            r'TEST',
            r'サンプル',
            r'sample',
            r'SAMPLE',
            r'ダミー',
            r'dummy',
            r'DUMMY',
            r'正常企業',
            r'テスト企業',
            r'サンプル企業',
            r'ダミー企業',
            r'株式会社テスト',
            r'株式会社サンプル',
            r'株式会社ダミー',
            r'Example',
            r'EXAMPLE',
            r'Demo',
            r'DEMO',
            r'デモ',
        ]
        
        test_companies = []
        
        for index, row in df.iterrows():
            company_name = str(row.get('企業名', '')).strip()
            website = str(row.get('企業ホームページ', '')).strip()
            email = str(row.get('担当者メールアドレス', '')).strip()
            
            # 企業名チェック
            for pattern in test_patterns:
                if re.search(pattern, company_name, re.IGNORECASE):
                    test_companies.append({
                        'ID': row['ID'],
                        '企業名': company_name,
                        '理由': f'企業名にテスト関連文字列: {pattern}',
                        'データ': f"企業名: {company_name}"
                    })
                    break
            
            # ウェブサイトチェック
            test_domains = ['test.com', 'example.com', 'dummy.com', 'sample.com', 'demo.com']
            for domain in test_domains:
                if domain in website.lower():
                    test_companies.append({
                        'ID': row['ID'],
                        '企業名': company_name,
                        '理由': f'テスト用ドメイン: {domain}',
                        'データ': f"ウェブサイト: {website}"
                    })
                    break
            
            # メールアドレスチェック
            test_email_patterns = ['test@', 'sample@', 'dummy@', 'demo@', 'example@']
            for pattern in test_email_patterns:
                if email.lower().startswith(pattern):
                    test_companies.append({
                        'ID': row['ID'],
                        '企業名': company_name,
                        '理由': f'テスト用メールアドレス: {pattern}',
                        'データ': f"メール: {email}"
                    })
                    break
        
        return test_companies
    
    def detect_invalid_companies(self, df):
        """不正な企業データを検出"""
        invalid_companies = []
        
        for index, row in df.iterrows():
            company_name = str(row.get('企業名', '')).strip()
            website = str(row.get('企業ホームページ', '')).strip()
            email = str(row.get('担当者メールアドレス', '')).strip()
            
            # 企業名が空白または記号のみ
            if not company_name or company_name in ['', 'nan', 'NaN', 'null', 'NULL']:
                invalid_companies.append({
                    'ID': row['ID'],
                    '企業名': company_name,
                    '理由': '企業名が空白',
                    'データ': f"企業名: '{company_name}'"
                })
                continue
            
            # 企業名が記号のみ
            if re.match(r'^[^\w\s]+$', company_name):
                invalid_companies.append({
                    'ID': row['ID'],
                    '企業名': company_name,
                    '理由': '企業名が記号のみ',
                    'データ': f"企業名: {company_name}"
                })
                continue
            
            # 企業名が短すぎる（1文字）
            if len(company_name) == 1:
                invalid_companies.append({
                    'ID': row['ID'],
                    '企業名': company_name,
                    '理由': '企業名が1文字のみ',
                    'データ': f"企業名: {company_name}"
                })
                continue
            
            # ウェブサイトとメールアドレスの両方が空白
            website_empty = website in ['', '‐', '-', 'nan', 'NaN', 'null', 'NULL']
            email_empty = email in ['', '‐', '-', 'nan', 'NaN', 'null', 'NULL']
            
            if website_empty and email_empty:
                invalid_companies.append({
                    'ID': row['ID'],
                    '企業名': company_name,
                    '理由': 'ウェブサイトとメールアドレスの両方が空白',
                    'データ': f"ウェブサイト: {website}, メール: {email}"
                })
        
        return invalid_companies
    
    def detect_duplicate_companies(self, df):
        """重複企業を検出"""
        duplicates = []
        
        # 企業名での重複チェック
        name_duplicates = df[df.duplicated(subset=['企業名'], keep=False)]
        
        for index, row in name_duplicates.iterrows():
            duplicates.append({
                'ID': row['ID'],
                '企業名': row['企業名'],
                '理由': '企業名重複',
                'データ': f"企業名: {row['企業名']}"
            })
        
        # ドメインでの重複チェック
        df_with_domain = df.copy()
        df_with_domain['ドメイン'] = df_with_domain['企業ホームページ'].apply(self.extract_domain)
        
        domain_duplicates = df_with_domain[
            (df_with_domain['ドメイン'] != '') & 
            (df_with_domain.duplicated(subset=['ドメイン'], keep=False))
        ]
        
        for index, row in domain_duplicates.iterrows():
            duplicates.append({
                'ID': row['ID'],
                '企業名': row['企業名'],
                '理由': 'ドメイン重複',
                'データ': f"ドメイン: {row['ドメイン']}"
            })
        
        return duplicates
    
    def extract_domain(self, url):
        """URLからドメインを抽出"""
        if not url or url in ['', '‐', '-']:
            return ''
        
        try:
            # http://やhttps://を除去
            domain = url.replace('https://', '').replace('http://', '')
            # www.を除去
            domain = domain.replace('www.', '')
            # パスを除去
            domain = domain.split('/')[0]
            # ポート番号を除去
            domain = domain.split(':')[0]
            return domain.lower()
        except:
            return ''
    
    def generate_report(self, test_companies, invalid_companies, duplicate_companies):
        """レポートを生成"""
        print("\n" + "="*60)
        print("📋 HUGANJOB企業データクリーニングレポート")
        print("="*60)
        
        total_issues = len(test_companies) + len(invalid_companies) + len(duplicate_companies)
        
        print(f"🔍 検出された問題企業: {total_issues}社")
        print()
        
        # テスト関連企業
        if test_companies:
            print(f"🧪 テスト関連企業: {len(test_companies)}社")
            for company in test_companies:
                print(f"  ID {company['ID']}: {company['企業名']}")
                print(f"    理由: {company['理由']}")
                print(f"    データ: {company['データ']}")
                print()
        
        # 不正データ企業
        if invalid_companies:
            print(f"❌ 不正データ企業: {len(invalid_companies)}社")
            for company in invalid_companies:
                print(f"  ID {company['ID']}: {company['企業名']}")
                print(f"    理由: {company['理由']}")
                print(f"    データ: {company['データ']}")
                print()
        
        # 重複企業
        if duplicate_companies:
            print(f"🔄 重複企業: {len(duplicate_companies)}社")
            for company in duplicate_companies:
                print(f"  ID {company['ID']}: {company['企業名']}")
                print(f"    理由: {company['理由']}")
                print(f"    データ: {company['データ']}")
                print()
        
        return total_issues
    
    def remove_companies(self, df, companies_to_remove):
        """指定された企業を削除"""
        if not companies_to_remove:
            print("✅ 削除対象の企業はありません")
            return df
        
        ids_to_remove = [company['ID'] for company in companies_to_remove]
        
        print(f"🗑️ {len(ids_to_remove)}社を削除します...")
        
        # 削除前のデータ数
        before_count = len(df)
        
        # 企業を削除
        df_cleaned = df[~df['ID'].isin(ids_to_remove)].copy()
        
        # 削除後のデータ数
        after_count = len(df_cleaned)
        
        print(f"✅ 削除完了: {before_count}社 → {after_count}社 ({before_count - after_count}社削除)")
        
        return df_cleaned
    
    def resequence_ids(self, df):
        """IDを連番に振り直し"""
        print("🔢 IDを連番に振り直しています...")
        
        df_resequenced = df.copy()
        df_resequenced['ID'] = range(1, len(df) + 1)
        
        print(f"✅ ID振り直し完了: 1 〜 {len(df)}")
        
        return df_resequenced
    
    def save_cleaned_data(self, df):
        """クリーニング済みデータを保存"""
        try:
            df.to_csv(self.csv_file, index=False, encoding='utf-8-sig')
            print(f"✅ クリーニング済みデータ保存: {self.csv_file}")
            return True
        except Exception as e:
            print(f"❌ データ保存エラー: {e}")
            return False

    def remove_specific_companies(self, df, company_ids):
        """指定されたIDの企業を削除"""
        print(f"🗑️ 指定された{len(company_ids)}社を削除します...")
        print(f"削除対象ID: {company_ids}")

        # 削除前のデータ数
        before_count = len(df)

        # 削除対象企業の詳細を表示
        for company_id in company_ids:
            company_row = df[df['ID'] == company_id]
            if not company_row.empty:
                company_name = company_row.iloc[0]['企業名']
                email = company_row.iloc[0].get('担当者メールアドレス', '未登録')
                print(f"  ID {company_id}: {company_name} ({email})")

        # 企業を削除
        df_cleaned = df[~df['ID'].isin(company_ids)].copy()

        # 削除後のデータ数
        after_count = len(df_cleaned)

        print(f"✅ 削除完了: {before_count}社 → {after_count}社 ({before_count - after_count}社削除)")

        return df_cleaned

    def update_related_files(self, old_to_new_id_mapping):
        """関連ファイルのIDを更新"""
        print("\n🔄 関連ファイルを更新中...")

        # メールアドレス抽出結果ファイルの更新
        self.update_email_results_file(old_to_new_id_mapping)

        # 送信結果ファイルの更新
        self.update_sending_results_file(old_to_new_id_mapping)

        # 送信履歴ファイルの更新
        self.update_sending_history_file(old_to_new_id_mapping)

    def update_email_results_file(self, old_to_new_id_mapping):
        """メールアドレス抽出結果ファイルを更新"""
        if not os.path.exists(self.email_results_file):
            print(f"⚠️ {self.email_results_file} が見つかりません")
            return

        try:
            df = pd.read_csv(self.email_results_file, encoding='utf-8-sig')
            original_count = len(df)

            # 削除されたIDを除外
            df = df[df['企業ID'].isin(old_to_new_id_mapping.keys())]

            # IDを新しい値に更新
            df['企業ID'] = df['企業ID'].map(old_to_new_id_mapping)

            # 保存
            df.to_csv(self.email_results_file, index=False, encoding='utf-8-sig')
            print(f"✅ {self.email_results_file} 更新完了: {original_count} → {len(df)}行")

        except Exception as e:
            print(f"❌ {self.email_results_file} 更新エラー: {e}")

    def update_sending_results_file(self, old_to_new_id_mapping):
        """送信結果ファイルを更新"""
        if not os.path.exists(self.sending_results_file):
            print(f"⚠️ {self.sending_results_file} が見つかりません")
            return

        try:
            # CSVファイルを手動で読み込み（列数が不定のため）
            updated_rows = []
            with open(self.sending_results_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header:
                    updated_rows.append(header)

                for row in reader:
                    if len(row) > 0:
                        try:
                            old_id = int(row[0])
                            if old_id in old_to_new_id_mapping:
                                row[0] = str(old_to_new_id_mapping[old_id])
                                updated_rows.append(row)
                        except (ValueError, IndexError):
                            continue

            # 更新されたデータを保存
            with open(self.sending_results_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(updated_rows)

            print(f"✅ {self.sending_results_file} 更新完了: {len(updated_rows)-1}行")

        except Exception as e:
            print(f"❌ {self.sending_results_file} 更新エラー: {e}")

    def update_sending_history_file(self, old_to_new_id_mapping):
        """送信履歴ファイルを更新"""
        if not os.path.exists(self.sending_history_file):
            print(f"⚠️ {self.sending_history_file} が見つかりません")
            return

        try:
            with open(self.sending_history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)

            updated_history = {}
            for timestamp, entries in history_data.items():
                updated_entries = []
                for entry in entries:
                    if 'company_id' in entry:
                        old_id = entry['company_id']
                        if old_id in old_to_new_id_mapping:
                            entry['company_id'] = old_to_new_id_mapping[old_id]
                            updated_entries.append(entry)

                if updated_entries:
                    updated_history[timestamp] = updated_entries

            # 更新されたデータを保存
            with open(self.sending_history_file, 'w', encoding='utf-8') as f:
                json.dump(updated_history, f, ensure_ascii=False, indent=2)

            print(f"✅ {self.sending_history_file} 更新完了")

        except Exception as e:
            print(f"❌ {self.sending_history_file} 更新エラー: {e}")

    def create_id_mapping(self, df_before, df_after):
        """削除前後のIDマッピングを作成"""
        mapping = {}
        for new_id, (_, row) in enumerate(df_after.iterrows(), 1):
            old_id = row['ID']
            mapping[old_id] = new_id
        return mapping

def main():
    print("🧹 HUGANJOB企業データクリーナー")
    print("="*50)

    cleaner = HuganjobDataCleaner()

    # バックアップ作成
    if not cleaner.create_backup():
        return

    # データ読み込み
    df = cleaner.load_data()
    if df is None:
        return

    print(f"📊 読み込み完了: {len(df)}社")

    # 問題企業を検出
    print("\n🔍 問題企業を検出中...")
    test_companies = cleaner.detect_test_companies(df)
    invalid_companies = cleaner.detect_invalid_companies(df)
    duplicate_companies = cleaner.detect_duplicate_companies(df)

    # レポート生成
    total_issues = cleaner.generate_report(test_companies, invalid_companies, duplicate_companies)

    if total_issues == 0:
        print("✅ 問題企業は見つかりませんでした")
        return

    # 削除確認
    print(f"\n❓ {total_issues}社の問題企業を削除しますか？")
    choice = input("削除する場合は 'yes' を入力してください: ").strip().lower()

    if choice != 'yes':
        print("❌ 削除をキャンセルしました")
        return

    # 削除対象をまとめる
    all_companies_to_remove = test_companies + invalid_companies + duplicate_companies

    # 企業削除
    df_cleaned = cleaner.remove_companies(df, all_companies_to_remove)

    # ID振り直し確認
    print(f"\n❓ IDを連番に振り直しますか？")
    choice = input("振り直す場合は 'yes' を入力してください: ").strip().lower()

    if choice == 'yes':
        df_cleaned = cleaner.resequence_ids(df_cleaned)

    # 保存
    if cleaner.save_cleaned_data(df_cleaned):
        print(f"\n🎉 データクリーニング完了！")
        print(f"📁 バックアップ: {cleaner.backup_file}")
        print(f"📁 クリーニング済み: {cleaner.csv_file}")
    else:
        print(f"\n❌ データクリーニング失敗")

def main_specific_cleanup():
    """指定された企業IDを削除する専用関数"""
    print("🧹 HUGANJOB指定企業削除ツール")
    print("="*50)

    # 削除対象企業ID
    target_ids = [2995, 2996, 2997, 4837, 4838, 4839, 4840, 4832, 4833, 4834]

    cleaner = HuganjobDataCleaner()

    # バックアップ作成
    print("📁 バックアップを作成中...")
    if not cleaner.create_backup():
        return

    # データ読み込み
    df = cleaner.load_data()
    if df is None:
        return

    print(f"📊 読み込み完了: {len(df)}社")

    # 削除対象企業の確認
    print(f"\n🎯 削除対象企業: {len(target_ids)}社")
    for target_id in target_ids:
        company_row = df[df['ID'] == target_id]
        if not company_row.empty:
            company_name = company_row.iloc[0]['企業名']
            email = company_row.iloc[0].get('担当者メールアドレス', '未登録')
            print(f"  ID {target_id}: {company_name} ({email})")
        else:
            print(f"  ID {target_id}: 企業が見つかりません")

    # 削除確認
    print(f"\n❓ 上記{len(target_ids)}社を削除しますか？")
    choice = input("削除する場合は 'yes' を入力してください: ").strip().lower()

    if choice != 'yes':
        print("❌ 削除をキャンセルしました")
        return

    # 削除前のIDマッピングを作成（ID振り直し用）
    df_before_deletion = df.copy()

    # 指定企業を削除
    df_cleaned = cleaner.remove_specific_companies(df, target_ids)

    # ID振り直し
    print(f"\n🔢 IDを連番に振り直しています...")
    df_resequenced = cleaner.resequence_ids(df_cleaned)

    # IDマッピングを作成
    old_to_new_mapping = cleaner.create_id_mapping(df_before_deletion, df_resequenced)

    # メインCSVファイルを保存
    if cleaner.save_cleaned_data(df_resequenced):
        print(f"✅ メインデータ保存完了")

        # 関連ファイルを更新
        cleaner.update_related_files(old_to_new_mapping)

        print(f"\n🎉 データクリーニング完了！")
        print(f"📁 バックアップ: {cleaner.backup_file}")
        print(f"📁 クリーニング済み: {cleaner.csv_file}")
        print(f"📊 最終企業数: {len(df_resequenced)}社")
        print(f"🗑️ 削除企業数: {len(target_ids)}社")

        # ダッシュボード確認の案内
        print(f"\n💡 ダッシュボードで確認してください:")
        print(f"   http://127.0.0.1:5002/companies")

    else:
        print(f"\n❌ データクリーニング失敗")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--specific":
        main_specific_cleanup()
    else:
        main()
