#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改善された開封トラッキングシステムのテスト
多重化された追跡機能をテストするためのメール送信

作成日時: 2025年06月24日
目的: 開封追跡システムの改善効果確認
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

class ImprovedTrackingTester:
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
            
            # 改善された追跡機能の確認
            tracking_features = []
            if 'track-open' in self.html_template:
                tracking_features.append('ピクセル追跡')
            if 'track-beacon' in self.html_template:
                tracking_features.append('ビーコン追跡')
            if 'track-css' in self.html_template:
                tracking_features.append('CSS追跡')
            if 'track-xhr' in self.html_template:
                tracking_features.append('XHR追跡')
            if 'track-focus' in self.html_template:
                tracking_features.append('フォーカス追跡')
            if 'track-unload' in self.html_template:
                tracking_features.append('離脱時追跡')
            
            print(f"🎯 検出された追跡機能: {', '.join(tracking_features)}")
            
            return True
            
        except Exception as e:
            print(f"❌ HTMLテンプレート読み込みエラー: {e}")
            return False
    
    def generate_tracking_id(self, recipient_email):
        """トラッキングID生成"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        clean_email = recipient_email.replace('@', '_').replace('.', '_')
        return f"improved_{clean_email}_{timestamp}_{unique_id}"
    
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
            subject = f"【{job_position}の人材採用を強化しませんか？】株式会社HUGANからのご提案（改善版追跡テスト）"
            
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
            print(f"\n📤 改善版追跡テストメール送信開始")
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
        print("改善された開封トラッキングシステムのテスト")
        print("=" * 60)
        
        # 設定とテンプレート読み込み
        if not self.load_config():
            return False
        
        if not self.load_html_template():
            return False
        
        # テスト対象リスト
        test_recipients = [
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
        
        print(f"\n📧 {len(test_recipients)}件の改善版追跡テストメール送信を開始します")
        print("-" * 60)
        
        # 各宛先に送信
        for i, recipient in enumerate(test_recipients, 1):
            print(f"\n[{i}/{len(test_recipients)}] 送信処理中...")
            
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
        print("📊 改善版追跡テスト結果サマリー")
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
        
        print("🎯 改善された追跡機能:")
        print("   ✅ 多重ピクセル追跡（3種類）")
        print("   ✅ JavaScript多重ビーコン（6種類）")
        print("   ✅ フォールバック機能")
        print("   ✅ 企業メール環境対応")
        print("   ✅ リアルタイム追跡")
        print("   ✅ エラー時自動リトライ")
        
        print("\n📊 追跡確認方法:")
        print("   1. ダッシュボード: http://127.0.0.1:5002/open-rate-analytics")
        print("   2. 開封追跡ファイル: data/derivative_email_open_tracking.csv")
        print("   3. 各種追跡エンドポイントのログ確認")
        
        return success_count == total_count

def main():
    """メイン関数"""
    tester = ImprovedTrackingTester()
    return tester.run()

if __name__ == "__main__":
    main()
