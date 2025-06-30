#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大阪企業データ全体をダッシュボード用形式に変換するスクリプト
"""

import pandas as pd
import sys
from datetime import datetime

def classify_industry(company_name, url):
    """企業名とURLから業界を推定"""
    company_lower = company_name.lower()
    url_lower = url.lower()
    
    # 業界キーワードマッピング
    industry_keywords = {
        'IT・サービス業': ['システム', 'ソフト', 'データ', 'ネット', 'web', 'it', 'tech', 'digital'],
        '製造業': ['製作所', '工業', '機械', '電機', '化学', '金属', '鉄工', '製造', 'manufacturing'],
        '建設業': ['建設', '工務店', '建築', '設計', '土木', 'construction'],
        '医薬品・製造業': ['製薬', '薬品', '医療', 'pharma', 'medical'],
        '金融・保険業': ['銀行', '保険', '金融', '証券', 'bank', 'insurance'],
        '商社・卸売業': ['商事', '貿易', '商会', 'trading'],
        '運輸・物流業': ['運輸', '物流', '運送', 'logistics', 'transport'],
        '不動産業': ['不動産', '住宅', 'real estate', 'housing'],
        '食品・飲料業': ['食品', '食糧', '飲料', 'food'],
        'エンターテイメント': ['芸能', 'entertainment', 'テレビ', 'tv'],
        '教育・学校法人': ['学校', '学園', '教育', 'education', 'school'],
        '医療・福祉': ['医療法人', '福祉', '病院', 'hospital', 'welfare'],
        'エネルギー・電力': ['電力', 'ガス', 'energy', 'power'],
        '小売業': ['小売', 'retail'],
        'その他サービス業': []  # デフォルト
    }
    
    for industry, keywords in industry_keywords.items():
        if industry == 'その他サービス業':
            continue
        for keyword in keywords:
            if keyword in company_lower or keyword in url_lower:
                return industry
    
    return 'その他サービス業'

def clean_data(value):
    """データをクリーンアップ"""
    if pd.isna(value) or value == '‐' or value == '-' or value == '':
        return '‐'
    return str(value).strip()

def main():
    try:
        print("=== 大阪企業データ全体変換開始 ===")
        
        # test_input.csvを読み込み
        df = pd.read_csv('test_input.csv', encoding='utf-8')
        print(f"読み込み完了: {len(df)}社")
        
        # ダッシュボード用データに変換
        dashboard_data = []
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for i, row in df.iterrows():
            company_name = clean_data(row['企業名'])
            url = clean_data(row['URL'])
            email = clean_data(row['担当者メールアドレス'])
            revenue = clean_data(row['売上高'])
            capital = clean_data(row['資本金'])
            employees = clean_data(row['従業員数'])
            
            # 業界分類
            industry = classify_industry(company_name, url)
            
            # 説明文作成
            description = f"資本金: {capital}, 売上高: {revenue}"
            
            dashboard_row = {
                'id': i + 1,
                'company_name': company_name,
                'website_url': url,
                'industry': industry,
                'location': '大阪府',
                'employees': employees,
                'description': description,
                'campaign_type': 'osaka_companies',
                'created_date': current_time
            }
            
            dashboard_data.append(dashboard_row)
            
            # 進捗表示
            if (i + 1) % 100 == 0:
                print(f"処理中... {i + 1}/{len(df)}社")
        
        # DataFrameに変換
        df_dashboard = pd.DataFrame(dashboard_data)
        
        # derivative_ad_input.csvに保存
        df_dashboard.to_csv('data/derivative_ad_input.csv', index=False, encoding='utf-8')
        
        print(f"✅ 変換完了: {len(df_dashboard)}社のデータを保存しました")
        print("保存先: data/derivative_ad_input.csv")
        
        # 業界別統計
        industry_stats = df_dashboard['industry'].value_counts()
        print("\n=== 業界別統計 ===")
        for industry, count in industry_stats.items():
            print(f"{industry}: {count}社")
        
        # 有効メールアドレス統計
        valid_emails = df[df['担当者メールアドレス'].str.contains('@', na=False)]
        print(f"\n=== メールアドレス統計 ===")
        print(f"有効なメールアドレス: {len(valid_emails)}社")
        print(f"メールアドレス無し: {len(df) - len(valid_emails)}社")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
