#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
メール認証診断ツール
SPF/DKIM/DMARC設定の確認と迷惑メール判定原因の特定
"""

import dns.resolver
import smtplib
import socket
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formatdate

def check_dns_records(domain):
    """DNS設定の確認"""
    print(f"\n🔍 {domain} のDNS設定確認")
    print("-" * 50)
    
    results = {}
    
    # SPFレコード確認
    try:
        spf_records = dns.resolver.resolve(domain, 'TXT')
        spf_found = False
        for record in spf_records:
            txt_value = record.to_text().strip('"')
            if txt_value.startswith('v=spf1'):
                print(f"✅ SPFレコード: {txt_value}")
                results['spf'] = txt_value
                spf_found = True
                break
        
        if not spf_found:
            print("❌ SPFレコードが見つかりません")
            results['spf'] = None
            
    except Exception as e:
        print(f"❌ SPFレコード確認エラー: {e}")
        results['spf'] = None
    
    # DKIMレコード確認（一般的なセレクター）
    dkim_selectors = ['default', 'mail', 'google', 'k1', 'selector1', 'selector2']
    dkim_found = False
    
    for selector in dkim_selectors:
        try:
            dkim_domain = f"{selector}._domainkey.{domain}"
            dkim_records = dns.resolver.resolve(dkim_domain, 'TXT')
            for record in dkim_records:
                txt_value = record.to_text().strip('"')
                if 'v=DKIM1' in txt_value:
                    print(f"✅ DKIMレコード ({selector}): {txt_value[:100]}...")
                    results['dkim'] = {'selector': selector, 'record': txt_value}
                    dkim_found = True
                    break
            if dkim_found:
                break
        except:
            continue
    
    if not dkim_found:
        print("❌ DKIMレコードが見つかりません")
        results['dkim'] = None
    
    # DMARCレコード確認
    try:
        dmarc_domain = f"_dmarc.{domain}"
        dmarc_records = dns.resolver.resolve(dmarc_domain, 'TXT')
        for record in dmarc_records:
            txt_value = record.to_text().strip('"')
            if txt_value.startswith('v=DMARC1'):
                print(f"✅ DMARCレコード: {txt_value}")
                results['dmarc'] = txt_value
                break
    except Exception as e:
        print(f"❌ DMARCレコード確認エラー: {e}")
        results['dmarc'] = None
    
    # MXレコード確認
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        print(f"✅ MXレコード:")
        for mx in mx_records:
            print(f"   {mx.preference} {mx.exchange}")
        results['mx'] = [str(mx.exchange) for mx in mx_records]
    except Exception as e:
        print(f"❌ MXレコード確認エラー: {e}")
        results['mx'] = None
    
    return results

def check_smtp_server_reputation(smtp_server):
    """SMTPサーバーの評判確認"""
    print(f"\n🔍 SMTPサーバー評判確認: {smtp_server}")
    print("-" * 50)
    
    try:
        # IPアドレス取得
        ip_address = socket.gethostbyname(smtp_server)
        print(f"📡 IPアドレス: {ip_address}")
        
        # 逆引きDNS確認
        try:
            reverse_dns = socket.gethostbyaddr(ip_address)[0]
            print(f"🔄 逆引きDNS: {reverse_dns}")
        except:
            print("❌ 逆引きDNS設定なし")
        
        # ブラックリスト確認（簡易）
        blacklists = [
            'zen.spamhaus.org',
            'bl.spamcop.net',
            'dnsbl.sorbs.net'
        ]
        
        print("🛡️ ブラックリスト確認:")
        for bl in blacklists:
            try:
                # IPアドレスを逆順にしてブラックリストに問い合わせ
                reversed_ip = '.'.join(ip_address.split('.')[::-1])
                query = f"{reversed_ip}.{bl}"
                dns.resolver.resolve(query, 'A')
                print(f"   ❌ {bl}: リストに登録されています")
            except:
                print(f"   ✅ {bl}: 問題なし")
        
        return ip_address
        
    except Exception as e:
        print(f"❌ サーバー確認エラー: {e}")
        return None

def create_authentication_test_email(recipient_email):
    """認証テスト用メールを作成"""
    
    msg = MIMEMultipart('alternative')
    
    # 認証改善のためのヘッダー設定
    msg['From'] = 'HUGAN採用事務局 <contact@huganjob.jp>'
    msg['To'] = recipient_email
    msg['Subject'] = Header('【HUGAN JOB】メール認証改善テスト - SPF/DKIM対応', 'utf-8')
    msg['Date'] = formatdate(localtime=True)
    msg['Reply-To'] = 'contact@huganjob.jp'
    
    # 認証改善のための追加ヘッダー
    msg['Return-Path'] = 'contact@huganjob.jp'
    msg['Sender'] = 'contact@huganjob.jp'
    msg['Message-ID'] = f"<huganjob-auth-{int(time.time())}@huganjob.jp>"
    msg['X-Mailer'] = 'HUGAN JOB Authentication System'
    msg['X-Priority'] = '3'
    msg['Organization'] = 'HUGAN JOB'
    
    # 迷惑メール対策ヘッダー
    msg['List-Unsubscribe'] = '<mailto:unsubscribe@huganjob.jp>'
    msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
    msg['Precedence'] = 'bulk'
    
    # テキスト版
    text_content = """
【HUGAN JOB】メール認証改善テスト

いつもお世話になっております。
HUGAN採用事務局です。

このメールは、メール認証（SPF/DKIM/DMARC）の改善テストです。

■ 実施した認証改善
・SPF設定の確認と最適化
・DKIM署名の設定
・DMARC ポリシーの設定
・送信者認証の強化

■ 確認ポイント
・送信者が正しく認証されているか
・迷惑メール判定が改善されているか
・メールヘッダーの認証結果

このメールが正常に受信でき、迷惑メールフォルダに入っていない場合、
認証改善が成功しています。

--
HUGAN採用事務局
contact@huganjob.jp
https://huganjob.jp/

※このメールはメール認証改善テスト用です。
    """.strip()
    
    # HTML版
    html_content = """
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { font-family: 'Hiragino Sans', 'Yu Gothic', 'Meiryo', sans-serif; line-height: 1.6; color: #333; }
            .header { background-color: #2c5aa0; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; }
            .section { margin-bottom: 20px; }
            .highlight { background-color: #e8f4fd; padding: 15px; border-left: 4px solid #2c5aa0; }
            .footer { background-color: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #666; }
            ul { padding-left: 20px; }
            li { margin-bottom: 5px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>【HUGAN JOB】メール認証改善テスト</h1>
            <p>SPF/DKIM/DMARC対応</p>
        </div>
        
        <div class="content">
            <div class="section">
                <p>いつもお世話になっております。<br>
                HUGAN採用事務局です。</p>
                <p>このメールは、メール認証（SPF/DKIM/DMARC）の改善テストです。</p>
            </div>
            
            <div class="section highlight">
                <h3>■ 実施した認証改善</h3>
                <ul>
                    <li>SPF設定の確認と最適化</li>
                    <li>DKIM署名の設定</li>
                    <li>DMARC ポリシーの設定</li>
                    <li>送信者認証の強化</li>
                </ul>
            </div>
            
            <div class="section">
                <h3>■ 確認ポイント</h3>
                <ul>
                    <li>送信者が正しく認証されているか</li>
                    <li>迷惑メール判定が改善されているか</li>
                    <li>メールヘッダーの認証結果</li>
                </ul>
            </div>
            
            <div class="section">
                <p><strong>このメールが正常に受信でき、迷惑メールフォルダに入っていない場合、認証改善が成功しています。</strong></p>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>HUGAN採用事務局</strong><br>
            contact@huganjob.jp<br>
            <a href="https://huganjob.jp/">https://huganjob.jp/</a></p>
            <p style="margin-top: 10px; font-size: 11px;">※このメールはメール認証改善テスト用です。</p>
        </div>
    </body>
    </html>
    """
    
    # メール本文を追加
    text_part = MIMEText(text_content, 'plain', 'utf-8')
    html_part = MIMEText(html_content, 'html', 'utf-8')
    
    msg.attach(text_part)
    msg.attach(html_part)
    
    return msg

def generate_dns_recommendations(domain, dns_results, smtp_server):
    """DNS設定の推奨事項を生成"""
    print(f"\n📋 {domain} DNS設定推奨事項")
    print("=" * 60)
    
    recommendations = []
    
    # SPF設定
    if not dns_results.get('spf'):
        print("🔧 SPFレコード設定が必要:")
        print(f"   TXT レコード: v=spf1 include:xserver.ne.jp ~all")
        recommendations.append("SPF設定")
    else:
        spf = dns_results['spf']
        if 'xserver.ne.jp' not in spf:
            print("🔧 SPFレコード更新推奨:")
            print(f"   現在: {spf}")
            print(f"   推奨: v=spf1 include:xserver.ne.jp ~all")
            recommendations.append("SPF更新")
    
    # DKIM設定
    if not dns_results.get('dkim'):
        print("🔧 DKIMレコード設定が必要:")
        print("   Xserverの管理画面でDKIM設定を有効化してください")
        recommendations.append("DKIM設定")
    
    # DMARC設定
    if not dns_results.get('dmarc'):
        print("🔧 DMARCレコード設定が必要:")
        print(f"   _dmarc.{domain} TXT レコード: v=DMARC1; p=quarantine; rua=mailto:dmarc@{domain}")
        recommendations.append("DMARC設定")
    
    return recommendations

def main():
    """メイン処理"""
    print("=" * 60)
    print("📧 メール認証診断ツール")
    print("送信者アドレス不明問題の解決")
    print("=" * 60)
    
    domain = "huganjob.jp"
    smtp_server = "smtp.huganjob.jp"
    
    # DNS設定確認
    dns_results = check_dns_records(domain)
    
    # SMTPサーバー確認
    smtp_ip = check_smtp_server_reputation(smtp_server)
    
    # 推奨事項生成
    recommendations = generate_dns_recommendations(domain, dns_results, smtp_server)
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 診断結果サマリー")
    print("=" * 60)
    
    if recommendations:
        print("⚠️ 改善が必要な項目:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
        
        print("\n🔧 迷惑メール判定改善のための対策:")
        print("1. Xserver管理画面でDKIM設定を有効化")
        print("2. SPFレコードにXserverを含める")
        print("3. DMARCポリシーを設定")
        print("4. 送信頻度を調整（1日100通以下推奨）")
        print("5. メール内容の改善（営業色を薄める）")
    else:
        print("✅ DNS設定は適切です")
    
    print(f"\n📧 テストメール送信の準備ができました")
    print("認証改善後のテストメール送信を実行しますか？")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ エラーが発生: {e}")
        import traceback
        traceback.print_exc()
