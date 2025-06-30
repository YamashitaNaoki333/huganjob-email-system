#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
送信結果の詳細確認スクリプト
"""

import pandas as pd

def main():
    # 送信結果の詳細確認
    df_results = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')

    # 問題IDの送信結果を詳しく確認
    problem_ids = [16, 20, 22, 36, 51, 74, 76, 105, 108]

    print('=== 問題IDの送信結果詳細 ===')
    for check_id in problem_ids:
        matching_results = df_results[df_results['企業ID'] == check_id]
        if len(matching_results) > 0:
            result = matching_results.iloc[0]
            print(f'ID {check_id}:')
            print(f'  送信結果: "{result["送信結果"]}"')
            print(f'  送信結果の型: {type(result["送信結果"])}')
            print(f'  送信結果 == "success": {result["送信結果"] == "success"}')
            print(f'  送信結果.strip() == "success": {str(result["送信結果"]).strip() == "success"}')
            print()

    # 送信結果の値の種類を確認
    print('=== 送信結果の値の種類 ===')
    unique_results = df_results['送信結果'].value_counts()
    print(unique_results)

if __name__ == "__main__":
    main()
