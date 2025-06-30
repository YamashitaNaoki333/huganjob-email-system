#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB URL迷惑メール判定調査ツール
HTMLメール内のURLが迷惑メール判定に与える影響を調査

作成日時: 2025年06月26日 21:00:00
目的: 同じHTMLでもURLの有無で迷惑メール判定が変わる原因を特定
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

class URLSpamInvestigator:
    """URL迷惑メール判定調査クラス"""
    
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
    
    def create_email_with_all_urls(self, recipient_email="n.yamashita@raxus.inc"):
        """全URL含有版メール作成"""
        try:
            msg = MIMEMultipart('alternative')
            
            # 件名
            subject = "システムエンジニア採用について - HUGAN JOB"
            msg['Subject'] = Header(subject, 'utf-8')
            
            # 送信者情報
            sender_name = self.config.get('SMTP', 'sender_name')
            from_email = self.config.get('SMTP', 'from_email')
            msg['From'] = formataddr((sender_name, from_email))
            msg['To'] = recipient_email
            msg['Reply-To'] = self.config.get('SMTP', 'reply_to')
            
            # 最小限のヘッダー
            msg['Date'] = formatdate(localtime=True)
            msg['Message-ID'] = make_msgid(domain='huganjob.jp')
            
            # 全URL含有HTMLコンテンツ
            html_content = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>システムエンジニア採用について</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto;">
        
        <div style="background-color: #3498db; padding: 20px; text-align: center; color: white; margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 24px;">HUGAN JOB</h1>
            <p style="margin: 5px 0 0 0; font-size: 14px;">採用サポートサービス</p>
        </div>
        
        <div style="padding: 0 10px;">
            <p>株式会社Raxus<br>採用ご担当者様</p>
            
            <p>いつもお疲れ様です。<br>
            HUGAN JOB採用サポートチームです。</p>
            
            <p>株式会社Raxus様のシステムエンジニアの採用について、弊社の人材紹介サービスでお手伝いできることがございます。</p>
            
            <h3>HUGAN JOBの特徴</h3>
            <ul>
                <li>採用工数の大幅削減</li>
                <li>ミスマッチの防止</li>
                <li>専門性の高い人材紹介</li>
            </ul>
            
            <!-- 🚨 迷惑メール判定要因となる可能性のあるURL群 -->
            
            <!-- 1. 外部サイトへのリンク（営業色強い） -->
            <div style="text-align: center; margin: 20px 0;">
                <a href="https://www.hugan.co.jp/business?utm_source=contactmail&utm_medium=email&utm_campaign=20250620_sale&utm_content=mainbtn" 
                   style="display: inline-block; background-color: #e74c3c; color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none; font-weight: 700;">
                    📝 サービス詳細を見る
                </a>
            </div>
            
            <!-- 2. 複数のCTAボタン（営業メールの典型） -->
            <div style="text-align: center; margin: 20px 0;">
                <a href="https://www.hugan.co.jp/business?utm_source=contactmail&utm_medium=email&utm_campaign=20250620_sale&utm_content=kabubtn1" 
                   style="display: inline-block; background-color: #e74c3c; color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none; margin: 5px;">
                    💼 サービス詳細・お問い合わせ
                </a>
                <a href="https://www.hugan.co.jp/business?utm_source=contactmail&utm_medium=email&utm_campaign=20250620_sale&utm_content=kabubtn2" 
                   style="display: inline-block; background-color: transparent; color: #3498db; border: 2px solid #3498db; padding: 12px 25px; border-radius: 25px; text-decoration: none; margin: 5px;">
                    📞 無料相談を申し込む
                </a>
            </div>
            
            <!-- 3. 配信停止URL（大量送信メールの証拠） -->
            <p style="font-size: 12px; color: #666; text-align: center;">
                配信停止をご希望の場合は<a href="https://forms.gle/49BTNfSgUeNkH7rz5" style="color: #666;">こちら</a>からお手続きください。
            </p>
            
            <!-- 4. 追跡ピクセル（スパム判定要因） -->
            <img src="http://127.0.0.1:5002/track-open/test_tracking_123" width="1" height="1" style="display: none;" alt="" />
            
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

サービス詳細: https://www.hugan.co.jp/business
お問い合わせ: https://www.hugan.co.jp/business
配信停止: https://forms.gle/49BTNfSgUeNkH7rz5

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
            
            return msg, "with_all_urls"
            
        except Exception as e:
            print(f"❌ 全URL版メール作成エラー: {e}")
            return None, None
    
    def create_email_without_urls(self, recipient_email="n.yamashita@raxus.inc"):
        """URL削除版メール作成"""
        try:
            msg = MIMEMultipart('alternative')
            
            # 件名
            subject = "システムエンジニア採用について - HUGAN JOB"
            msg['Subject'] = Header(subject, 'utf-8')
            
            # 送信者情報
            sender_name = self.config.get('SMTP', 'sender_name')
            from_email = self.config.get('SMTP', 'from_email')
            msg['From'] = formataddr((sender_name, from_email))
            msg['To'] = recipient_email
            msg['Reply-To'] = self.config.get('SMTP', 'reply_to')
            
            # 最小限のヘッダー
            msg['Date'] = formatdate(localtime=True)
            msg['Message-ID'] = make_msgid(domain='huganjob.jp')
            
            # URL削除版HTMLコンテンツ
            html_content = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>システムエンジニア採用について</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto;">
        
        <div style="background-color: #3498db; padding: 20px; text-align: center; color: white; margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 24px;">HUGAN JOB</h1>
            <p style="margin: 5px 0 0 0; font-size: 14px;">採用サポートサービス</p>
        </div>
        
        <div style="padding: 0 10px;">
            <p>株式会社Raxus<br>採用ご担当者様</p>
            
            <p>いつもお疲れ様です。<br>
            HUGAN JOB採用サポートチームです。</p>
            
            <p>株式会社Raxus様のシステムエンジニアの採用について、弊社の人材紹介サービスでお手伝いできることがございます。</p>
            
            <h3>HUGAN JOBの特徴</h3>
            <ul>
                <li>採用工数の大幅削減</li>
                <li>ミスマッチの防止</li>
                <li>専門性の高い人材紹介</li>
            </ul>
            
            <!-- 🚨 全てのURL・リンク・追跡要素を削除 -->
            
            <div style="text-align: center; margin: 20px 0; padding: 15px; background-color: #e74c3c; color: white; border-radius: 25px;">
                <strong>📝 サービス詳細についてはお問い合わせください</strong>
            </div>
            
            <div style="text-align: center; margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 25px;">
                <strong>💼 お問い合わせ・ご相談は下記メールアドレスまで</strong><br>
                <strong>📞 無料相談も承っております</strong>
            </div>
            
            <p>詳細については、お気軽にお問い合わせください。</p>
            
            <div style="margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #3498db;">
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
            
            # プレーンテキスト版（URL削除）
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
Tel: 0120-917-906
            """.strip()
            
            # パート追加
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(text_part)
            msg.attach(html_part)
            
            return msg, "without_urls"
            
        except Exception as e:
            print(f"❌ URL削除版メール作成エラー: {e}")
            return None, None
    
    def send_investigation_email(self, msg, test_type, recipient_email="n.yamashita@raxus.inc"):
        """調査用メール送信"""
        try:
            print(f"\n📧 {test_type} メール送信中")
            print(f"   宛先: {recipient_email}")
            
            # SMTP設定
            smtp_server = self.config.get('SMTP', 'server')
            smtp_port = int(self.config.get('SMTP', 'port'))
            smtp_user = self.config.get('SMTP', 'user')
            smtp_password = self.config.get('SMTP', 'password')
            
            print(f"   📡 SMTP: {smtp_server}:{smtp_port}")
            
            # URL分析
            html_content = ""
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    html_content = part.get_payload(decode=True).decode('utf-8')
                    break
            
            # URL数カウント
            import re
            urls = re.findall(r'https?://[^\s<>"\']+', html_content)
            tracking_pixels = re.findall(r'track-open|track/', html_content)
            
            print(f"   🔗 含有URL数: {len(urls)}")
            print(f"   📊 追跡要素数: {len(tracking_pixels)}")
            
            if urls:
                print(f"   📋 検出されたURL:")
                for i, url in enumerate(urls[:3], 1):  # 最初の3つのみ表示
                    print(f"     {i}. {url}")
                if len(urls) > 3:
                    print(f"     ... 他{len(urls)-3}個")
            
            # SMTP送信
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            
            # 結果記録
            result = {
                'timestamp': datetime.now().isoformat(),
                'test_type': test_type,
                'recipient': recipient_email,
                'status': 'sent',
                'url_count': len(urls),
                'tracking_count': len(tracking_pixels),
                'urls': urls[:5],  # 最初の5つのみ記録
                'subject': str(msg['Subject']),
                'from': str(msg['From'])
            }
            self.investigation_results.append(result)
            
            print(f"   ✅ 送信成功: {test_type}")
            return True
            
        except Exception as e:
            print(f"   ❌ 送信失敗: {test_type} - {e}")
            
            # エラー記録
            result = {
                'timestamp': datetime.now().isoformat(),
                'test_type': test_type,
                'recipient': recipient_email,
                'status': 'failed',
                'error': str(e)
            }
            self.investigation_results.append(result)
            return False
    
    def run_url_investigation(self):
        """URL迷惑メール判定調査実行"""
        print("="*60)
        print("🔍 HUGANJOB URL迷惑メール判定調査")
        print("同じHTMLでもURLの有無による迷惑メール判定の違いを調査")
        print("="*60)
        
        recipient = "n.yamashita@raxus.inc"
        
        # 1. 全URL含有版テスト
        print(f"\n1️⃣ 全URL含有版テスト")
        print(f"   🔗 含有要素: 外部リンク、CTAボタン、配信停止URL、追跡ピクセル")
        with_urls_msg, with_urls_type = self.create_email_with_all_urls(recipient)
        if with_urls_msg:
            self.send_investigation_email(with_urls_msg, with_urls_type, recipient)
        
        # 送信間隔
        print(f"\n⏳ 送信間隔待機中（15秒）...")
        time.sleep(15)
        
        # 2. URL削除版テスト
        print(f"\n2️⃣ URL削除版テスト")
        print(f"   ❌ 削除要素: 全てのURL、リンク、追跡要素")
        without_urls_msg, without_urls_type = self.create_email_without_urls(recipient)
        if without_urls_msg:
            self.send_investigation_email(without_urls_msg, without_urls_type, recipient)
        
        # 結果分析
        self.analyze_url_impact()
        
        # 結果保存
        self.save_investigation_results()
        
        return self.investigation_results
    
    def analyze_url_impact(self):
        """URL影響分析"""
        print(f"\n" + "="*60)
        print("📊 URL迷惑メール判定影響分析")
        print("="*60)
        
        if len(self.investigation_results) >= 2:
            with_urls = self.investigation_results[0]
            without_urls = self.investigation_results[1]
            
            print(f"\n🔍 URL含有状況比較:")
            print(f"   全URL含有版:")
            print(f"     URL数: {with_urls.get('url_count', 0)}個")
            print(f"     追跡要素: {with_urls.get('tracking_count', 0)}個")
            print(f"     主要URL: {', '.join(with_urls.get('urls', [])[:2])}")
            
            print(f"\n   URL削除版:")
            print(f"     URL数: {without_urls.get('url_count', 0)}個")
            print(f"     追跡要素: {without_urls.get('tracking_count', 0)}個")
            
            print(f"\n⚠️ 迷惑メール判定に影響する可能性の高いURL要因:")
            print(f"   1. 外部サイトリンク: https://www.hugan.co.jp/business")
            print(f"   2. UTMパラメータ: utm_source=contactmail&utm_campaign=sale")
            print(f"   3. 複数CTAボタン: 営業メールの典型的パターン")
            print(f"   4. 配信停止URL: https://forms.gle/49BTNfSgUeNkH7rz5")
            print(f"   5. 追跡ピクセル: http://127.0.0.1:5002/track-open/")
        
        print(f"\n💡 推奨改善策:")
        print(f"   ✅ 外部リンクの削除または最小化")
        print(f"   ✅ UTMパラメータの削除")
        print(f"   ✅ CTAボタンの簡素化")
        print(f"   ✅ 配信停止URLの削除")
        print(f"   ✅ 追跡ピクセルの削除")
        print(f"   ✅ メール内容をテキスト中心に変更")
    
    def save_investigation_results(self):
        """調査結果保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'huganjob_url_spam_investigation_{timestamp}.json'
        
        report = {
            'investigation_info': {
                'timestamp': datetime.now().isoformat(),
                'purpose': 'HTMLメール内のURLが迷惑メール判定に与える影響調査',
                'comparison': '全URL含有版 vs URL削除版'
            },
            'results': self.investigation_results,
            'url_factors': [
                '外部サイトリンク（営業色強い）',
                'UTMパラメータ（トラッキング）',
                '複数CTAボタン（営業メールの典型）',
                '配信停止URL（大量送信の証拠）',
                '追跡ピクセル（スパム判定要因）'
            ],
            'recommendations': [
                '外部リンクの削除または最小化',
                'UTMパラメータの削除',
                'CTAボタンの簡素化',
                '配信停止URLの削除',
                '追跡ピクセルの削除'
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 調査結果保存: {filename}")
        return filename

def main():
    """メイン処理"""
    investigator = URLSpamInvestigator()
    
    # 設定読み込み
    if not investigator.load_config():
        return False
    
    # URL影響調査実行
    results = investigator.run_url_investigation()
    
    print(f"\n🏁 URL迷惑メール判定調査完了")
    print(f"📬 n.yamashita@raxus.incでの受信状況をご確認ください")
    print(f"📊 2通のメールの受信場所を比較してください:")
    print(f"   1. 全URL含有版 → 迷惑メール判定の可能性")
    print(f"   2. URL削除版 → 受信トレイ到達の可能性")
    
    return True

if __name__ == "__main__":
    main()
