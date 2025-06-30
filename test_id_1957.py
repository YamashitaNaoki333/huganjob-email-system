#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ID 1957 (アイリスオーヤマ株式会社) の送信テスト
停止原因の調査
"""

import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime

def test_id_1957():
    """ID 1957の送信テスト"""
    
    print("🔍 ID 1957 送信テスト開始")
    print("=" * 50)
    
    # 企業情報
    company_id = 1957
    company_name = "アイリスオーヤマ株式会社"
    recipient_email = "iriscareer@irisohyama.co.jp"
    job_position = "法人営業"
    
    print(f"企業ID: {company_id}")
    print(f"企業名: {company_name}")
    print(f"メールアドレス: {recipient_email}")
    print(f"募集職種: {job_position}")
    print()
    
    try:
        # 1. メールアドレス形式チェック
        print("📧 1. メールアドレス形式チェック")
        if '@' not in recipient_email or '.' not in recipient_email.split('@')[1]:
            print(f"❌ 無効なメールアドレス形式: {recipient_email}")
            return False
        print(f"✅ メールアドレス形式: 正常")
        
        # 2. メール作成テスト
        print("\n📝 2. メール作成テスト")
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"【{job_position}の人材採用を強化しませんか？】株式会社HUGANからのご提案"
        msg['From'] = formataddr(('竹下隼平【株式会社HUGAN】', 'contact@huganjob.jp'))
        msg['To'] = recipient_email
        msg['Reply-To'] = 'contact@huganjob.jp'
        
        # HTMLメール作成
        html_content = f"""
        <html>
        <body>
        <p>{company_name} 採用ご担当者様</p>
        <p>いつもお疲れ様です。<br>
        株式会社HUGANの竹下と申します。</p>
        <p>{company_name}様の{job_position}の採用活動について、<br>
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
        print("✅ メール作成: 成功")
        
        # 3. SMTP接続テスト
        print("\n🌐 3. SMTP接続テスト")
        print("   サーバー: smtp.huganjob.jp:587")
        
        server = smtplib.SMTP('smtp.huganjob.jp', 587, timeout=30)
        print("✅ SMTP接続: 成功")
        
        server.starttls()
        print("✅ STARTTLS: 成功")
        
        server.login('contact@huganjob.jp', 'gD34bEmB')
        print("✅ SMTP認証: 成功")
        
        # 4. 送信テスト（実際には送信しない）
        print("\n📤 4. 送信テスト（ドライラン）")
        print(f"   宛先: {recipient_email}")
        print(f"   件名: {msg['Subject']}")
        print("   ※実際の送信は行いません")
        
        # 実際に送信する場合は以下のコメントアウトを外す
        # server.send_message(msg)
        # print("✅ メール送信: 成功")
        
        server.quit()
        print("✅ SMTP切断: 成功")
        
        # 5. DNS解決テスト
        print("\n🌍 5. DNS解決テスト")
        import socket
        try:
            domain = recipient_email.split('@')[1]
            ip = socket.gethostbyname(domain)
            print(f"✅ DNS解決: {domain} -> {ip}")
        except Exception as dns_error:
            print(f"❌ DNS解決エラー: {dns_error}")
            return False
        
        print("\n✅ 全てのテストが成功しました")
        print("ID 1957の送信に技術的な問題はありません")
        
        return True
        
    except smtplib.SMTPException as smtp_error:
        print(f"\n❌ SMTP エラー: {smtp_error}")
        print(f"   エラータイプ: {type(smtp_error).__name__}")
        return False
        
    except Exception as e:
        print(f"\n❌ 一般エラー: {e}")
        print(f"   エラータイプ: {type(e).__name__}")
        import traceback
        print(f"   スタックトレース: {traceback.format_exc()}")
        return False

def check_system_resources():
    """システムリソースチェック"""
    print("\n💻 システムリソースチェック")
    print("-" * 30)
    
    try:
        import psutil
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"CPU使用率: {cpu_percent}%")
        
        # メモリ使用率
        memory = psutil.virtual_memory()
        print(f"メモリ使用率: {memory.percent}%")
        print(f"利用可能メモリ: {memory.available / 1024 / 1024 / 1024:.1f} GB")
        
        # ディスク使用率
        disk = psutil.disk_usage('.')
        print(f"ディスク使用率: {disk.percent}%")
        
        if cpu_percent > 90:
            print("⚠️ CPU使用率が高すぎます")
        if memory.percent > 90:
            print("⚠️ メモリ使用率が高すぎます")
        if disk.percent > 90:
            print("⚠️ ディスク使用率が高すぎます")
            
    except ImportError:
        print("psutilが利用できません - 基本チェックのみ")
    except Exception as e:
        print(f"リソースチェックエラー: {e}")

if __name__ == "__main__":
    print(f"テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # システムリソースチェック
    check_system_resources()
    
    # ID 1957テスト
    success = test_id_1957()
    
    print(f"\nテスト終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"テスト結果: {'成功' if success else '失敗'}")
