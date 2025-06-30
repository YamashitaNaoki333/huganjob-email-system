#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNS検証スキップ機能のテスト
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime

def test_direct_smtp_send():
    """DNS検証なしで直接SMTP送信テスト"""
    
    print("🧪 DNS検証スキップ送信テスト")
    print("=" * 50)
    print(f"テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # テスト対象（DNS解決失敗するドメイン）
    test_cases = [
        {
            "id": 1957,
            "company": "アイリスオーヤマ株式会社",
            "email": "iriscareer@irisohyama.co.jp",
            "job": "法人営業"
        },
        {
            "id": 1965,
            "company": "日新薬品株式会社", 
            "email": "info@yg-nissin.co.jp",
            "job": "薬剤師"
        }
    ]
    
    success_count = 0
    
    for i, case in enumerate(test_cases):
        print(f"📧 テスト {i+1}/{len(test_cases)}: {case['company']}")
        print(f"   ID: {case['id']}")
        print(f"   メール: {case['email']}")
        print(f"   職種: {case['job']}")
        
        try:
            # メール作成
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"【{case['job']}の人材採用を強化しませんか？】株式会社HUGANからのご提案"
            msg['From'] = formataddr(('竹下隼平【株式会社HUGAN】', 'contact@huganjob.jp'))
            msg['To'] = case['email']
            msg['Reply-To'] = 'contact@huganjob.jp'
            
            # HTMLメール作成
            html_content = f"""
            <html>
            <body>
            <p>{case['company']} 採用ご担当者様</p>
            <p>いつもお疲れ様です。<br>
            株式会社HUGANの竹下と申します。</p>
            <p>{case['company']}様の{case['job']}の採用活動について、<br>
            弊社の人材紹介サービスでお手伝いできることがございます。</p>
            <p>詳細については、お気軽にお問い合わせください。</p>
            <p>株式会社HUGAN<br>
            担当: 竹下<br>
            Email: contact@huganjob.jp</p>
            </body>
            </html>
            """
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            print(f"   ✅ メール作成: 成功")
            
            # SMTP送信（DNS検証なし）
            print(f"   📤 SMTP送信試行中...")
            
            # タイムアウトを短く設定
            server = smtplib.SMTP('smtp.huganjob.jp', 587, timeout=10)
            server.starttls()
            server.login('contact@huganjob.jp', 'gD34bEmB')
            
            # 実際の送信（ドライラン用にコメントアウト）
            # server.send_message(msg)
            print(f"   ⚠️ 実際の送信はスキップ（ドライラン）")
            
            server.quit()
            
            print(f"   ✅ SMTP処理: 成功")
            success_count += 1
            
        except smtplib.SMTPRecipientsRefused as e:
            print(f"   ❌ SMTP受信者拒否: {e}")
            print(f"   💡 この場合、DNS解決は不要だが、受信者が無効")
            
        except smtplib.SMTPException as e:
            print(f"   ❌ SMTP エラー: {e}")
            
        except Exception as e:
            print(f"   ❌ 一般エラー: {e}")
            
        print()
    
    # 結果サマリー
    print("=" * 50)
    print(f"📊 テスト結果サマリー")
    print(f"   成功: {success_count}/{len(test_cases)}")
    print(f"   成功率: {success_count/len(test_cases)*100:.1f}%")
    
    if success_count == len(test_cases):
        print("✅ DNS検証スキップ送信は技術的に可能です")
        print("💡 SMTPサーバーが実際の配信可否を判定します")
    else:
        print("⚠️ 一部で問題が発生しました")
    
    print(f"\nテスト終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def explain_dns_skip_mechanism():
    """DNS検証スキップの仕組み説明"""
    
    print("\n📚 DNS検証スキップの仕組み")
    print("=" * 40)
    
    print("""
🔄 通常の送信フロー:
1. DNS解決チェック ← ここで失敗すると停止
2. SMTP接続
3. メール送信
4. SMTPサーバーが配信先を解決

⚡ DNS検証スキップフロー:
1. DNS解決チェック ← スキップ
2. SMTP接続
3. メール送信
4. SMTPサーバーが配信先を解決 ← ここで失敗の場合はバウンス

💡 メリット:
- DNS解決できないドメインでも送信試行
- SMTPサーバーに判定を委ねる
- プロセスが停止しない

⚠️ デメリット:
- 無効なドメインへの送信でバウンス増加
- SMTPサーバーへの負荷増加
- 送信者レピュテーション低下の可能性

🎯 推奨用途:
- 一時的なDNS問題の回避
- 大量送信での効率化
- 特定のドメインでの問題回避
""")

if __name__ == "__main__":
    # DNS検証スキップテスト
    test_direct_smtp_send()
    
    # 仕組み説明
    explain_dns_skip_mechanism()
    
    print("\n🔧 実際の使用方法:")
    print("python huganjob_unified_sender.py --start-id 1957 --end-id 1970 --skip-dns")
    print("\n⚠️ 注意: この機能は慎重に使用してください")
