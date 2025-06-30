#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
バックアップファイルでID 1201-1296の記録を検索
"""

import pandas as pd
import glob
import os

def main():
    print("=" * 60)
    print("📂 送信結果バックアップファイルでID 1201-1296を検索")
    print("=" * 60)
    
    # バックアップファイルを検索
    backup_patterns = [
        '*email_sending_results*.csv',
        '*backup*.csv',
        '*sending_results*.csv',
        'huganjob_sending_results*.csv'
    ]
    
    backup_files = []
    for pattern in backup_patterns:
        backup_files.extend(glob.glob(pattern))
    
    # 重複を除去
    backup_files = list(set(backup_files))
    
    print(f"検索対象ファイル数: {len(backup_files)}件")
    
    found_files = []
    
    for file_path in backup_files:
        if not os.path.exists(file_path):
            continue
            
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            
            if '企業ID' in df.columns:
                range_records = df[(df['企業ID'] >= 1201) & (df['企業ID'] <= 1296)]
                
                if len(range_records) > 0:
                    print(f"\n✅ {file_path}: {len(range_records)}件")
                    found_files.append((file_path, len(range_records)))
                    
                    # ファイル情報
                    stat = os.stat(file_path)
                    file_size = stat.st_size
                    mod_time = pd.to_datetime(stat.st_mtime, unit='s')
                    print(f"   ファイルサイズ: {file_size:,} bytes")
                    print(f"   最終更新: {mod_time}")
                    
                    # 最初の5件を表示
                    print(f"   最初の5件:")
                    for _, record in range_records.head(5).iterrows():
                        company_name = record.get('企業名', 'N/A')
                        send_time = record.get('送信日時', 'N/A')
                        print(f"     ID {record['企業ID']}: {company_name} - {send_time}")
                else:
                    print(f"❌ {file_path}: 0件")
            else:
                print(f"⚠️ {file_path}: 企業ID列なし")
                
        except Exception as e:
            print(f"⚠️ {file_path}: エラー - {e}")
    
    if found_files:
        print(f"\n📋 ID 1201-1296の記録が見つかったファイル:")
        for file_path, count in found_files:
            print(f"  {file_path}: {count}件")
        
        # 最も多くの記録があるファイルを特定
        best_file = max(found_files, key=lambda x: x[1])
        print(f"\n🎯 最も多くの記録があるファイル: {best_file[0]} ({best_file[1]}件)")
        
        # そのファイルの詳細分析
        try:
            df_best = pd.read_csv(best_file[0], encoding='utf-8-sig')
            range_records = df_best[(df_best['企業ID'] >= 1201) & (df_best['企業ID'] <= 1296)]
            
            print(f"\n📊 {best_file[0]}の詳細分析:")
            print(f"   ID範囲: {range_records['企業ID'].min()} - {range_records['企業ID'].max()}")
            
            if '送信結果' in range_records.columns:
                result_counts = range_records['送信結果'].value_counts()
                print(f"   送信結果:")
                for result, count in result_counts.items():
                    print(f"     {result}: {count}件")
            
            if '送信日時' in range_records.columns:
                # 送信日時の範囲
                valid_times = []
                for send_time in range_records['送信日時']:
                    try:
                        if pd.notna(send_time) and len(str(send_time)) > 10:
                            dt = pd.to_datetime(send_time)
                            valid_times.append(dt)
                    except:
                        continue
                
                if valid_times:
                    print(f"   送信時刻範囲:")
                    print(f"     最初: {min(valid_times)}")
                    print(f"     最後: {max(valid_times)}")
        
        except Exception as e:
            print(f"詳細分析エラー: {e}")
    
    else:
        print(f"\n❌ ID 1201-1296の記録が見つかったバックアップファイルはありません")
        
        # メインファイルとの比較
        print(f"\n🔍 メインファイルとの比較:")
        try:
            df_main = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
            main_ids = set(df_main['企業ID'].tolist())
            
            print(f"メインファイルの企業ID数: {len(main_ids)}")
            print(f"メインファイルの最小ID: {min(main_ids)}")
            print(f"メインファイルの最大ID: {max(main_ids)}")
            
            # ID 1200と1297の記録を確認
            id_1200 = df_main[df_main['企業ID'] == 1200]
            id_1297 = df_main[df_main['企業ID'] == 1297]
            
            if len(id_1200) > 0:
                print(f"ID 1200の記録: あり - {id_1200.iloc[0]['送信日時']}")
            else:
                print(f"ID 1200の記録: なし")
                
            if len(id_1297) > 0:
                print(f"ID 1297の記録: あり - {id_1297.iloc[0]['送信日時']}")
            else:
                print(f"ID 1297の記録: なし")
        
        except Exception as e:
            print(f"メインファイル分析エラー: {e}")

if __name__ == "__main__":
    main()
