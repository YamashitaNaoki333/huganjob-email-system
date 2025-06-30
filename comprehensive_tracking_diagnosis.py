#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
包括的追跡システム診断スクリプト
企業ID 1200以降の開封率0%問題の根本原因分析

作成日時: 2025年06月24日
目的: 追跡システムの技術的問題を徹底調査
"""

import csv
import json
import os
import requests
import time
from datetime import datetime
from collections import defaultdict
import re

class ComprehensiveTrackingDiagnosis:
    def __init__(self):
        self.dashboard_url = "http://127.0.0.1:5002"
        self.tracking_endpoints = [
            "/track-open/",
            "/track/",
            "/track-css/",
            "/track-beacon/",
            "/track-xhr/",
            "/track-focus/",
            "/track-unload/"
        ]
        self.test_tracking_ids = []
        self.diagnosis_results = {}
        
    def test_dashboard_connectivity(self):
        """ダッシュボードの接続性をテスト"""
        print("🌐 ダッシュボード接続性テスト")
        print("=" * 60)
        
        try:
            response = requests.get(self.dashboard_url, timeout=5)
            if response.status_code == 200:
                print(f"✅ ダッシュボード接続成功: {self.dashboard_url}")
                self.diagnosis_results['dashboard_connectivity'] = True
                return True
            else:
                print(f"❌ ダッシュボード接続失敗: HTTP {response.status_code}")
                self.diagnosis_results['dashboard_connectivity'] = False
                return False
        except Exception as e:
            print(f"❌ ダッシュボード接続エラー: {e}")
            self.diagnosis_results['dashboard_connectivity'] = False
            return False
    
    def test_tracking_endpoints(self):
        """各追跡エンドポイントの動作テスト"""
        print("\n🎯 追跡エンドポイント動作テスト")
        print("=" * 60)
        
        test_id = f"diagnosis_test_{int(time.time())}"
        endpoint_results = {}
        
        for endpoint in self.tracking_endpoints:
            try:
                url = f"{self.dashboard_url}{endpoint}{test_id}"
                
                if endpoint in ["/track-beacon/", "/track-xhr/", "/track-focus/", "/track-unload/"]:
                    # POST メソッドのエンドポイント
                    response = requests.post(url, timeout=5)
                else:
                    # GET メソッドのエンドポイント
                    response = requests.get(url, timeout=5)
                
                if response.status_code in [200, 204]:
                    print(f"✅ {endpoint}: 正常動作 (HTTP {response.status_code})")
                    endpoint_results[endpoint] = True
                else:
                    print(f"❌ {endpoint}: エラー (HTTP {response.status_code})")
                    endpoint_results[endpoint] = False
                    
            except Exception as e:
                print(f"❌ {endpoint}: 接続エラー - {e}")
                endpoint_results[endpoint] = False
        
        self.diagnosis_results['tracking_endpoints'] = endpoint_results
        return endpoint_results
    
    def analyze_tracking_data_integrity(self):
        """追跡データの整合性分析"""
        print("\n📊 追跡データ整合性分析")
        print("=" * 60)
        
        # 1. 送信結果から1200以降の追跡IDを収集
        tracking_ids_1200_plus = set()
        companies_1200_plus = {}
        
        try:
            with open('new_email_sending_results.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    company_id_str = row.get('企業ID', '').strip()
                    if company_id_str.isdigit():
                        company_id = int(company_id_str)
                        if company_id >= 1200:
                            tracking_id = row.get('トラッキングID', '').strip()
                            if tracking_id:
                                tracking_ids_1200_plus.add(tracking_id)
                                companies_1200_plus[company_id] = {
                                    'name': row.get('企業名', ''),
                                    'tracking_id': tracking_id,
                                    'sent_at': row.get('送信日時', ''),
                                    'email': row.get('メールアドレス', '')
                                }
            
            print(f"📋 企業ID 1200以降の追跡ID数: {len(tracking_ids_1200_plus)}")
            print(f"📋 企業ID 1200以降の企業数: {len(companies_1200_plus)}")
            
        except Exception as e:
            print(f"❌ 送信結果読み込みエラー: {e}")
            return False
        
        # 2. 開封記録から該当する追跡IDを確認
        found_opens = set()
        try:
            with open('data/derivative_email_open_tracking.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    tracking_id = row.get('tracking_id', '').strip()
                    if tracking_id in tracking_ids_1200_plus:
                        found_opens.add(tracking_id)
                        print(f"✅ 開封記録発見: {tracking_id}")
            
            print(f"📊 1200以降で開封記録のある追跡ID数: {len(found_opens)}")
            
        except Exception as e:
            print(f"❌ 開封記録読み込みエラー: {e}")
            return False
        
        # 3. 追跡IDパターン分析
        print(f"\n🔍 追跡IDパターン分析:")
        pattern_analysis = defaultdict(int)
        
        for tracking_id in list(tracking_ids_1200_plus)[:10]:  # サンプル10件
            print(f"  {tracking_id}")
            # パターン分析
            if '_' in tracking_id:
                parts = tracking_id.split('_')
                if len(parts) >= 3:
                    pattern_analysis[f"parts_{len(parts)}"] += 1
        
        self.diagnosis_results['data_integrity'] = {
            'total_tracking_ids': len(tracking_ids_1200_plus),
            'found_opens': len(found_opens),
            'companies_count': len(companies_1200_plus),
            'pattern_analysis': dict(pattern_analysis)
        }
        
        return companies_1200_plus, tracking_ids_1200_plus, found_opens
    
    def test_tracking_id_functionality(self, sample_tracking_ids):
        """実際の追跡IDでの機能テスト"""
        print("\n🧪 実際の追跡ID機能テスト")
        print("=" * 60)
        
        # サンプル追跡IDを使用してテスト
        sample_ids = list(sample_tracking_ids)[:5]  # 最初の5件をテスト
        
        for tracking_id in sample_ids:
            print(f"\n🔗 テスト対象: {tracking_id}")
            
            for endpoint in self.tracking_endpoints:
                try:
                    url = f"{self.dashboard_url}{endpoint}{tracking_id}"
                    
                    if endpoint in ["/track-beacon/", "/track-xhr/", "/track-focus/", "/track-unload/"]:
                        response = requests.post(url, timeout=3)
                    else:
                        response = requests.get(url, timeout=3)
                    
                    if response.status_code in [200, 204]:
                        print(f"  ✅ {endpoint}: 成功")
                    else:
                        print(f"  ❌ {endpoint}: HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"  ❌ {endpoint}: エラー - {e}")
    
    def check_html_template_tracking_elements(self):
        """HTMLテンプレートの追跡要素確認"""
        print("\n📄 HTMLテンプレート追跡要素確認")
        print("=" * 60)
        
        template_file = "templates/corporate-email-newsletter.html"
        
        if not os.path.exists(template_file):
            print(f"❌ テンプレートファイルが見つかりません: {template_file}")
            return False
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 追跡要素の確認
            tracking_elements = {
                'pixel_tracking': 'track-open',
                'fallback_pixel': '/track/',
                'css_tracking': 'track-css',
                'beacon_tracking': 'track-beacon',
                'xhr_tracking': 'track-xhr',
                'focus_tracking': 'track-focus',
                'unload_tracking': 'track-unload'
            }
            
            found_elements = {}
            for element_name, pattern in tracking_elements.items():
                if pattern in content:
                    found_elements[element_name] = True
                    print(f"✅ {element_name}: 発見")
                else:
                    found_elements[element_name] = False
                    print(f"❌ {element_name}: 未発見")
            
            # JavaScript追跡コードの確認
            js_patterns = [
                'navigator.sendBeacon',
                'fetch(',
                'XMLHttpRequest',
                'beforeunload',
                'focus'
            ]
            
            print(f"\n📜 JavaScript追跡コード確認:")
            for pattern in js_patterns:
                if pattern in content:
                    print(f"✅ {pattern}: 発見")
                else:
                    print(f"❌ {pattern}: 未発見")
            
            self.diagnosis_results['template_elements'] = found_elements
            return found_elements
            
        except Exception as e:
            print(f"❌ テンプレート読み込みエラー: {e}")
            return False
    
    def check_dashboard_logs(self):
        """ダッシュボードログの確認"""
        print("\n📋 ダッシュボードログ確認")
        print("=" * 60)
        
        log_files = [
            "logs/huganjob_dashboard/huganjob_dashboard.log",
            "logs/huganjob_email_resolver.log"
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                print(f"\n📄 ログファイル: {log_file}")
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # 最新の100行を確認
                    recent_lines = lines[-100:] if len(lines) > 100 else lines
                    
                    # エラーパターンを検索
                    error_patterns = ['ERROR', 'Exception', 'Traceback', 'Failed']
                    error_count = 0
                    
                    for line in recent_lines:
                        for pattern in error_patterns:
                            if pattern in line:
                                error_count += 1
                                print(f"⚠️  エラー発見: {line.strip()}")
                                break
                    
                    if error_count == 0:
                        print(f"✅ エラーなし（最新100行確認）")
                    else:
                        print(f"❌ エラー数: {error_count}件")
                        
                except Exception as e:
                    print(f"❌ ログ読み込みエラー: {e}")
            else:
                print(f"❌ ログファイルが見つかりません: {log_file}")
    
    def run_comprehensive_diagnosis(self):
        """包括的診断の実行"""
        print("🔬 包括的追跡システム診断開始")
        print("=" * 80)
        print(f"📅 診断実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. ダッシュボード接続性テスト
        dashboard_ok = self.test_dashboard_connectivity()
        
        if dashboard_ok:
            # 2. 追跡エンドポイントテスト
            self.test_tracking_endpoints()
        
        # 3. データ整合性分析
        companies_data, tracking_ids, found_opens = self.analyze_tracking_data_integrity()
        
        if dashboard_ok and tracking_ids:
            # 4. 実際の追跡ID機能テスト
            self.test_tracking_id_functionality(tracking_ids)
        
        # 5. HTMLテンプレート確認
        self.check_html_template_tracking_elements()
        
        # 6. ダッシュボードログ確認
        self.check_dashboard_logs()
        
        # 7. 診断結果サマリー
        self.print_diagnosis_summary()
        
        return self.diagnosis_results
    
    def print_diagnosis_summary(self):
        """診断結果サマリーの表示"""
        print("\n📊 診断結果サマリー")
        print("=" * 80)
        
        # 重要な問題点の特定
        critical_issues = []
        warnings = []
        
        if not self.diagnosis_results.get('dashboard_connectivity', False):
            critical_issues.append("ダッシュボード接続不可")
        
        endpoint_results = self.diagnosis_results.get('tracking_endpoints', {})
        failed_endpoints = [ep for ep, status in endpoint_results.items() if not status]
        if failed_endpoints:
            critical_issues.append(f"追跡エンドポイント失敗: {len(failed_endpoints)}件")
        
        data_integrity = self.diagnosis_results.get('data_integrity', {})
        if data_integrity.get('found_opens', 0) == 0:
            critical_issues.append("1200以降の開封記録が完全に0件")
        
        template_elements = self.diagnosis_results.get('template_elements', {})
        missing_elements = [elem for elem, status in template_elements.items() if not status]
        if missing_elements:
            warnings.append(f"テンプレート要素不足: {len(missing_elements)}件")
        
        # 結果表示
        if critical_issues:
            print("🚨 重大な問題:")
            for issue in critical_issues:
                print(f"   - {issue}")
        
        if warnings:
            print("\n⚠️  警告:")
            for warning in warnings:
                print(f"   - {warning}")
        
        if not critical_issues and not warnings:
            print("✅ 重大な技術的問題は検出されませんでした")
        
        print(f"\n📈 統計:")
        print(f"   - 追跡ID総数: {data_integrity.get('total_tracking_ids', 0)}")
        print(f"   - 開封記録数: {data_integrity.get('found_opens', 0)}")
        print(f"   - 成功エンドポイント: {sum(endpoint_results.values())}/{len(endpoint_results)}")

def main():
    """メイン関数"""
    diagnosis = ComprehensiveTrackingDiagnosis()
    results = diagnosis.run_comprehensive_diagnosis()
    return results

if __name__ == "__main__":
    main()
