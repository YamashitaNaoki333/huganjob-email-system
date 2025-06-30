#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
派生版広告営業データ変換スクリプト
test_input.csvを派生版システム用のフォーマットに変換
"""

import os
import csv
import logging
import pandas as pd
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_test_input_to_derivative():
    """test_input.csvを派生版フォーマットに変換"""
    try:
        # 入力ファイルパス
        input_file = 'test_input.csv'
        output_file = 'data/derivative_ad_input.csv'
        
        if not os.path.exists(input_file):
            logger.error(f"入力ファイルが見つかりません: {input_file}")
            return False
        
        # test_input.csvを読み込み
        logger.info(f"入力ファイルを読み込み中: {input_file}")
        
        # 複数のエンコーディングを試す
        encodings = ['utf-8-sig', 'utf-8', 'shift_jis', 'cp932']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(input_file, encoding=encoding)
                logger.info(f"ファイル読み込み成功 (エンコーディング: {encoding})")
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"ファイル読み込みエラー ({encoding}): {e}")
                continue
        
        if df is None:
            logger.error("ファイルを読み込めませんでした")
            return False
        
        # データ確認
        logger.info(f"読み込んだデータ: {len(df)}行")
        logger.info(f"カラム: {list(df.columns)}")
        
        # 派生版フォーマットに変換
        converted_data = []
        
        for index, row in df.iterrows():
            # 空行をスキップ
            if pd.isna(row.iloc[0]) or str(row.iloc[0]).strip() == '':
                continue
                
            company_name = str(row.iloc[0]).strip()  # 事務所名
            website_url = str(row.iloc[1]).strip() if len(row) > 1 and not pd.isna(row.iloc[1]) else ''
            
            # URLの正規化
            if website_url and not website_url.startswith(('http://', 'https://')):
                website_url = 'https://' + website_url
            
            converted_row = {
                'id': index + 1,
                'company_name': company_name,
                'website_url': website_url,
                'industry': '司法書士事務所',
                'location': '未設定',
                'employees': '未設定',
                'description': f'広告運用代行営業対象: {company_name}',
                'campaign_type': 'ad_agency',  # 営業内容識別用
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            converted_data.append(converted_row)
        
        # 出力ディレクトリ作成
        os.makedirs('data', exist_ok=True)
        
        # CSVファイルとして保存
        output_df = pd.DataFrame(converted_data)
        output_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        logger.info(f"変換完了: {len(converted_data)}社のデータを {output_file} に保存")
        
        # 変換結果の表示
        print("\n" + "="*60)
        print("📊 データ変換結果")
        print("="*60)
        print(f"入力ファイル: {input_file}")
        print(f"出力ファイル: {output_file}")
        print(f"変換データ数: {len(converted_data)}社")
        print(f"営業内容: 広告運用代行")
        print("="*60)
        
        # サンプルデータ表示
        if len(converted_data) > 0:
            print("\n📋 変換データサンプル:")
            sample = converted_data[0]
            for key, value in sample.items():
                print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        logger.error(f"データ変換中にエラーが発生しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """メイン処理"""
    print("🔄 派生版広告営業データ変換スクリプト")
    print("test_input.csv → data/derivative_ad_input.csv")
    print("-" * 50)
    
    success = convert_test_input_to_derivative()
    
    if success:
        print("\n✅ データ変換が正常に完了しました")
        print("次のステップ: 広告営業ワークフローを実行してください")
    else:
        print("\n❌ データ変換に失敗しました")
        print("ログを確認してください")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
