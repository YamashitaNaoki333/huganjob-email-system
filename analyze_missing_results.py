#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
送信結果記録の欠落原因分析
送信履歴にあるが送信結果ファイルにない記録を詳細調査
"""

import json
import csv
import pandas as pd
from datetime import datetime
import os

def main():
    print("=" * 60)
    print("🔍 送信結果記録欠落の原因分析")
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
    
    # 送信結果を読み込み
    try:
        df_results = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
        result_ids = set(df_results['企業ID'].tolist())
        print(f"📋 送信結果のユニーク企業ID数: {len(result_ids)}社")
        
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
    
    # 送信結果ファイルの最後の記録時刻を確認
    print(f"\n📅 送信結果ファイルの時刻分析:")
    df_results['送信日時_dt'] = pd.to_datetime(df_results['送信日時'])
    print(f"送信結果の時刻範囲:")
    print(f"  最初: {df_results['送信日時_dt'].min()}")
    print(f"  最後: {df_results['送信日時_dt'].max()}")
    
    # 最後の記録の企業IDを確認
    last_record = df_results.loc[df_results['送信日時_dt'].idxmax()]
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
    
    # 送信プロセスが中断された可能性を調査
    print(f"\n🔍 送信プロセス中断の可能性調査:")
    
    # 送信履歴の時系列順で確認
    history_records = sorted(history['sending_records'], key=lambda x: x['send_time'])
    
    # 送信結果に記録された最後の企業IDの送信時刻を特定
    if result_ids:
        max_result_id = max(result_ids)
        max_result_record = None
        for record in history_records:
            try:
                if int(record['company_id']) == max_result_id:
                    max_result_record = record
                    break
            except:
                continue
        
        if max_result_record:
            print(f"送信結果に記録された最後の企業:")
            print(f"  ID {max_result_record['company_id']}: {max_result_record['company_name']}")
            print(f"  送信時刻: {max_result_record['send_time']}")
            
            # その後の送信履歴を確認
            max_result_time = max_result_record['send_time']
            subsequent_records = [r for r in history_records if r['send_time'] > max_result_time]
            
            if subsequent_records:
                print(f"\nその後の送信履歴: {len(subsequent_records)}件")
                print(f"次の送信: ID {subsequent_records[0]['company_id']} - {subsequent_records[0]['send_time']}")
                print(f"最後の送信: ID {subsequent_records[-1]['company_id']} - {subsequent_records[-1]['send_time']}")
    
    # 送信結果ファイルの書き込みエラーの可能性を調査
    print(f"\n💾 送信結果ファイル書き込み状況:")
    
    # 送信結果の企業IDの連続性を確認
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
                print(f"  ID {start}-{end}")

if __name__ == "__main__":
    main()
