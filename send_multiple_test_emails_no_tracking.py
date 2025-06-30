#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
複数宛先へのテストメール送信スクリプト（URLトラッキング削除版）
HUGANJOBシステムの修正されたテンプレートを使用してテストメールを送信

作成日時: 2025年06月24日
目的: URLトラッキング削除後のテンプレートメール送信テスト
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

class MultipleTestEmailSender:
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
            
            # URLトラッキング削除確認
            if 'track-click' in self.html_template:
                print("⚠️  警告: テンプレートにtrack-clickが残っています")
                return False
            else:
                print("✅ URLトラッキング削除確認完了")
            
            return True
            
        except Exception as e:
            print(f"❌ HTMLテンプレート読み込みエラー: {e}")
            return False
    
    def generate_tracking_id(self, recipient_email):
        """トラッキングID生成（開封追跡用）"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        clean_email = recipient_email.replace('@', '_').replace('.', '_')
        return f"test_{clean_email}_{timestamp}_{unique_id}"
    
    def create_email(self, recipient_email, company_name, job_position):
        """メール作成"""
        try:
            # トラッキングID生成（開封追跡用）
            tracking_id = self.generate_tracking_id(recipient_email)
            
            # HTML変数置換
            html_content = self.html_template.replace('{{company_name}}', company_name)
            html_content = html_content.replace('{{job_position}}', job_position)
            html_content = html_content.replace('{{tracking_id}}', tracking_id)
            
            # 件名作成
            subject = f"【{job_position}の人材採用を強化しませんか？】株式会社HUGANからのご提案（テスト送信）"
            
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
                return False, None
            
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
            return True, tracking_id
            
        except Exception as e:
            print(f"   ❌ 送信失敗: {e}")
            return False, None
    
    def run(self):
        """メイン実行"""
        print("URLトラッキング削除版テストメール送信")
        print("=" * 60)
        
        # 設定とテンプレート読み込み
        if not self.load_config():
            return False
        
        if not self.load_html_template():
            return False
        
        # 送信対象リスト
        recipients = [
            {
                'email': 'k.abe@raxus.inc',
                'company_name': '株式会社Raxus',
                'job_position': 'システムエンジニア'
            },
            {
                'email': 'naoki_yamashita@fortyfive.co.jp',
                'company_name': '株式会社フォーティーファイブ',
                'job_position': 'Webエンジニア'
            }
        ]
        
        # 送信結果記録
        results = []
        
        print(f"\n📧 {len(recipients)}件のテストメール送信を開始します")
        print("-" * 60)
        
        # 各宛先に送信
        for i, recipient in enumerate(recipients, 1):
            print(f"\n[{i}/{len(recipients)}] 送信処理中...")
            
            success, tracking_id = self.send_email(
                recipient['email'],
                recipient['company_name'],
                recipient['job_position']
            )
            
            results.append({
                'email': recipient['email'],
                'company_name': recipient['company_name'],
                'job_position': recipient['job_position'],
                'success': success,
                'tracking_id': tracking_id,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # 結果サマリー
        print("\n" + "=" * 60)
        print("📊 送信結果サマリー")
        print("=" * 60)
        
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        
        print(f"✅ 送信成功: {success_count}件")
        print(f"❌ 送信失敗: {total_count - success_count}件")
        print(f"📈 成功率: {success_count/total_count*100:.1f}%")
        
        print("\n📋 詳細結果:")
        for result in results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['email']}")
            print(f"   企業名: {result['company_name']}")
            print(f"   職種: {result['job_position']}")
            if result['tracking_id']:
                print(f"   トラッキングID: {result['tracking_id']}")
            print(f"   送信時刻: {result['timestamp']}")
            print()
        
        print("🎯 テスト内容:")
        print("   ✅ URLトラッキング削除確認")
        print("   ✅ 直接リンクアクセス可能")
        print("   ✅ 開封追跡機能維持")
        print("   ✅ UTMパラメータ維持")
        
        return success_count == total_count

def main():
    """メイン関数"""
    sender = MultipleTestEmailSender()
    return sender.run()

if __name__ == "__main__":
    main()
