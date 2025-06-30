#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
メール内容検証スクリプト
実際に送信されたメールの内容と追跡要素を検証

作成日時: 2025年06月24日
目的: 送信メールの追跡要素が正しく埋め込まれているか確認
"""

import csv
import json
import os
import re
from datetime import datetime

class EmailContentVerification:
    def __init__(self):
        self.template_file = "corporate-email-newsletter.html"
        self.tracking_patterns = {
            'pixel_tracking': r'track-open/\{\{tracking_id\}\}',
            'css_tracking': r'track-css/\{\{tracking_id\}\}',
            'beacon_tracking': r'track-beacon/\{\{tracking_id\}\}',
            'xhr_tracking': r'track-xhr/\{\{tracking_id\}\}',
            'focus_tracking': r'track-focus/\{\{tracking_id\}\}',
            'unload_tracking': r'track-unload/\{\{tracking_id\}\}'
        }
        
    def analyze_template_content(self):
        """テンプレートファイルの内容分析"""
        print("📄 HTMLテンプレート内容分析")
        print("=" * 60)
        
        if not os.path.exists(self.template_file):
            print(f"❌ テンプレートファイルが見つかりません: {self.template_file}")
            return False
        
        try:
            with open(self.template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"✅ テンプレートファイル読み込み成功")
            print(f"📊 ファイルサイズ: {len(content)} 文字")
            
            # 追跡要素の確認
            found_patterns = {}
            for pattern_name, pattern in self.tracking_patterns.items():
                matches = re.findall(pattern, content)
                found_patterns[pattern_name] = len(matches)
                if matches:
                    print(f"✅ {pattern_name}: {len(matches)}件発見")
                else:
                    print(f"❌ {pattern_name}: 未発見")
            
            # JavaScript追跡コードの確認
            js_elements = {
                'sendBeacon': 'navigator.sendBeacon',
                'fetch_api': 'fetch(',
                'xhr_request': 'XMLHttpRequest',
                'beforeunload': 'beforeunload',
                'focus_event': 'addEventListener.*focus'
            }
            
            print(f"\n📜 JavaScript要素確認:")
            for element_name, pattern in js_elements.items():
                if re.search(pattern, content):
                    print(f"✅ {element_name}: 発見")
                else:
                    print(f"❌ {element_name}: 未発見")
            
            # tracking_id変数の使用確認
            tracking_id_usage = re.findall(r'\{\{tracking_id\}\}', content)
            print(f"\n🔗 tracking_id使用箇所: {len(tracking_id_usage)}件")
            
            return True, content
            
        except Exception as e:
            print(f"❌ テンプレート読み込みエラー: {e}")
            return False, None
    
    def simulate_email_generation(self, sample_tracking_ids):
        """メール生成のシミュレーション"""
        print("\n🧪 メール生成シミュレーション")
        print("=" * 60)
        
        template_ok, template_content = self.analyze_template_content()
        if not template_ok:
            return False
        
        # サンプル追跡IDでメール生成をシミュレート
        sample_ids = list(sample_tracking_ids)[:3]
        
        for tracking_id in sample_ids:
            print(f"\n🔗 追跡ID: {tracking_id}")
            
            # テンプレート変数の置換をシミュレート
            simulated_content = template_content.replace('{{tracking_id}}', tracking_id)
            
            # 生成されたURLの確認
            generated_urls = []
            for endpoint in ['/track-open/', '/track-css/', '/track-beacon/', '/track-xhr/', '/track-focus/', '/track-unload/']:
                pattern = f'http://127.0.0.1:5002{endpoint}{re.escape(tracking_id)}'
                if re.search(pattern, simulated_content):
                    generated_urls.append(f"{endpoint}{tracking_id}")
            
            print(f"   生成されたURL数: {len(generated_urls)}")
            for url in generated_urls[:3]:  # 最初の3つを表示
                print(f"   - {url}")
            
            if len(generated_urls) == 0:
                print(f"   ❌ 追跡URLが生成されていません")
            else:
                print(f"   ✅ 追跡URL正常生成")
    
    def check_sending_process_integration(self):
        """送信プロセスとの統合確認"""
        print("\n🔄 送信プロセス統合確認")
        print("=" * 60)
        
        # 送信スクリプトの確認
        sending_scripts = [
            'huganjob_unified_sender.py',
            'huganjob_email_sender.py',
            'huganjob_duplicate_prevention.py'
        ]
        
        for script in sending_scripts:
            if os.path.exists(script):
                print(f"✅ 送信スクリプト存在: {script}")
                
                # スクリプト内でのテンプレート使用確認
                try:
                    with open(script, 'r', encoding='utf-8') as f:
                        script_content = f.read()
                    
                    # テンプレートファイル参照の確認
                    if 'corporate-email-newsletter.html' in script_content:
                        print(f"   ✅ テンプレート参照あり")
                    else:
                        print(f"   ❌ テンプレート参照なし")
                    
                    # tracking_id生成の確認
                    if 'tracking_id' in script_content:
                        print(f"   ✅ tracking_id処理あり")
                    else:
                        print(f"   ❌ tracking_id処理なし")
                        
                except Exception as e:
                    print(f"   ❌ スクリプト読み込みエラー: {e}")
            else:
                print(f"❌ 送信スクリプト未発見: {script}")
    
    def analyze_1200_plus_specific_issues(self):
        """企業ID 1200以降特有の問題分析"""
        print("\n🔍 企業ID 1200以降特有問題分析")
        print("=" * 60)
        
        # 送信時期の分析
        try:
            with open('new_email_sending_results.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                before_1200 = []
                after_1200 = []
                
                for row in reader:
                    company_id_str = row.get('企業ID', '').strip()
                    if company_id_str.isdigit():
                        company_id = int(company_id_str)
                        sent_time = row.get('送信日時', '')
                        
                        if company_id < 1200:
                            before_1200.append(sent_time)
                        else:
                            after_1200.append(sent_time)
                
                print(f"📊 企業ID 1200未満の送信数: {len(before_1200)}")
                print(f"📊 企業ID 1200以降の送信数: {len(after_1200)}")
                
                if before_1200:
                    print(f"📅 1200未満の送信期間: {min(before_1200)} ～ {max(before_1200)}")
                if after_1200:
                    print(f"📅 1200以降の送信期間: {min(after_1200)} ～ {max(after_1200)}")
                
                # 送信時期の違いを分析
                if before_1200 and after_1200:
                    # 日付の比較
                    before_dates = [t.split(' ')[0] for t in before_1200 if ' ' in t]
                    after_dates = [t.split(' ')[0] for t in after_1200 if ' ' in t]
                    
                    unique_before = set(before_dates)
                    unique_after = set(after_dates)
                    
                    print(f"📅 1200未満の送信日数: {len(unique_before)}")
                    print(f"📅 1200以降の送信日数: {len(unique_after)}")
                    
                    if unique_before != unique_after:
                        print(f"⚠️  送信日に違いがあります")
                        print(f"   1200未満のみ: {unique_before - unique_after}")
                        print(f"   1200以降のみ: {unique_after - unique_before}")
                
        except Exception as e:
            print(f"❌ 送信結果分析エラー: {e}")
    
    def check_dashboard_tracking_functionality(self):
        """ダッシュボードの追跡機能確認"""
        print("\n🌐 ダッシュボード追跡機能確認")
        print("=" * 60)
        
        dashboard_file = "dashboard/derivative_dashboard.py"
        
        if os.path.exists(dashboard_file):
            try:
                with open(dashboard_file, 'r', encoding='utf-8') as f:
                    dashboard_content = f.read()
                
                # 追跡エンドポイントの確認
                endpoints_to_check = [
                    'track-open',
                    'track-css',
                    'track-beacon',
                    'track-xhr',
                    'track-focus',
                    'track-unload'
                ]
                
                found_endpoints = []
                for endpoint in endpoints_to_check:
                    if endpoint in dashboard_content:
                        found_endpoints.append(endpoint)
                        print(f"✅ エンドポイント実装: {endpoint}")
                    else:
                        print(f"❌ エンドポイント未実装: {endpoint}")
                
                # 開封記録保存処理の確認
                save_patterns = [
                    'derivative_email_open_tracking.csv',
                    'csv.writer',
                    'writerow'
                ]
                
                print(f"\n💾 開封記録保存処理確認:")
                for pattern in save_patterns:
                    if pattern in dashboard_content:
                        print(f"✅ {pattern}: 発見")
                    else:
                        print(f"❌ {pattern}: 未発見")
                
                return len(found_endpoints) == len(endpoints_to_check)
                
            except Exception as e:
                print(f"❌ ダッシュボード読み込みエラー: {e}")
                return False
        else:
            print(f"❌ ダッシュボードファイル未発見: {dashboard_file}")
            return False
    
    def run_comprehensive_verification(self):
        """包括的検証の実行"""
        print("🔬 メール内容包括的検証開始")
        print("=" * 80)
        print(f"📅 検証実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. テンプレート内容分析
        template_ok, template_content = self.analyze_template_content()
        
        # 2. 1200以降の追跡IDを取得
        tracking_ids_1200_plus = set()
        try:
            with open('new_email_sending_results.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    company_id_str = row.get('企業ID', '').strip()
                    if company_id_str.isdigit() and int(company_id_str) >= 1200:
                        tracking_id = row.get('トラッキングID', '').strip()
                        if tracking_id:
                            tracking_ids_1200_plus.add(tracking_id)
        except Exception as e:
            print(f"❌ 追跡ID取得エラー: {e}")
        
        # 3. メール生成シミュレーション
        if template_ok and tracking_ids_1200_plus:
            self.simulate_email_generation(tracking_ids_1200_plus)
        
        # 4. 送信プロセス統合確認
        self.check_sending_process_integration()
        
        # 5. 1200以降特有問題分析
        self.analyze_1200_plus_specific_issues()
        
        # 6. ダッシュボード追跡機能確認
        dashboard_ok = self.check_dashboard_tracking_functionality()
        
        # 7. 総合判定
        print(f"\n📊 検証結果サマリー")
        print("=" * 60)
        print(f"テンプレート状態: {'✅ 正常' if template_ok else '❌ 問題あり'}")
        print(f"ダッシュボード状態: {'✅ 正常' if dashboard_ok else '❌ 問題あり'}")
        print(f"1200以降追跡ID数: {len(tracking_ids_1200_plus)}")
        
        if template_ok and dashboard_ok and tracking_ids_1200_plus:
            print(f"\n💡 結論: 技術的には正常に動作するはずです")
            print(f"   開封率0%の原因は企業環境の厳格さによる可能性が高い")
        else:
            print(f"\n🚨 結論: 技術的問題が存在します")

def main():
    """メイン関数"""
    verification = EmailContentVerification()
    verification.run_comprehensive_verification()

if __name__ == "__main__":
    main()
