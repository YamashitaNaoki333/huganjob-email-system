#!/usr/bin/env python3
"""
CSVファイルのバウンス状態確認スクリプト
"""

import csv

def check_bounce_status():
    """CSVファイル内のバウンス状態を確認"""
    input_file = 'data/new_input_test.csv'
    
    total_companies = 0
    permanent_bounces = 0
    success_companies = 0
    other_status = 0
    
    bounce_companies = []
    success_companies_list = []
    
    with open(input_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader)  # ヘッダーをスキップ
        
        print("CSVファイルのヘッダー:")
        for i, col in enumerate(header):
            print(f"  {i}: {col}")
        print()
        
        for row in reader:
            if len(row) < 6:
                continue
                
            try:
                company_id = int(row[0])
                company_name = row[1]
                email_status = row[5] if len(row) > 5 else ''
                
                total_companies += 1
                
                if email_status == 'permanent':
                    permanent_bounces += 1
                    bounce_companies.append({
                        'id': company_id,
                        'name': company_name,
                        'status': email_status,
                        'date': row[6] if len(row) > 6 else '',
                        'reason': row[7] if len(row) > 7 else ''
                    })
                elif email_status == 'success':
                    success_companies += 1
                    if 6 <= company_id <= 15:  # ID6~15の企業をチェック
                        success_companies_list.append({
                            'id': company_id,
                            'name': company_name,
                            'status': email_status
                        })
                else:
                    other_status += 1
                    
            except (ValueError, IndexError):
                continue
    
    print(f"📊 CSVファイル分析結果:")
    print(f"  総企業数: {total_companies}")
    print(f"  バウンス企業数 (permanent): {permanent_bounces}")
    print(f"  送信成功企業数 (success): {success_companies}")
    print(f"  その他のステータス: {other_status}")
    print()
    
    print(f"🚫 バウンス企業一覧 (最初の10社):")
    for i, company in enumerate(bounce_companies[:10]):
        print(f"  ID {company['id']}: {company['name']} - {company['status']}")
        if company['reason']:
            print(f"    理由: {company['reason']}")
    
    if len(bounce_companies) > 10:
        print(f"  ... 他 {len(bounce_companies) - 10}社")
    print()
    
    print(f"✅ ID6~15の送信成功企業:")
    for company in success_companies_list:
        print(f"  ID {company['id']}: {company['name']} - {company['status']}")
    print()
    
    # ID6~15のバウンス企業もチェック
    id6_15_bounces = [c for c in bounce_companies if 6 <= c['id'] <= 15]
    if id6_15_bounces:
        print(f"🚫 ID6~15のバウンス企業:")
        for company in id6_15_bounces:
            print(f"  ID {company['id']}: {company['name']} - {company['status']}")
    
    return {
        'total': total_companies,
        'permanent_bounces': permanent_bounces,
        'success': success_companies,
        'other': other_status,
        'bounce_list': bounce_companies
    }

if __name__ == "__main__":
    result = check_bounce_status()
    print(f"\n📈 サマリー:")
    print(f"  バウンス率: {result['permanent_bounces'] / result['total'] * 100:.1f}%")
    print(f"  送信成功率: {result['success'] / result['total'] * 100:.1f}%")
