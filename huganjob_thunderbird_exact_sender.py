#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB Thunderbird完全模倣送信システム
Thunderbirdの送信方式を完全に模倣して迷惑メール判定を回避

作成日: 2025年6月27日
目的: Thunderbirdと全く同じ方式でメール送信
"""

import smtplib
import configparser
import argparse
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid, formataddr
from email.header import Header
import pandas as pd
import os

class HuganjobThunderbirdExactSender:
    def __init__(self):
        # 設定読み込み
        self.config = configparser.ConfigParser()
        self.config.read('config/huganjob_email_config.ini', encoding='utf-8')
        
        # SMTP設定
        self.smtp_server = self.config.get('SMTP', 'server')
        self.smtp_port = int(self.config.get('SMTP', 'port'))
        self.smtp_user = self.config.get('SMTP', 'user')
        self.smtp_password = self.config.get('SMTP', 'password')
        
        # 送信者情報
        self.sender_name = self.config.get('SMTP', 'sender_name')
        self.sender_email = self.config.get('SMTP', 'from_email')
        
        # HTMLテンプレート読み込み
        self.load_html_template()
        
    def load_html_template(self):
        """HTMLテンプレート読み込み"""
        try:
            with open('corporate-email-newsletter.html', 'r', encoding='utf-8') as f:
                self.html_template = f.read()
            print("✅ HTMLテンプレート読み込み完了")
        except Exception as e:
            print(f"❌ HTMLテンプレート読み込みエラー: {e}")
            self.html_template = None
            
    def create_thunderbird_exact_email(self, company_name, job_position, recipient_email):
        """Thunderbird完全模倣メール作成"""
        
        # HTMLコンテンツ作成（変数置換）
        html_content = self.html_template.replace('{{company_name}}', company_name)
        html_content = html_content.replace('{{job_position}}', job_position)
        
        # 件名作成
        subject_template = self.config.get('EMAIL_CONTENT', 'subject')
        subject = subject_template.replace('{job_position}', job_position)
        
        # 🚨 重要：Thunderbird方式 - MIMEMultipartではなく単純なMIMEText
        msg = MIMEText(html_content, 'html', 'utf-8')
        
        # 🚨 重要：Thunderbird方式のヘッダー（最小限）
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = formataddr((self.sender_name, self.sender_email))
        msg['To'] = recipient_email
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid(domain='huganjob.jp')
        
        # 🚨 重要：Thunderbird特有のヘッダーは一切追加しない
        # ❌ X-Mailer なし
        # ❌ User-Agent なし  
        # ❌ X-Priority なし
        # ❌ List-Unsubscribe なし
        # ❌ Authentication-Results なし
        
        return msg, subject
        
    def send_email(self, start_id=None, end_id=None):
        """Thunderbird完全模倣送信"""
        
        # 企業データ読み込み
        try:
            df = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')
        except Exception as e:
            print(f"❌ CSVファイル読み込みエラー: {e}")
            return
            
        # ID範囲でフィルタリング
        if start_id is not None:
            df = df[df['ID'] >= start_id]
        if end_id is not None:
            df = df[df['ID'] <= end_id]
            
        print(f"📧 Thunderbird完全模倣送信開始: {len(df)}社")
        
        # SMTP接続
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            
            for index, row in df.iterrows():
                try:
                    company_id = str(row['ID'])
                    company_name = row['企業名']
                    job_position = row['募集職種'].split('/')[0] if pd.notna(row['募集職種']) else 'システムエンジニア'
                    
                    # メールアドレス取得
                    email_address = row.get('担当者メールアドレス', '')
                    if pd.isna(email_address) or email_address in ['', '未登録', '-', '‐']:
                        print(f"⚠️ ID {company_id}: メールアドレス不明")
                        continue
                    
                    print(f"\n📤 ID {company_id}: {company_name} 送信開始")
                    print(f"   📧 宛先: {email_address}")
                    print(f"   💼 職種: {job_position}")
                    
                    # Thunderbird完全模倣メール作成
                    msg, subject = self.create_thunderbird_exact_email(
                        company_name, job_position, email_address
                    )
                    
                    print(f"   📝 件名: {subject}")
                    print(f"   🎨 形式: HTML単体（MIMEMultipartなし）")
                    print(f"   🔧 ヘッダー: Thunderbird完全模倣")
                    
                    # メール送信
                    server.send_message(msg)
                    
                    print(f"   ✅ 送信成功: {email_address}")
                    
                except Exception as e:
                    print(f"   ❌ ID {company_id}: 送信エラー - {e}")
                    
            server.quit()
            print(f"\n🎉 Thunderbird完全模倣送信完了")
            
        except Exception as e:
            print(f"❌ SMTP接続エラー: {e}")

def main():
    parser = argparse.ArgumentParser(description='HUGANJOB Thunderbird完全模倣送信システム')
    parser.add_argument('--start-id', type=int, help='送信開始ID')
    parser.add_argument('--end-id', type=int, help='送信終了ID')
    
    args = parser.parse_args()
    
    sender = HuganjobThunderbirdExactSender()
    sender.send_email(args.start_id, args.end_id)

if __name__ == "__main__":
    main()
