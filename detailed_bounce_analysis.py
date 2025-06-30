#!/usr/bin/env python3
"""
詳細なバウンス状態分析スクリプト
現在の状況を正確に把握し、ID6~15を除いて復元が必要な企業を特定
"""

import csv
import re
from datetime import datetime

# 統合送信システムのバウンス履歴リスト（完全版）
BOUNCE_ADDRESSES = [
    'info@sincere.co.jp', 'info@www.advance-1st.co.jp', 'info@www.aoikokuban.co.jp',
    'info@www.crosscorporation.co.jp', 'info@www.flex-og.jp', 'info@www.h2j.jp',
    'info@www.hanei-co.jp', 'info@www.hayashikazuji.co.jp', 'info@www.konishi-mark.com',
    'info@www.koutokudenkou.co.jp', 'info@www.manneken.co.jp', 'info@www.naniwakanri.co.jp',
    'info@www.nikki-tr.co.jp', 'info@www.orientalbakery.co.jp', 'info@www.osakagaigo.ac.jp',
    'info@www.seedassist.co.jp', 'info@www.somax.co.jp', 'info@www.teruteru.co.jp',
    'info@www.tsukitora.com', 'info@www.yoshimoto.co.jp:443',
    # 追加のバウンス企業
    'info@www.aiengineering.jp', 'info@www.kirin-e-s.co.jp', 'info@www.live-create.co.jp',
    'info@www.tenmasamatsushita.co.jp', 'info@www.toray.co.jp', 'info@www.artner.co.jp',
    'info@www.ytv.co.jp', 'info@www.lighting-daiko.co.jp', 'info@www.ksdh.or.jp',
    'info@www.kinryu-foods.co.jp', 'info@www.sanei-yakuhin.co.jp', 'info@www.nissin.com',
    'info@www.rex.co.jp', 'info@www.kk-maekawa.co.jp', 'info@www.askme.co.jp',
    'info@miyakohotels.ne.jp', 'info@hankyu-hanshin-dept.co.jp', 'info@sumitomo-chem.co.jp',
    'info@syusei.ac.jp'
]

def extract_email_from_url(url):
    """URLからメールアドレスを推定"""
    if not url:
        return None
    
    # URLからドメインを抽出
    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
    if not domain_match:
        return None
    
    domain = domain_match.group(1)
    
    # www.を除去
    if domain.startswith('www.'):
        domain = domain[4:]
    
    # ポート番号を除去
    if ':' in domain:
        domain = domain.split(':')[0]
    
    return f"info@{domain}"

def analyze_current_status():
    """現在のCSVファイルの状況を詳細分析"""
    input_file = 'data/new_input_test.csv'
    
    current_bounces = []
    should_be_bounces = []
    id6_15_status = []
    
    with open(input_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader)  # ヘッダーをスキップ
        
        print("📊 CSVファイル詳細分析")
        print("=" * 50)
        
        for row in reader:
            if len(row) < 6:
                continue
                
            try:
                company_id = int(row[0])
                company_name = row[1]
                url = row[2]
                bounce_status = row[5] if len(row) > 5 else ''
                bounce_date = row[6] if len(row) > 6 else ''
                bounce_reason = row[7] if len(row) > 7 else ''
                
                # ID6~15の状況を記録
                if 6 <= company_id <= 15:
                    id6_15_status.append({
                        'id': company_id,
                        'name': company_name,
                        'bounce_status': bounce_status,
                        'url': url
                    })
                
                # 現在バウンス状態の企業
                if bounce_status == 'permanent':
                    current_bounces.append({
                        'id': company_id,
                        'name': company_name,
                        'url': url,
                        'date': bounce_date,
                        'reason': bounce_reason
                    })
                
                # バウンス履歴リストに含まれているかチェック
                estimated_email = extract_email_from_url(url)
                if estimated_email and estimated_email in BOUNCE_ADDRESSES:
                    should_be_bounces.append({
                        'id': company_id,
                        'name': company_name,
                        'url': url,
                        'estimated_email': estimated_email,
                        'current_bounce': bounce_status == 'permanent',
                        'in_id6_15': 6 <= company_id <= 15
                    })
                    
            except (ValueError, IndexError):
                continue
    
    print(f"🔍 現在バウンス状態の企業: {len(current_bounces)}社")
    for company in current_bounces:
        print(f"  ID {company['id']}: {company['name']}")
    
    print(f"\n📋 ID6~15の状況:")
    for company in id6_15_status:
        status = "バウンス" if company['bounce_status'] == 'permanent' else "正常"
        print(f"  ID {company['id']}: {company['name']} - {status}")
    
    print(f"\n🎯 バウンス履歴リストに含まれる企業: {len(should_be_bounces)}社")
    
    # 復元が必要な企業（ID6~15以外でバウンス履歴リストに含まれるが現在バウンス状態でない）
    need_restore = []
    for company in should_be_bounces:
        if not company['in_id6_15'] and not company['current_bounce']:
            need_restore.append(company)
    
    print(f"\n⚠️  復元が必要な企業: {len(need_restore)}社")
    for company in need_restore:
        print(f"  ID {company['id']}: {company['name']} - {company['estimated_email']}")
    
    return {
        'current_bounces': current_bounces,
        'should_be_bounces': should_be_bounces,
        'need_restore': need_restore,
        'id6_15_status': id6_15_status
    }

def restore_bounce_companies(need_restore):
    """バウンス企業を復元"""
    input_file = 'data/new_input_test.csv'
    output_file = 'data/new_input_test_fixed.csv'
    
    restored_count = 0
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        # ヘッダー行をコピー
        header = next(reader)
        writer.writerow(header)
        
        for row in reader:
            if len(row) < 8:
                # 行が短い場合は8列に拡張
                while len(row) < 8:
                    row.append('')
            
            try:
                company_id = int(row[0])
                
                # 復元が必要な企業かチェック
                for company in need_restore:
                    if company['id'] == company_id:
                        # バウンス状態を復元
                        row[5] = 'permanent'
                        row[6] = '2025-06-23 17:10:00'
                        row[7] = 'Restored from bounce history list'
                        restored_count += 1
                        print(f"✅ 復元: ID {company_id} - {company['name']}")
                        break
                
                writer.writerow(row)
                
            except (ValueError, IndexError):
                writer.writerow(row)
    
    print(f"\n🎯 復元完了: {restored_count}社")
    return restored_count

if __name__ == "__main__":
    print("🔍 バウンス状態詳細分析を開始します...")
    analysis = analyze_current_status()
    
    if analysis['need_restore']:
        print(f"\n📝 {len(analysis['need_restore'])}社の復元を実行します...")
        restored = restore_bounce_companies(analysis['need_restore'])
        print(f"\n✅ 復元作業完了: {restored}社を復元しました")
        print("\n📁 修正されたファイル: data/new_input_test_fixed.csv")
        print("💡 次のステップ: 修正されたファイルを元のファイルに置き換えてください")
    else:
        print("\n✅ 復元が必要な企業はありません")
