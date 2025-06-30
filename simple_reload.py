#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
シンプルなダッシュボードデータ再読み込み
"""

import requests
import json

def main():
    print("🔄 ダッシュボードデータ再読み込み")
    
    try:
        url = "http://127.0.0.1:5002/api/reload_data"
        print(f"📡 API呼び出し: {url}")
        
        response = requests.post(url, timeout=30)
        print(f"📊 ステータス: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 成功")
            print(f"結果: {result}")
        else:
            print(f"❌ 失敗: {response.text}")
            
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    main()
