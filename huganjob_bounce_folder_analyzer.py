#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB bounceフォルダ分析システム

INBOX.bounceフォルダに移動されたバウンスメールを分析し、
企業データベースを更新するシステム
"""

import imaplib
import email
import pandas as pd
import datetime
import re
import os
import json
from email.header import decode_header

class HuganjobBouncefolderAnalyzer:
    def __init__(self):
        # IMAPサーバー設定
        self.imap_server = 'sv12053.xserver.jp'
        self.imap_port = 993
        self.username = 'contact@huganjob.jp'
        self.password = 'gD34bEmB'
        
        # バウンス検知パターン
        self.bounce_patterns = [
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'The following address\(es\) failed:\s*([^\s]+)',
            r'<([^>]+)>.*failed',
            r'user unknown.*<([^>]+)>',
            r'mailbox unavailable.*<([^>]+)>',
        ]
        
        self.bounce_emails = []
        self.company_bounces = []
        
    def connect_to_mailbox(self):
        """メールボックスに接続"""
        try:
            print('📧 contact@huganjob.jpのメールボックスに接続中...')
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.mail.login(self.username, self.password)
            print('✅ メールボックス接続成功')
            return True
        except Exception as e:
            print(f'❌ メールボックス接続失敗: {e}')
            return False
    
    def analyze_bounce_folder(self):
        """bounceフォルダのメールを分析"""
        try:
            print('\n📁 INBOX.bounceフォルダを分析中...')
            
            # bounceフォルダを選択
            self.mail.select('INBOX.bounce')
            
            # 全メールを取得
            status, messages = self.mail.search(None, 'ALL')
            if status != 'OK':
                print('❌ bounceフォルダの検索に失敗')
                return False
            
            message_ids = messages[0].split()
            print(f'📊 bounceフォルダ内のメール数: {len(message_ids)}件')
            
            if not message_ids:
                print('📭 bounceフォルダにメールがありません')
                return True
            
            # 各メールを分析
            for i, msg_id in enumerate(message_ids, 1):
                try:
                    print(f'   分析中: {i}/{len(message_ids)}件')
                    
                    status, msg_data = self.mail.fetch(msg_id, '(RFC822)')
                    if status == 'OK':
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        
                        # ヘッダー情報を取得
                        subject = self.decode_mime_words(email_message.get('Subject', ''))
                        from_addr = email_message.get('From', '')
                        date = email_message.get('Date', '')
                        
                        # メール本文を取得
                        body = self.extract_email_body(email_message)
                        
                        # バウンスしたメールアドレスを抽出
                        bounced_addresses = self.extract_bounced_addresses(subject, body)
                        
                        if bounced_addresses:
                            bounce_info = {
                                'message_id': msg_id.decode(),
                                'subject': subject,
                                'from': from_addr,
                                'date': date,
                                'bounced_addresses': bounced_addresses,
                                'bounce_type': self.classify_bounce_type(subject, body),
                                'body_snippet': body[:300] + '...' if len(body) > 300 else body
                            }
                            self.bounce_emails.append(bounce_info)
                            
                            # 企業IDとの関連付け
                            self.match_bounces_to_companies(bounced_addresses, bounce_info)
                
                except Exception as e:
                    print(f'   ⚠️ メール分析エラー (ID: {msg_id}): {e}')
            
            print(f'✅ bounceフォルダ分析完了: {len(self.bounce_emails)}件のバウンスメール検出')
            print(f'🏢 企業バウンス検出: {len(self.company_bounces)}社')
            
            return True
            
        except Exception as e:
            print(f'❌ bounceフォルダ分析失敗: {e}')
            return False
    
    def decode_mime_words(self, s):
        """MIMEエンコードされた文字列をデコード"""
        if s is None:
            return ''
        try:
            decoded_fragments = decode_header(s)
            decoded_string = ''
            for fragment, encoding in decoded_fragments:
                if isinstance(fragment, bytes):
                    if encoding:
                        decoded_string += fragment.decode(encoding)
                    else:
                        decoded_string += fragment.decode('utf-8', errors='ignore')
                else:
                    decoded_string += fragment
            return decoded_string
        except Exception:
            return str(s)
    
    def extract_email_body(self, email_message):
        """メール本文を抽出"""
        body = ""
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        charset = part.get_content_charset() or 'utf-8'
                        body += part.get_payload(decode=True).decode(charset, errors='ignore')
            else:
                charset = email_message.get_content_charset() or 'utf-8'
                body = email_message.get_payload(decode=True).decode(charset, errors='ignore')
        except Exception as e:
            print(f'   ⚠️ 本文抽出エラー: {e}')
        return body
    
    def extract_bounced_addresses(self, subject, body):
        """バウンスしたメールアドレスを抽出"""
        bounced_addresses = set()
        text = f"{subject} {body}"
        
        for pattern in self.bounce_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else match[1]
                
                # 有効なメールアドレスかチェック
                if '@' in match and '.' in match.split('@')[1]:
                    # 除外するアドレス
                    exclude_patterns = [
                        'postmaster@', 'mailer-daemon@', 'noreply@',
                        'contact@huganjob.jp', 'no-reply@'
                    ]
                    
                    if not any(exclude in match.lower() for exclude in exclude_patterns):
                        bounced_addresses.add(match.lower())
        
        return list(bounced_addresses)
    
    def classify_bounce_type(self, subject, body):
        """バウンスタイプを分類"""
        text = f"{subject} {body}".lower()
        
        # 永続的エラー
        permanent_indicators = [
            'user unknown', 'no such user', 'invalid recipient',
            'mailbox unavailable', 'address rejected', 'does not exist',
            '550', '551', '553', '554'
        ]
        
        # 一時的エラー
        temporary_indicators = [
            'mailbox full', 'quota exceeded', 'temporary failure',
            'try again later', 'deferred', '421', '450', '451', '452'
        ]
        
        for indicator in permanent_indicators:
            if indicator in text:
                return 'permanent'
        
        for indicator in temporary_indicators:
            if indicator in text:
                return 'temporary'
        
        return 'unknown'
    
    def match_bounces_to_companies(self, bounced_addresses, bounce_info):
        """バウンスメールアドレスを企業IDと関連付け"""
        try:
            # 送信結果ファイルを読み込み
            df_results = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')
            
            for bounced_email in bounced_addresses:
                # 送信結果から該当企業を検索
                matches = df_results[df_results['メールアドレス'].str.lower() == bounced_email.lower()]
                
                for _, match in matches.iterrows():
                    company_bounce = {
                        'company_id': match['企業ID'],
                        'company_name': match['企業名'],
                        'email_address': bounced_email,
                        'job_position': match['募集職種'],
                        'bounce_type': bounce_info['bounce_type'],
                        'bounce_date': bounce_info['date'],
                        'bounce_reason': bounce_info['subject'],
                        'tracking_id': match.get('トラッキングID', ''),
                        'send_date': match['送信日時']
                    }
                    self.company_bounces.append(company_bounce)
                    print(f'   🎯 バウンス企業特定: ID {company_bounce["company_id"]} - {company_bounce["company_name"]} ({bounced_email})')
        
        except Exception as e:
            print(f'   ⚠️ 企業関連付けエラー: {e}')
    
    def update_company_database(self):
        """企業データベースを更新"""
        if not self.company_bounces:
            print('📝 更新対象の企業バウンスがありません')
            return True
        
        try:
            print(f'\n📝 企業データベースを更新中... ({len(self.company_bounces)}社)')
            
            # バックアップ作成
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'data/new_input_test_backup_bounce_folder_{timestamp}.csv'
            
            df_companies = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
            df_companies.to_csv(backup_filename, index=False, encoding='utf-8-sig')
            print(f'📁 バックアップ作成: {backup_filename}')
            
            # バウンス状態列を確認・追加
            if 'バウンス状態' not in df_companies.columns:
                df_companies['バウンス状態'] = ''
            if 'バウンス日時' not in df_companies.columns:
                df_companies['バウンス日時'] = ''
            if 'バウンス理由' not in df_companies.columns:
                df_companies['バウンス理由'] = ''
            
            # バウンス企業の情報を更新
            updated_count = 0
            for bounce in self.company_bounces:
                company_id = bounce['company_id']
                
                # 該当企業を特定
                mask = df_companies['ID'] == company_id
                if mask.any():
                    df_companies.loc[mask, 'バウンス状態'] = bounce['bounce_type']
                    df_companies.loc[mask, 'バウンス日時'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    df_companies.loc[mask, 'バウンス理由'] = bounce['bounce_reason']
                    
                    updated_count += 1
                    print(f'   ✅ ID {company_id}: {bounce["company_name"]} - {bounce["bounce_type"]}バウンス')
            
            # 更新されたデータを保存
            df_companies.to_csv('data/new_input_test.csv', index=False, encoding='utf-8-sig')
            print(f'💾 企業データベース更新完了: {updated_count}社')
            
            return True
            
        except Exception as e:
            print(f'❌ 企業データベース更新失敗: {e}')
            return False
    
    def generate_report(self):
        """分析レポートを生成"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = f'huganjob_bounce_folder_analysis_{timestamp}.json'
            
            report_data = {
                'analysis_date': datetime.datetime.now().isoformat(),
                'total_bounce_emails': len(self.bounce_emails),
                'total_company_bounces': len(self.company_bounces),
                'bounce_emails': self.bounce_emails,
                'company_bounces': self.company_bounces,
                'summary': {
                    'permanent_bounces': len([b for b in self.company_bounces if b['bounce_type'] == 'permanent']),
                    'temporary_bounces': len([b for b in self.company_bounces if b['bounce_type'] == 'temporary']),
                    'unknown_bounces': len([b for b in self.company_bounces if b['bounce_type'] == 'unknown'])
                }
            }
            
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            print(f'📄 分析レポート生成: {report_filename}')
            return report_filename
            
        except Exception as e:
            print(f'❌ レポート生成失敗: {e}')
            return None
    
    def disconnect(self):
        """メールボックス接続を切断"""
        try:
            if hasattr(self, 'mail'):
                self.mail.close()
                self.mail.logout()
                print('✅ メールボックス接続を切断しました')
        except Exception as e:
            print(f'⚠️ 切断エラー: {e}')

def main():
    print('=== HUGANJOB bounceフォルダ分析システム ===')
    print('📁 INBOX.bounceフォルダのバウンスメールを分析し、企業データベースを更新します')
    print()
    
    analyzer = HuganjobBouncefolderAnalyzer()
    
    try:
        # メールボックスに接続
        if not analyzer.connect_to_mailbox():
            return False
        
        # bounceフォルダを分析
        if not analyzer.analyze_bounce_folder():
            return False
        
        # 企業データベースを更新
        if not analyzer.update_company_database():
            return False
        
        # レポート生成
        report_file = analyzer.generate_report()
        
        print('\n🎯 bounceフォルダ分析完了')
        print(f'📊 検出バウンスメール: {len(analyzer.bounce_emails)}件')
        print(f'🏢 バウンス企業: {len(analyzer.company_bounces)}社')
        
        if report_file:
            print(f'📄 詳細レポート: {report_file}')
        
        return True
        
    except Exception as e:
        print(f'❌ 処理中にエラーが発生しました: {e}')
        return False
    
    finally:
        analyzer.disconnect()

if __name__ == "__main__":
    main()
