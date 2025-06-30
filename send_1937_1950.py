#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ID 1937-1950の送信実行スクリプト
"""

import requests
import time

def send_huganjob_emails():
    """ダッシュボードAPIを使用してID 1937-1950の送信を実行"""
    
    print("🚀 HUGANJOB ID 1937-1950 送信開始")
    print("=" * 50)
    
    # ダッシュボードAPIエンドポイント
    url = "http://127.0.0.1:5002/api/huganjob/production_send"
    
    # 送信パラメータ
    data = {
        'start_id': 1937,
        'end_id': 1950,
        'email_format': 'html'  # HTMLメール形式
    }
    
    try:
        print(f"📤 送信範囲: ID {data['start_id']} ～ {data['end_id']}")
        print(f"📧 メール形式: {data['email_format']}")
        print(f"🌐 API URL: {url}")
        print()
        
        # API呼び出し
        print("📡 ダッシュボードAPIに送信リクエスト送信中...")
        response = requests.post(url, data=data, timeout=30)
        
        print(f"📊 レスポンスステータス: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 送信リクエスト成功")
            print(f"📋 レスポンス: {result}")
            
            if result.get('success'):
                print(f"🎉 送信プロセス開始成功")
                print(f"🔧 プロセスID: {result.get('process_id', 'N/A')}")
                print(f"📝 メッセージ: {result.get('message', '')}")
                
                # プロセス監視
                print("\n⏳ プロセス実行中... (5分間監視)")
                monitor_process(result.get('process_id'))
                
            else:
                print(f"❌ 送信プロセス開始失敗: {result.get('message', '')}")
                
        else:
            print(f"❌ API呼び出し失敗: {response.status_code}")
            print(f"📄 レスポンス内容: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ API呼び出しタイムアウト")
    except requests.exceptions.ConnectionError:
        print("🔌 ダッシュボードへの接続失敗")
    except Exception as e:
        print(f"❌ エラー: {e}")

def monitor_process(process_id):
    """プロセスの実行状況を監視"""
    
    if not process_id:
        print("⚠️ プロセスIDが取得できませんでした")
        return
    
    print(f"👀 プロセス {process_id} を監視中...")
    
    for i in range(60):  # 5分間監視（5秒間隔）
        try:
            # プロセス状況確認API
            status_url = f"http://127.0.0.1:5002/api/get_active_processes"
            response = requests.get(status_url, timeout=10)
            
            if response.status_code == 200:
                processes = response.json()
                
                # 対象プロセスを検索
                target_process = None
                for proc in processes:
                    if str(proc.get('id')) == str(process_id):
                        target_process = proc
                        break
                
                if target_process:
                    status = target_process.get('status', 'unknown')
                    duration = target_process.get('duration', 'N/A')
                    
                    print(f"📊 プロセス状況: {status} (実行時間: {duration})")
                    
                    if status in ['completed', 'error', 'failed']:
                        print(f"🏁 プロセス終了: {status}")
                        break
                else:
                    print("✅ プロセス完了（アクティブプロセス一覧から削除済み）")
                    break
            
            time.sleep(5)  # 5秒待機
            
        except Exception as e:
            print(f"⚠️ 監視エラー: {e}")
            time.sleep(5)
    
    print("📋 監視完了")

def check_results():
    """送信結果を確認"""
    print("\n📊 送信結果確認")
    print("=" * 30)
    
    try:
        # 送信履歴確認
        import json
        with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        # ID 1937-1950の送信記録を検索
        sent_records = []
        for record in history['sending_records']:
            try:
                company_id = int(record['company_id'])
                if 1937 <= company_id <= 1950:
                    sent_records.append(record)
            except:
                continue
        
        print(f"📤 ID 1937-1950 送信済み: {len(sent_records)}社")
        
        if sent_records:
            print("\n送信詳細:")
            for record in sorted(sent_records, key=lambda x: int(x['company_id'])):
                print(f"  ID {record['company_id']}: {record['company_name']}")
                print(f"    送信時刻: {record['send_time']}")
        
        # 送信結果ファイル確認
        try:
            import pandas as pd
            df = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
            result_records = df[(df['企業ID'] >= 1937) & (df['企業ID'] <= 1950)]
            
            print(f"\n📋 送信結果ファイル: {len(result_records)}件")
            
            if len(result_records) > 0:
                success_count = len(result_records[result_records['送信結果'] == 'success'])
                print(f"   成功: {success_count}件")
                print(f"   失敗: {len(result_records) - success_count}件")
            
        except Exception as e:
            print(f"⚠️ 送信結果ファイル確認エラー: {e}")
        
    except Exception as e:
        print(f"❌ 結果確認エラー: {e}")

def main():
    print("🎯 HUGANJOB ID 1937-1950 HTMLメール送信")
    print("=" * 60)
    
    # 送信実行
    send_huganjob_emails()
    
    # 結果確認
    check_results()
    
    print("\n🎉 送信処理完了")

if __name__ == "__main__":
    main()
