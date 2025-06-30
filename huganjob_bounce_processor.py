#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB バウンスメール処理システム
contact@huganjob.jpのバウンスメールを処理し、企業データベースを更新する
"""

import imaplib
import email
import pandas as pd
import datetime
import re
import os
import json
from email.header import decode_header

class HuganjobBounceProcessor:
    def __init__(self):
        # IMAPサーバー設定を修正
        self.imap_server = 'sv12053.xserver.jp'  # Xserver IMAP
        self.imap_port = 993
        self.username = 'contact@huganjob.jp'
        self.password = 'gD34bEmB'
        self.bounce_patterns = [
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',  # 一般的なメールアドレス
            r'The following address\(es\) failed:\s*([^\s]+)',     # Exim形式
            r'<([^>]+)>.*failed',                                  # <>で囲まれたアドレス
            r'user unknown.*<([^>]+)>',                           # ユーザー不明
            r'mailbox unavailable.*<([^>]+)>',                    # メールボックス利用不可
        ]
        self.bounce_emails = []
        self.processed_results = []
        self.processed_tracking_file = 'huganjob_processed_bounces.json'
        self.processed_message_ids = set()
        self.force_reprocess = False  # 強制再処理フラグ

        # 処理済みメールIDを読み込み
        self.load_processed_tracking()

    def load_processed_tracking(self):
        """処理済みメールIDの追跡ファイルを読み込み"""
        try:
            if os.path.exists(self.processed_tracking_file):
                with open(self.processed_tracking_file, 'r', encoding='utf-8') as f:
                    tracking_data = json.load(f)
                    self.processed_message_ids = set(tracking_data.get('processed_message_ids', []))
                    print(f'📋 処理済み追跡ファイル読み込み: {len(self.processed_message_ids)}件')
            else:
                print('📋 新規処理済み追跡ファイルを作成します')
        except Exception as e:
            print(f'⚠️ 処理済み追跡ファイル読み込みエラー: {e}')
            self.processed_message_ids = set()

    def save_processed_tracking(self):
        """処理済みメールIDを追跡ファイルに保存"""
        try:
            tracking_data = {
                'last_updated': datetime.datetime.now().isoformat(),
                'processed_message_ids': list(self.processed_message_ids),
                'total_processed': len(self.processed_message_ids)
            }

            with open(self.processed_tracking_file, 'w', encoding='utf-8') as f:
                json.dump(tracking_data, f, ensure_ascii=False, indent=2)

            print(f'💾 処理済み追跡ファイル更新: {len(self.processed_message_ids)}件')
            return True
        except Exception as e:
            print(f'❌ 処理済み追跡ファイル保存エラー: {e}')
            return False

    def connect_to_mailbox(self):
        """メールボックスに接続"""
        try:
            print('📧 contact@huganjob.jpのメールボックスに接続中...')
            print(f'   サーバー: {self.imap_server}:{self.imap_port}')

            # SSL接続を試行
            print('   SSL接続を試行中...')
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            print('   ✅ SSL接続成功')

            # ログイン
            print('   認証中...')
            self.mail.login(self.username, self.password)
            print('✅ メールボックス接続成功')

            # メールボックス一覧を確認
            print('   メールボックス一覧を取得中...')
            status, mailboxes = self.mail.list()
            if status == 'OK':
                print('   利用可能なメールボックス:')
                for mailbox in mailboxes[:10]:  # 最初の10個を表示
                    print(f'     {mailbox.decode()}')

            return True
        except Exception as e:
            print(f'❌ メールボックス接続失敗: {e}')
            print('   代替サーバーを試行中...')

            # 代替サーバーを試行
            try:
                self.imap_server = 'huganjob.jp'
                print(f'   代替サーバー: {self.imap_server}:{self.imap_port}')
                self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                self.mail.login(self.username, self.password)
                print('✅ 代替サーバーで接続成功')
                return True
            except Exception as e2:
                print(f'❌ 代替サーバーも失敗: {e2}')
                return False

    def identify_bounce_emails(self):
        """バウンスメールを特定"""
        try:
            print('\n🔍 バウンスメールを特定中...')
            
            # INBOXを選択
            self.mail.select('INBOX')
            
            # バウンスメールの検索条件を拡張
            bounce_subjects = [
                'SUBJECT "Mail delivery failed"',
                'SUBJECT "Undelivered Mail"',
                'SUBJECT "Delivery Status Notification"',
                'SUBJECT "failure notice"',
                'SUBJECT "returned mail"',
                'SUBJECT "Mail Delivery Subsystem"',
                'SUBJECT "Undeliverable"',
                'SUBJECT "Delivery Failure"',
                'SUBJECT "Message could not be delivered"',
                'SUBJECT "Returned mail"',
                'FROM "Mail Delivery Subsystem"',
                'FROM "postmaster"',
                'FROM "mailer-daemon"',
                'FROM "MAILER-DAEMON"',
                'FROM "noreply"'
            ]
            
            all_bounce_ids = set()
            
            for search_criteria in bounce_subjects:
                try:
                    status, messages = self.mail.search(None, search_criteria)
                    if status == 'OK':
                        message_ids = messages[0].split()
                        all_bounce_ids.update(message_ids)
                        print(f'   {search_criteria}: {len(message_ids)}件')
                except Exception as e:
                    print(f'   ⚠️ 検索エラー ({search_criteria}): {e}')
            
            print(f'\n📊 合計バウンスメール候補: {len(all_bounce_ids)}件')
            
            # バウンスメールの詳細を取得（重複処理防止）
            print(f'📧 バウンスメールの詳細を取得中...')
            new_bounce_count = 0
            skipped_count = 0

            for i, msg_id in enumerate(list(all_bounce_ids), 1):
                try:
                    if i % 10 == 0:
                        print(f'   処理中: {i}/{len(all_bounce_ids)}件 (新規: {new_bounce_count}, スキップ: {skipped_count})')

                    msg_id_str = msg_id.decode()

                    # 既に処理済みかチェック（強制再処理モードでない場合のみ）
                    if not self.force_reprocess and msg_id_str in self.processed_message_ids:
                        skipped_count += 1
                        continue

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
                                'message_id': msg_id_str,
                                'subject': subject,
                                'from': from_addr,
                                'date': date,
                                'bounced_addresses': bounced_addresses,
                                'bounce_type': self.classify_bounce_type(subject, body),
                                'body_snippet': body[:200] + '...' if len(body) > 200 else body,
                                'processed_date': datetime.datetime.now().isoformat()
                            }
                            self.bounce_emails.append(bounce_info)
                            new_bounce_count += 1

                except Exception as e:
                    print(f'   ⚠️ メール処理エラー (ID: {msg_id}): {e}')

            print(f'✅ バウンスメール特定完了: 新規 {new_bounce_count}件, スキップ {skipped_count}件')

            # 処理済みメールIDを追跡リストに追加
            for bounce_info in self.bounce_emails:
                self.processed_message_ids.add(bounce_info['message_id'])

            return True
            
        except Exception as e:
            print(f'❌ バウンスメール特定失敗: {e}')
            return False

    def decode_mime_words(self, s):
        """MIMEエンコードされた文字列をデコード"""
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
        except:
            return s

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
                    # 除外するアドレス（システムアドレスなど）
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

    def organize_bounce_emails(self):
        """バウンスメールを整理（bounceフォルダへ移動）"""
        try:
            print('\n📁 バウンスメールを整理中...')

            # bounceフォルダの存在確認
            bounce_folder = 'bounce'
            bounce_folder_exists = False

            try:
                # 利用可能なフォルダ一覧を取得
                status, mailboxes = self.mail.list()
                if status == 'OK':
                    for mailbox in mailboxes:
                        mailbox_name = mailbox.decode().split('"')[-2] if '"' in mailbox.decode() else mailbox.decode().split()[-1]
                        if mailbox_name.lower() == 'bounce':
                            bounce_folder_exists = True
                            bounce_folder = mailbox_name
                            print(f'   ✅ bounceフォルダが見つかりました: {bounce_folder}')
                            break

                if not bounce_folder_exists:
                    print(f'   ⚠️ bounceフォルダが見つかりません。利用可能なフォルダ:')
                    for mailbox in mailboxes[:10]:  # 最初の10個を表示
                        print(f'     {mailbox.decode()}')

                    # bounceフォルダを作成を試行
                    try:
                        self.mail.create('bounce')
                        bounce_folder = 'bounce'
                        bounce_folder_exists = True
                        print(f'   ✅ bounceフォルダを作成しました')
                    except Exception as create_error:
                        print(f'   ❌ bounceフォルダ作成失敗: {create_error}')
                        # INBOX.bounceを試行
                        try:
                            self.mail.create('INBOX.bounce')
                            bounce_folder = 'INBOX.bounce'
                            bounce_folder_exists = True
                            print(f'   ✅ INBOX.bounceフォルダを作成しました')
                        except Exception as create_error2:
                            print(f'   ❌ INBOX.bounceフォルダ作成も失敗: {create_error2}')

            except Exception as e:
                print(f'   ⚠️ フォルダ確認エラー: {e}')

            # INBOXを選択
            self.mail.select('INBOX')

            moved_count = 0
            failed_count = 0

            for bounce_info in self.bounce_emails:
                try:
                    msg_id = bounce_info['message_id']
                    subject = bounce_info['subject'][:50]

                    if bounce_folder_exists:
                        # bounceフォルダに移動
                        try:
                            self.mail.move(msg_id, bounce_folder)
                            moved_count += 1
                            print(f'   ✅ 移動完了: ID {msg_id} - {subject}... → {bounce_folder}フォルダ')
                        except AttributeError:
                            # moveメソッドがない場合はcopy + delete
                            self.mail.copy(msg_id, bounce_folder)
                            self.mail.store(msg_id, '+FLAGS', '\\Deleted')
                            moved_count += 1
                            print(f'   ✅ 移動完了: ID {msg_id} - {subject}... → {bounce_folder}フォルダ (copy+delete)')
                        except Exception as move_error:
                            print(f'   ❌ 移動失敗: ID {msg_id} - {subject}... エラー: {move_error}')
                            # フォールバック: フラグ設定のみ
                            self.mail.store(msg_id, '+FLAGS', '\\Flagged')
                            self.mail.store(msg_id, '+FLAGS', '\\Seen')
                            failed_count += 1
                    else:
                        # bounceフォルダがない場合はフラグ設定のみ
                        self.mail.store(msg_id, '+FLAGS', '\\Flagged')
                        self.mail.store(msg_id, '+FLAGS', '\\Seen')
                        failed_count += 1
                        print(f'   ⚠️ フラグ設定のみ: ID {msg_id} - {subject}... (bounceフォルダなし)')

                except Exception as e:
                    print(f'   ⚠️ 処理エラー (ID: {msg_id}): {e}')
                    failed_count += 1

            # 削除フラグを適用（moveまたはcopy+deleteの場合）
            if moved_count > 0:
                try:
                    self.mail.expunge()
                    print(f'✅ バウンスメール整理完了:')
                    print(f'   bounceフォルダに移動: {moved_count}件')
                    if failed_count > 0:
                        print(f'   フラグ設定のみ: {failed_count}件')
                    print(f'   📧 バウンスメールは{bounce_folder}フォルダに移動されました')
                except Exception as e:
                    print(f'✅ バウンスメール整理完了:')
                    print(f'   移動処理: {moved_count}件')
                    if failed_count > 0:
                        print(f'   フラグ設定のみ: {failed_count}件')
                    print(f'   ⚠️ expunge処理でエラー: {e}')
            else:
                print(f'✅ バウンスメール整理完了:')
                if failed_count > 0:
                    print(f'   フラグ設定のみ: {failed_count}件')
                print(f'   📧 処理対象メールなし')

            return True

        except Exception as e:
            print(f'❌ バウンスメール整理失敗: {e}')
            return False

    def generate_bounce_report(self):
        """バウンス処理レポートを生成"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = f'huganjob_bounce_report_{timestamp}.json'
            
            report_data = {
                'processing_date': datetime.datetime.now().isoformat(),
                'total_bounce_emails': len(self.bounce_emails),
                'bounce_details': self.bounce_emails,
                'summary': {
                    'permanent_bounces': len([b for b in self.bounce_emails if b['bounce_type'] == 'permanent']),
                    'temporary_bounces': len([b for b in self.bounce_emails if b['bounce_type'] == 'temporary']),
                    'unknown_bounces': len([b for b in self.bounce_emails if b['bounce_type'] == 'unknown'])
                }
            }
            
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            print(f'📄 バウンスレポートを生成しました: {report_filename}')
            return report_filename

        except Exception as e:
            print(f'❌ レポート生成失敗: {e}')
            return None

    def update_company_database(self):
        """企業データベースを更新"""
        if not self.bounce_emails:
            print('📝 更新対象のバウンスメールがありません')
            return True

        try:
            print(f'\n📝 企業データベースを更新中... ({len(self.bounce_emails)}件のバウンスメール)')

            # バックアップ作成
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'data/new_input_test_backup_bounce_processor_{timestamp}.csv'

            df_companies = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
            df_companies.to_csv(backup_filename, index=False, encoding='utf-8-sig')
            print(f'📁 バックアップ作成: {backup_filename}')

            # 送信結果ファイルを読み込み
            df_results = pd.read_csv('new_email_sending_results.csv', encoding='utf-8-sig')

            # バウンス状態列を確認・追加
            if 'バウンス状態' not in df_companies.columns:
                df_companies['バウンス状態'] = ''
            if 'バウンス日時' not in df_companies.columns:
                df_companies['バウンス日時'] = ''
            if 'バウンス理由' not in df_companies.columns:
                df_companies['バウンス理由'] = ''

            updated_count = 0

            # 各バウンスメールを処理
            for bounce_info in self.bounce_emails:
                bounced_addresses = bounce_info['bounced_addresses']

                for bounced_email in bounced_addresses:
                    # 送信結果から該当企業を検索
                    matches = df_results[df_results['メールアドレス'].str.lower() == bounced_email.lower()]

                    for _, match in matches.iterrows():
                        company_id = match['企業ID']
                        company_name = match['企業名']

                        # 企業データベースを更新
                        mask = df_companies['ID'] == company_id
                        if mask.any():
                            df_companies.loc[mask, 'バウンス状態'] = bounce_info['bounce_type']
                            df_companies.loc[mask, 'バウンス日時'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            df_companies.loc[mask, 'バウンス理由'] = bounce_info['subject']

                            updated_count += 1
                            print(f'   ✅ ID {company_id}: {company_name} - {bounce_info["bounce_type"]}バウンス ({bounced_email})')

            # 更新されたデータを保存
            df_companies.to_csv('data/new_input_test.csv', index=False, encoding='utf-8-sig')
            print(f'💾 企業データベース更新完了: {updated_count}社')

            return True

        except Exception as e:
            print(f'❌ 企業データベース更新失敗: {e}')
            return False

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
    print('=== HUGANJOB バウンスメール処理システム ===')
    print('📧 バウンスメールをbounceフォルダに移動して整理・管理します')
    print()

    processor = HuganjobBounceProcessor()

    try:
        # メールボックスに接続
        if not processor.connect_to_mailbox():
            return False

        # バウンスメールを特定（重複処理防止）
        if not processor.identify_bounce_emails():
            return False

        # 新規バウンスメールがある場合のみ処理
        if len(processor.bounce_emails) > 0:
            # バウンスメールを整理（bounceフォルダに移動）
            if not processor.organize_bounce_emails():
                return False

            # 企業データベースを更新
            if not processor.update_company_database():
                return False

            # 処理済み追跡ファイルを更新
            processor.save_processed_tracking()

            # レポート生成
            report_file = processor.generate_bounce_report()

            print('\n🎯 バウンスメール処理完了')
            print(f'📊 新規処理: {len(processor.bounce_emails)}件')
            print(f'📁 処理済み総数: {len(processor.processed_message_ids)}件')
            print(f'📧 バウンスメールはbounceフォルダに移動されました')
            print(f'🏢 企業データベースが更新されました')

            if report_file:
                print(f'📄 詳細レポート: {report_file}')
        else:
            print('✅ 新規バウンスメールはありません')
            print(f'📁 処理済み総数: {len(processor.processed_message_ids)}件')

        return True

    except Exception as e:
        print(f'❌ 処理中にエラーが発生しました: {e}')
        return False

    finally:
        processor.disconnect()

if __name__ == "__main__":
    main()
