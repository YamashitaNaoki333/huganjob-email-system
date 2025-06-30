#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
送信結果記録の欠落原因分析（修正版）
データ形式の問題を考慮した分析
"""

import json
import csv
import pandas as pd
from datetime import datetime
import os

def main():
    print("=" * 60)
    print("🔍 送信結果記録欠落の原因分析（修正版）")
    print("=" * 60)
    
    # 送信履歴を読み込み
    try:
        with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        print(f"📋 送信履歴総記録数: {len(history['sending_records'])}件")
        
        # 送信履歴の企業IDを抽出
        history_ids = set()
        history_by_id = {}
        for record in history['sending_records']:
            try:
                company_id = int(record['company_id'])
                history_ids.add(company_id)
                history_by_id[company_id] = record
            except:
                continue
        
        print(f"📋 送信履歴のユニーク企業ID数: {len(history_ids)}社")
        
    except Exception as e:
        print(f"❌ 送信履歴読み込みエラー: {e}")
        return
    
    # 送信結果を読み込み（データ形式の問題を考慮）
    try:
        df_results = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
        result_ids = set(df_results['企業ID'].tolist())
        print(f"📋 送信結果のユニーク企業ID数: {len(result_ids)}社")
        
        # 送信日時列の確認
        print(f"📋 送信結果ファイルの列: {list(df_results.columns)}")
        
    except Exception as e:
        print(f"❌ 送信結果読み込みエラー: {e}")
        return
    
    # 送信履歴にあるが送信結果にない企業IDを特定
    missing_from_results = history_ids - result_ids
    print(f"\n🚨 送信履歴にあるが送信結果にない企業ID数: {len(missing_from_results)}社")
    
    if missing_from_results:
        missing_list = sorted(missing_from_results)
        print(f"欠落企業ID範囲: {min(missing_list)} - {max(missing_list)}")
        
        # 欠落パターンを分析
        print(f"\n📊 欠落パターン分析:")
        
        # 連続する範囲を特定
        ranges = []
        start = None
        prev = None
        
        for company_id in missing_list:
            if start is None:
                start = company_id
                prev = company_id
            elif company_id == prev + 1:
                prev = company_id
            else:
                ranges.append((start, prev))
                start = company_id
                prev = company_id
        
        if start is not None:
            ranges.append((start, prev))
        
        print(f"連続する欠落範囲:")
        for start, end in ranges:
            if start == end:
                print(f"  ID {start}")
            else:
                print(f"  ID {start}-{end} ({end-start+1}社)")
        
        # 欠落した記録の送信時刻を分析
        print(f"\n⏰ 欠落記録の送信時刻分析:")
        missing_times = []
        for company_id in missing_list[:10]:  # 最初の10件
            if company_id in history_by_id:
                record = history_by_id[company_id]
                missing_times.append(record['send_time'])
                print(f"  ID {company_id}: {record['send_time']} - {record['company_name']}")
        
        if missing_times:
            print(f"\n送信時刻範囲:")
            print(f"  最初: {min(missing_times)}")
            print(f"  最後: {max(missing_times)}")
    
    # 送信結果ファイルの時刻分析（安全な方法で）
    print(f"\n📅 送信結果ファイルの時刻分析:")
    
    # 送信日時列を手動で解析
    valid_times = []
    for _, row in df_results.iterrows():
        send_time = str(row['送信日時'])
        # 日時形式かチェック
        if len(send_time) > 10 and '-' in send_time and ':' in send_time:
            try:
                dt = pd.to_datetime(send_time)
                valid_times.append(dt)
            except:
                continue
    
    if valid_times:
        print(f"有効な送信日時記録数: {len(valid_times)}件")
        print(f"送信結果の時刻範囲:")
        print(f"  最初: {min(valid_times)}")
        print(f"  最後: {max(valid_times)}")
        
        # 最後の記録の企業IDを確認
        last_time = max(valid_times)
        last_records = df_results[df_results['送信日時'].str.contains(last_time.strftime('%Y-%m-%d %H:%M'), na=False)]
        if len(last_records) > 0:
            last_record = last_records.iloc[-1]
            print(f"最後の送信結果記録: ID {last_record['企業ID']} - {last_record['送信日時']}")
    
    # 送信結果ファイルのサイズと更新時刻を確認
    print(f"\n📁 送信結果ファイル情報:")
    file_path = 'new_email_sending_results.csv'
    if os.path.exists(file_path):
        stat = os.stat(file_path)
        file_size = stat.st_size
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        print(f"ファイルサイズ: {file_size:,} bytes")
        print(f"最終更新時刻: {mod_time}")
    
    # 送信結果の企業IDの連続性を確認
    print(f"\n💾 送信結果の企業ID連続性分析:")
    result_id_list = sorted(result_ids)
    gaps = []
    for i in range(len(result_id_list) - 1):
        current_id = result_id_list[i]
        next_id = result_id_list[i + 1]
        if next_id - current_id > 1:
            gaps.append((current_id + 1, next_id - 1))
    
    if gaps:
        print(f"送信結果の企業IDギャップ:")
        for start, end in gaps[:10]:  # 最初の10個のギャップ
            if start == end:
                print(f"  ID {start}")
            else:
                print(f"  ID {start}-{end} ({end-start+1}社)")
    
    # 最大の企業IDを確認
    max_result_id = max(result_ids) if result_ids else 0
    max_history_id = max(history_ids) if history_ids else 0
    
    print(f"\n📈 企業ID範囲比較:")
    print(f"送信結果の最大企業ID: {max_result_id}")
    print(f"送信履歴の最大企業ID: {max_history_id}")
    
    # ID 1201-1300の詳細分析
    print(f"\n🎯 ID 1201-1300範囲の詳細分析:")
    range_1201_1300 = [i for i in range(1201, 1301)]
    
    in_history = [i for i in range_1201_1300 if i in history_ids]
    in_results = [i for i in range_1201_1300 if i in result_ids]
    
    print(f"ID 1201-1300で送信履歴にある: {len(in_history)}社")
    print(f"ID 1201-1300で送信結果にある: {len(in_results)}社")
    print(f"ID 1201-1300で欠落: {len(in_history) - len(in_results)}社")
    
    if in_results:
        print(f"送信結果にあるID 1201-1300: {in_results}")
    
    # 送信プロセスの中断時刻を推定
    if missing_from_results and history_by_id:
        print(f"\n🕐 送信プロセス中断時刻の推定:")
        
        # 送信結果に記録された最後の企業IDを特定
        if result_ids:
            # 送信結果の最後の企業IDの送信時刻を送信履歴から取得
            last_result_id = max(result_ids)
            if last_result_id in history_by_id:
                last_result_time = history_by_id[last_result_id]['send_time']
                print(f"送信結果に記録された最後の企業: ID {last_result_id}")
                print(f"その送信時刻: {last_result_time}")
                
                # 欠落した最初の企業IDの送信時刻
                first_missing_id = min(missing_from_results)
                if first_missing_id in history_by_id:
                    first_missing_time = history_by_id[first_missing_id]['send_time']
                    print(f"欠落した最初の企業: ID {first_missing_id}")
                    print(f"その送信時刻: {first_missing_time}")
                    
                    # 時刻差を計算
                    try:
                        last_dt = datetime.fromisoformat(last_result_time.replace('T', ' '))
                        first_missing_dt = datetime.fromisoformat(first_missing_time.replace('T', ' '))
                        time_diff = first_missing_dt - last_dt
                        print(f"時刻差: {time_diff}")
                    except:
                        print("時刻差の計算に失敗")

if __name__ == "__main__":
    main()
