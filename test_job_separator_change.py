#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
職種区切り文字変更テスト
「/」区切りの職種抽出機能をテストする
"""

import pandas as pd
import sys
import os

# huganjob_unified_sender.pyのパスを追加
sys.path.append('.')

from huganjob_unified_sender import HuganjobEmailSender

def test_job_position_extraction():
    """職種抽出機能のテスト"""
    
    print('=== 職種区切り文字変更テスト ===')
    print()
    
    # テストケース
    test_cases = [
        {
            'input': '人材コーディネーター/CADオペレーター/プログラマー/プロジェクトアシスタント',
            'expected': '人材コーディネーター',
            'description': '株式会社ワーキテクノ（4職種統合）'
        },
        {
            'input': '製造スタッフ/ITエンジニア/人事',
            'expected': '製造スタッフ',
            'description': '株式会社フジワーク（3職種統合）'
        },
        {
            'input': '見積りスタッフ/営業職',
            'expected': '見積りスタッフ',
            'description': '株式会社サカイ引越センター（2職種統合）'
        },
        {
            'input': '点検・取付スタッフ',
            'expected': '点検・取付スタッフ',
            'description': '単一職種（・を含むが統合ではない）'
        },
        {
            'input': '営業職',
            'expected': '営業職',
            'description': '単一職種（通常）'
        }
    ]
    
    # HuganjobEmailSenderインスタンスを作成
    sender = HuganjobEmailSender()
    
    print('職種抽出テスト結果:')
    print('-' * 60)
    
    all_passed = True
    for i, test_case in enumerate(test_cases, 1):
        input_job = test_case['input']
        expected = test_case['expected']
        description = test_case['description']
        
        # 職種抽出を実行
        result = sender.extract_primary_job_position(input_job)
        
        # 結果を検証
        passed = result == expected
        status = '✅ PASS' if passed else '❌ FAIL'
        
        print(f'{i}. {description}')
        print(f'   入力: {input_job}')
        print(f'   期待: {expected}')
        print(f'   結果: {result}')
        print(f'   判定: {status}')
        print()
        
        if not passed:
            all_passed = False
    
    print('=' * 60)
    if all_passed:
        print('🎯 全テストケースが正常に動作しました')
    else:
        print('❌ 一部のテストケースが失敗しました')
    
    return all_passed

def test_actual_csv_data():
    """実際のCSVデータでのテスト"""
    
    print('\n=== 実際のCSVデータテスト ===')
    print()
    
    try:
        df = pd.read_csv('data/new_input_test.csv')
        
        # 「/」を含む職種を検索
        slash_jobs = df[df['募集職種'].str.contains('/', na=False)]
        
        print(f'「/」区切り職種企業数: {len(slash_jobs)}社')
        print()
        
        if len(slash_jobs) > 0:
            print('「/」区切り職種の例:')
            sender = HuganjobEmailSender()
            
            for i, (_, row) in enumerate(slash_jobs.head(5).iterrows(), 1):
                company_name = row['企業名']
                job_position = row['募集職種']
                primary_job = sender.extract_primary_job_position(job_position)
                
                print(f'{i}. {company_name}')
                print(f'   統合職種: {job_position}')
                print(f'   メール用職種: {primary_job}')
                print(f'   件名: 【{primary_job}の人材採用を強化しませんか？】株式会社HUGANからのご提案')
                print()
        
        # 「・」を含む職種も確認（単一職種として残っているもの）
        dot_jobs = df[df['募集職種'].str.contains('・', na=False)]
        print(f'「・」を含む職種企業数: {len(dot_jobs)}社（単一職種として保持）')
        
        if len(dot_jobs) > 0:
            print('「・」を含む単一職種の例:')
            for i, (_, row) in enumerate(dot_jobs.head(3).iterrows(), 1):
                print(f'{i}. {row["企業名"]}: {row["募集職種"]}')
        
        return True
        
    except Exception as e:
        print(f'❌ エラー: CSVデータテストに失敗しました: {e}')
        return False

if __name__ == "__main__":
    # 職種抽出機能のテスト
    extraction_test_passed = test_job_position_extraction()
    
    # 実際のCSVデータでのテスト
    csv_test_passed = test_actual_csv_data()
    
    print('\n' + '=' * 60)
    print('📊 テスト結果サマリー')
    print('=' * 60)
    print(f'職種抽出機能テスト: {"✅ PASS" if extraction_test_passed else "❌ FAIL"}')
    print(f'CSVデータテスト: {"✅ PASS" if csv_test_passed else "❌ FAIL"}')
    
    if extraction_test_passed and csv_test_passed:
        print('\n🎯 職種区切り文字変更が正常に完了しました')
        print('📧 メール送信テストの準備が整いました')
    else:
        print('\n❌ テストに失敗しました。設定を確認してください')
