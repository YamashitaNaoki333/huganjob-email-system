#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ID=2 ラ・シンシア株式会社向け即座メール送信
"""

import os
import smtplib
import uuid
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr, formatdate

def send_test_email():
    """テストメール送信"""
    try:
        # 企業データ
        company_name = "ラ・シンシア株式会社"
        job_position = "製造スタッフ"
        recipient_email = "naoki_yamashita@fortyfive.co.jp"
        
        print(f"📧 送信開始: {company_name} ({job_position})")
        print(f"📧 送信先: {recipient_email}")
        
        # SMTP設定
        smtp_server = "smtp.huganjob.jp"
        smtp_port = 587
        smtp_user = "contact@huganjob.jp"
        smtp_password = "gD34bEmB"
        sender_name = "竹下隼平【株式会社HUGAN】"
        from_email = "contact@huganjob.jp"
        
        # メール件名
        subject = f"【{job_position}の人材採用を強化しませんか？】株式会社HUGANからのご提案"
        
        # メッセージ作成
        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr((sender_name, from_email))
        msg['To'] = recipient_email
        msg['Subject'] = Header(subject, 'utf-8')
        msg['Reply-To'] = from_email
        msg['Message-ID'] = f"<huganjob-test-{int(datetime.now().timestamp())}@huganjob.jp>"
        msg['Date'] = formatdate(localtime=True)
        
        # プレーンテキスト
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

詳細: https://www.hugan.co.jp/business

---
株式会社HUGAN 竹下隼平
Email: contact@huganjob.jp
Tel: 0120-917-906

送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
更新版テンプレート使用
"""
        
        text_part = MIMEText(plain_text.strip(), 'plain', 'utf-8')
        msg.attach(text_part)
        
        # HTMLテンプレート読み込み
        template_file = 'corporate-email-newsletter.html'
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 変数置換
            html_content = html_content.replace('{{company_name}}', company_name)
            html_content = html_content.replace('{{job_position}}', job_position)
            
            # トラッキングピクセル追加
            tracking_id = str(uuid.uuid4())
            tracking_pixel = f'<img src="http://127.0.0.1:5002/track/{tracking_id}" width="1" height="1" style="display:none;" />'
            html_content = html_content.replace('</body>', f'{tracking_pixel}</body>')
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            print("✅ HTMLメール作成")
        
        # SMTP送信
        print("📤 送信中...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        print("✅ 送信完了！")
        print(f"📧 件名: {subject}")
        print(f"📧 送信者: {sender_name}")
        print(f"🕐 送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 送信失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚀 HUGAN JOB テストメール送信")
    print("=" * 40)
    
    success = send_test_email()
    
    if success:
        print("\n🎉 送信成功！")
        print("\n📝 確認事項:")
        print("  • 件名に「製造スタッフ」が含まれているか")
        print("  • 企業名が「ラ・シンシア株式会社」になっているか")
        print("  • 担当者名が「竹下」になっているか")
        print("  • 送信者名が「竹下隼平【株式会社HUGAN】」になっているか")
    else:
        print("\n❌ 送信失敗")
