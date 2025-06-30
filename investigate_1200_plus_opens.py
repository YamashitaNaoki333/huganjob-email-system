#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企業ID 1200以降の開封記録詳細調査スクリプト
送信状況、追跡ID、開封記録の詳細分析

作成日時: 2025年06月24日
目的: 企業ID 1200以降の開封記録詳細調査
"""

import csv
import json
import os
from datetime import datetime
from collections import defaultdict

class OpenInvestigator1200Plus:
    def __init__(self):
        self.start_id = 1200
        self.companies_data = {}
        self.sending_history = []
        self.open_records = {}
        self.tracking_ids = set()
        
    def load_sending_history(self):
        """送信履歴を読み込み（JSON形式）"""
        print("📤 送信履歴読み込み中...")

        try:
            with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
                data = json.load(f)

                # sending_recordsキーが存在するか確認
                if 'sending_records' in data and isinstance(data['sending_records'], list):
                    for record in data['sending_records']:
                        if isinstance(record, dict):
                            company_id = record.get('company_id', 0)
                            if isinstance(company_id, int) and company_id >= self.start_id:
                                self.sending_history.append(record)
                elif isinstance(data, list):
                    # 直接リストの場合
                    for record in data:
                        if isinstance(record, dict):
                            company_id = record.get('company_id', 0)
                            if isinstance(company_id, int) and company_id >= self.start_id:
                                self.sending_history.append(record)
                else:
                    print("❌ 送信履歴ファイルの形式が不正です")
                    return False

            print(f"✅ 送信履歴読み込み完了: {len(self.sending_history)}社")
            return True

        except Exception as e:
            print(f"❌ 送信履歴読み込みエラー: {e}")
            print("📋 CSV送信結果のみで調査を継続します")
            return True  # CSVデータがあれば継続可能
    
    def load_csv_sending_results(self):
        """CSV送信結果を読み込み"""
        print("📋 CSV送信結果読み込み中...")
        
        try:
            with open('new_email_sending_results.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                csv_results = {}
                for row in reader:
                    company_id_str = row.get('企業ID', '').strip()
                    if company_id_str.isdigit():
                        company_id = int(company_id_str)
                        if company_id >= self.start_id:
                            csv_results[company_id] = {
                                'company_name': row.get('企業名', ''),
                                'email_address': row.get('メールアドレス', ''),
                                'tracking_id': row.get('トラッキングID', ''),
                                'sent_at': row.get('送信日時', ''),
                                'send_result': row.get('送信結果', ''),
                                'job_position': row.get('募集職種', ''),
                                'subject': row.get('件名', '')
                            }
                            
                            # 追跡IDを記録
                            tracking_id = row.get('トラッキングID', '').strip()
                            if tracking_id:
                                self.tracking_ids.add(tracking_id)
                
                print(f"✅ CSV送信結果読み込み完了: {len(csv_results)}社")
                print(f"✅ 追跡ID収集完了: {len(self.tracking_ids)}件")
                return csv_results
                
        except Exception as e:
            print(f"❌ CSV送信結果読み込みエラー: {e}")
            return {}
    
    def load_open_records(self):
        """開封記録を読み込み"""
        print("👁️  開封記録読み込み中...")
        
        try:
            with open('data/derivative_email_open_tracking.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    tracking_id = row.get('tracking_id', '').strip()
                    if tracking_id:
                        if tracking_id not in self.open_records:
                            self.open_records[tracking_id] = []
                        
                        self.open_records[tracking_id].append({
                            'opened_at': row.get('opened_at', ''),
                            'ip_address': row.get('ip_address', ''),
                            'device_type': row.get('device_type', ''),
                            'user_agent': row.get('user_agent', ''),
                            'tracking_method': row.get('tracking_method', ''),
                            'referer': row.get('referer', '')
                        })
            
            print(f"✅ 開封記録読み込み完了: {len(self.open_records)}件のトラッキングID")
            return True
            
        except Exception as e:
            print(f"❌ 開封記録読み込みエラー: {e}")
            return False
    
    def analyze_tracking_status(self, csv_results):
        """追跡状況を分析"""
        print("\n📊 企業ID 1200以降の追跡状況分析")
        print("=" * 80)
        
        # 統計情報
        total_companies = len(csv_results)
        companies_with_tracking = 0
        opened_companies = 0
        total_opens = 0
        
        # 詳細結果
        detailed_results = []
        
        for company_id in sorted(csv_results.keys()):
            company = csv_results[company_id]
            tracking_id = company['tracking_id']
            
            # 追跡IDの有無
            has_tracking = bool(tracking_id)
            if has_tracking:
                companies_with_tracking += 1
            
            # 開封記録の確認
            opens = self.open_records.get(tracking_id, [])
            is_opened = len(opens) > 0
            if is_opened:
                opened_companies += 1
                total_opens += len(opens)
            
            detailed_results.append({
                'company_id': company_id,
                'company_name': company['company_name'],
                'email_address': company['email_address'],
                'tracking_id': tracking_id,
                'has_tracking': has_tracking,
                'is_opened': is_opened,
                'open_count': len(opens),
                'opens': opens,
                'sent_at': company['sent_at'],
                'job_position': company['job_position']
            })
        
        # 統計表示
        print(f"📈 統計サマリー:")
        print(f"   総企業数: {total_companies}社")
        print(f"   追跡ID付き企業数: {companies_with_tracking}社")
        print(f"   開封企業数: {opened_companies}社")
        print(f"   総開封回数: {total_opens}回")
        
        if companies_with_tracking > 0:
            open_rate = (opened_companies / companies_with_tracking) * 100
            print(f"   📊 開封率: {open_rate:.2f}%")
        else:
            print(f"   📊 開封率: 計算不可（追跡ID付き企業なし）")
        
        return detailed_results
    
    def show_detailed_results(self, detailed_results):
        """詳細結果を表示"""
        print(f"\n📋 詳細結果（企業ID {self.start_id}以降）:")
        print("=" * 80)
        
        # 開封済み企業
        opened_companies = [r for r in detailed_results if r['is_opened']]
        if opened_companies:
            print(f"✅ 開封済み企業 ({len(opened_companies)}社):")
            for result in opened_companies[:20]:  # 上位20社まで表示
                print(f"  ID {result['company_id']}: {result['company_name']}")
                print(f"    📧 {result['email_address']}")
                print(f"    🔗 {result['tracking_id']}")
                print(f"    👁️  開封回数: {result['open_count']}回")
                for i, open_record in enumerate(result['opens'][:3]):  # 最大3回まで表示
                    print(f"      [{i+1}] {open_record['opened_at']} ({open_record['tracking_method']})")
                print()
        else:
            print("❌ 開封済み企業: なし")
        
        # 未開封企業（一部表示）
        unopened_companies = [r for r in detailed_results if not r['is_opened']]
        if unopened_companies:
            print(f"\n❌ 未開封企業 ({len(unopened_companies)}社) - 一部表示:")
            for i, result in enumerate(unopened_companies[:20]):
                tracking_status = "追跡ID有り" if result['has_tracking'] else "追跡ID無し"
                print(f"  [{i+1:2d}] ID {result['company_id']}: {result['company_name']} [{tracking_status}]")
                if result['has_tracking']:
                    print(f"       🔗 {result['tracking_id']}")
                print()
    
    def check_tracking_id_patterns(self, detailed_results):
        """追跡IDのパターンを分析"""
        print(f"\n🔍 追跡IDパターン分析:")
        print("=" * 80)
        
        tracking_patterns = defaultdict(int)
        
        for result in detailed_results:
            if result['has_tracking']:
                tracking_id = result['tracking_id']
                # パターン分析（日付部分を抽出）
                if '_' in tracking_id:
                    parts = tracking_id.split('_')
                    if len(parts) >= 3:
                        date_part = parts[2]
                        tracking_patterns[date_part] += 1
        
        print("📅 送信日別追跡ID数:")
        for date_pattern in sorted(tracking_patterns.keys()):
            count = tracking_patterns[date_pattern]
            print(f"  {date_pattern}: {count}件")
    
    def investigate_specific_companies(self, detailed_results):
        """特定企業の詳細調査"""
        print(f"\n🔬 特定企業詳細調査:")
        print("=" * 80)
        
        # 企業ID 1200, 1250, 1300の詳細調査
        target_ids = [1200, 1250, 1300]
        
        for target_id in target_ids:
            result = next((r for r in detailed_results if r['company_id'] == target_id), None)
            if result:
                print(f"🏢 企業ID {target_id}: {result['company_name']}")
                print(f"   📧 メールアドレス: {result['email_address']}")
                print(f"   📅 送信日時: {result['sent_at']}")
                print(f"   🔗 追跡ID: {result['tracking_id']}")
                print(f"   👁️  開封状況: {'開封済み' if result['is_opened'] else '未開封'}")
                if result['is_opened']:
                    for open_record in result['opens']:
                        print(f"      - {open_record['opened_at']} ({open_record['tracking_method']})")
                print()
            else:
                print(f"❌ 企業ID {target_id}: データなし")
                print()
    
    def run(self):
        """メイン実行"""
        print(f"企業ID {self.start_id}以降の開封記録詳細調査")
        print("=" * 80)
        print(f"🎯 調査対象: 企業ID {self.start_id}以降")
        print()
        
        # データ読み込み
        if not self.load_sending_history():
            return False
        
        csv_results = self.load_csv_sending_results()
        if not csv_results:
            return False
        
        if not self.load_open_records():
            return False
        
        # 分析実行
        detailed_results = self.analyze_tracking_status(csv_results)
        
        # 詳細結果表示
        self.show_detailed_results(detailed_results)
        
        # 追跡IDパターン分析
        self.check_tracking_id_patterns(detailed_results)
        
        # 特定企業調査
        self.investigate_specific_companies(detailed_results)
        
        # 改善提案
        print(f"\n💡 改善提案:")
        print("=" * 80)
        print("1. 多重化追跡システムの効果測定")
        print("   - 企業環境での追跡成功率を詳細分析")
        print("   - 追跡方法別の成功率比較")
        print()
        print("2. 間接的開封証拠の活用")
        print("   - 配信停止申請の記録・分析")
        print("   - 返信メールの自動検出")
        print()
        print("3. 追跡精度向上")
        print("   - より多様な追跡方法の実装")
        print("   - 企業環境特化型追跡技術の開発")
        
        return True

def main():
    """メイン関数"""
    investigator = OpenInvestigator1200Plus()
    return investigator.run()

if __name__ == "__main__":
    main()
