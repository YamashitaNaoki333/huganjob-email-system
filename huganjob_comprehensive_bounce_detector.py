#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB 包括的バウンス検出システム
ID 30-150の企業のバウンス状況を詳細に調査
"""

import pandas as pd
import datetime
import os
import json
import re
import imaplib
import email
from email.header import decode_header

class ComprehensiveBounceDetector:
    def __init__(self):
        self.csv_file = 'data/new_input_test.csv'
        self.sending_results_file = 'new_email_sending_results.csv'
        
        # IMAP設定
        self.imap_server = 'sv12053.xserver.jp'
        self.imap_port = 993
        self.username = 'contact@huganjob.jp'
        self.password = 'gD34bEmB'
        
        self.detected_bounces = []
        self.suspicious_addresses = []

    def analyze_email_addresses(self):
        """ID 30-150の企業のメールアドレスを分析"""
        try:
            print('=== ID 30-150 企業メールアドレス分析 ===')
            
            # 企業データを読み込み
            df_companies = pd.read_csv(self.csv_file)
            target_companies = df_companies[(df_companies['ID'] >= 30) & (df_companies['ID'] <= 150)]
            
            print(f'📊 分析対象企業: {len(target_companies)}社 (ID 30-150)')
            
            # 送信結果を読み込み
            df_results = pd.read_csv(self.sending_results_file)
            
            suspicious_patterns = []
            
            for _, company in target_companies.iterrows():
                company_id = company['ID']
                company_name = company['企業名']
                
                # 送信結果を確認
                send_records = df_results[df_results['企業ID'] == company_id]
                
                if len(send_records) > 0:
                    email_address = send_records.iloc[0]['メールアドレス']
                    send_result = send_records.iloc[0]['送信結果']
                    
                    # 疑わしいパターンを検出
                    suspicious_flags = []
                    
                    # 1. www.プレフィックス付きメールアドレス
                    if 'info@www.' in email_address:
                        suspicious_flags.append('www_prefix')
                    
                    # 2. 大企業の一般的なinfoアドレス（バウンスしやすい）
                    if email_address.startswith('info@') and any(keyword in company_name for keyword in ['株式会社', '大学', '学校法人', '財団法人']):
                        suspicious_flags.append('generic_info')
                    
                    # 3. 特定のドメインパターン
                    domain = email_address.split('@')[1] if '@' in email_address else ''
                    if any(pattern in domain for pattern in ['.ac.jp', '.or.jp', '.go.jp']):
                        suspicious_flags.append('institutional_domain')
                    
                    # 4. 送信結果がsuccessでも疑わしい
                    if send_result == 'success' and suspicious_flags:
                        suspicious_patterns.append({
                            'company_id': company_id,
                            'company_name': company_name,
                            'email_address': email_address,
                            'send_result': send_result,
                            'suspicious_flags': suspicious_flags,
                            'risk_level': len(suspicious_flags)
                        })
            
            # 疑わしいパターンを表示
            print(f'\n🔍 疑わしいメールアドレスパターン: {len(suspicious_patterns)}件')
            
            high_risk = [p for p in suspicious_patterns if p['risk_level'] >= 2]
            medium_risk = [p for p in suspicious_patterns if p['risk_level'] == 1]
            
            print(f'  高リスク (2+フラグ): {len(high_risk)}件')
            print(f'  中リスク (1フラグ): {len(medium_risk)}件')
            
            # 高リスクアドレスを詳細表示
            if high_risk:
                print('\n高リスクアドレス詳細:')
                for pattern in high_risk[:10]:  # 最初の10件
                    print(f'  ID {pattern["company_id"]}: {pattern["company_name"]}')
                    print(f'    メール: {pattern["email_address"]}')
                    print(f'    フラグ: {", ".join(pattern["suspicious_flags"])}')
                    print()
            
            self.suspicious_addresses = suspicious_patterns
            return True
            
        except Exception as e:
            print(f'❌ メールアドレス分析失敗: {e}')
            return False

    def connect_to_mailbox(self):
        """メールボックスに接続してバウンスメールを検索"""
        try:
            print('\n=== 受信ボックスバウンス検索 ===')
            print('📧 contact@huganjob.jpのメールボックスに接続中...')
            
            # IMAP接続
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.mail.login(self.username, self.password)
            print('✅ メールボックス接続成功')
            
            # INBOXを選択
            self.mail.select('INBOX')
            
            # バウンスメールの検索条件を拡張
            bounce_search_terms = [
                'SUBJECT "Mail delivery failed"',
                'SUBJECT "Undelivered Mail"',
                'SUBJECT "Delivery Status Notification"',
                'SUBJECT "failure notice"',
                'SUBJECT "returned mail"',
                'SUBJECT "Mail Delivery Subsystem"',
                'SUBJECT "Undeliverable"',
                'SUBJECT "Message could not be delivered"',
                'FROM "Mail Delivery Subsystem"',
                'FROM "postmaster"',
                'FROM "mailer-daemon"',
                'FROM "MAILER-DAEMON"'
            ]
            
            all_bounce_ids = set()
            
            for search_term in bounce_search_terms:
                try:
                    status, messages = self.mail.search(None, search_term)
                    if status == 'OK' and messages[0]:
                        bounce_ids = messages[0].split()
                        all_bounce_ids.update(bounce_ids)
                        print(f'  {search_term}: {len(bounce_ids)}件')
                except Exception as e:
                    print(f'  検索エラー ({search_term}): {e}')
            
            print(f'\n📧 総バウンスメール数: {len(all_bounce_ids)}件')
            
            # バウンスメールの詳細を分析
            if all_bounce_ids:
                self.analyze_bounce_emails(list(all_bounce_ids))
            
            self.mail.close()
            self.mail.logout()
            return True
            
        except Exception as e:
            print(f'❌ メールボックス接続失敗: {e}')
            return False

    def analyze_bounce_emails(self, bounce_ids):
        """バウンスメールの詳細を分析"""
        try:
            print(f'\n🔍 バウンスメール詳細分析中...')
            
            # ID 30-150の企業のメールアドレスリストを作成
            df_results = pd.read_csv(self.sending_results_file)
            target_emails = {}
            
            for _, row in df_results.iterrows():
                company_id = row['企業ID']
                if 30 <= company_id <= 150:
                    email_addr = row['メールアドレス']
                    target_emails[email_addr] = {
                        'company_id': company_id,
                        'company_name': row['企業名'],
                        'email_address': email_addr
                    }
            
            print(f'  対象メールアドレス: {len(target_emails)}件')
            
            detected_bounces = []
            
            # バウンスメールを解析（最初の50件）
            for i, msg_id in enumerate(bounce_ids[:50], 1):
                try:
                    if i % 10 == 0:
                        print(f'  処理中: {i}/{min(50, len(bounce_ids))}件')
                    
                    status, msg_data = self.mail.fetch(msg_id, '(RFC822)')
                    if status == 'OK':
                        email_message = email.message_from_bytes(msg_data[0][1])
                        
                        # 件名を取得
                        subject = email_message.get('Subject', '')
                        if subject:
                            subject = str(decode_header(subject)[0][0])
                        
                        # 本文を取得
                        body = self.get_email_body(email_message)
                        
                        # バウンスしたメールアドレスを抽出
                        bounced_addresses = self.extract_bounced_addresses(subject + ' ' + body)
                        
                        # 対象企業のバウンスかチェック
                        for bounced_addr in bounced_addresses:
                            if bounced_addr in target_emails:
                                company_info = target_emails[bounced_addr]
                                
                                bounce_info = {
                                    'company_id': company_info['company_id'],
                                    'company_name': company_info['company_name'],
                                    'email_address': bounced_addr,
                                    'bounce_subject': subject,
                                    'bounce_reason': self.extract_bounce_reason(body),
                                    'bounce_type': self.classify_bounce_type(body),
                                    'detection_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                }
                                
                                detected_bounces.append(bounce_info)
                                print(f'  🔍 バウンス検出: ID {company_info["company_id"]} - {company_info["company_name"]}')
                
                except Exception as e:
                    print(f'  メール解析エラー: {e}')
            
            self.detected_bounces = detected_bounces
            print(f'\n✅ ID 30-150範囲でのバウンス検出: {len(detected_bounces)}件')
            
            return True
            
        except Exception as e:
            print(f'❌ バウンスメール分析失敗: {e}')
            return False

    def get_email_body(self, email_message):
        """メール本文を取得"""
        body = ""
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
            else:
                body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            body = str(email_message)
        return body

    def extract_bounced_addresses(self, text):
        """バウンスしたメールアドレスを抽出"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        addresses = re.findall(email_pattern, text)
        
        # HUGANJOBから送信されたアドレスのみを対象
        huganjob_addresses = []
        for addr in addresses:
            # 送信者アドレスを除外
            if 'huganjob.jp' not in addr and 'fortyfive.co.jp' not in addr:
                huganjob_addresses.append(addr)
        
        return huganjob_addresses

    def extract_bounce_reason(self, body):
        """バウンス理由を抽出"""
        common_reasons = {
            'User unknown': 'ユーザー不明',
            'Mailbox full': 'メールボックス満杯',
            'Host unknown': 'ホスト不明',
            'Connection refused': '接続拒否',
            'Temporary failure': '一時的障害',
            'Permanent failure': '永続的障害',
            'Bad recipient address': 'アドレス形式エラー'
        }
        
        for pattern, reason in common_reasons.items():
            if pattern.lower() in body.lower():
                return reason
        
        return 'バウンス理由不明'

    def classify_bounce_type(self, body):
        """バウンスタイプを分類"""
        permanent_indicators = ['permanent', 'user unknown', 'host unknown', 'bad recipient']
        temporary_indicators = ['temporary', 'mailbox full', 'try again']
        
        body_lower = body.lower()
        
        for indicator in permanent_indicators:
            if indicator in body_lower:
                return 'permanent'
        
        for indicator in temporary_indicators:
            if indicator in body_lower:
                return 'temporary'
        
        return 'unknown'

    def generate_comprehensive_report(self):
        """包括的レポートを生成"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = f'huganjob_comprehensive_bounce_analysis_{timestamp}.json'
            
            report_data = {
                'analysis_date': datetime.datetime.now().isoformat(),
                'target_range': 'ID 30-150',
                'suspicious_addresses': {
                    'total_count': len(self.suspicious_addresses),
                    'high_risk_count': len([s for s in self.suspicious_addresses if s['risk_level'] >= 2]),
                    'medium_risk_count': len([s for s in self.suspicious_addresses if s['risk_level'] == 1]),
                    'details': self.suspicious_addresses
                },
                'detected_bounces': {
                    'total_count': len(self.detected_bounces),
                    'permanent_count': len([b for b in self.detected_bounces if b['bounce_type'] == 'permanent']),
                    'temporary_count': len([b for b in self.detected_bounces if b['bounce_type'] == 'temporary']),
                    'details': self.detected_bounces
                },
                'recommendations': [
                    'www.プレフィックス付きメールアドレスの見直し',
                    '大企業の一般的なinfoアドレスの代替手段検討',
                    '教育機関・公的機関への送信方法の改善',
                    '定期的なバウンス監視の実施'
                ]
            }
            
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            print(f'\n📄 包括的分析レポート生成: {report_filename}')
            return report_filename
            
        except Exception as e:
            print(f'❌ レポート生成失敗: {e}')
            return None

    def display_summary(self):
        """分析結果サマリーを表示"""
        print('\n' + '=' * 60)
        print('📊 ID 30-150 包括的バウンス分析結果')
        print('=' * 60)
        
        print(f'🔍 疑わしいアドレス: {len(self.suspicious_addresses)}件')
        if self.suspicious_addresses:
            high_risk = len([s for s in self.suspicious_addresses if s['risk_level'] >= 2])
            medium_risk = len([s for s in self.suspicious_addresses if s['risk_level'] == 1])
            print(f'  高リスク: {high_risk}件')
            print(f'  中リスク: {medium_risk}件')
        
        print(f'📧 実際のバウンス検出: {len(self.detected_bounces)}件')
        if self.detected_bounces:
            permanent = len([b for b in self.detected_bounces if b['bounce_type'] == 'permanent'])
            temporary = len([b for b in self.detected_bounces if b['bounce_type'] == 'temporary'])
            print(f'  永続的エラー: {permanent}件')
            print(f'  一時的エラー: {temporary}件')
        
        print('\n推奨アクション:')
        print('1. 疑わしいアドレスの手動確認')
        print('2. バウンス検出企業のCSV更新')
        print('3. 送信除外リストの更新')
        print('4. 代替メールアドレスの調査')

def main():
    detector = ComprehensiveBounceDetector()
    
    try:
        # メールアドレスパターン分析
        if not detector.analyze_email_addresses():
            return False
        
        # 受信ボックスのバウンス検索
        if not detector.connect_to_mailbox():
            print('⚠️ メールボックス接続に失敗しましたが、分析を続行します')
        
        # レポート生成
        report_file = detector.generate_comprehensive_report()
        
        # 結果サマリー表示
        detector.display_summary()
        
        print('\n🎯 包括的バウンス分析が完了しました')
        if report_file:
            print(f'📄 詳細レポート: {report_file}')
        
        return True
        
    except Exception as e:
        print(f'❌ 分析中にエラーが発生しました: {e}')
        return False

if __name__ == "__main__":
    main()
