#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
送信記録にない企業の確認
"""

import pandas as pd

def main():
    # 企業データベースでID 1297-1300を確認
    df_companies = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
    missing_companies = df_companies[df_companies['ID'].isin([1297, 1298, 1299, 1300])]

    print("🔍 送信記録にない企業（ID 1297-1300）:")
    for _, company in missing_companies.iterrows():
        company_id = company['ID']
        company_name = company['企業名']
        email = company.get('担当者メールアドレス', 'N/A')
        print(f"  ID {company_id}: {company_name} - {email}")

if __name__ == "__main__":
    main()
