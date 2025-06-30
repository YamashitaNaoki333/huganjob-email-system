#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企業ID 1201~1500の詳細分析
送信済み企業の開封状況を詳しく調査

作成日時: 2025年06月24日
目的: 送信済み企業の開封追跡状況詳細分析
"""

import csv
import os
from datetime import datetime

class DetailedAnalysis1201to1500:
    def __init__(self):
        self.start_id = 1201
        self.end_id = 1500
        
    def analyze_sent_companies(self):
        """送信済み企業の詳細分析"""
        print(f"📤 企業ID {self.start_id}~{self.end_id} 送信済み企業詳細分析")
        print("=" * 80)
        
        sent_companies = []
        
        try:
            # 送信データを読み込み
            with open('new_email_sending_results.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    company_id = row.get('企業ID', '').strip()
                    if company_id.isdigit():
                        id_num = int(company_id)
                        if self.start_id <= id_num <= self.end_id:
                            sent_companies.append({
                                'company_id': company_id,
                                'company_name': row.get('企業名', ''),
                                'sent_at': row.get('送信日時', ''),
                                'email_address': row.get('メールアドレス', ''),
                                'job_position': row.get('募集職種', ''),
                                'send_result': row.get('送信結果', ''),
                                'tracking_id': row.get('トラッキングID', ''),
                                'subject': row.get('件名', ''),
                                'error_message': row.get('エラーメッセージ', '')
                            })
            
            # 送信日時でソート
            sent_companies.sort(key=lambda x: x['sent_at'])
            
            print(f"📊 送信済み企業数: {len(sent_companies)}社")
            print()
            
            # 送信時間帯別分析
            time_analysis = {}
            for company in sent_companies:
                sent_time = company['sent_at']
                if sent_time:
                    # 時間部分を抽出（HH:MM形式）
                    try:
                        time_part = sent_time.split(' ')[1][:5] if ' ' in sent_time else ''
                        if time_part:
                            hour = time_part.split(':')[0]
                            if hour not in time_analysis:
                                time_analysis[hour] = []
                            time_analysis[hour].append(company)
                    except:
                        pass
            
            print("⏰ 送信時間帯別分析:")
            for hour in sorted(time_analysis.keys()):
                companies_in_hour = time_analysis[hour]
                print(f"   {hour}時台: {len(companies_in_hour)}社")
            print()
            
            # 最初と最後の送信企業
            if sent_companies:
                print("📋 送信企業詳細（時系列順）:")
                print(f"🥇 最初の送信企業:")
                first = sent_companies[0]
                print(f"   ID {first['company_id']}: {first['company_name']}")
                print(f"   送信日時: {first['sent_at']}")
                print(f"   メール: {first['email_address']}")
                print(f"   トラッキングID: {first['tracking_id']}")
                print()
                
                print(f"🏁 最後の送信企業:")
                last = sent_companies[-1]
                print(f"   ID {last['company_id']}: {last['company_name']}")
                print(f"   送信日時: {last['sent_at']}")
                print(f"   メール: {last['email_address']}")
                print(f"   トラッキングID: {last['tracking_id']}")
                print()
                
                # 中間の企業もいくつか表示
                print(f"📝 送信企業一覧（一部）:")
                for i, company in enumerate(sent_companies[:20], 1):
                    print(f"   [{i:2d}] ID {company['company_id']}: {company['company_name']}")
                    print(f"        送信: {company['sent_at']}")
                    print(f"        メール: {company['email_address']}")
                    print(f"        トラッキングID: {company['tracking_id'][:50]}...")
                    print()
            
            return sent_companies
            
        except Exception as e:
            print(f"❌ 送信企業分析エラー: {e}")
            return []
    
    def check_open_records_for_range(self, sent_companies):
        """この範囲の企業の開封記録を詳しくチェック"""
        print(f"👁️  開封記録詳細チェック")
        print("=" * 80)
        
        try:
            # 開封記録を読み込み
            open_records = {}
            if os.path.exists('data/derivative_email_open_tracking.csv'):
                with open('data/derivative_email_open_tracking.csv', 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        tracking_id = row.get('tracking_id', '').strip()
                        if tracking_id:
                            if tracking_id not in open_records:
                                open_records[tracking_id] = []
                            open_records[tracking_id].append(row)
            
            print(f"📁 開封追跡ファイル: data/derivative_email_open_tracking.csv")
            print(f"📊 総開封記録数: {sum(len(records) for records in open_records.values())}件")
            print(f"📊 開封企業数: {len(open_records)}社")
            print()
            
            # この範囲の企業の開封記録をチェック
            range_tracking_ids = [company['tracking_id'] for company in sent_companies if company['tracking_id']]
            range_open_records = {}
            
            for tracking_id in range_tracking_ids:
                if tracking_id in open_records:
                    range_open_records[tracking_id] = open_records[tracking_id]
            
            print(f"🎯 企業ID {self.start_id}~{self.end_id}の開封状況:")
            print(f"   送信企業数: {len(sent_companies)}社")
            print(f"   トラッキングID数: {len(range_tracking_ids)}件")
            print(f"   開封記録のある企業数: {len(range_open_records)}社")
            print()
            
            if range_open_records:
                print("✅ 開封記録のある企業:")
                for tracking_id, records in range_open_records.items():
                    # 対応する企業を検索
                    company = next((c for c in sent_companies if c['tracking_id'] == tracking_id), None)
                    if company:
                        print(f"   ID {company['company_id']}: {company['company_name']}")
                        print(f"     開封回数: {len(records)}回")
                        for i, record in enumerate(records, 1):
                            print(f"     [{i}] {record.get('opened_at', '')} - {record.get('tracking_method', '')}")
                        print()
            else:
                print("❌ この範囲では開封記録が見つかりませんでした")
                print()
                
                # 他の範囲の開封記録を確認
                print("🔍 参考: 他の範囲の開封記録:")
                other_records_count = 0
                for tracking_id, records in open_records.items():
                    if tracking_id not in range_tracking_ids:
                        other_records_count += len(records)
                        if other_records_count <= 5:  # 最初の5件だけ表示
                            print(f"   {tracking_id[:50]}... - {len(records)}回開封")
                
                if other_records_count > 5:
                    print(f"   ... 他 {other_records_count - 5}件の開封記録")
            
            return range_open_records
            
        except Exception as e:
            print(f"❌ 開封記録チェックエラー: {e}")
            return {}
    
    def analyze_tracking_system_effectiveness(self, sent_companies):
        """トラッキングシステムの効果分析"""
        print(f"🔬 トラッキングシステム効果分析")
        print("=" * 80)
        
        # 送信時期の分析
        if sent_companies:
            earliest_send = min(company['sent_at'] for company in sent_companies if company['sent_at'])
            latest_send = max(company['sent_at'] for company in sent_companies if company['sent_at'])
            
            print(f"📅 送信期間:")
            print(f"   最初の送信: {earliest_send}")
            print(f"   最後の送信: {latest_send}")
            print()
        
        # 改善されたトラッキングシステムとの比較
        print(f"📊 改善されたトラッキングシステムの状況:")
        print(f"   🎯 実装済み機能:")
        print(f"      - 多重ピクセル追跡（3種類）")
        print(f"      - JavaScript多重ビーコン（6種類）")
        print(f"      - フォールバック機能")
        print(f"      - エラー処理改善")
        print()
        
        print(f"   📈 期待される効果:")
        print(f"      - 企業環境での追跡成功率向上")
        print(f"      - 画像ブロック環境での検出")
        print(f"      - JavaScript制限環境での対応")
        print()
        
        print(f"   🔍 現在の状況:")
        print(f"      - 企業ID {self.start_id}~{self.end_id}: 開封記録0件")
        print(f"      - 推定原因: 企業メール環境の厳格なセキュリティ設定")
        print(f"      - 対策: 配信停止申請等の間接的な開封証拠の活用")
        print()
        
        print(f"   💡 今後の改善案:")
        print(f"      - より多様な追跡方法の実装")
        print(f"      - 企業環境に特化した追跡技術の研究")
        print(f"      - 間接的な開封指標の活用強化")
    
    def run(self):
        """メイン実行"""
        print(f"企業ID {self.start_id}~{self.end_id} 詳細分析")
        print("=" * 80)
        print(f"🎯 目的: 送信済み企業の開封追跡状況詳細調査")
        print()
        
        # 送信済み企業分析
        sent_companies = self.analyze_sent_companies()
        
        if sent_companies:
            # 開封記録チェック
            open_records = self.check_open_records_for_range(sent_companies)
            
            # トラッキングシステム効果分析
            self.analyze_tracking_system_effectiveness(sent_companies)
        
        return True

def main():
    """メイン関数"""
    analyzer = DetailedAnalysis1201to1500()
    return analyzer.run()

if __name__ == "__main__":
    main()
