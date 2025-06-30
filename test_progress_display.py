#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB進行状況表示機能テストスクリプト
"""

import requests
import json
import time

def test_progress_api():
    """進行状況APIをテスト"""
    
    print("🧪 HUGANJOB進行状況表示機能テスト")
    print("=" * 50)
    
    # 1. 進行状況API確認
    print("📊 1. 進行状況API確認")
    try:
        response = requests.get('http://127.0.0.1:5002/api/huganjob/progress', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API応答成功")
            print(f"   アクティブプロセス数: {data.get('active_processes', 0)}")
            print(f"   プロセス詳細: {len(data.get('processes', []))}件")
            
            if data.get('processes'):
                for i, process in enumerate(data['processes']):
                    print(f"   プロセス{i+1}: {process.get('status', 'unknown')}")
                    progress = process.get('progress', {})
                    if progress.get('type') == 'huganjob_unified_sender':
                        print(f"     進行率: {progress.get('progress_percent', 0)}%")
                        print(f"     処理済み: {progress.get('processed_companies', 0)}/{progress.get('total_companies', 0)}")
            else:
                print("   📝 現在アクティブなプロセスはありません")
        else:
            print(f"❌ API応答エラー: {response.status_code}")
    except Exception as e:
        print(f"❌ API接続エラー: {e}")
    
    # 2. アクティブプロセスAPI確認
    print("\n📋 2. アクティブプロセスAPI確認")
    try:
        response = requests.get('http://127.0.0.1:5002/api/huganjob/active_processes', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API応答成功")
            print(f"   アクティブプロセス数: {data.get('count', 0)}")
            
            if data.get('processes'):
                for process in data['processes']:
                    print(f"   プロセスID: {process.get('process_id')}")
                    print(f"   コマンド: {process.get('command', '')[:50]}...")
                    print(f"   状況: {process.get('status')}")
                    print(f"   実行時間: {process.get('duration')}")
            else:
                print("   📝 現在アクティブなプロセスはありません")
        else:
            print(f"❌ API応答エラー: {response.status_code}")
    except Exception as e:
        print(f"❌ API接続エラー: {e}")
    
    # 3. ダッシュボードメインページ確認
    print("\n🌐 3. ダッシュボードメインページ確認")
    try:
        response = requests.get('http://127.0.0.1:5002/', timeout=10)
        if response.status_code == 200:
            print(f"✅ メインページ正常表示")
            print(f"   レスポンスサイズ: {len(response.text)}文字")
            
            # 進行状況表示要素の確認
            if 'progressCard' in response.text:
                print(f"   ✅ 進行状況カード要素が存在")
            else:
                print(f"   ❌ 進行状況カード要素が見つかりません")
                
            if 'updateProgress' in response.text:
                print(f"   ✅ 進行状況更新JavaScript関数が存在")
            else:
                print(f"   ❌ 進行状況更新JavaScript関数が見つかりません")
        else:
            print(f"❌ メインページエラー: {response.status_code}")
    except Exception as e:
        print(f"❌ メインページ接続エラー: {e}")
    
    print("\n🎯 テスト完了")
    print("💡 ダッシュボードで進行状況表示機能を確認してください")
    print("🌐 http://127.0.0.1:5002/")

if __name__ == "__main__":
    test_progress_api()
