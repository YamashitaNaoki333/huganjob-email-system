#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB DMARC設定後テストメール送信ツール
迷惑メール判定改善効果の測定

作成日時: 2025年06月26日 20:00:00
目的: DMARC設定後の配信改善効果を測定
"""

import smtplib
import configparser
import time
import json
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid

class DMARCTestSender:
    """DMARC設定後テストメール送信クラス"""
    
    def __init__(self):
        self.config = None
        self.test_results = []
        
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
    
    def create_dmarc_test_email(self, recipient_email, test_type="standard"):
        """DMARC対応テストメール作成"""
        try:
            msg = MIMEMultipart('alternative')
            
            # テストタイプ別の件名
            if test_type == "standard":
                subject = "DMARC設定テスト - HUGAN JOB"
            elif test_type == "business":
                subject = "システムエンジニア採用のご相談 - HUGAN JOB"
            else:
                subject = f"DMARC テスト ({test_type}) - HUGAN JOB"
            
            msg['Subject'] = Header(subject, 'utf-8')
            
            # 送信者情報（DMARC対応）
            sender_name = self.config.get('SMTP', 'sender_name')
            from_email = self.config.get('SMTP', 'from_email')
            msg['From'] = formataddr((sender_name, from_email))
            msg['To'] = recipient_email
            msg['Reply-To'] = self.config.get('SMTP', 'reply_to')
            
            # DMARC対応ヘッダー
            msg['Date'] = formatdate(localtime=True)
            msg['Message-ID'] = make_msgid(domain='huganjob.jp')
            # 🚨 迷惑メール判定要因ヘッダーを削除
            # ❌ msg['X-Mailer'] = 削除済み（自動送信システム識別回避）
            # ❌ msg['Authentication-Results'] = 削除済み（認証結果偽装は迷惑メール判定要因）
            
            # 配信停止ヘッダー
            msg['List-Unsubscribe'] = '<https://forms.gle/49BTNfSgUeNkH7rz5>'
            msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
            
            # HTMLコンテンツ
            html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DMARC設定テスト</title>
</head>
<body style="font-family: 'Hiragino Sans', sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #3498db 0%, #1abc9c 100%); padding: 20px; text-align: center; color: white; border-radius: 8px;">
            <h1 style="margin: 0; font-size: 24px;">HUGAN JOB</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">DMARC設定テスト</p>
        </div>
        
        <div style="padding: 30px 20px; background: #f8f9fa; margin: 20px 0; border-radius: 8px;">
            <h2 style="color: #2c3e50; margin-bottom: 15px;">テスト内容</h2>
            <p><strong>テストタイプ:</strong> {test_type}</p>
            <p><strong>送信日時:</strong> {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
            <p><strong>認証設定:</strong> SPF + DKIM + DMARC</p>
            
            <h3 style="color: #2c3e50; margin-top: 25px;">確認項目</h3>
            <ul style="color: #555;">
                <li>受信トレイに到達したか</li>
                <li>迷惑メールフォルダに分類されていないか</li>
                <li>送信者認証が正常に表示されるか</li>
                <li>メール内容が正常に表示されるか</li>
            </ul>
        </div>
        
        <div style="padding: 20px; text-align: center; background: white; border-radius: 8px; border: 1px solid #ddd;">
            <p style="margin: 0; color: #666; font-size: 14px;">
                このメールはDMARC設定の効果測定のためのテストメールです。<br>
                受信状況をご確認ください。
            </p>
        </div>
        
        <div style="padding: 20px; text-align: center; color: #888; font-size: 12px;">
            <p>HUGAN JOB採用サポート<br>
            Email: contact@huganjob.jp<br>
            配信停止: <a href="https://forms.gle/49BTNfSgUeNkH7rz5">こちら</a></p>
        </div>
    </div>
</body>
</html>
            """
            
            # プレーンテキスト版
            text_content = f"""
HUGAN JOB DMARC設定テスト

テストタイプ: {test_type}
送信日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
認証設定: SPF + DKIM + DMARC

【確認項目】
- 受信トレイに到達したか
- 迷惑メールフォルダに分類されていないか
- 送信者認証が正常に表示されるか
- メール内容が正常に表示されるか

このメールはDMARC設定の効果測定のためのテストメールです。
受信状況をご確認ください。

---
HUGAN JOB採用サポート
Email: contact@huganjob.jp
配信停止: https://forms.gle/49BTNfSgUeNkH7rz5
            """
            
            # パート追加
            html_part = MIMEText(html_content, 'html', 'utf-8')
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(text_part)
            msg.attach(html_part)
            
            return msg
            
        except Exception as e:
            print(f"❌ メール作成エラー: {e}")
            return None
    
    def send_test_email(self, recipient_email, test_type="standard"):
        """テストメール送信"""
        try:
            print(f"\n📧 DMARC対応テストメール送信")
            print(f"   宛先: {recipient_email}")
            print(f"   テストタイプ: {test_type}")
            
            # メール作成
            msg = self.create_dmarc_test_email(recipient_email, test_type)
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
            
            # 結果記録
            result = {
                'timestamp': datetime.now().isoformat(),
                'recipient': recipient_email,
                'test_type': test_type,
                'status': 'sent',
                'subject': msg['Subject'],
                'from': msg['From']
            }
            self.test_results.append(result)
            
            print(f"   ✅ 送信成功: {recipient_email}")
            return True
            
        except Exception as e:
            print(f"   ❌ 送信失敗: {e}")
            
            # エラー記録
            result = {
                'timestamp': datetime.now().isoformat(),
                'recipient': recipient_email,
                'test_type': test_type,
                'status': 'failed',
                'error': str(e)
            }
            self.test_results.append(result)
            return False
    
    def run_comprehensive_test(self):
        """包括的テスト実行"""
        print("="*60)
        print("📧 HUGANJOB DMARC設定後 包括的テスト")
        print("迷惑メール判定改善効果測定")
        print("="*60)
        
        # テスト対象
        test_cases = [
            ("n.yamashita@raxus.inc", "standard"),
            ("n.yamashita@raxus.inc", "business")
        ]
        
        success_count = 0
        
        for recipient, test_type in test_cases:
            success = self.send_test_email(recipient, test_type)
            if success:
                success_count += 1
            
            # 送信間隔
            print(f"   ⏳ 送信間隔待機中（10秒）...")
            time.sleep(10)
        
        # 結果サマリー
        print(f"\n📊 テスト結果サマリー")
        print(f"   総送信数: {len(test_cases)}")
        print(f"   成功数: {success_count}")
        print(f"   失敗数: {len(test_cases) - success_count}")
        print(f"   成功率: {(success_count/len(test_cases)*100):.1f}%")
        
        # 結果保存
        self.save_test_results()
        
        print(f"\n📋 受信確認のお願い")
        print(f"   以下のメールアドレスで受信状況をご確認ください:")
        for recipient, _ in test_cases:
            print(f"   - {recipient}")
        
        print(f"\n🔍 確認項目:")
        print(f"   1. 受信トレイに到達しているか")
        print(f"   2. 迷惑メールフォルダに分類されていないか")
        print(f"   3. 送信者認証マークが表示されているか")
        print(f"   4. メール内容が正常に表示されているか")
        
        return self.test_results
    
    def save_test_results(self):
        """テスト結果保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'huganjob_dmarc_test_results_{timestamp}.json'
        
        report = {
            'test_info': {
                'timestamp': datetime.now().isoformat(),
                'purpose': 'DMARC設定後の迷惑メール判定改善効果測定',
                'total_tests': len(self.test_results)
            },
            'results': self.test_results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 テスト結果保存: {filename}")
        return filename

def main():
    """メイン処理"""
    sender = DMARCTestSender()
    
    # 設定読み込み
    if not sender.load_config():
        return False
    
    # 包括的テスト実行
    results = sender.run_comprehensive_test()
    
    print(f"\n🏁 DMARC設定後テスト完了")
    print(f"📈 迷惑メール判定の改善効果をご確認ください")
    
    return True

if __name__ == "__main__":
    main()
