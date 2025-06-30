#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ID=2 ラ・シンシア株式会社向けテストメール送信スクリプト
更新されたHUGAN JOBテンプレートを使用
"""

import os
import sys
import configparser
import smtplib
import uuid
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr, formatdate

def load_template():
    """corporate-email-newsletter.htmlテンプレートを読み込み"""
    template_file = 'corporate-email-newsletter.html'
    if not os.path.exists(template_file):
        print(f"❌ テンプレートファイルが見つかりません: {template_file}")
        return None
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✅ テンプレートファイルを読み込みました: {template_file}")
        return content
    except Exception as e:
        print(f"❌ テンプレートファイルの読み込みに失敗: {e}")
        return None

def generate_email_content(template_content, company_name, job_position):
    """メール内容を生成（企業名と募集職種を挿入）"""
    try:
        # テンプレート内の変数を実際の値に置換
        email_content = template_content.replace('{{company_name}}', company_name)
        email_content = email_content.replace('{{job_position}}', job_position)
        
        # 追跡用のユニークIDを生成
        tracking_id = str(uuid.uuid4())
        
        # 開封追跡用の画像タグを追加
        tracking_pixel = f'<img src="http://127.0.0.1:5002/track/{tracking_id}" width="1" height="1" style="display:none;" />'
        email_content = email_content.replace('</body>', f'{tracking_pixel}</body>')
        
        return email_content, tracking_id
    except Exception as e:
        print(f"❌ メール内容生成に失敗: {e}")
        return None, None

def send_email():
    """ID=2のラ・シンシア株式会社にメール送信"""
    try:
        # 企業データ
        company_name = "ラ・シンシア株式会社"
        job_position = "製造スタッフ"
        recipient_email = "naoki_yamashita@fortyfive.co.jp"
        
        print("🚀 HUGAN JOB メール送信開始")
        print("=" * 50)
        print(f"📋 送信先企業: {company_name}")
        print(f"📋 募集職種: {job_position}")
        print(f"📋 送信先メール: {recipient_email}")
        print("=" * 50)
        
        # 設定ファイルを読み込み
        config = configparser.ConfigParser()
        config_file = 'config/huganjob_email_config.ini'
        
        if not os.path.exists(config_file):
            print(f"❌ 設定ファイルが見つかりません: {config_file}")
            return False
            
        config.read(config_file, encoding='utf-8')
        
        # SMTP設定を取得
        smtp_server = config.get('SMTP', 'server')
        smtp_port = config.getint('SMTP', 'port')
        smtp_user = config.get('SMTP', 'user')
        smtp_password = config.get('SMTP', 'password')
        sender_name = config.get('SMTP', 'sender_name')
        from_email = config.get('SMTP', 'from_email')
        
        print(f"📡 SMTPサーバー: {smtp_server}:{smtp_port}")
        print(f"📧 送信者: {sender_name} <{from_email}>")
        
        # メール件名を生成（募集職種を含む）
        subject = f'【{job_position}の人材採用を強化しませんか？】株式会社HUGANからのご提案'
        
        # メッセージを作成
        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr((sender_name, from_email))
        msg['To'] = recipient_email
        msg['Subject'] = Header(subject, 'utf-8')
        msg['Reply-To'] = from_email
        
        # 迷惑メール対策のための追加ヘッダー
        msg['Message-ID'] = f"<huganjob-{int(time.time())}-{uuid.uuid4().hex[:8]}@huganjob.jp>"
        msg['Date'] = formatdate(localtime=True)
        msg['X-Mailer'] = 'HUGAN JOB Marketing System'
        msg['X-Priority'] = '3'
        
        print(f"📧 件名: {subject}")
        
        # プレーンテキスト版を作成
        plain_text = f"""
{company_name}
採用ご担当者様

初めてご連絡いたします。
株式会社HUGANで、人材紹介サービス「HUGAN JOB」を担当しております竹下と申します。

この度、貴社が募集されております「{job_position}」の求人を拝見し、弊社のサービスが貴社の採用活動に貢献できるものと考え、ご連絡いたしました。

まずは、弊社のサービスが選ばれる3つの理由をご覧ください。

【サービスの特徴】
✓ 初期費用0円（完全成功報酬型）
✓ 採用工数の大幅削減
✓ 早期退職時の一部返金保証
✓ 正社員・契約社員・パート・アルバイト全対応

詳細はこちら: https://www.hugan.co.jp/business

ご不明な点がございましたら、お気軽にお問い合わせください。

---
株式会社HUGAN
竹下隼平
Email: contact@huganjob.jp
Tel: 0120-917-906

配信停止をご希望の場合は下記フォームよりお手続きください：
https://forms.gle/49BTNfSgUeNkH7rz5

送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
送信先: {recipient_email}
更新版テンプレート使用
"""
        
        # プレーンテキストパートを追加
        text_part = MIMEText(plain_text.strip(), 'plain', 'utf-8')
        msg.attach(text_part)
        
        # HTMLテンプレートを読み込み
        template_content = load_template()
        if template_content:
            html_content, tracking_id = generate_email_content(template_content, company_name, job_position)
            if html_content:
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
                print("✅ HTMLメール作成成功")
                print(f"🔍 トラッキングID: {tracking_id}")
            else:
                print("⚠️ HTMLメール生成に失敗（プレーンテキストのみ）")
        else:
            print("⚠️ HTMLテンプレートが見つかりません（プレーンテキストのみ）")
        
        # SMTP接続してメール送信
        print("\n📤 メール送信中...")
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # TLS暗号化を開始
            server.login(smtp_user, smtp_password)
            
            # メール送信
            server.send_message(msg)
            
        print("✅ メール送信成功！")
        print(f"📧 送信完了: {recipient_email}")
        print(f"🕐 送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ メール送信失敗: {e}")
        import traceback
        print(f"詳細エラー: {traceback.format_exc()}")
        return False

def main():
    """メイン関数"""
    print("🎯 ID=2 ラ・シンシア株式会社向けテストメール送信")
    
    success = send_email()
    
    if success:
        print("\n🎉 送信完了！")
        print("\n📝 確認事項:")
        print("  • 件名に「製造スタッフ」が含まれているか")
        print("  • 企業名が「ラ・シンシア株式会社」になっているか")
        print("  • 担当者名が「竹下」になっているか")
        print("  • 送信者名が「竹下隼平【株式会社HUGAN】」になっているか")
        print("  • 求人内容で「製造スタッフ」が言及されているか")
    else:
        print("\n❌ 送信失敗")

if __name__ == "__main__":
    main()
