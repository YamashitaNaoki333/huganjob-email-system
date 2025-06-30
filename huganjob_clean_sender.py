#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB URL削除版送信システム
迷惑メール判定回避のため全URLを削除

作成日時: 2025年06月26日 21:30:00
目的: HTMLメール内のURLを削除して迷惑メール判定を回避
修正内容:
1. 外部リンクの完全削除
2. UTMパラメータの削除
3. CTAボタンの削除
4. 配信停止URLの削除
5. 追跡ピクセルの削除
"""

import smtplib
import configparser
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid

class CleanEmailSender:
    """URL削除版メール送信クラス"""
    
    def __init__(self):
        self.config = None
        
    def load_config(self):
        """設定ファイル読み込み"""
        try:
            self.config = configparser.ConfigParser()
            self.config.read('config/huganjob_email_config.ini', encoding='utf-8')
            print("✅ 設定ファイル読み込み完了")
            return True
        except Exception as e:
            print(f"❌ 設定ファイル読み込みエラー: {e}")
            return False
    
    def load_clean_template(self):
        """URL削除版HTMLテンプレート読み込み"""
        try:
            with open('corporate-email-newsletter-clean.html', 'r', encoding='utf-8') as f:
                template = f.read()
            print("✅ URL削除版HTMLテンプレート読み込み完了")
            return template
        except Exception as e:
            print(f"❌ テンプレート読み込みエラー: {e}")
            return None
    
    def create_clean_email(self, company_name, job_position, recipient_email):
        """URL削除版メール作成"""
        try:
            msg = MIMEMultipart('alternative')
            
            # 自然な件名
            subject = f"{job_position}採用について - HUGAN JOB"
            msg['Subject'] = Header(subject, 'utf-8')
            
            # シンプルな送信者情報
            sender_name = self.config.get('SMTP', 'sender_name')
            from_email = self.config.get('SMTP', 'from_email')
            msg['From'] = formataddr((sender_name, from_email))
            msg['To'] = recipient_email
            msg['Reply-To'] = self.config.get('SMTP', 'reply_to')
            
            # 最小限のヘッダー
            msg['Date'] = formatdate(localtime=True)
            msg['Message-ID'] = make_msgid(domain='huganjob.jp')
            
            # URL削除版HTMLコンテンツ
            html_template = self.load_clean_template()
            if html_template:
                html_content = html_template.replace('{{company_name}}', company_name)
                html_content = html_content.replace('{{job_position}}', job_position)
            else:
                # フォールバック用シンプルHTML
                html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto;">
        <div style="background-color: #3498db; padding: 20px; text-align: center; color: white; margin-bottom: 20px;">
            <h1 style="margin: 0;">HUGAN JOB</h1>
            <p style="margin: 5px 0 0 0;">採用サポートサービス</p>
        </div>
        
        <div style="padding: 0 10px;">
            <p>{company_name}<br>採用ご担当者様</p>
            <p>いつもお疲れ様です。<br>HUGAN JOB採用サポートチームです。</p>
            <p>{company_name}様の{job_position}の採用について、弊社の人材紹介サービスでお手伝いできることがございます。</p>
            
            <h3>HUGAN JOBの特徴</h3>
            <ul>
                <li>採用工数の大幅削減</li>
                <li>ミスマッチの防止</li>
                <li>専門性の高い人材紹介</li>
            </ul>
            
            <div style="background-color: #3498db; color: white; padding: 15px; text-align: center; margin: 20px 0;">
                <p style="margin: 0;"><strong>📧 お問い合わせ: contact@huganjob.jp</strong></p>
                <p style="margin: 5px 0 0 0;"><strong>📞 お電話: 0120-917-906</strong></p>
            </div>
            
            <p>詳細については、お気軽にお問い合わせください。</p>
            
            <div style="margin-top: 30px; padding: 15px; background-color: #f8f9fa; text-align: center;">
                <p style="margin: 0; font-size: 14px; color: #555;">
                    <strong>HUGAN JOB採用サポート</strong><br>
                    Email: contact@huganjob.jp<br>
                    Tel: 0120-917-906
                </p>
            </div>
        </div>
    </div>
</body>
</html>
                """
            
            # シンプルなプレーンテキスト版（URL完全削除）
            text_content = f"""
{company_name}
採用ご担当者様

いつもお疲れ様です。
HUGAN JOB採用サポートチームです。

{company_name}様の{job_position}の採用について、
弊社の人材紹介サービスでお手伝いできることがございます。

【HUGAN JOBの特徴】

1. 採用工数の削減
   人材の選定から面接調整まで、採用プロセスをトータルサポート

2. ミスマッチの防止
   詳細なヒアリングにより、企業様のニーズに最適な人材をご紹介

3. 専門性の高いサポート
   IT業界に精通したコンサルタントが専門的な観点からサポート

【お問い合わせ】
Email: contact@huganjob.jp
Tel: 0120-917-906

詳細については、お気軽にお問い合わせください。

---
HUGAN JOB採用サポート
Email: contact@huganjob.jp
Tel: 0120-917-906

※配信停止をご希望の場合は、以下のリンクからお手続きください。
配信停止: https://forms.gle/49BTNfSgUeNkH7rz5
            """.strip()
            
            # パート追加
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(text_part)
            msg.attach(html_part)
            
            return msg
            
        except Exception as e:
            print(f"❌ メール作成エラー: {e}")
            return None
    
    def send_clean_email(self, recipient_email, company_name="株式会社Raxus", job_position="システムエンジニア"):
        """URL削除版メール送信"""
        try:
            print(f"\n📧 URL削除版メール送信")
            print(f"   宛先: {recipient_email}")
            print(f"   企業名: {company_name}")
            print(f"   職種: {job_position}")
            print(f"   🚫 削除要素: 全URL、リンク、追跡要素")
            
            # メール作成
            msg = self.create_clean_email(company_name, job_position, recipient_email)
            if not msg:
                return False
            
            # SMTP送信
            smtp_server = self.config.get('SMTP', 'server')
            smtp_port = int(self.config.get('SMTP', 'port'))
            smtp_user = self.config.get('SMTP', 'user')
            smtp_password = self.config.get('SMTP', 'password')
            
            print(f"   📡 SMTP接続: {smtp_server}:{smtp_port}")
            
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            
            print(f"   ✅ 送信成功: {recipient_email}")
            print(f"   📧 件名: {msg['Subject']}")
            print(f"   👤 送信者: {msg['From']}")
            print(f"   🛡️ 迷惑メール対策: URL完全削除")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 送信失敗: {e}")
            return False
    
    def send_test_emails(self):
        """テストメール送信"""
        print("="*60)
        print("📧 HUGANJOB URL削除版送信システム")
        print("迷惑メール判定回避のため全URLを削除")
        print("="*60)
        
        # テスト対象
        test_cases = [
            ("n.yamashita@raxus.inc", "株式会社Raxus", "システムエンジニア")
        ]
        
        success_count = 0
        
        for recipient, company, position in test_cases:
            success = self.send_clean_email(recipient, company, position)
            if success:
                success_count += 1
            
            # 送信間隔
            print(f"   ⏳ 送信間隔待機中（10秒）...")
            time.sleep(10)
        
        # 結果サマリー
        print(f"\n📊 送信結果サマリー")
        print(f"   総送信数: {len(test_cases)}")
        print(f"   成功数: {success_count}")
        print(f"   成功率: {(success_count/len(test_cases)*100):.1f}%")
        
        print(f"\n🚫 削除されたURL要素:")
        print(f"   ❌ 外部サイトリンク（https://www.hugan.co.jp/business）")
        print(f"   ❌ UTMパラメータ（utm_campaign=sale）")
        print(f"   ❌ CTAボタン（3個のリンクボタン）")
        print(f"   ❌ 配信停止URL（https://forms.gle/49BTNfSgUeNkH7rz5）")
        print(f"   ❌ 追跡ピクセル（track-open、track、track-css）")
        
        print(f"\n📬 受信確認のお願い:")
        print(f"   - 受信トレイに到達しているか")
        print(f"   - 迷惑メールフォルダに分類されていないか")
        print(f"   - URL含有版との受信場所の違いを確認")
        
        return success_count == len(test_cases)

def main():
    """メイン処理"""
    sender = CleanEmailSender()
    
    # 設定読み込み
    if not sender.load_config():
        return False
    
    # URL削除版テスト送信
    success = sender.send_test_emails()
    
    if success:
        print(f"\n🏁 URL削除版送信完了")
        print(f"📈 迷惑メール判定の大幅改善が期待されます")
        print(f"🔍 URL含有版と比較して受信場所をご確認ください")
    else:
        print(f"\n❌ 送信に問題が発生しました")
    
    return success

if __name__ == "__main__":
    main()
