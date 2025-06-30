#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB メールボックス調査システム

全メールボックスを調査してバウンスメールの所在を特定
"""

import imaplib
import email
from email.header import decode_header

class HuganjobMailboxInvestigator:
    def __init__(self):
        self.imap_server = 'sv12053.xserver.jp'
        self.imap_port = 993
        self.username = 'contact@huganjob.jp'
        self.password = 'gD34bEmB'
    
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
    
    def investigate_all_folders(self):
        """全フォルダを調査"""
        try:
            print('\n📁 全メールボックスフォルダを調査中...')
            
            # フォルダ一覧を取得
            status, mailboxes = self.mail.list()
            if status != 'OK':
                print('❌ フォルダ一覧取得失敗')
                return False
            
            print(f'📊 利用可能なフォルダ数: {len(mailboxes)}個')
            print('-' * 60)
            
            total_bounce_candidates = 0
            
            for mailbox in mailboxes:
                try:
                    # フォルダ名を抽出
                    mailbox_str = mailbox.decode()
                    folder_name = mailbox_str.split('"')[-2] if '"' in mailbox_str else mailbox_str.split()[-1]
                    
                    print(f'\n📂 フォルダ: {folder_name}')
                    
                    # フォルダを選択
                    self.mail.select(folder_name)
                    
                    # 全メール数を取得
                    status, messages = self.mail.search(None, 'ALL')
                    if status == 'OK':
                        total_messages = len(messages[0].split()) if messages[0] else 0
                        print(f'   📧 総メール数: {total_messages}件')
                        
                        if total_messages > 0:
                            # バウンス関連メールを検索
                            bounce_count = self.search_bounce_emails_in_folder(folder_name)
                            total_bounce_candidates += bounce_count
                            
                            # 最近のメールを確認（最新5件）
                            if total_messages > 0:
                                recent_count = min(5, total_messages)
                                self.show_recent_emails(folder_name, recent_count)
                    else:
                        print(f'   ❌ フォルダアクセス失敗: {folder_name}')
                
                except Exception as e:
                    print(f'   ⚠️ フォルダ調査エラー ({folder_name}): {e}')
            
            print(f'\n📊 調査結果サマリー:')
            print(f'   🎯 バウンス候補メール総数: {total_bounce_candidates}件')
            
            return True
            
        except Exception as e:
            print(f'❌ フォルダ調査失敗: {e}')
            return False
    
    def search_bounce_emails_in_folder(self, folder_name):
        """指定フォルダでバウンスメールを検索"""
        bounce_subjects = [
            'SUBJECT "Mail delivery failed"',
            'SUBJECT "Undelivered Mail"',
            'SUBJECT "Delivery Status Notification"',
            'SUBJECT "failure notice"',
            'SUBJECT "returned mail"',
            'SUBJECT "Returned mail"',
            'FROM "Mail Delivery Subsystem"',
            'FROM "postmaster"',
            'FROM "mailer-daemon"',
            'FROM "MAILER-DAEMON"'
        ]
        
        total_bounce_count = 0
        
        for search_criteria in bounce_subjects:
            try:
                status, messages = self.mail.search(None, search_criteria)
                if status == 'OK' and messages[0]:
                    count = len(messages[0].split())
                    if count > 0:
                        print(f'     🚨 {search_criteria}: {count}件')
                        total_bounce_count += count
            except Exception as e:
                print(f'     ⚠️ 検索エラー ({search_criteria}): {e}')
        
        if total_bounce_count > 0:
            print(f'   🎯 バウンス候補: {total_bounce_count}件')
        
        return total_bounce_count
    
    def show_recent_emails(self, folder_name, count=5):
        """最近のメールを表示"""
        try:
            # 最新のメールIDを取得
            status, messages = self.mail.search(None, 'ALL')
            if status == 'OK' and messages[0]:
                message_ids = messages[0].split()
                recent_ids = message_ids[-count:] if len(message_ids) >= count else message_ids
                
                print(f'   📋 最新{len(recent_ids)}件のメール:')
                
                for i, msg_id in enumerate(reversed(recent_ids), 1):
                    try:
                        status, msg_data = self.mail.fetch(msg_id, '(ENVELOPE)')
                        if status == 'OK':
                            envelope = msg_data[0][1]
                            # 簡易的な件名抽出
                            envelope_str = str(envelope)
                            
                            # より詳細な情報を取得
                            status, msg_data = self.mail.fetch(msg_id, '(RFC822.HEADER)')
                            if status == 'OK':
                                header_data = msg_data[0][1]
                                email_message = email.message_from_bytes(header_data)
                                
                                subject = self.decode_mime_words(email_message.get('Subject', ''))
                                from_addr = email_message.get('From', '')
                                date = email_message.get('Date', '')
                                
                                print(f'     {i}. 件名: {subject[:50]}...')
                                print(f'        送信者: {from_addr}')
                                print(f'        日時: {date}')
                                
                                # バウンス関連キーワードをチェック
                                bounce_keywords = ['delivery', 'failed', 'bounce', 'undelivered', 'returned']
                                if any(keyword in subject.lower() for keyword in bounce_keywords):
                                    print(f'        🚨 バウンス関連メールの可能性')
                                print()
                    
                    except Exception as e:
                        print(f'     ⚠️ メール{i}の詳細取得エラー: {e}')
        
        except Exception as e:
            print(f'   ⚠️ 最新メール表示エラー: {e}')
    
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
    print('=== HUGANJOB メールボックス調査システム ===')
    print('🔍 全メールボックスを調査してバウンスメールの所在を特定します')
    print()
    
    investigator = HuganjobMailboxInvestigator()
    
    try:
        # メールボックスに接続
        if not investigator.connect_to_mailbox():
            return False
        
        # 全フォルダを調査
        if not investigator.investigate_all_folders():
            return False
        
        print('\n🎯 メールボックス調査完了')
        
        return True
        
    except Exception as e:
        print(f'❌ 処理中にエラーが発生しました: {e}')
        return False
    
    finally:
        investigator.disconnect()

if __name__ == "__main__":
    main()
