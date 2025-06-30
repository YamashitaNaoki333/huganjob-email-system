#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB バウンスメール管理システム
送信履歴からバウンス企業を特定し、データベースを更新する
"""

import pandas as pd
import datetime
import os
import json
import re

class HuganjobBounceManager:
    def __init__(self):
        self.csv_file = 'data/new_input_test.csv'
        self.sending_results_file = 'new_email_sending_results.csv'
        self.bounce_list = []
        self.processed_results = []

    def analyze_sending_results(self):
        """送信結果からバウンス企業を分析"""
        try:
            print('=== HUGANJOB バウンスメール管理システム ===')
            print('Phase 2: 企業データベース更新を開始します')
            print()
            
            print('📊 送信履歴を分析中...')
            
            # 送信結果ファイルを読み込み
            if not os.path.exists(self.sending_results_file):
                print(f'❌ 送信結果ファイルが見つかりません: {self.sending_results_file}')
                return False
            
            df_results = pd.read_csv(self.sending_results_file)
            print(f'   総送信記録数: {len(df_results)}件')
            
            # 失敗した送信を特定
            failed_sends = df_results[df_results['送信結果'] == 'failed']
            print(f'   送信失敗記録: {len(failed_sends)}件')
            
            if len(failed_sends) == 0:
                print('✅ 送信失敗記録が見つかりませんでした')
                return True
            
            # バウンス企業の詳細を分析
            for _, row in failed_sends.iterrows():
                bounce_info = {
                    'company_id': row['企業ID'],
                    'company_name': row['企業名'],
                    'email_address': row['メールアドレス'],
                    'job_position': row['募集職種'],
                    'send_datetime': row['送信日時'],
                    'error_message': row['エラーメッセージ'],
                    'bounce_type': self.classify_bounce_error(row['エラーメッセージ'])
                }
                self.bounce_list.append(bounce_info)
                
                print(f'🔍 バウンス企業発見:')
                print(f'   ID {bounce_info["company_id"]}: {bounce_info["company_name"]}')
                print(f'   メールアドレス: {bounce_info["email_address"]}')
                print(f'   エラー: {bounce_info["error_message"]}')
                print(f'   分類: {bounce_info["bounce_type"]}')
                print()
            
            return True
            
        except Exception as e:
            print(f'❌ 送信結果分析失敗: {e}')
            return False

    def classify_bounce_error(self, error_message):
        """エラーメッセージからバウンスタイプを分類"""
        if pd.isna(error_message) or error_message == '':
            return 'unknown'
        
        error_lower = str(error_message).lower()
        
        # 永続的エラー（アドレス不正など）
        permanent_patterns = [
            'bad recipient address syntax',
            'invalid recipient',
            'user unknown',
            'no such user',
            'mailbox unavailable',
            'address rejected',
            '550', '551', '553', '554'
        ]
        
        # 一時的エラー
        temporary_patterns = [
            'mailbox full',
            'quota exceeded',
            'temporary failure',
            'try again later',
            'deferred',
            '421', '450', '451', '452'
        ]
        
        for pattern in permanent_patterns:
            if pattern in error_lower:
                return 'permanent'
        
        for pattern in temporary_patterns:
            if pattern in error_lower:
                return 'temporary'
        
        return 'unknown'

    def update_company_database(self):
        """企業データベースを更新"""
        try:
            print('📝 企業データベースを更新中...')
            
            # バックアップファイルを作成
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'data/new_input_test_backup_bounce_{timestamp}.csv'
            
            if os.path.exists(self.csv_file):
                df_original = pd.read_csv(self.csv_file)
                df_original.to_csv(backup_filename, index=False, encoding='utf-8-sig')
                print(f'📁 バックアップファイル作成: {backup_filename}')
            
            # 企業データを読み込み
            df_companies = pd.read_csv(self.csv_file)
            
            # バウンス状態列を追加（存在しない場合）
            if 'バウンス状態' not in df_companies.columns:
                df_companies['バウンス状態'] = ''
            
            if 'バウンス日時' not in df_companies.columns:
                df_companies['バウンス日時'] = ''
            
            if 'バウンス理由' not in df_companies.columns:
                df_companies['バウンス理由'] = ''
            
            # バウンス企業の情報を更新
            updated_count = 0
            for bounce_info in self.bounce_list:
                company_id = bounce_info['company_id']
                
                # 該当企業を特定
                company_mask = df_companies['ID'] == company_id
                if company_mask.any():
                    # バウンス情報を更新
                    df_companies.loc[company_mask, 'バウンス状態'] = bounce_info['bounce_type']
                    df_companies.loc[company_mask, 'バウンス日時'] = bounce_info['send_datetime']
                    df_companies.loc[company_mask, 'バウンス理由'] = bounce_info['error_message']
                    
                    updated_count += 1
                    print(f'   ✅ ID {company_id}: {bounce_info["company_name"]} - バウンス状態更新')
            
            # 更新されたデータを保存
            df_companies.to_csv(self.csv_file, index=False, encoding='utf-8-sig')
            print(f'💾 企業データベース更新完了: {updated_count}社')
            
            return True
            
        except Exception as e:
            print(f'❌ 企業データベース更新失敗: {e}')
            return False

    def update_sending_results(self):
        """送信履歴ファイルを更新"""
        try:
            print('📝 送信履歴ファイルを更新中...')
            
            # バックアップファイルを作成
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'new_email_sending_results_backup_bounce_{timestamp}.csv'
            
            if os.path.exists(self.sending_results_file):
                df_original = pd.read_csv(self.sending_results_file)
                df_original.to_csv(backup_filename, index=False, encoding='utf-8-sig')
                print(f'📁 送信履歴バックアップ作成: {backup_filename}')
            
            # 送信結果を読み込み
            df_results = pd.read_csv(self.sending_results_file)
            
            # バウンス企業の送信結果を更新
            updated_count = 0
            for bounce_info in self.bounce_list:
                company_id = bounce_info['company_id']
                email_address = bounce_info['email_address']
                
                # 該当送信記録を特定
                result_mask = (df_results['企業ID'] == company_id) & (df_results['メールアドレス'] == email_address)
                if result_mask.any():
                    # 送信結果を'bounced'に更新
                    df_results.loc[result_mask, '送信結果'] = 'bounced'
                    updated_count += 1
                    print(f'   ✅ ID {company_id}: 送信結果を"bounced"に更新')
            
            # 更新されたデータを保存
            df_results.to_csv(self.sending_results_file, index=False, encoding='utf-8-sig')
            print(f'💾 送信履歴更新完了: {updated_count}件')
            
            return True
            
        except Exception as e:
            print(f'❌ 送信履歴更新失敗: {e}')
            return False

    def update_bounce_list_in_sender(self):
        """huganjob_unified_sender.pyのバウンスリストを更新"""
        try:
            print('📝 送信システムのバウンスリストを更新中...')
            
            # バウンスしたメールアドレスのリストを作成
            bounce_addresses = [bounce['email_address'] for bounce in self.bounce_list]
            
            if not bounce_addresses:
                print('   更新対象のバウンスアドレスがありません')
                return True
            
            # huganjob_unified_sender.pyを読み込み
            sender_file = 'huganjob_unified_sender.py'
            if not os.path.exists(sender_file):
                print(f'❌ 送信システムファイルが見つかりません: {sender_file}')
                return False
            
            with open(sender_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 既存のバウンスリストを検索
            bounce_pattern = r"bounce_addresses\s*=\s*\[(.*?)\]"
            match = re.search(bounce_pattern, content, re.DOTALL)
            
            if match:
                # 既存のバウンスリストを取得
                existing_list_str = match.group(1)
                existing_addresses = []
                
                # 既存のアドレスを抽出
                addr_pattern = r"'([^']+)'"
                existing_addresses = re.findall(addr_pattern, existing_list_str)
                
                # 新しいバウンスアドレスを追加
                all_addresses = list(set(existing_addresses + bounce_addresses))
                
                # 新しいリストを作成
                new_list_str = ', '.join([f"'{addr}'" for addr in sorted(all_addresses)])
                new_bounce_list = f"bounce_addresses = [{new_list_str}]"
                
                # ファイル内容を更新
                updated_content = re.sub(bounce_pattern, new_bounce_list, content, flags=re.DOTALL)
                
                # ファイルを保存
                with open(sender_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                print(f'   ✅ バウンスリストを更新: {len(all_addresses)}件のアドレス')
                print(f'   追加されたアドレス: {bounce_addresses}')
                
            else:
                print('   ⚠️ 既存のバウンスリストが見つかりませんでした')
            
            return True
            
        except Exception as e:
            print(f'❌ バウンスリスト更新失敗: {e}')
            return False

    def generate_bounce_report(self):
        """バウンス処理レポートを生成"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = f'huganjob_bounce_management_report_{timestamp}.json'
            
            report_data = {
                'processing_date': datetime.datetime.now().isoformat(),
                'total_bounce_companies': len(self.bounce_list),
                'bounce_details': self.bounce_list,
                'summary': {
                    'permanent_bounces': len([b for b in self.bounce_list if b['bounce_type'] == 'permanent']),
                    'temporary_bounces': len([b for b in self.bounce_list if b['bounce_type'] == 'temporary']),
                    'unknown_bounces': len([b for b in self.bounce_list if b['bounce_type'] == 'unknown'])
                },
                'actions_taken': [
                    'Updated company database with bounce status',
                    'Updated sending results to mark as bounced',
                    'Updated bounce list in sender system'
                ]
            }
            
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            print(f'📄 バウンス管理レポートを生成しました: {report_filename}')
            return report_filename
            
        except Exception as e:
            print(f'❌ レポート生成失敗: {e}')
            return None

    def display_summary(self):
        """処理結果サマリーを表示"""
        print('\n' + '=' * 60)
        print('📊 バウンス処理結果サマリー')
        print('=' * 60)
        
        if not self.bounce_list:
            print('✅ バウンス企業は見つかりませんでした')
            return
        
        print(f'🔍 検出されたバウンス企業: {len(self.bounce_list)}社')
        print()
        
        # タイプ別集計
        permanent_count = len([b for b in self.bounce_list if b['bounce_type'] == 'permanent'])
        temporary_count = len([b for b in self.bounce_list if b['bounce_type'] == 'temporary'])
        unknown_count = len([b for b in self.bounce_list if b['bounce_type'] == 'unknown'])
        
        print('バウンスタイプ別集計:')
        print(f'  永続的エラー: {permanent_count}社')
        print(f'  一時的エラー: {temporary_count}社')
        print(f'  不明エラー: {unknown_count}社')
        print()
        
        print('バウンス企業一覧:')
        for bounce in self.bounce_list:
            print(f'  ID {bounce["company_id"]}: {bounce["company_name"]}')
            print(f'    メール: {bounce["email_address"]}')
            print(f'    タイプ: {bounce["bounce_type"]}')
            print(f'    理由: {bounce["error_message"]}')
            print()

def main():
    manager = HuganjobBounceManager()
    
    try:
        # 送信結果を分析
        if not manager.analyze_sending_results():
            return False
        
        # バウンス企業が見つからない場合
        if not manager.bounce_list:
            print('✅ バウンス企業が見つかりませんでした。処理を終了します。')
            return True
        
        # 企業データベースを更新
        if not manager.update_company_database():
            return False
        
        # 送信履歴を更新
        if not manager.update_sending_results():
            return False
        
        # 送信システムのバウンスリストを更新
        if not manager.update_bounce_list_in_sender():
            return False
        
        # レポート生成
        report_file = manager.generate_bounce_report()
        
        # 結果サマリー表示
        manager.display_summary()
        
        print('🎯 Phase 2: 企業データベース更新が完了しました')
        if report_file:
            print(f'📄 詳細レポート: {report_file}')
        
        return True
        
    except Exception as e:
        print(f'❌ 処理中にエラーが発生しました: {e}')
        return False

if __name__ == "__main__":
    main()
