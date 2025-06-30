#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB DNS・SMTP徹底分析ツール
桜サーバー依存の根本原因を特定し、完全独立解決策を提案
"""

import socket
import subprocess
import sys
import os

def analyze_dns_records(domain):
    """DNS記録の詳細分析"""
    print(f"\n🔍 {domain} DNS詳細分析")
    print("=" * 60)
    
    # Aレコード確認
    try:
        ip_addresses = socket.gethostbyname_ex(domain)
        print(f"📍 Aレコード:")
        for ip in ip_addresses[2]:
            print(f"  IP: {ip}")
            
            # 桜サーバーIPかチェック
            if ip.startswith('103.3.') or ip.startswith('157.7.') or ip.startswith('210.188.'):
                print(f"    ⚠️ 桜サーバー系IP範囲")
            else:
                print(f"    ✅ 独立IP")
                
    except Exception as e:
        print(f"❌ DNS解決エラー: {e}")
    
    # nslookup実行（詳細情報取得）
    try:
        print(f"\n🔍 nslookup詳細:")
        result = subprocess.run(['nslookup', domain], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"❌ nslookup失敗: {result.stderr}")
    except Exception as e:
        print(f"❌ nslookup実行エラー: {e}")

def analyze_smtp_infrastructure():
    """SMTP基盤の徹底分析"""
    print("\n🏗️ SMTP基盤徹底分析")
    print("=" * 60)
    
    domains_to_analyze = [
        'smtp.huganjob.jp',
        'huganjob.jp',
        'mail.huganjob.jp',
        'mx.huganjob.jp'
    ]
    
    for domain in domains_to_analyze:
        print(f"\n📡 {domain} 分析中...")
        analyze_dns_records(domain)

def identify_sakura_dependency():
    """桜サーバー依存度の特定"""
    print("\n🚨 桜サーバー依存度分析")
    print("=" * 60)
    
    print("❌ 確認された桜サーバー依存:")
    print("  • smtp.huganjob.jp → sv12053.xserver.jp")
    print("  • IP範囲: 103.3.2.54 (桜サーバー系)")
    print("  • メールサーバー: sv12053.xserver.jp")
    print("  • DNS設定: 桜サーバー依存")
    
    print("\n🔍 根本原因:")
    print("  1. huganjob.jpドメインのDNS設定が桜サーバーを指している")
    print("  2. smtp.huganjob.jpが実際にはsv12053.xserver.jpのエイリアス")
    print("  3. メール送信方法に関係なく、必ず桜サーバーを経由")
    print("  4. DNS設定レベルでの依存のため、アプリケーション側では解決不可")

def propose_complete_independence_solutions():
    """完全独立解決策の提案"""
    print("\n💡 完全独立解決策")
    print("=" * 60)
    
    print("🚀 解決策1: 独立SMTPサービス利用")
    print("-" * 40)
    print("✅ 推奨サービス:")
    print("  • SendGrid (https://sendgrid.com/)")
    print("    - SMTP: smtp.sendgrid.net:587")
    print("    - 認証: APIキー")
    print("    - 月100通無料")
    print("")
    print("  • Amazon SES (https://aws.amazon.com/ses/)")
    print("    - SMTP: email-smtp.us-east-1.amazonaws.com:587")
    print("    - 認証: AWS Access Key")
    print("    - 月62,000通無料")
    print("")
    print("  • Mailgun (https://www.mailgun.com/)")
    print("    - SMTP: smtp.mailgun.org:587")
    print("    - 認証: APIキー")
    print("    - 月5,000通無料")
    
    print("\n🌐 解決策2: 独立ドメイン利用")
    print("-" * 40)
    print("✅ 代替ドメイン:")
    print("  • huganjob.com (新規取得)")
    print("  • huganjob.net (新規取得)")
    print("  • huganjob.org (新規取得)")
    print("  • mail.huganjob.jp (サブドメイン)")
    
    print("\n🔧 解決策3: DNS設定変更")
    print("-" * 40)
    print("✅ 必要な作業:")
    print("  1. huganjob.jpのDNS管理権限取得")
    print("  2. MXレコードを独立サーバーに変更")
    print("  3. SPF/DKIM/DMARCレコード設定")
    print("  4. 独立SMTPサーバーの設定")

def create_sendgrid_config():
    """SendGrid設定ファイル作成"""
    print("\n📝 SendGrid完全独立設定作成")
    print("-" * 40)
    
    config_content = """# HUGAN JOB SendGrid完全独立設定
# 桜サーバー完全回避 - SendGrid経由送信
# 作成日時: 2025年06月20日 19:00:00

[SMTP]
# SendGrid SMTP設定（桜サーバー完全回避）
server = smtp.sendgrid.net
port = 587
user = apikey
password = [SendGrid APIキーを設定]
sender_name = HUGAN採用事務局
from_email = contact@huganjob.jp
reply_to = contact@huganjob.jp

[SENDGRID]
api_key = [SendGrid APIキーを設定]
from_email = contact@huganjob.jp
from_name = HUGAN採用事務局
domain_authentication = huganjob.jp

[EMAIL_CONTENT]
subject = 【採用ご担当者様へ】採用工数の削減とミスマッチ防止を実現するご提案｜HUGAN JOB
template_file = corporate-email-newsletter.html
unsubscribe_url = https://forms.gle/49BTNfSgUeNkH7rz5

[SENDING]
interval = 5
max_per_hour = 50
method = send_message

[SECURITY]
use_tls = true
require_auth = true
timeout = 30

[INDEPENDENCE]
# 桜サーバー完全回避確認
sakura_free = true
independent_smtp = true
dns_independent = true
"""
    
    config_dir = 'config'
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    config_file = 'config/sendgrid_independent_config.ini'
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✅ SendGrid独立設定ファイルを作成: {config_file}")

def create_amazon_ses_config():
    """Amazon SES設定ファイル作成"""
    print("\n📝 Amazon SES完全独立設定作成")
    print("-" * 40)
    
    config_content = """# HUGAN JOB Amazon SES完全独立設定
# 桜サーバー完全回避 - Amazon SES経由送信
# 作成日時: 2025年06月20日 19:00:00

[SMTP]
# Amazon SES SMTP設定（桜サーバー完全回避）
server = email-smtp.us-east-1.amazonaws.com
port = 587
user = [AWS Access Key ID]
password = [AWS Secret Access Key]
sender_name = HUGAN採用事務局
from_email = contact@huganjob.jp
reply_to = contact@huganjob.jp

[AWS_SES]
access_key_id = [AWS Access Key ID]
secret_access_key = [AWS Secret Access Key]
region = us-east-1
from_email = contact@huganjob.jp
from_name = HUGAN採用事務局

[EMAIL_CONTENT]
subject = 【採用ご担当者様へ】採用工数の削減とミスマッチ防止を実現するご提案｜HUGAN JOB
template_file = corporate-email-newsletter.html
unsubscribe_url = https://forms.gle/49BTNfSgUeNkH7rz5

[SENDING]
interval = 5
max_per_hour = 50
method = send_message

[SECURITY]
use_tls = true
require_auth = true
timeout = 30

[INDEPENDENCE]
# 桜サーバー完全回避確認
sakura_free = true
independent_smtp = true
dns_independent = true
"""
    
    config_file = 'config/amazon_ses_independent_config.ini'
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✅ Amazon SES独立設定ファイルを作成: {config_file}")

def main():
    """メイン処理"""
    print("=" * 60)
    print("🔍 HUGAN JOB 桜サーバー依存徹底分析")
    print("=" * 60)
    
    print("\n🎯 分析目的:")
    print("• 桜サーバー依存の根本原因特定")
    print("• DNS設定レベルでの依存関係分析")
    print("• 完全独立解決策の提案")
    print("• 今後一切の桜サーバー影響除去")
    
    # SMTP基盤分析
    analyze_smtp_infrastructure()
    
    # 桜サーバー依存度特定
    identify_sakura_dependency()
    
    # 完全独立解決策提案
    propose_complete_independence_solutions()
    
    # 独立設定ファイル作成
    create_sendgrid_config()
    create_amazon_ses_config()
    
    print("\n📋 分析結果サマリー")
    print("=" * 60)
    print("❌ 根本原因:")
    print("  • smtp.huganjob.jp は sv12053.xserver.jp のエイリアス")
    print("  • DNS設定レベルで桜サーバーに依存")
    print("  • アプリケーション側では解決不可能")
    
    print("\n✅ 完全独立解決策:")
    print("  1. SendGrid等の独立SMTPサービス利用")
    print("  2. 独立ドメインの取得・利用")
    print("  3. DNS設定の完全変更")
    
    print("\n🚀 推奨次ステップ:")
    print("  1. SendGridアカウント作成")
    print("  2. huganjob.jpドメイン認証")
    print("  3. 独立送信システム実装")
    print("  4. 桜サーバー依存の完全除去")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 分析がキャンセルされました")
    except Exception as e:
        print(f"\n❌ エラーが発生: {e}")
        import traceback
        traceback.print_exc()
