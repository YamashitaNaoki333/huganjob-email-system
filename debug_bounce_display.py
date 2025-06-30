#!/usr/bin/env python3
"""
バウンス表示問題デバッグスクリプト
ダッシュボードと同じロジックでバウンス状態を確認
"""

import pandas as pd
import os

def debug_bounce_status():
    """ダッシュボードと同じロジックでバウンス状態をデバッグ"""
    
    print("🔍 バウンス状態デバッグ開始")
    print("=" * 50)
    
    # CSVファイルを読み込み
    csv_file = 'data/new_input_test.csv'
    if not os.path.exists(csv_file):
        print(f"❌ CSVファイルが見つかりません: {csv_file}")
        return
    
    print(f"📁 CSVファイル読み込み: {csv_file}")
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    
    print(f"📊 総行数: {len(df)}")
    print(f"📊 列数: {len(df.columns)}")
    print(f"📊 列名: {list(df.columns)}")
    print()
    
    # ダッシュボードと同じロジックでバウンス状態をチェック
    bounce_companies = []
    total_companies = 0
    
    for idx, row in df.iterrows():
        try:
            company_id = int(row.iloc[0])
            company_name = str(row.iloc[1]).strip()
            
            # ダッシュボードと同じロジック
            bounce_status = row.iloc[5] if len(row) > 5 and pd.notna(row.iloc[5]) else ''
            bounce_date = row.iloc[6] if len(row) > 6 and pd.notna(row.iloc[6]) else ''
            bounce_reason = row.iloc[7] if len(row) > 7 and pd.notna(row.iloc[7]) else ''
            
            # 文字列として処理
            bounce_status = str(bounce_status).strip() if bounce_status else ''
            bounce_date = str(bounce_date).strip() if bounce_date else ''
            bounce_reason = str(bounce_reason).strip() if bounce_reason else ''
            
            # バウンス判定
            is_bounced = bounce_status == 'permanent'
            
            total_companies += 1
            
            if is_bounced:
                bounce_companies.append({
                    'id': company_id,
                    'name': company_name,
                    'bounce_status': bounce_status,
                    'bounce_date': bounce_date,
                    'bounce_reason': bounce_reason,
                    'raw_status': repr(row.iloc[5]) if len(row) > 5 else 'None'
                })
                
                # 最初の10社と最後の10社を詳細表示
                if len(bounce_companies) <= 10 or len(bounce_companies) > len(bounce_companies) - 10:
                    print(f"🚫 バウンス企業発見: ID {company_id} - {company_name}")
                    print(f"   ステータス: '{bounce_status}' (raw: {repr(row.iloc[5])})")
                    print(f"   日時: '{bounce_date}'")
                    print(f"   理由: '{bounce_reason}'")
                    print()
            
        except Exception as e:
            print(f"⚠️  行 {idx} 処理エラー: {e}")
            continue
    
    print(f"📈 処理結果:")
    print(f"  総企業数: {total_companies}")
    print(f"  バウンス企業数: {len(bounce_companies)}")
    print(f"  バウンス率: {len(bounce_companies) / total_companies * 100:.1f}%")
    print()
    
    # ID6~15の状況確認
    print(f"🎯 ID6~15の状況:")
    for company in bounce_companies:
        if 6 <= company['id'] <= 15:
            print(f"  ID {company['id']}: {company['name']} - {company['bounce_status']}")
    
    # バウンス企業の分布確認
    if bounce_companies:
        print(f"\n📊 バウンス企業ID分布:")
        id_ranges = {
            '1-50': 0,
            '51-100': 0,
            '101-500': 0,
            '501-1000': 0,
            '1001+': 0
        }
        
        for company in bounce_companies:
            company_id = company['id']
            if company_id <= 50:
                id_ranges['1-50'] += 1
            elif company_id <= 100:
                id_ranges['51-100'] += 1
            elif company_id <= 500:
                id_ranges['101-500'] += 1
            elif company_id <= 1000:
                id_ranges['501-1000'] += 1
            else:
                id_ranges['1001+'] += 1
        
        for range_name, count in id_ranges.items():
            print(f"  {range_name}: {count}社")
    
    return bounce_companies

def create_simple_bounce_test():
    """シンプルなバウンス状態テストファイルを作成"""
    print("\n🔧 シンプルなバウンス状態テストファイルを作成します...")
    
    # 元のCSVファイルを読み込み
    df = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
    
    # 最初の20行のみを抽出してテスト
    test_df = df.head(20).copy()
    
    # 明示的にバウンス状態を設定
    test_df.iloc[1, 5] = 'permanent'  # ID 2
    test_df.iloc[7, 5] = 'permanent'  # ID 8
    test_df.iloc[9, 5] = 'permanent'  # ID 10
    test_df.iloc[10, 5] = 'permanent' # ID 11
    
    # バウンス日時と理由も設定
    for idx in [1, 7, 9, 10]:
        test_df.iloc[idx, 6] = '2025-06-23 17:20:00'
        test_df.iloc[idx, 7] = 'Test bounce status'
    
    # テストファイルとして保存
    test_file = 'data/bounce_test.csv'
    test_df.to_csv(test_file, index=False, encoding='utf-8-sig')
    
    print(f"✅ テストファイル作成完了: {test_file}")
    print(f"📊 テストデータ: {len(test_df)}社（うち4社がバウンス状態）")
    
    return test_file

if __name__ == "__main__":
    # 現在の状況をデバッグ
    bounce_companies = debug_bounce_status()
    
    # シンプルなテストファイルを作成
    test_file = create_simple_bounce_test()
    
    print(f"\n💡 次のステップ:")
    print(f"1. テストファイル {test_file} でダッシュボードをテスト")
    print(f"2. ダッシュボードの設定を一時的に変更してテストファイルを使用")
    print(f"3. バウンス表示が正しく動作するか確認")
