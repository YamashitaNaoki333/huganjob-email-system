#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB 迷惑メール判定原因調査ツール
ダッシュボード送信 vs Thunderbird送信の違いを特定

作成日時: 2025年06月26日 20:30:00
目的: ダッシュボードからの送信が迷惑メール判定される原因を特定
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

class SpamInvestigator:
    """迷惑メール判定原因調査クラス"""
    
    def __init__(self):
        self.config = None
        self.investigation_results = []
        
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
    
    def create_dashboard_style_email(self, recipient_email="n.yamashita@raxus.inc"):
        """ダッシュボード方式のメール作成（現在の問題のある方式）"""
        try:
            msg = MIMEMultipart('alternative')
            
            # ダッシュボードで使用されている設定
            subject = self.config.get('EMAIL_CONTENT', 'subject').replace('{{job_position}}', 'システムエンジニア')
            msg['Subject'] = Header(subject, 'utf-8')
            
            # 送信者情報（現在の設定）
            sender_name = self.config.get('SMTP', 'sender_name')
            from_email = self.config.get('SMTP', 'from_email')
            msg['From'] = formataddr((sender_name, from_email))
            msg['To'] = recipient_email
            msg['Reply-To'] = self.config.get('SMTP', 'reply_to')
            
            # ダッシュボードで追加されるヘッダー
            msg['Date'] = formatdate(localtime=True)
            msg['Message-ID'] = make_msgid(domain='huganjob.jp')
            # 🚨 X-Mailerヘッダーを削除（自動送信システム識別回避）
            # ❌ msg['X-Mailer'] = 削除済み（迷惑メール判定要因）
            msg['X-Priority'] = '3'
            msg['X-MSMail-Priority'] = 'Normal'
            
            # 配信停止ヘッダー
            unsubscribe_url = self.config.get('EMAIL_CONTENT', 'unsubscribe_url')
            msg['List-Unsubscribe'] = f'<{unsubscribe_url}>'
            msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
            
            # 🚨 認証結果偽装ヘッダーを削除（迷惑メール判定の主要因）
            # ❌ msg['Authentication-Results'] = 削除済み（偽装ヘッダーは迷惑メール判定要因）
            
            # HTMLコンテンツ
            html_content = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>システムエンジニア採用のご相談</title>
</head>
<body style="font-family: sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #3498db 0%, #1abc9c 100%); padding: 20px; text-align: center; color: white; border-radius: 8px;">
            <h1 style="margin: 0;">HUGAN JOB</h1>
            <p style="margin: 10px 0 0 0;">採用サポートサービス</p>
        </div>
        
        <div style="padding: 30px 20px;">
            <p>株式会社Raxus<br>採用ご担当者様</p>
            <p>いつもお疲れ様です。<br>HUGAN JOB採用サポートチームです。</p>
            <p>株式会社Raxus様のシステムエンジニアの採用について、弊社の人材紹介サービスでお手伝いできることがございます。</p>
            
            <h3>HUGAN JOBの特徴</h3>
            <ul>
                <li>採用工数の大幅削減</li>
                <li>ミスマッチの防止</li>
                <li>専門性の高い人材紹介</li>
            </ul>
            
            <p>詳細については、お気軽にお問い合わせください。</p>
        </div>
        
        <div style="padding: 20px; text-align: center; background: #f8f9fa; border-radius: 8px;">
            <p style="margin: 0; color: #666; font-size: 14px;">
                HUGAN JOB採用サポート<br>
                Email: contact@huganjob.jp<br>
                配信停止: <a href="https://forms.gle/49BTNfSgUeNkH7rz5">こちら</a>
            </p>
        </div>
    </div>
</body>
</html>
            """
            
            # プレーンテキスト版
            text_content = """
株式会社Raxus
採用ご担当者様

いつもお疲れ様です。
HUGAN JOB採用サポートチームです。

株式会社Raxus様のシステムエンジニアの採用について、
弊社の人材紹介サービスでお手伝いできることがございます。

【HUGAN JOBの特徴】
・採用工数の大幅削減
・ミスマッチの防止
・専門性の高い人材紹介

詳細については、お気軽にお問い合わせください。

---
HUGAN JOB採用サポート
Email: contact@huganjob.jp
配信停止: https://forms.gle/49BTNfSgUeNkH7rz5
            """
            
            # パート追加
            text_part = MIMEText(text_content.strip(), 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(text_part)
            msg.attach(html_part)
            
            return msg, "dashboard_style"
            
        except Exception as e:
            print(f"❌ ダッシュボード方式メール作成エラー: {e}")
            return None, None
    
    def create_thunderbird_style_email(self, recipient_email="n.yamashita@raxus.inc"):
        """Thunderbird方式のメール作成（正常に受信される方式）"""
        try:
            msg = MIMEMultipart('alternative')
            
            # シンプルな件名（Thunderbirdで使用される形式）
            msg['Subject'] = Header("システムエンジニア採用のご相談 - HUGAN JOB", 'utf-8')
            
            # シンプルな送信者情報
            msg['From'] = formataddr(("HUGAN JOB採用サポート", "contact@huganjob.jp"))
            msg['To'] = recipient_email
            msg['Reply-To'] = "contact@huganjob.jp"
            
            # 最小限のヘッダー（Thunderbirdスタイル）
            msg['Date'] = formatdate(localtime=True)
            msg['Message-ID'] = make_msgid(domain='huganjob.jp')
            
            # 余計なヘッダーを追加しない（重要）
            # msg['X-Mailer'] = 削除
            # msg['Authentication-Results'] = 削除
            # msg['List-Unsubscribe'] = 削除
            
            # シンプルなHTMLコンテンツ
            html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <p>株式会社Raxus 採用ご担当者様</p>
    <p>いつもお疲れ様です。<br>HUGAN JOB採用サポートチームです。</p>
    <p>株式会社Raxus様のシステムエンジニアの採用について、弊社の人材紹介サービスでお手伝いできることがございます。</p>
    
    <h3>HUGAN JOBの特徴</h3>
    <ul>
        <li>採用工数の大幅削減</li>
        <li>ミスマッチの防止</li>
        <li>専門性の高い人材紹介</li>
    </ul>
    
    <p>詳細については、お気軽にお問い合わせください。</p>
    
    <p>HUGAN JOB採用サポート<br>
    Email: contact@huganjob.jp</p>
</body>
</html>
            """
            
            # プレーンテキスト版
            text_content = """
株式会社Raxus 採用ご担当者様

いつもお疲れ様です。
HUGAN JOB採用サポートチームです。

株式会社Raxus様のシステムエンジニアの採用について、
弊社の人材紹介サービスでお手伝いできることがございます。

【HUGAN JOBの特徴】
・採用工数の大幅削減
・ミスマッチの防止
・専門性の高い人材紹介

詳細については、お気軽にお問い合わせください。

HUGAN JOB採用サポート
Email: contact@huganjob.jp
            """
            
            # パート追加
            text_part = MIMEText(text_content.strip(), 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(text_part)
            msg.attach(html_part)
            
            return msg, "thunderbird_style"
            
        except Exception as e:
            print(f"❌ Thunderbird方式メール作成エラー: {e}")
            return None, None
    
    def send_investigation_email(self, msg, style_type, recipient_email="n.yamashita@raxus.inc"):
        """調査用メール送信"""
        try:
            print(f"\n📧 {style_type} メール送信中")
            print(f"   宛先: {recipient_email}")
            
            # SMTP設定
            smtp_server = self.config.get('SMTP', 'server')
            smtp_port = int(self.config.get('SMTP', 'port'))
            smtp_user = self.config.get('SMTP', 'user')
            smtp_password = self.config.get('SMTP', 'password')
            
            print(f"   📡 SMTP: {smtp_server}:{smtp_port}")
            
            # ヘッダー詳細表示
            print(f"   📧 件名: {msg['Subject']}")
            print(f"   👤 送信者: {msg['From']}")
            print(f"   🔧 X-Mailer: {msg.get('X-Mailer', '未設定')}")
            print(f"   🔐 Auth-Results: {msg.get('Authentication-Results', '未設定')}")
            print(f"   📋 List-Unsubscribe: {msg.get('List-Unsubscribe', '未設定')}")
            
            # SMTP送信
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            
            # 結果記録
            result = {
                'timestamp': datetime.now().isoformat(),
                'style_type': style_type,
                'recipient': recipient_email,
                'status': 'sent',
                'headers': {
                    'subject': str(msg['Subject']),
                    'from': str(msg['From']),
                    'x_mailer': str(msg.get('X-Mailer', '')),
                    'auth_results': str(msg.get('Authentication-Results', '')),
                    'list_unsubscribe': str(msg.get('List-Unsubscribe', ''))
                }
            }
            self.investigation_results.append(result)
            
            print(f"   ✅ 送信成功: {style_type}")
            return True
            
        except Exception as e:
            print(f"   ❌ 送信失敗: {style_type} - {e}")
            
            # エラー記録
            result = {
                'timestamp': datetime.now().isoformat(),
                'style_type': style_type,
                'recipient': recipient_email,
                'status': 'failed',
                'error': str(e)
            }
            self.investigation_results.append(result)
            return False
    
    def run_comparative_investigation(self):
        """比較調査実行"""
        print("="*60)
        print("🔍 HUGANJOB 迷惑メール判定原因調査")
        print("ダッシュボード vs Thunderbird 比較分析")
        print("="*60)
        
        recipient = "n.yamashita@raxus.inc"
        
        # 1. ダッシュボード方式テスト
        print(f"\n1️⃣ ダッシュボード方式テスト")
        dashboard_msg, dashboard_type = self.create_dashboard_style_email(recipient)
        if dashboard_msg:
            self.send_investigation_email(dashboard_msg, dashboard_type, recipient)
        
        # 送信間隔
        print(f"\n⏳ 送信間隔待機中（15秒）...")
        time.sleep(15)
        
        # 2. Thunderbird方式テスト
        print(f"\n2️⃣ Thunderbird方式テスト")
        thunderbird_msg, thunderbird_type = self.create_thunderbird_style_email(recipient)
        if thunderbird_msg:
            self.send_investigation_email(thunderbird_msg, thunderbird_type, recipient)
        
        # 結果分析
        self.analyze_differences()
        
        # 結果保存
        self.save_investigation_results()
        
        return self.investigation_results
    
    def analyze_differences(self):
        """差異分析"""
        print(f"\n" + "="*60)
        print("📊 差異分析結果")
        print("="*60)
        
        if len(self.investigation_results) >= 2:
            dashboard_result = self.investigation_results[0]
            thunderbird_result = self.investigation_results[1]
            
            print(f"\n🔍 ヘッダー比較:")
            print(f"   ダッシュボード方式:")
            for key, value in dashboard_result.get('headers', {}).items():
                print(f"     {key}: {value}")
            
            print(f"\n   Thunderbird方式:")
            for key, value in thunderbird_result.get('headers', {}).items():
                print(f"     {key}: {value}")
            
            print(f"\n⚠️ 迷惑メール判定の可能性が高い要因:")
            print(f"   1. X-Mailer: 'HUGAN JOB System v2.0' - 自動送信システムの識別")
            print(f"   2. Authentication-Results: 偽装された認証結果ヘッダー")
            print(f"   3. List-Unsubscribe: 大量送信メールの特徴")
            print(f"   4. 複雑なHTMLテンプレート: linear-gradient等の高度なCSS")
            print(f"   5. 営業色の強い件名: '採用のご相談'")
        
        print(f"\n💡 推奨改善策:")
        print(f"   ✅ X-Mailerヘッダーの削除")
        print(f"   ✅ Authentication-Resultsヘッダーの削除")
        print(f"   ✅ List-Unsubscribeヘッダーの削除")
        print(f"   ✅ HTMLテンプレートの簡素化")
        print(f"   ✅ 件名の自然な表現への変更")
    
    def save_investigation_results(self):
        """調査結果保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'huganjob_spam_investigation_{timestamp}.json'
        
        report = {
            'investigation_info': {
                'timestamp': datetime.now().isoformat(),
                'purpose': 'ダッシュボード送信が迷惑メール判定される原因調査',
                'comparison': 'ダッシュボード方式 vs Thunderbird方式'
            },
            'results': self.investigation_results,
            'recommendations': [
                'X-Mailerヘッダーの削除',
                'Authentication-Resultsヘッダーの削除',
                'List-Unsubscribeヘッダーの削除',
                'HTMLテンプレートの簡素化',
                '件名の自然な表現への変更'
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 調査結果保存: {filename}")
        return filename

def main():
    """メイン処理"""
    investigator = SpamInvestigator()
    
    # 設定読み込み
    if not investigator.load_config():
        return False
    
    # 比較調査実行
    results = investigator.run_comparative_investigation()
    
    print(f"\n🏁 迷惑メール判定原因調査完了")
    print(f"📬 n.yamashita@raxus.incでの受信状況をご確認ください")
    print(f"📊 2通のメールの受信場所（受信トレイ vs 迷惑メール）を比較してください")
    
    return True

if __name__ == "__main__":
    main()
