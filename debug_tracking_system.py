#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改善されたトラッキングシステムのデバッグスクリプト
なぜ自動追跡が機能していないかを調査

作成日時: 2025年06月24日
目的: トラッキングシステムの問題点特定と修正
"""

import requests
import time
from datetime import datetime

class TrackingSystemDebugger:
    def __init__(self):
        self.base_url = 'http://127.0.0.1:5002'
        self.test_tracking_ids = {
            'k.abe@raxus.inc': 'improved_k_abe_raxus_inc_20250624152839_b5e1ece7',
            'naoki_yamashita@fortyfive.co.jp': 'improved_naoki_yamashita_fortyfive_co_jp_20250624152840_2d93127e'
        }
    
    def test_tracking_endpoints(self):
        """各追跡エンドポイントをテスト"""
        print("🔧 追跡エンドポイントのテスト")
        print("=" * 60)
        
        tracking_id = self.test_tracking_ids['k.abe@raxus.inc']
        
        # テストするエンドポイント
        endpoints = [
            ('track-open', 'GET', f'/track-open/{tracking_id}'),
            ('track-beacon', 'POST', f'/track-beacon/{tracking_id}'),
            ('track-css', 'GET', f'/track-css/{tracking_id}'),
            ('track-xhr', 'POST', f'/track-xhr/{tracking_id}'),
            ('track-focus', 'POST', f'/track-focus/{tracking_id}'),
            ('track-unload', 'POST', f'/track-unload/{tracking_id}'),
            ('track (fallback)', 'GET', f'/track/{tracking_id}'),
        ]
        
        results = []
        
        for name, method, endpoint in endpoints:
            try:
                url = self.base_url + endpoint
                print(f"\n🧪 テスト中: {name}")
                print(f"   URL: {url}")
                print(f"   メソッド: {method}")
                
                if method == 'GET':
                    response = requests.get(url, timeout=10)
                else:
                    response = requests.post(url, timeout=10, json={
                        'tracking_id': tracking_id,
                        'timestamp': datetime.now().isoformat(),
                        'test': True
                    })
                
                print(f"   ステータス: {response.status_code}")
                print(f"   レスポンス: {response.text[:100]}...")
                
                results.append({
                    'name': name,
                    'method': method,
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                    'response': response.text[:200]
                })
                
                if response.status_code == 200:
                    print(f"   ✅ 成功")
                else:
                    print(f"   ❌ 失敗")
                
            except Exception as e:
                print(f"   ❌ エラー: {e}")
                results.append({
                    'name': name,
                    'method': method,
                    'endpoint': endpoint,
                    'status_code': None,
                    'success': False,
                    'error': str(e)
                })
            
            time.sleep(1)  # レート制限回避
        
        return results
    
    def test_html_template_tracking(self):
        """HTMLテンプレートの追跡機能をテスト"""
        print("\n📧 HTMLテンプレートの追跡機能テスト")
        print("=" * 60)
        
        try:
            with open('corporate-email-newsletter.html', 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            tracking_id = self.test_tracking_ids['k.abe@raxus.inc']
            
            # テンプレート内の追跡要素を確認
            tracking_elements = []
            
            if 'track-open' in template_content:
                tracking_elements.append('ピクセル追跡 (track-open)')
            
            if 'track-beacon' in template_content:
                tracking_elements.append('ビーコン追跡 (track-beacon)')
            
            if 'track-css' in template_content:
                tracking_elements.append('CSS追跡 (track-css)')
            
            if 'track-xhr' in template_content:
                tracking_elements.append('XHR追跡 (track-xhr)')
            
            if 'track-focus' in template_content:
                tracking_elements.append('フォーカス追跡 (track-focus)')
            
            if 'track-unload' in template_content:
                tracking_elements.append('離脱時追跡 (track-unload)')
            
            if 'track/' in template_content:
                tracking_elements.append('フォールバック追跡 (track/)')
            
            print(f"📁 テンプレートファイル: corporate-email-newsletter.html")
            print(f"🎯 検出された追跡要素: {len(tracking_elements)}個")
            
            for element in tracking_elements:
                print(f"   ✅ {element}")
            
            if not tracking_elements:
                print("   ❌ 追跡要素が見つかりません")
                return False
            
            # 実際のHTMLを生成してテスト
            test_html = template_content.replace('{{tracking_id}}', tracking_id)
            test_html = test_html.replace('{{company_name}}', 'テスト株式会社')
            test_html = test_html.replace('{{job_position}}', 'テストエンジニア')
            
            print(f"\n📝 生成されたHTMLの追跡URL:")
            
            # 追跡URLを抽出
            import re
            
            # track-open URL
            track_open_urls = re.findall(r'http://127\.0\.0\.1:5002/track-open/[^"\'>\s]+', test_html)
            for url in track_open_urls:
                print(f"   🎯 ピクセル追跡: {url}")
            
            # track-beacon URL
            track_beacon_urls = re.findall(r'http://127\.0\.0\.1:5002/track-beacon/[^"\'>\s]+', test_html)
            for url in track_beacon_urls:
                print(f"   🎯 ビーコン追跡: {url}")
            
            # その他の追跡URL
            other_track_urls = re.findall(r'http://127\.0\.0\.1:5002/track[^/]*?/[^"\'>\s]+', test_html)
            for url in other_track_urls:
                if 'track-open' not in url and 'track-beacon' not in url:
                    print(f"   🎯 その他追跡: {url}")
            
            return len(tracking_elements) > 0
            
        except Exception as e:
            print(f"❌ HTMLテンプレート確認エラー: {e}")
            return False
    
    def check_dashboard_endpoints(self):
        """ダッシュボードのエンドポイント実装を確認"""
        print("\n🌐 ダッシュボードエンドポイント確認")
        print("=" * 60)
        
        try:
            # ダッシュボードのルート一覧を取得（簡易版）
            response = requests.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                print("✅ ダッシュボードは稼働中")
            else:
                print(f"❌ ダッシュボード接続エラー: {response.status_code}")
                return False
            
            # 各エンドポイントの存在確認
            test_tracking_id = "test_tracking_id"
            
            endpoints_to_check = [
                f"/track-open/{test_tracking_id}",
                f"/track-beacon/{test_tracking_id}",
                f"/track-css/{test_tracking_id}",
                f"/track-xhr/{test_tracking_id}",
                f"/track-focus/{test_tracking_id}",
                f"/track-unload/{test_tracking_id}",
                f"/track/{test_tracking_id}",
            ]
            
            for endpoint in endpoints_to_check:
                try:
                    url = self.base_url + endpoint
                    response = requests.get(url, timeout=5)
                    
                    if response.status_code in [200, 404, 405]:  # 405 = Method Not Allowed (POSTが必要)
                        print(f"✅ {endpoint} - エンドポイント存在 (ステータス: {response.status_code})")
                    else:
                        print(f"❌ {endpoint} - 予期しないステータス: {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ {endpoint} - エラー: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ ダッシュボード確認エラー: {e}")
            return False
    
    def run(self):
        """メイン実行"""
        print("改善されたトラッキングシステムのデバッグ")
        print("=" * 60)
        print("🎯 目的: なぜ自動追跡が機能していないかを調査")
        print()
        
        # 1. HTMLテンプレートの確認
        template_ok = self.test_html_template_tracking()
        
        # 2. ダッシュボードエンドポイントの確認
        dashboard_ok = self.check_dashboard_endpoints()
        
        # 3. 追跡エンドポイントのテスト
        if dashboard_ok:
            results = self.test_tracking_endpoints()
            
            # 結果サマリー
            print("\n" + "=" * 60)
            print("📊 デバッグ結果サマリー")
            print("=" * 60)
            
            print(f"📧 HTMLテンプレート: {'✅ OK' if template_ok else '❌ NG'}")
            print(f"🌐 ダッシュボード: {'✅ OK' if dashboard_ok else '❌ NG'}")
            
            success_count = sum(1 for r in results if r['success'])
            total_count = len(results)
            
            print(f"🔧 追跡エンドポイント: {success_count}/{total_count} 成功")
            
            for result in results:
                status = "✅" if result['success'] else "❌"
                print(f"   {status} {result['name']}")
            
            # 問題の特定
            print(f"\n🔍 問題の特定:")
            
            if not template_ok:
                print("   ❌ HTMLテンプレートに追跡要素が不足")
            
            if success_count < total_count:
                print("   ❌ 一部の追跡エンドポイントが機能していない")
            
            if template_ok and success_count == total_count:
                print("   🤔 システムは正常だが、実際のメール開封時に追跡されていない")
                print("   💡 可能性:")
                print("      - メールクライアントが画像/JavaScriptをブロック")
                print("      - 実際にはメールが開封されていない")
                print("      - 追跡URLが正しく生成されていない")
        
        return template_ok and dashboard_ok

def main():
    """メイン関数"""
    debugger = TrackingSystemDebugger()
    return debugger.run()

if __name__ == "__main__":
    main()
