#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB バウンスメール管理システム テスト
"""

import json
import os
import datetime

def test_tracking_system():
    """処理済み追跡システムのテスト"""
    print('=== バウンス管理システム テスト ===')
    
    # 1. 追跡ファイルの確認
    tracking_file = 'huganjob_processed_bounces.json'
    
    if os.path.exists(tracking_file):
        with open(tracking_file, 'r', encoding='utf-8') as f:
            tracking_data = json.load(f)
        
        print(f'✅ 追跡ファイル存在: {tracking_file}')
        print(f'📊 処理済み総数: {tracking_data.get("total_processed", 0)}件')
        print(f'📅 最終更新: {tracking_data.get("last_updated", "不明")}')
        
        processed_ids = tracking_data.get('processed_message_ids', [])
        print(f'📋 処理済みメールID: {len(processed_ids)}件')
        
        if processed_ids:
            print(f'   最初のID: {processed_ids[0]}')
            print(f'   最後のID: {processed_ids[-1]}')
    else:
        print(f'❌ 追跡ファイル未存在: {tracking_file}')
        print('💡 初回実行時に作成されます')
    
    # 2. レポートファイルの確認
    print(f'\n📄 バウンスレポートファイル:')
    report_files = [f for f in os.listdir('.') if f.startswith('huganjob_bounce_report_')]
    
    if report_files:
        report_files.sort(reverse=True)  # 最新順
        print(f'   総数: {len(report_files)}件')
        
        for i, report_file in enumerate(report_files[:3], 1):  # 最新3件
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                
                processing_date = report_data.get('processing_date', '不明')
                total_bounces = report_data.get('total_bounce_emails', 0)
                
                print(f'   {i}. {report_file}')
                print(f'      処理日時: {processing_date}')
                print(f'      バウンス数: {total_bounces}件')
                
                summary = report_data.get('summary', {})
                permanent = summary.get('permanent_bounces', 0)
                temporary = summary.get('temporary_bounces', 0)
                unknown = summary.get('unknown_bounces', 0)
                
                print(f'      永続的: {permanent}, 一時的: {temporary}, 不明: {unknown}')
                
            except Exception as e:
                print(f'   ❌ {report_file}: 読み込みエラー ({e})')
    else:
        print('   📄 レポートファイルなし')
    
    # 3. システム状態の確認
    print(f'\n🔧 システム状態:')
    
    # 必要なファイルの存在確認
    required_files = [
        'huganjob_bounce_processor.py',
        'data/new_input_test.csv',
        'new_email_sending_results.csv'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f'   ✅ {file_path}')
        else:
            print(f'   ❌ {file_path} (未存在)')
    
    # 4. 推奨アクション
    print(f'\n💡 推奨アクション:')
    print('1. huganjob_bounce_processor.py を実行してバウンス処理')
    print('2. contact@huganjob.jp のINBOXでフラグ付きメール確認')
    print('3. HUGANJOB_Processed_Bounces フォルダで処理済みメール確認')
    print('4. 追跡ファイルとレポートで処理状況確認')

def create_sample_tracking():
    """サンプル追跡ファイルの作成"""
    print(f'\n📝 サンプル追跡ファイル作成...')
    
    sample_data = {
        'last_updated': datetime.datetime.now().isoformat(),
        'processed_message_ids': [
            '12345', '12346', '12347', '12348', '12349'
        ],
        'total_processed': 5
    }
    
    tracking_file = 'huganjob_processed_bounces_sample.json'
    
    with open(tracking_file, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
    
    print(f'✅ サンプル作成: {tracking_file}')

def simulate_bounce_processing():
    """バウンス処理のシミュレーション"""
    print(f'\n🎭 バウンス処理シミュレーション:')
    
    # シミュレーション用データ
    bounce_emails = [
        {
            'message_id': '54321',
            'subject': 'Mail delivery failed: returning message to sender',
            'bounced_addresses': ['info@example.com'],
            'bounce_type': 'permanent',
            'processed_date': datetime.datetime.now().isoformat()
        },
        {
            'message_id': '54322',
            'subject': 'Undelivered Mail Returned to Sender',
            'bounced_addresses': ['contact@test.co.jp'],
            'bounce_type': 'temporary',
            'processed_date': datetime.datetime.now().isoformat()
        }
    ]
    
    print(f'📧 シミュレーション対象: {len(bounce_emails)}件')
    
    for i, bounce in enumerate(bounce_emails, 1):
        print(f'   {i}. ID {bounce["message_id"]}: {bounce["bounce_type"]} - {bounce["bounced_addresses"][0]}')
    
    # シミュレーションレポート作成
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f'huganjob_bounce_report_simulation_{timestamp}.json'
    
    report_data = {
        'processing_date': datetime.datetime.now().isoformat(),
        'total_bounce_emails': len(bounce_emails),
        'bounce_details': bounce_emails,
        'summary': {
            'permanent_bounces': len([b for b in bounce_emails if b['bounce_type'] == 'permanent']),
            'temporary_bounces': len([b for b in bounce_emails if b['bounce_type'] == 'temporary']),
            'unknown_bounces': len([b for b in bounce_emails if b['bounce_type'] == 'unknown'])
        },
        'simulation': True
    }
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f'📄 シミュレーションレポート: {report_filename}')

def main():
    print('HUGANJOB バウンスメール管理システム テスト')
    print('=' * 50)
    
    # 基本テスト
    test_tracking_system()
    
    # サンプル作成
    create_sample_tracking()
    
    # シミュレーション
    simulate_bounce_processing()
    
    print(f'\n🎯 テスト完了')
    print('実際のバウンス処理を実行するには:')
    print('python huganjob_bounce_processor.py')

if __name__ == "__main__":
    main()
