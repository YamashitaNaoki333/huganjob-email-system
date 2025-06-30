#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
データ形式変換ツール
様々な形式のデータをHUGAN JOBシステム用に変換
"""

import os
import csv
import pandas as pd
import json
from datetime import datetime
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataFormatConverter:
    def __init__(self):
        self.standard_columns = {
            'ID': 'ID',
            '企業名': '企業名',
            'URL': 'URL',
            '業種': '業種',
            '所在地': '所在地',
            '従業員数': '従業員数',
            '資本金': '資本金',
            '売上高': '売上高',
            'メールアドレス': 'メールアドレス'
        }
        
        # よくあるカラム名のマッピング
        self.column_mappings = {
            # 企業名のバリエーション
            '会社名': '企業名',
            '法人名': '企業名',
            '事務所名': '企業名',
            '組織名': '企業名',
            'company_name': '企業名',
            'Company Name': '企業名',
            
            # URLのバリエーション
            '企業URL': 'URL',
            'ウェブサイト': 'URL',
            'ホームページ': 'URL',
            'website': 'URL',
            'Website': 'URL',
            'url': 'URL',
            'HP': 'URL',
            
            # メールアドレスのバリエーション
            '担当者メールアドレス': 'メールアドレス',
            'Email': 'メールアドレス',
            'email': 'メールアドレス',
            'E-mail': 'メールアドレス',
            'mail': 'メールアドレス',
            'Mail': 'メールアドレス',
            
            # 業種のバリエーション
            '業界': '業種',
            'industry': '業種',
            'Industry': '業種',
            '事業内容': '業種',
            
            # 所在地のバリエーション
            '住所': '所在地',
            '本社所在地': '所在地',
            '所在地住所': '所在地',
            'address': '所在地',
            'Address': '所在地',
            'location': '所在地',
            'Location': '所在地',
            
            # 従業員数のバリエーション
            '社員数': '従業員数',
            '人数': '従業員数',
            'employees': '従業員数',
            'Employees': '従業員数',
            '従業員': '従業員数',
            
            # 資本金のバリエーション
            'capital': '資本金',
            'Capital': '資本金',
            '資本': '資本金',
            
            # 売上高のバリエーション
            '売上': '売上高',
            'revenue': '売上高',
            'Revenue': '売上高',
            'sales': '売上高',
            'Sales': '売上高'
        }
    
    def detect_format(self, file_path):
        """ファイル形式を検出"""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext == '.csv':
            return 'csv'
        elif ext in ['.xlsx', '.xls']:
            return 'excel'
        elif ext == '.json':
            return 'json'
        elif ext == '.txt':
            return 'text'
        else:
            return 'unknown'
    
    def convert_csv_format(self, input_file, output_file=None):
        """CSV形式の変換"""
        print(f"📊 CSV形式変換: {input_file}")
        print("-" * 50)
        
        # 複数エンコーディングで読み込み試行
        encodings = ['utf-8-sig', 'utf-8', 'shift_jis', 'cp932', 'iso-2022-jp']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(input_file, encoding=encoding)
                print(f"✅ 読み込み成功 (エンコーディング: {encoding})")
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"CSV読み込みエラー ({encoding}): {e}")
                continue
        
        if df is None:
            print("❌ ファイルを読み込めませんでした")
            return None
        
        return self._standardize_dataframe(df, output_file)
    
    def convert_excel_format(self, input_file, output_file=None, sheet_name=0):
        """Excel形式の変換"""
        print(f"📊 Excel形式変換: {input_file}")
        print("-" * 50)
        
        try:
            # Excelファイルのシート一覧を取得
            excel_file = pd.ExcelFile(input_file)
            print(f"📋 検出されたシート: {excel_file.sheet_names}")
            
            # シート選択
            if isinstance(sheet_name, int):
                if sheet_name < len(excel_file.sheet_names):
                    selected_sheet = excel_file.sheet_names[sheet_name]
                else:
                    selected_sheet = excel_file.sheet_names[0]
            else:
                selected_sheet = sheet_name if sheet_name in excel_file.sheet_names else excel_file.sheet_names[0]
            
            print(f"📄 使用シート: {selected_sheet}")
            
            # データ読み込み
            df = pd.read_excel(input_file, sheet_name=selected_sheet)
            print(f"✅ 読み込み成功: {len(df)}行 × {len(df.columns)}列")
            
            return self._standardize_dataframe(df, output_file)
            
        except Exception as e:
            print(f"❌ Excel読み込みエラー: {e}")
            return None
    
    def convert_json_format(self, input_file, output_file=None):
        """JSON形式の変換"""
        print(f"📊 JSON形式変換: {input_file}")
        print("-" * 50)
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # JSONの構造を分析
            if isinstance(data, list):
                # リスト形式の場合
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # 辞書形式の場合
                if 'data' in data:
                    df = pd.DataFrame(data['data'])
                elif 'companies' in data:
                    df = pd.DataFrame(data['companies'])
                else:
                    # 辞書の値がリストの場合
                    for key, value in data.items():
                        if isinstance(value, list):
                            df = pd.DataFrame(value)
                            break
                    else:
                        # 単一レコードの場合
                        df = pd.DataFrame([data])
            else:
                print("❌ サポートされていないJSON構造です")
                return None
            
            print(f"✅ 読み込み成功: {len(df)}行 × {len(df.columns)}列")
            
            return self._standardize_dataframe(df, output_file)
            
        except Exception as e:
            print(f"❌ JSON読み込みエラー: {e}")
            return None
    
    def convert_text_format(self, input_file, output_file=None, delimiter='\t'):
        """テキスト形式の変換"""
        print(f"📊 テキスト形式変換: {input_file}")
        print("-" * 50)
        
        # 区切り文字の自動検出
        delimiters = ['\t', ',', ';', '|']
        
        for delim in delimiters:
            try:
                df = pd.read_csv(input_file, delimiter=delim, encoding='utf-8')
                if len(df.columns) > 1:  # 複数列に分かれている場合
                    print(f"✅ 区切り文字検出: '{delim}'")
                    break
            except:
                continue
        else:
            print("❌ 適切な区切り文字が見つかりませんでした")
            return None
        
        print(f"✅ 読み込み成功: {len(df)}行 × {len(df.columns)}列")
        
        return self._standardize_dataframe(df, output_file)
    
    def _standardize_dataframe(self, df, output_file=None):
        """データフレームを標準形式に変換"""
        print(f"\n🔄 データ標準化処理")
        print("-" * 30)
        
        # 元のカラム名を表示
        print(f"📋 元のカラム: {list(df.columns)}")
        
        # カラム名をマッピング
        df_renamed = df.rename(columns=self.column_mappings)
        
        # マッピング結果を表示
        renamed_columns = {old: new for old, new in self.column_mappings.items() if old in df.columns}
        if renamed_columns:
            print(f"🔄 カラム名変更:")
            for old, new in renamed_columns.items():
                print(f"  {old} → {new}")
        
        # 必須カラムの確認
        if '企業名' not in df_renamed.columns:
            # 最初のカラムを企業名として使用
            if len(df_renamed.columns) > 0:
                first_col = df_renamed.columns[0]
                df_renamed = df_renamed.rename(columns={first_col: '企業名'})
                print(f"📝 '{first_col}' を '企業名' として使用")
        
        # URLカラムの処理
        if 'URL' not in df_renamed.columns:
            # URL候補を探す
            url_candidates = [col for col in df_renamed.columns 
                            if 'url' in col.lower() or 'http' in str(df_renamed[col].iloc[0] if len(df_renamed) > 0 else '').lower()]
            if url_candidates:
                df_renamed = df_renamed.rename(columns={url_candidates[0]: 'URL'})
                print(f"📝 '{url_candidates[0]}' を 'URL' として使用")
            else:
                df_renamed['URL'] = ''
                print(f"📝 空の 'URL' カラムを作成")
        
        # データクリーニング
        print(f"\n🧹 データクリーニング:")
        
        # 空行の削除
        original_len = len(df_renamed)
        df_renamed = df_renamed.dropna(how='all')
        if len(df_renamed) != original_len:
            print(f"  空行削除: {original_len - len(df_renamed)}行")
        
        # 企業名が空の行を削除
        if '企業名' in df_renamed.columns:
            original_len = len(df_renamed)
            df_renamed = df_renamed[df_renamed['企業名'].notna() & (df_renamed['企業名'] != '')]
            if len(df_renamed) != original_len:
                print(f"  企業名空白行削除: {original_len - len(df_renamed)}行")
        
        # URLの正規化
        if 'URL' in df_renamed.columns:
            df_renamed['URL'] = df_renamed['URL'].fillna('')
            df_renamed['URL'] = df_renamed['URL'].astype(str)
            
            # httpが含まれていないURLにhttps://を追加
            mask = (df_renamed['URL'] != '') & (~df_renamed['URL'].str.contains('http', na=False))
            df_renamed.loc[mask, 'URL'] = 'https://' + df_renamed.loc[mask, 'URL']
            print(f"  URL正規化完了")
        
        # メールアドレスの検証
        if 'メールアドレス' in df_renamed.columns:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            valid_emails = df_renamed['メールアドレス'].str.match(email_pattern, na=False)
            invalid_count = (~valid_emails & df_renamed['メールアドレス'].notna()).sum()
            if invalid_count > 0:
                df_renamed.loc[~valid_emails, 'メールアドレス'] = ''
                print(f"  無効メールアドレスクリア: {invalid_count}件")
        
        # IDカラムの追加
        df_renamed.insert(0, 'ID', range(1, len(df_renamed) + 1))
        
        # 標準カラム順序に並び替え
        available_columns = ['ID'] + [col for col in self.standard_columns.values() if col in df_renamed.columns and col != 'ID']
        other_columns = [col for col in df_renamed.columns if col not in available_columns]
        final_columns = available_columns + other_columns
        
        df_final = df_renamed[final_columns]
        
        print(f"✅ 標準化完了: {len(df_final)}行 × {len(df_final.columns)}列")
        print(f"📋 最終カラム: {list(df_final.columns)}")
        
        # ファイル保存
        if output_file:
            try:
                df_final.to_csv(output_file, index=False, encoding='utf-8-sig')
                print(f"💾 保存完了: {output_file}")
            except Exception as e:
                print(f"❌ 保存エラー: {e}")
        
        return df_final
    
    def interactive_conversion(self):
        """対話式変換"""
        print("=" * 80)
        print("🔄 HUGAN JOB データ形式変換ツール")
        print("=" * 80)
        
        # ファイル選択
        print("\n📁 変換するファイルのパスを入力してください:")
        input_file = input("ファイルパス: ").strip().strip('"')
        
        if not input_file or not os.path.exists(input_file):
            print("❌ ファイルが見つかりません")
            return False
        
        # 形式検出
        file_format = self.detect_format(input_file)
        print(f"📊 検出された形式: {file_format}")
        
        # 出力ファイル名
        print(f"\n💾 出力ファイル名を入力してください (空白でデフォルト):")
        output_file = input("出力ファイル名: ").strip()
        if not output_file:
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_file = f"{base_name}_converted.csv"
        
        # 変換実行
        try:
            if file_format == 'csv':
                result = self.convert_csv_format(input_file, output_file)
            elif file_format == 'excel':
                result = self.convert_excel_format(input_file, output_file)
            elif file_format == 'json':
                result = self.convert_json_format(input_file, output_file)
            elif file_format == 'text':
                result = self.convert_text_format(input_file, output_file)
            else:
                print(f"❌ サポートされていない形式: {file_format}")
                return False
            
            if result is not None:
                print(f"\n🎉 変換が完了しました！")
                print(f"📁 出力ファイル: {output_file}")
                print(f"📊 データ件数: {len(result)}件")
                
                # 統計情報
                print(f"\n📋 データ統計:")
                if '企業名' in result.columns:
                    print(f"  企業名: {result['企業名'].notna().sum()}件")
                if 'URL' in result.columns:
                    valid_urls = result['URL'].str.contains('http', na=False).sum()
                    print(f"  有効URL: {valid_urls}件")
                if 'メールアドレス' in result.columns:
                    valid_emails = result['メールアドレス'].notna().sum()
                    print(f"  メールアドレス: {valid_emails}件")
                
                return True
            else:
                print(f"❌ 変換に失敗しました")
                return False
                
        except Exception as e:
            print(f"❌ 変換エラー: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """メイン処理"""
    converter = DataFormatConverter()
    
    try:
        success = converter.interactive_conversion()
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
