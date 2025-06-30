#!/usr/bin/env python3
"""
包括的バウンス状態復元スクリプト
ID6~15を除いて、バウンス履歴リストに基づいて全てのバウンス企業を復元
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
    # 追加のバウンス企業（ID30以降）
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

def comprehensive_restore():
    """包括的バウンス状態復元"""
    input_file = 'data/new_input_test.csv'
    output_file = 'data/new_input_test_comprehensive.csv'
    
    restored_companies = []
    current_bounces = []
    
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
                company_name = row[1]
                url = row[2]
                current_bounce_status = row[5] if len(row) > 5 else ''
                
                # ID6~15は現在の状態を維持
                if 6 <= company_id <= 15:
                    if current_bounce_status == 'permanent':
                        current_bounces.append({
                            'id': company_id,
                            'name': company_name,
                            'status': 'maintained'
                        })
                    writer.writerow(row)
                    continue
                
                # URLからメールアドレスを推定
                estimated_email = extract_email_from_url(url)
                
                # バウンス履歴リストに含まれているかチェック
                if estimated_email and estimated_email in BOUNCE_ADDRESSES:
                    # バウンス状態を設定
                    row[5] = 'permanent'
                    row[6] = '2025-06-23 17:15:00'
                    row[7] = 'Comprehensive restore from bounce history'
                    
                    restored_companies.append({
                        'id': company_id,
                        'name': company_name,
                        'url': url,
                        'estimated_email': estimated_email,
                        'previous_status': current_bounce_status
                    })
                    
                    print(f"✅ 復元: ID {company_id} - {company_name} ({estimated_email})")
                
                writer.writerow(row)
                
            except (ValueError, IndexError) as e:
                # IDが数値でない場合やデータが不完全な場合はそのまま出力
                writer.writerow(row)
    
    print(f"\n📊 復元作業完了:")
    print(f"  新規復元企業数: {len(restored_companies)}社")
    print(f"  ID6~15維持企業数: {len(current_bounces)}社")
    
    # 復元された企業の詳細を表示
    if restored_companies:
        print(f"\n🔄 新規復元された企業:")
        for company in restored_companies:
            status = f"({company['previous_status']}→permanent)" if company['previous_status'] else "(新規)"
            print(f"  ID {company['id']}: {company['name']} {status}")
    
    # ID6~15の維持状況
    if current_bounces:
        print(f"\n✅ ID6~15の維持されたバウンス企業:")
        for company in current_bounces:
            print(f"  ID {company['id']}: {company['name']}")
    
    return len(restored_companies)

def verify_restoration():
    """復元結果を検証"""
    file_path = 'data/new_input_test_comprehensive.csv'
    
    total_companies = 0
    bounce_companies = 0
    id6_15_bounces = 0
    
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader)  # ヘッダーをスキップ
        
        for row in reader:
            if len(row) < 6:
                continue
                
            try:
                company_id = int(row[0])
                bounce_status = row[5] if len(row) > 5 else ''
                
                total_companies += 1
                
                if bounce_status == 'permanent':
                    bounce_companies += 1
                    if 6 <= company_id <= 15:
                        id6_15_bounces += 1
                        
            except (ValueError, IndexError):
                continue
    
    print(f"\n📈 復元結果検証:")
    print(f"  総企業数: {total_companies}")
    print(f"  バウンス企業数: {bounce_companies}")
    print(f"  ID6~15のバウンス企業数: {id6_15_bounces}")
    print(f"  バウンス率: {bounce_companies / total_companies * 100:.1f}%")
    
    return bounce_companies

if __name__ == "__main__":
    print("🔧 包括的バウンス状態復元を開始します...")
    
    # 復元実行
    restored_count = comprehensive_restore()
    
    # 結果検証
    total_bounces = verify_restoration()
    
    print(f"\n🎯 最終結果:")
    print(f"  復元企業数: {restored_count}社")
    print(f"  総バウンス企業数: {total_bounces}社")
    print(f"\n📁 復元されたファイル: data/new_input_test_comprehensive.csv")
    print(f"💡 次のステップ: 復元されたファイルを元のファイルに置き換えてください")
    print(f"   コマンド: cp data/new_input_test_comprehensive.csv data/new_input_test.csv")
