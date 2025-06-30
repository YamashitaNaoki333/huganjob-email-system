#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ダッシュボードキャッシュ強制リフレッシュツール

送信記録復旧後にダッシュボードのキャッシュを強制的にクリアして、
最新のCSVデータを反映させます。
"""

import requests
import time
import json

def force_refresh_dashboard_cache():
    """ダッシュボードキャッシュを強制リフレッシュ"""
    
    print("🔄 ダッシュボードキャッシュ強制リフレッシュ")
    print("=" * 60)
    
    dashboard_url = "http://127.0.0.1:5002"
    
    # 1. 全キャッシュクリア
    print("1️⃣ 全キャッシュクリア実行中...")
    try:
        response = requests.post(f"{dashboard_url}/api/refresh", timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 全キャッシュクリア成功: {result.get('message', 'OK')}")
        else:
            print(f"   ⚠️ 全キャッシュクリア失敗: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ 全キャッシュクリアエラー: {e}")
    
    # 2. データ再読み込み
    print("\n2️⃣ データ再読み込み実行中...")
    try:
        response = requests.post(f"{dashboard_url}/api/refresh_data", timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ データ再読み込み成功: {result.get('message', 'OK')}")
        else:
            print(f"   ⚠️ データ再読み込み失敗: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ データ再読み込みエラー: {e}")
    
    # 3. 少し待機
    print("\n3️⃣ キャッシュ更新待機中...")
    time.sleep(3)
    
    # 4. 企業一覧ページにアクセスして更新を確認
    print("\n4️⃣ 企業一覧ページアクセステスト...")
    try:
        response = requests.get(f"{dashboard_url}/companies?page=20&filter=all", timeout=30)
        if response.status_code == 200:
            print("   ✅ 企業一覧ページアクセス成功")
            
            # ID 1971-1975の表示確認
            content = response.text
            if "医療法人徳洲会" in content and "info@yamauchi.or.jp" in content:
                print("   🎉 ID 1971 (医療法人徳洲会) の送信記録が表示されています！")
            else:
                print("   ⚠️ ID 1971の送信記録がまだ表示されていません")
                
            if "山崎金属産業株式会社" in content and "info@yamakin.co.jp" in content:
                print("   🎉 ID 1973 (山崎金属産業株式会社) の送信記録が表示されています！")
            else:
                print("   ⚠️ ID 1973の送信記録がまだ表示されていません")
                
        else:
            print(f"   ⚠️ 企業一覧ページアクセス失敗: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ 企業一覧ページアクセスエラー: {e}")
    
    print("\n🎯 キャッシュリフレッシュ完了")
    print("   ブラウザでダッシュボードを更新して確認してください")
    print(f"   URL: {dashboard_url}/companies?page=20&filter=all")

def check_dashboard_status():
    """ダッシュボードの状態確認"""
    
    print("\n📊 ダッシュボード状態確認")
    print("-" * 30)
    
    try:
        response = requests.get("http://127.0.0.1:5002/", timeout=10)
        if response.status_code == 200:
            print("✅ ダッシュボードは正常に動作中")
            return True
        else:
            print(f"⚠️ ダッシュボードエラー: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ダッシュボード接続エラー: {e}")
        return False

def main():
    """メイン実行関数"""
    
    print("🚀 HUGANJOBダッシュボード キャッシュ強制リフレッシュツール")
    print("   送信記録復旧後のキャッシュ更新を実行します")
    print()
    
    # ダッシュボード状態確認
    if not check_dashboard_status():
        print("❌ ダッシュボードが動作していません。先にダッシュボードを起動してください。")
        return
    
    # キャッシュリフレッシュ実行
    force_refresh_dashboard_cache()

if __name__ == "__main__":
    main()
