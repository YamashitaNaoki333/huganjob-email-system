#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB Thunderbird方式送信システム
迷惑メール判定回避版

作成日時: 2025年06月26日 20:45:00
目的: Thunderbirdと同様の送信方式で迷惑メール判定を回避
修正内容:
1. Authentication-Resultsヘッダーの削除
2. X-Mailerヘッダーの削除
3. List-Unsubscribeヘッダーの削除
4. HTMLテンプレートの簡素化
5. 件名の自然な表現への変更
"""

import smtplib
import configparser
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid

class ThunderbirdStyleSender:
    """Thunderbird方式送信クラス（迷惑メール判定回避）"""
    
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
    
    def create_thunderbird_style_email(self, company_name, job_position, recipient_email):
        """Thunderbird方式メール作成（迷惑メール判定回避）"""
        try:
            msg = MIMEMultipart('alternative')
            
            # 自然な件名（営業色を薄める）
            subject = f"{job_position}採用について - HUGAN JOB"
            msg['Subject'] = Header(subject, 'utf-8')
            
            # シンプルな送信者情報
            sender_name = self.config.get('SMTP', 'sender_name')
            from_email = self.config.get('SMTP', 'from_email')
            msg['From'] = formataddr((sender_name, from_email))
            msg['To'] = recipient_email
            msg['Reply-To'] = self.config.get('SMTP', 'reply_to')
            
            # 最小限のヘッダー（Thunderbirdスタイル）
            msg['Date'] = formatdate(localtime=True)
            msg['Message-ID'] = make_msgid(domain='huganjob.jp')
            
            # 🚨 迷惑メール判定要因となるヘッダーを削除
            # ❌ msg['X-Mailer'] = 削除（自動送信システムの識別回避）
            # ❌ msg['Authentication-Results'] = 削除（偽装ヘッダー回避）
            # ❌ msg['List-Unsubscribe'] = 削除（大量送信メールの特徴回避）
            # ❌ msg['X-Priority'] = 削除
            # ❌ msg['X-MSMail-Priority'] = 削除
            
            # シンプルなHTMLコンテンツ（linear-gradient等の複雑なCSS削除）
            html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto;">
        
        <!-- シンプルなヘッダー（グラデーション削除） -->
        <div style="background-color: #3498db; padding: 20px; text-align: center; color: white; margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 24px;">HUGAN JOB</h1>
            <p style="margin: 5px 0 0 0; font-size: 14px;">採用サポートサービス</p>
        </div>
        
        <!-- メイン内容 -->
        <div style="padding: 0 10px;">
            <p>{company_name}<br>採用ご担当者様</p>
            
            <p>いつもお疲れ様です。<br>
            HUGAN JOB採用サポートチームです。</p>
            
            <p>{company_name}様の{job_position}の採用について、弊社の人材紹介サービスでお手伝いできることがございます。</p>
            
            <h3 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">HUGAN JOBの特徴</h3>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; background-color: #f8f9fa;">
                        <strong>採用工数の削減</strong><br>
                        <span style="color: #666; font-size: 14px;">人材の選定から面接調整まで、採用プロセスをトータルサポート</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;">
                        <strong>ミスマッチの防止</strong><br>
                        <span style="color: #666; font-size: 14px;">詳細なヒアリングにより、企業様のニーズに最適な人材をご紹介</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; background-color: #f8f9fa;">
                        <strong>専門性の高いサポート</strong><br>
                        <span style="color: #666; font-size: 14px;">IT業界に精通したコンサルタントが専門的な観点からサポート</span>
                    </td>
                </tr>
            </table>
            
            <p>詳細については、お気軽にお問い合わせください。</p>
            
            <div style="margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #3498db;">
                <p style="margin: 0; font-size: 14px; color: #555;">
                    <strong>HUGAN JOB採用サポート</strong><br>
                    Email: contact@huganjob.jp
                </p>
            </div>
        </div>
        
    </div>
</body>
</html>
            """
            
            # シンプルなプレーンテキスト版
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

詳細については、お気軽にお問い合わせください。

---
HUGAN JOB採用サポート
Email: contact@huganjob.jp
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
    
    def send_thunderbird_style_email(self, recipient_email, company_name="株式会社Raxus", job_position="システムエンジニア"):
        """Thunderbird方式メール送信"""
        try:
            print(f"\n📧 Thunderbird方式メール送信")
            print(f"   宛先: {recipient_email}")
            print(f"   企業名: {company_name}")
            print(f"   職種: {job_position}")
            print(f"   🔧 迷惑メール対策: 偽装ヘッダー削除済み")
            
            # メール作成
            msg = self.create_thunderbird_style_email(company_name, job_position, recipient_email)
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
            print(f"   🛡️ 迷惑メール対策: 適用済み")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 送信失敗: {e}")
            return False
    
    def send_multiple_tests(self):
        """複数テスト送信"""
        print("="*60)
        print("📧 HUGANJOB Thunderbird方式送信システム")
        print("迷惑メール判定回避版")
        print("="*60)
        
        # テスト対象
        test_cases = [
            ("n.yamashita@raxus.inc", "株式会社Raxus", "システムエンジニア")
        ]
        
        success_count = 0
        
        for recipient, company, position in test_cases:
            success = self.send_thunderbird_style_email(recipient, company, position)
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
        
        print(f"\n🔍 迷惑メール対策内容:")
        print(f"   ✅ Authentication-Resultsヘッダー削除")
        print(f"   ✅ X-Mailerヘッダー削除")
        print(f"   ✅ List-Unsubscribeヘッダー削除")
        print(f"   ✅ HTMLテンプレート簡素化")
        print(f"   ✅ 件名の自然な表現への変更")
        
        print(f"\n📬 受信確認のお願い:")
        print(f"   - 受信トレイに到達しているか")
        print(f"   - 迷惑メールフォルダに分類されていないか")
        print(f"   - 従来のダッシュボード送信との違いを確認")
        
        return success_count == len(test_cases)

def main():
    """メイン処理"""
    sender = ThunderbirdStyleSender()
    
    # 設定読み込み
    if not sender.load_config():
        return False
    
    # Thunderbird方式テスト送信
    success = sender.send_multiple_tests()
    
    if success:
        print(f"\n🏁 Thunderbird方式送信完了")
        print(f"📈 迷惑メール判定の大幅改善が期待されます")
    else:
        print(f"\n❌ 送信に問題が発生しました")
    
    return success

if __name__ == "__main__":
    main()
