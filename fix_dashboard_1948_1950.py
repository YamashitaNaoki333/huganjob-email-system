#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ID 1948-1950 ダッシュボード表示修正スクリプト
"""

import requests
import json
import time

def reload_dashboard_data():
    """ダッシュボードデータを強制再読み込み"""
    print("🔄 ダッシュボードデータ再読み込み実行")
    print("=" * 50)
    
    try:
        # データ再読み込みAPI呼び出し
        reload_url = "http://127.0.0.1:5002/api/reload_data"
        
        print(f"📡 API呼び出し: {reload_url}")
        response = requests.post(reload_url, timeout=60)
        
        print(f"📊 レスポンスステータス: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ データ再読み込み成功")
            print(f"📋 結果: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ データ再読み込み失敗: {response.status_code}")
            print(f"📄 レスポンス: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ API呼び出しタイムアウト")
        return False
    except requests.exceptions.ConnectionError:
        print("🔌 ダッシュボードへの接続失敗")
        return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def check_company_details():
    """ID 1948-1950の企業詳細をAPI経由で確認"""
    print("\n🔍 企業詳細API確認")
    print("=" * 50)
    
    target_ids = [1948, 1949, 1950]
    
    for company_id in target_ids:
        try:
            detail_url = f"http://127.0.0.1:5002/api/company_detail/{company_id}"
            
            print(f"\n📤 企業詳細取得: ID {company_id}")
            response = requests.get(detail_url, timeout=30)
            
            if response.status_code == 200:
                company_data = response.json()
                print(f"✅ ID {company_id}: {company_data.get('name', 'N/A')}")
                print(f"   メール: {company_data.get('email', 'N/A')}")
                print(f"   送信状況: {company_data.get('email_sent', False)}")
                print(f"   送信日時: {company_data.get('sent_date', 'N/A')}")
                print(f"   送信システム: {company_data.get('sending_system', 'N/A')}")
            else:
                print(f"❌ ID {company_id}: API呼び出し失敗 ({response.status_code})")
                
        except Exception as e:
            print(f"❌ ID {company_id}: エラー - {e}")

def force_update_company_status():
    """ID 1948-1950の送信状況を強制更新"""
    print("\n🔧 送信状況強制更新")
    print("=" * 50)
    
    # 送信記録データ
    companies_data = [
        {
            'id': 1948,
            'name': '株式会社ミック',
            'email': 'oonishi@mctv.ne.jp',
            'sent_time': '2025-06-25T19:11:50.507000'
        },
        {
            'id': 1949,
            'name': '株式会社マルイチ',
            'email': 'somu@ma-ru-i-chi.co.jp',
            'sent_time': '2025-06-25T19:11:55.735618'
        },
        {
            'id': 1950,
            'name': 'ブリンクスジャパン株式会社',
            'email': 'hr.japan@brinks.com',
            'sent_time': '2025-06-25T19:12:00.926761'
        }
    ]
    
    for company in companies_data:
        try:
            # 企業状況更新API（存在する場合）
            update_url = f"http://127.0.0.1:5002/api/update_company_status"
            
            update_data = {
                'company_id': company['id'],
                'email_sent': True,
                'sent_date': company['sent_time'],
                'sending_system': 'huganjob_unified'
            }
            
            print(f"📤 状況更新: ID {company['id']} - {company['name']}")
            response = requests.post(update_url, json=update_data, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ ID {company['id']}: 状況更新成功")
            else:
                print(f"⚠️ ID {company['id']}: 更新API未対応 ({response.status_code})")
                
        except Exception as e:
            print(f"⚠️ ID {company['id']}: 更新エラー - {e}")

def clear_dashboard_cache():
    """ダッシュボードキャッシュをクリア"""
    print("\n🧹 キャッシュクリア")
    print("=" * 50)
    
    try:
        cache_clear_url = "http://127.0.0.1:5002/api/clear_cache"
        
        print(f"📡 キャッシュクリア実行: {cache_clear_url}")
        response = requests.post(cache_clear_url, timeout=30)
        
        if response.status_code == 200:
            print("✅ キャッシュクリア成功")
        else:
            print(f"⚠️ キャッシュクリアAPI未対応 ({response.status_code})")
            
    except Exception as e:
        print(f"⚠️ キャッシュクリアエラー: {e}")

def verify_fix():
    """修正結果を確認"""
    print("\n✅ 修正結果確認")
    print("=" * 50)
    
    print("📋 確認手順:")
    print("1. ブラウザでダッシュボードを再読み込み")
    print("2. 企業一覧ページ (http://127.0.0.1:5002/companies) にアクセス")
    print("3. ID 1948-1950の企業の送信状況を確認")
    print()
    print("期待される表示:")
    print("- ID 1948: 株式会社ミック - 送信済み (2025-06-25 19:11:50)")
    print("- ID 1949: 株式会社マルイチ - 送信済み (2025-06-25 19:11:55)")
    print("- ID 1950: ブリンクスジャパン株式会社 - 送信済み (2025-06-25 19:12:00)")

def main():
    print("🔧 HUGANJOB ID 1948-1950 ダッシュボード表示修正")
    print("=" * 80)
    
    # 1. ダッシュボードデータ再読み込み
    success = reload_dashboard_data()
    
    if success:
        print("\n⏳ 5秒待機...")
        time.sleep(5)
        
        # 2. 企業詳細確認
        check_company_details()
        
        # 3. キャッシュクリア
        clear_dashboard_cache()
        
        # 4. 強制更新（必要に応じて）
        force_update_company_status()
        
        print("\n⏳ 3秒待機...")
        time.sleep(3)
        
        # 5. 最終確認
        check_company_details()
    
    # 6. 修正結果確認手順
    verify_fix()
    
    print("\n🎉 修正処理完了")

if __name__ == "__main__":
    main()
