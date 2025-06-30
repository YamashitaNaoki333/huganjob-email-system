#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HUGAN JOB データ入力管理システム
複数のデータソースを統合・管理するためのツール
"""

import os
import csv
import pandas as pd
import shutil
from datetime import datetime
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataInputManager:
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.xls']
        self.required_columns = ['企業名', 'URL']  # 最低限必要なカラム
        self.optional_columns = ['業種', '所在地', '従業員数', '資本金', '売上高', 'メールアドレス']
        
    def analyze_input_file(self, file_path):
        """入力ファイルの構造を分析"""
        print(f"📊 ファイル分析: {file_path}")
        print("=" * 60)
        
        if not os.path.exists(file_path):
            print(f"❌ ファイルが見つかりません: {file_path}")
            return None
        
        # ファイル拡張子チェック
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in self.supported_formats:
            print(f"❌ サポートされていないファイル形式: {ext}")
            print(f"サポート形式: {', '.join(self.supported_formats)}")
            return None
        
        try:
            # ファイル読み込み
            if ext.lower() == '.csv':
                df = self._read_csv_with_encoding(file_path)
            else:
                df = pd.read_excel(file_path)
            
            if df is None:
                return None
            
            # 基本情報表示
            print(f"✅ ファイル読み込み成功")
            print(f"📋 データ件数: {len(df)}件")
            print(f"📋 カラム数: {len(df.columns)}個")
            
            # カラム情報表示
            print(f"\n📋 検出されたカラム:")
            for i, col in enumerate(df.columns, 1):
                sample_data = df[col].dropna().head(1).values
                sample = sample_data[0] if len(sample_data) > 0 else "（データなし）"
                print(f"  {i:2d}. {col} - 例: {sample}")
            
            # 必須カラムチェック
            print(f"\n🔍 必須カラムチェック:")
            missing_required = []
            for req_col in self.required_columns:
                if req_col in df.columns:
                    print(f"  ✅ {req_col}")
                else:
                    print(f"  ❌ {req_col} (見つかりません)")
                    missing_required.append(req_col)
            
            # オプションカラムチェック
            print(f"\n📋 オプションカラムチェック:")
            for opt_col in self.optional_columns:
                if opt_col in df.columns:
                    non_null_count = df[opt_col].notna().sum()
                    print(f"  ✅ {opt_col} ({non_null_count}件のデータ)")
                else:
                    print(f"  ⚪ {opt_col} (なし)")
            
            # データ品質チェック
            print(f"\n🔍 データ品質チェック:")
            if '企業名' in df.columns:
                empty_names = df['企業名'].isna().sum()
                print(f"  企業名: {len(df) - empty_names}/{len(df)}件 (空白: {empty_names}件)")
            
            if 'URL' in df.columns:
                empty_urls = df['URL'].isna().sum()
                valid_urls = df['URL'].str.contains('http', na=False).sum()
                print(f"  URL: {len(df) - empty_urls}/{len(df)}件 (空白: {empty_urls}件, http含む: {valid_urls}件)")
            
            return {
                'dataframe': df,
                'file_path': file_path,
                'columns': list(df.columns),
                'row_count': len(df),
                'missing_required': missing_required,
                'has_email': 'メールアドレス' in df.columns or '担当者メールアドレス' in df.columns
            }
            
        except Exception as e:
            print(f"❌ ファイル分析エラー: {e}")
            return None
    
    def _read_csv_with_encoding(self, file_path):
        """複数のエンコーディングでCSVファイルを読み込み"""
        encodings = ['utf-8-sig', 'utf-8', 'shift_jis', 'cp932', 'iso-2022-jp']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                print(f"  エンコーディング: {encoding}")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"CSV読み込みエラー ({encoding}): {e}")
                continue
        
        print(f"❌ サポートされているエンコーディングでファイルを読み込めませんでした")
        return None
    
    def standardize_data(self, analysis_result):
        """データを標準形式に変換"""
        print(f"\n🔄 データ標準化処理")
        print("=" * 60)
        
        if not analysis_result:
            return None
        
        df = analysis_result['dataframe'].copy()
        
        # カラム名のマッピング
        column_mapping = {
            '事務所名': '企業名',
            '会社名': '企業名',
            '法人名': '企業名',
            '企業URL': 'URL',
            'ウェブサイト': 'URL',
            'ホームページ': 'URL',
            '担当者メールアドレス': 'メールアドレス',
            'Email': 'メールアドレス',
            'email': 'メールアドレス',
            'E-mail': 'メールアドレス'
        }
        
        # カラム名を標準化
        df = df.rename(columns=column_mapping)
        
        # 必須カラムの確認と作成
        if '企業名' not in df.columns:
            # 最初のカラムを企業名として使用
            if len(df.columns) > 0:
                first_col = df.columns[0]
                df = df.rename(columns={first_col: '企業名'})
                print(f"  📝 '{first_col}' を '企業名' として使用")
        
        if 'URL' not in df.columns:
            # URL関連のカラムを探す
            url_candidates = [col for col in df.columns if 'url' in col.lower() or 'http' in str(df[col].iloc[0] if len(df) > 0 else '').lower()]
            if url_candidates:
                df = df.rename(columns={url_candidates[0]: 'URL'})
                print(f"  📝 '{url_candidates[0]}' を 'URL' として使用")
            else:
                df['URL'] = ''  # 空のURLカラムを作成
                print(f"  📝 空の 'URL' カラムを作成")
        
        # データクリーニング
        print(f"\n🧹 データクリーニング:")
        
        # 企業名のクリーニング
        if '企業名' in df.columns:
            original_count = len(df)
            df = df[df['企業名'].notna() & (df['企業名'] != '')]
            cleaned_count = len(df)
            if original_count != cleaned_count:
                print(f"  企業名が空の行を削除: {original_count - cleaned_count}件")
        
        # URLのクリーニング
        if 'URL' in df.columns:
            # URLの正規化
            df['URL'] = df['URL'].fillna('')
            df['URL'] = df['URL'].astype(str)
            
            # httpが含まれていないURLにhttps://を追加
            mask = (df['URL'] != '') & (~df['URL'].str.contains('http', na=False))
            df.loc[mask, 'URL'] = 'https://' + df.loc[mask, 'URL']
            
            print(f"  URL正規化完了")
        
        # メールアドレスのクリーニング
        if 'メールアドレス' in df.columns:
            # 無効なメールアドレスを除去
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            valid_emails = df['メールアドレス'].str.match(email_pattern, na=False)
            invalid_count = (~valid_emails & df['メールアドレス'].notna()).sum()
            if invalid_count > 0:
                df.loc[~valid_emails, 'メールアドレス'] = ''
                print(f"  無効なメールアドレスをクリア: {invalid_count}件")
        
        # IDカラムの追加
        df.insert(0, 'ID', range(1, len(df) + 1))
        
        print(f"✅ 標準化完了: {len(df)}件のデータ")
        
        return df
    
    def merge_with_existing_data(self, new_df, existing_file='test_input.csv'):
        """既存データと新しいデータをマージ"""
        print(f"\n🔗 データマージ処理")
        print("=" * 60)
        
        if not os.path.exists(existing_file):
            print(f"  既存ファイルが見つかりません: {existing_file}")
            print(f"  新しいデータをそのまま使用します")
            return new_df
        
        # 既存データを読み込み
        existing_analysis = self.analyze_input_file(existing_file)
        if not existing_analysis:
            print(f"  既存ファイルの読み込みに失敗しました")
            return new_df
        
        existing_df = self.standardize_data(existing_analysis)
        if existing_df is None:
            print(f"  既存データの標準化に失敗しました")
            return new_df
        
        print(f"  既存データ: {len(existing_df)}件")
        print(f"  新規データ: {len(new_df)}件")
        
        # 重複チェック（企業名ベース）
        if '企業名' in existing_df.columns and '企業名' in new_df.columns:
            duplicates = new_df['企業名'].isin(existing_df['企業名'])
            duplicate_count = duplicates.sum()
            
            if duplicate_count > 0:
                print(f"  重複企業を検出: {duplicate_count}件")
                choice = input("  重複企業の処理方法を選択してください (1: スキップ, 2: 上書き, 3: 両方保持): ")
                
                if choice == '1':
                    new_df = new_df[~duplicates]
                    print(f"  重複企業をスキップしました")
                elif choice == '2':
                    existing_df = existing_df[~existing_df['企業名'].isin(new_df['企業名'])]
                    print(f"  重複企業を上書きします")
                # choice == '3' の場合は何もしない（両方保持）
        
        # データをマージ
        # IDを再採番
        existing_df['ID'] = range(1, len(existing_df) + 1)
        new_df['ID'] = range(len(existing_df) + 1, len(existing_df) + len(new_df) + 1)
        
        # カラムを統一
        all_columns = list(set(existing_df.columns) | set(new_df.columns))
        for col in all_columns:
            if col not in existing_df.columns:
                existing_df[col] = ''
            if col not in new_df.columns:
                new_df[col] = ''
        
        # カラム順序を統一
        existing_df = existing_df[all_columns]
        new_df = new_df[all_columns]
        
        # マージ
        merged_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        print(f"✅ マージ完了: {len(merged_df)}件のデータ")
        
        return merged_df
    
    def save_data(self, df, output_file=None):
        """データを保存"""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'merged_input_{timestamp}.csv'
        
        print(f"\n💾 データ保存")
        print("=" * 60)
        
        try:
            # バックアップ作成
            if os.path.exists('test_input.csv'):
                backup_file = f'test_input_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                shutil.copy2('test_input.csv', backup_file)
                print(f"  バックアップ作成: {backup_file}")
            
            # データ保存
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"✅ データ保存完了: {output_file}")
            
            # 統計情報表示
            print(f"\n📊 保存データ統計:")
            print(f"  総件数: {len(df)}件")
            
            if '企業名' in df.columns:
                print(f"  企業名あり: {df['企業名'].notna().sum()}件")
            
            if 'URL' in df.columns:
                valid_urls = df['URL'].str.contains('http', na=False).sum()
                print(f"  有効URL: {valid_urls}件")
            
            if 'メールアドレス' in df.columns:
                valid_emails = df['メールアドレス'].notna().sum()
                print(f"  メールアドレス: {valid_emails}件")
            
            return output_file
            
        except Exception as e:
            print(f"❌ データ保存エラー: {e}")
            return None
    
    def interactive_data_addition(self):
        """対話式データ追加"""
        print("=" * 80)
        print("📊 HUGAN JOB データ追加システム")
        print("=" * 80)
        
        # ファイル選択
        print("\n📁 追加するデータファイルのパスを入力してください:")
        file_path = input("ファイルパス: ").strip().strip('"')
        
        if not file_path:
            print("❌ ファイルパスが入力されていません")
            return False
        
        # ファイル分析
        analysis = self.analyze_input_file(file_path)
        if not analysis:
            return False
        
        # 必須カラムチェック
        if analysis['missing_required']:
            print(f"\n⚠️ 必須カラムが不足しています: {', '.join(analysis['missing_required'])}")
            print("カラムマッピングを行いますか？ (y/n): ", end="")
            if input().lower() != 'y':
                return False
        
        # データ標準化
        standardized_df = self.standardize_data(analysis)
        if standardized_df is None:
            return False
        
        # 既存データとのマージ
        print(f"\n🔗 既存データとマージしますか？ (y/n): ", end="")
        if input().lower() == 'y':
            merged_df = self.merge_with_existing_data(standardized_df)
        else:
            merged_df = standardized_df
        
        # 保存
        print(f"\n💾 保存ファイル名を指定してください (空白でデフォルト): ", end="")
        output_file = input().strip()
        if not output_file:
            output_file = 'test_input.csv'  # デフォルトファイル名
        
        saved_file = self.save_data(merged_df, output_file)
        
        if saved_file:
            print(f"\n🎉 データ追加が完了しました！")
            print(f"📁 保存先: {saved_file}")
            
            # 次のステップの提案
            print(f"\n📋 次のステップ:")
            print(f"1. メール抽出: python core_scripts/derivative_email_extractor.py")
            print(f"2. ウェブサイト分析: python core_scripts/derivative_website_analyzer.py")
            print(f"3. メール送信: python core_scripts/derivative_ad_email_sender.py")
            
            return True
        
        return False

def main():
    """メイン処理"""
    manager = DataInputManager()
    
    try:
        success = manager.interactive_data_addition()
        if success:
            print(f"\n✅ 処理が正常に完了しました")
        else:
            print(f"\n❌ 処理が失敗しました")
    except KeyboardInterrupt:
        print(f"\n\n❌ 処理がキャンセルされました")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
