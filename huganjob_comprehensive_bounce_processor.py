#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB 包括的バウンス処理システム
手動バウンス情報と送信履歴を統合してバウンス処理を実行
"""

import pandas as pd
import datetime
import os
import json
import re

class ComprehensiveBounceProcessor:
    def __init__(self):
        self.csv_file = 'data/new_input_test.csv'
        self.sending_results_file = 'new_email_sending_results.csv'
        
        # 手動で特定されたバウンスメールアドレス（受信ボックスから確認）
        self.manual_bounce_addresses = [
            # 既知のバウンス
            'info@www.yoshimoto.co.jp:443',  # アドレス形式エラー
            'info@sincere.co.jp',  # 既存のバウンス
            
            # 追加のバウンスアドレス（受信ボックスから特定）
            'info@www.osakagaigo.ac.jp',     # 学校法人文際学園
            'info@www.h2j.jp',               # ハウスホールドジャパン株式会社
            'info@www.orientalbakery.co.jp', # 株式会社オリエンタルベーカリー
            'info@www.flex-og.jp',           # 株式会社フレックス
            'info@www.aoikokuban.co.jp',     # 株式会社青井黒板製作所
            'info@www.hanei-co.jp',          # 阪栄株式会社
            'info@www.crosscorporation.co.jp', # 株式会社CROSS CORPORATION
            'info@www.konishi-mark.com',     # 小西マーク株式会社
            'info@www.somax.co.jp',          # ソマックス株式会社
            'info@www.nikki-tr.co.jp',       # 日機株式会社
            'info@www.manneken.co.jp',       # ローゼン製菓株式会社
            'info@www.seedassist.co.jp',     # 株式会社シードアシスト
            'info@www.advance-1st.co.jp',    # 株式会社アドバンス一世
            'info@www.koutokudenkou.co.jp',  # 光徳電興株式会社
            'info@www.teruteru.co.jp',       # 株式会社テルテルアドバンス
            'info@www.tsukitora.com',        # 株式会社月虎金属
            'info@www.naniwakanri.co.jp',    # 株式会社浪速技建
            'info@www.hayashikazuji.co.jp',  # 林一二株式会社
        ]
        
        self.bounce_list = []
        self.processed_results = []

    def identify_bounce_companies(self):
        """バウンス企業を特定"""
        try:
            print('=== HUGANJOB 包括的バウンス処理システム ===')
            print('受信ボックスのバウンスメールを処理します')
            print()
            
            # 企業データを読み込み
            df_companies = pd.read_csv(self.csv_file)
            print(f'📊 総企業数: {len(df_companies)}社')
            
            # 送信履歴を読み込み
            if os.path.exists(self.sending_results_file):
                df_results = pd.read_csv(self.sending_results_file)
                print(f'📊 送信履歴: {len(df_results)}件')
            else:
                df_results = pd.DataFrame()
                print('⚠️ 送信履歴ファイルが見つかりません')
            
            print(f'🔍 手動特定バウンスアドレス: {len(self.manual_bounce_addresses)}件')
            print()
            
            # バウンス企業を特定
            for bounce_email in self.manual_bounce_addresses:
                # 企業データから該当企業を検索
                company_matches = df_companies[
                    df_companies['担当者メールアドレス'].str.contains(bounce_email.replace('info@www.', '').replace('info@', ''), na=False) |
                    df_companies['企業ホームページ'].str.contains(bounce_email.replace('info@www.', '').replace('info@', '').replace(':443', ''), na=False)
                ]
                
                if len(company_matches) > 0:
                    for _, company in company_matches.iterrows():
                        # 送信履歴から詳細を取得
                        send_history = df_results[df_results['企業ID'] == company['ID']]
                        
                        bounce_info = {
                            'company_id': company['ID'],
                            'company_name': company['企業名'],
                            'email_address': bounce_email,
                            'job_position': company['募集職種'],
                            'bounce_type': self.classify_bounce_type(bounce_email),
                            'send_datetime': send_history['送信日時'].iloc[0] if len(send_history) > 0 else datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'error_message': self.get_bounce_reason(bounce_email)
                        }
                        
                        self.bounce_list.append(bounce_info)
                        
                        print(f'🔍 バウンス企業特定:')
                        print(f'   ID {bounce_info["company_id"]}: {bounce_info["company_name"]}')
                        print(f'   メール: {bounce_info["email_address"]}')
                        print(f'   タイプ: {bounce_info["bounce_type"]}')
                        print()
                else:
                    print(f'⚠️ 企業が見つかりません: {bounce_email}')
            
            print(f'✅ バウンス企業特定完了: {len(self.bounce_list)}社')
            return True
            
        except Exception as e:
            print(f'❌ バウンス企業特定失敗: {e}')
            return False

    def classify_bounce_type(self, email_address):
        """バウンスタイプを分類"""
        # アドレス形式エラー
        if ':443' in email_address or 'www.' in email_address:
            return 'permanent'
        
        # 一般的なバウンス（詳細不明）
        return 'permanent'

    def get_bounce_reason(self, email_address):
        """バウンス理由を取得"""
        if ':443' in email_address:
            return 'Bad recipient address syntax (port number included)'
        elif 'www.' in email_address:
            return 'Invalid email format (www prefix)'
        else:
            return 'Mail delivery failed (bounce detected in inbox)'

    def update_company_database(self):
        """企業データベースを更新"""
        try:
            print('📝 企業データベースを更新中...')
            
            # バックアップファイルを作成
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'data/new_input_test_backup_comprehensive_bounce_{timestamp}.csv'
            
            df_companies = pd.read_csv(self.csv_file)
            df_companies.to_csv(backup_filename, index=False, encoding='utf-8-sig')
            print(f'📁 バックアップファイル作成: {backup_filename}')
            
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
                print(f'   新規追加: {len(bounce_addresses)}件')
                
            else:
                print('   ⚠️ 既存のバウンスリストが見つかりませんでした')
            
            return True
            
        except Exception as e:
            print(f'❌ バウンスリスト更新失敗: {e}')
            return False

    def generate_comprehensive_report(self):
        """包括的レポートを生成"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = f'huganjob_comprehensive_bounce_report_{timestamp}.json'
            
            report_data = {
                'processing_date': datetime.datetime.now().isoformat(),
                'total_bounce_companies': len(self.bounce_list),
                'manual_bounce_addresses': self.manual_bounce_addresses,
                'bounce_details': self.bounce_list,
                'summary': {
                    'permanent_bounces': len([b for b in self.bounce_list if b['bounce_type'] == 'permanent']),
                    'temporary_bounces': len([b for b in self.bounce_list if b['bounce_type'] == 'temporary']),
                    'format_errors': len([b for b in self.bounce_list if 'syntax' in b['error_message']]),
                    'www_prefix_errors': len([b for b in self.bounce_list if 'www prefix' in b['error_message']])
                },
                'actions_taken': [
                    'Updated company database with bounce status',
                    'Updated bounce list in sender system',
                    'Processed manual bounce addresses from inbox'
                ]
            }
            
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            print(f'📄 包括的バウンスレポートを生成しました: {report_filename}')
            return report_filename
            
        except Exception as e:
            print(f'❌ レポート生成失敗: {e}')
            return None

    def display_summary(self):
        """処理結果サマリーを表示"""
        print('\n' + '=' * 60)
        print('📊 包括的バウンス処理結果サマリー')
        print('=' * 60)
        
        if not self.bounce_list:
            print('✅ バウンス企業は見つかりませんでした')
            return
        
        print(f'🔍 検出されたバウンス企業: {len(self.bounce_list)}社')
        print(f'📧 手動特定アドレス: {len(self.manual_bounce_addresses)}件')
        print()
        
        # タイプ別集計
        permanent_count = len([b for b in self.bounce_list if b['bounce_type'] == 'permanent'])
        format_errors = len([b for b in self.bounce_list if 'syntax' in b['error_message']])
        www_errors = len([b for b in self.bounce_list if 'www prefix' in b['error_message']])
        
        print('バウンス分類:')
        print(f'  永続的エラー: {permanent_count}社')
        print(f'  アドレス形式エラー: {format_errors}社')
        print(f'  WWWプレフィックスエラー: {www_errors}社')
        print()
        
        print('バウンス企業一覧:')
        for bounce in self.bounce_list:
            print(f'  ID {bounce["company_id"]}: {bounce["company_name"]}')
            print(f'    メール: {bounce["email_address"]}')
            print(f'    理由: {bounce["error_message"]}')
            print()

def main():
    processor = ComprehensiveBounceProcessor()
    
    try:
        # バウンス企業を特定
        if not processor.identify_bounce_companies():
            return False
        
        # バウンス企業が見つからない場合
        if not processor.bounce_list:
            print('✅ バウンス企業が見つかりませんでした。処理を終了します。')
            return True
        
        # 企業データベースを更新
        if not processor.update_company_database():
            return False
        
        # 送信システムのバウンスリストを更新
        if not processor.update_bounce_list_in_sender():
            return False
        
        # レポート生成
        report_file = processor.generate_comprehensive_report()
        
        # 結果サマリー表示
        processor.display_summary()
        
        print('🎯 包括的バウンス処理が完了しました')
        if report_file:
            print(f'📄 詳細レポート: {report_file}')
        
        return True
        
    except Exception as e:
        print(f'❌ 処理中にエラーが発生しました: {e}')
        return False

if __name__ == "__main__":
    main()
