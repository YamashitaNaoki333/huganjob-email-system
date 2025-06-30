#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
k.abe@raxus.incへのテンプレートメール送信スクリプト
HUGANJOBシステムのテンプレートを使用してテストメールを送信

作成日時: 2025年06月24日
目的: 指定されたメールアドレスへのテンプレートメール送信
"""

import smtplib
import os
import configparser
import uuid
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate

class RaxusEmailSender:
    def __init__(self):
        self.config = None
        self.html_template = None
        
    def load_config(self):
        """設定ファイルを読み込み"""
        try:
            self.config = configparser.ConfigParser()
            config_path = 'config/huganjob_email_config.ini'
            
            if not os.path.exists(config_path):
                print(f"❌ 設定ファイルが見つかりません: {config_path}")
                return False
            
            self.config.read(config_path, encoding='utf-8')
            print(f"✅ 設定ファイル読み込み完了: {config_path}")
            return True
            
        except Exception as e:
            print(f"❌ 設定ファイル読み込みエラー: {e}")
            return False
    
    def load_html_template(self):
        """HTMLテンプレートを読み込み"""
        try:
            template_path = 'corporate-email-newsletter.html'
            
            if not os.path.exists(template_path):
                print(f"❌ HTMLテンプレートが見つかりません: {template_path}")
                return False
            
            with open(template_path, 'r', encoding='utf-8') as f:
                self.html_template = f.read()
            
            print(f"✅ HTMLテンプレート読み込み完了: {template_path}")
            return True
            
        except Exception as e:
            print(f"❌ HTMLテンプレート読み込みエラー: {e}")
            return False
    
    def generate_tracking_id(self, recipient_email):
        """トラッキングID生成"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        return f"raxus_{recipient_email.replace('@', '_')}_{timestamp}_{unique_id}"
    
    def create_email(self, recipient_email, company_name, job_position):
        """メール作成"""
        try:
            # トラッキングID生成
            tracking_id = self.generate_tracking_id(recipient_email)
            
            # HTML変数置換
            html_content = self.html_template.replace('{{company_name}}', company_name)
            html_content = html_content.replace('{{job_position}}', job_position)
            html_content = html_content.replace('{{tracking_id}}', tracking_id)
            
            # 件名作成
            subject = f"【{job_position}の人材採用を強化しませんか？】株式会社HUGANからのご提案"
            
            # メール作成
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = formataddr(('竹下隼平【株式会社HUGAN】', 'contact@huganjob.jp'))
            msg['To'] = recipient_email
            msg['Reply-To'] = 'contact@huganjob.jp'
            msg['Date'] = formatdate(localtime=True)
            
            # HTMLパート追加
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            return msg, tracking_id
            
        except Exception as e:
            print(f"❌ メール作成エラー: {e}")
            return None, None
    
    def send_email(self, recipient_email, company_name, job_position):
        """メール送信"""
        try:
            print(f"\n📤 メール送信開始")
            print(f"   宛先: {recipient_email}")
            print(f"   企業名: {company_name}")
            print(f"   職種: {job_position}")
            
            # メール作成
            msg, tracking_id = self.create_email(recipient_email, company_name, job_position)
            if not msg:
                return False
            
            print(f"   トラッキングID: {tracking_id}")
            
            # SMTP設定取得
            smtp_server = self.config.get('SMTP', 'server')
            smtp_port = int(self.config.get('SMTP', 'port'))
            smtp_user = self.config.get('SMTP', 'user')
            smtp_password = self.config.get('SMTP', 'password')
            
            print(f"   SMTP: {smtp_server}:{smtp_port}")
            
            # SMTP送信
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            
            print(f"   ✅ 送信成功!")
            return True
            
        except Exception as e:
            print(f"   ❌ 送信失敗: {e}")
            return False
    
    def run(self):
        """メイン実行"""
        print("k.abe@raxus.incへのテンプレートメール送信")
        print("=" * 50)
        
        # 設定とテンプレート読み込み
        if not self.load_config():
            return False
        
        if not self.load_html_template():
            return False
        
        # 送信パラメータ
        recipient_email = "k.abe@raxus.inc"
        company_name = "株式会社Raxus"
        job_position = "システムエンジニア"
        
        # メール送信
        success = self.send_email(recipient_email, company_name, job_position)
        
        if success:
            print(f"\n🎉 テンプレートメール送信完了!")
            print(f"📧 宛先: {recipient_email}")
            print(f"🏢 企業名: {company_name}")
            print(f"💼 職種: {job_position}")
            print(f"📝 テンプレート: corporate-email-newsletter.html")
            print(f"👤 送信者: 竹下隼平【株式会社HUGAN】")
            print(f"📮 送信元: contact@huganjob.jp")
        else:
            print(f"\n❌ メール送信に失敗しました")
        
        return success

def main():
    """メイン関数"""
    sender = RaxusEmailSender()
    return sender.run()

if __name__ == "__main__":
    main()
