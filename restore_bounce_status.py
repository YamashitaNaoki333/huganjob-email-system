#!/usr/bin/env python3
"""
バウンス状態復元スクリプト
ID6~15以外の企業で、バウンス履歴リストに含まれているが現在バウンス状態になっていない企業を復元
"""

import csv
import re
from datetime import datetime

# バウンス履歴リスト（統合送信システムから）
BOUNCE_ADDRESSES = [
    'info@sincere.co.jp', 'info@www.advance-1st.co.jp', 'info@www.aoikokuban.co.jp',
    'info@www.crosscorporation.co.jp', 'info@www.flex-og.jp', 'info@www.h2j.jp',
    'info@www.hanei-co.jp', 'info@www.hayashikazuji.co.jp', 'info@www.konishi-mark.com',
    'info@www.koutokudenkou.co.jp', 'info@www.manneken.co.jp', 'info@www.naniwakanri.co.jp',
    'info@www.nikki-tr.co.jp', 'info@www.orientalbakery.co.jp', 'info@www.osakagaigo.ac.jp',
    'info@www.seedassist.co.jp', 'info@www.somax.co.jp', 'info@www.teruteru.co.jp',
    'info@www.tsukitora.com', 'info@www.yoshimoto.co.jp:443',
    # ID 30-150範囲の追加バウンス企業
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

def should_restore_bounce(company_id, url, current_bounce_status):
    """バウンス状態を復元すべきかどうかを判定"""
    # ID6~15は今回の処理結果を維持
    if 6 <= company_id <= 15:
        return False
    
    # 既にバウンス状態の企業はスキップ
    if current_bounce_status and current_bounce_status.strip():
        return False
    
    # URLからメールアドレスを推定
    estimated_email = extract_email_from_url(url)
    if not estimated_email:
        return False
    
    # バウンス履歴リストに含まれているかチェック
    return estimated_email in BOUNCE_ADDRESSES

def restore_bounce_status():
    """バウンス状態を復元"""
    input_file = 'data/new_input_test.csv'
    output_file = 'data/new_input_test_restored.csv'
    
    restored_companies = []
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        # ヘッダー行をコピー
        header = next(reader)
        writer.writerow(header)
        
        for row in reader:
            if len(row) < 7:
                writer.writerow(row)
                continue
            
            try:
                company_id = int(row[0])
                company_name = row[1]
                url = row[2]
                current_bounce_status = row[5] if len(row) > 5 else ''
                
                # バウンス状態を復元すべきかチェック
                if should_restore_bounce(company_id, url, current_bounce_status):
                    # バウンス状態を復元
                    row[5] = 'permanent'
                    row[6] = '2025-06-23 16:02:11'
                    row[7] = 'Restored from bounce history list'
                    
                    restored_companies.append({
                        'id': company_id,
                        'name': company_name,
                        'url': url,
                        'estimated_email': extract_email_from_url(url)
                    })
                    
                    print(f"復元: ID {company_id} - {company_name}")
                
                writer.writerow(row)
                
            except (ValueError, IndexError) as e:
                # IDが数値でない場合やデータが不完全な場合はそのまま出力
                writer.writerow(row)
    
    print(f"\n復元完了: {len(restored_companies)}社のバウンス状態を復元しました")
    
    # 復元された企業の詳細を表示
    if restored_companies:
        print("\n復元された企業:")
        for company in restored_companies:
            print(f"  ID {company['id']}: {company['name']} - {company['estimated_email']}")
    
    return len(restored_companies)

if __name__ == "__main__":
    restored_count = restore_bounce_status()
    print(f"\n総復元企業数: {restored_count}社")
