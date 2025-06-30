#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB 修正版メール送信スクリプト
変数置換エラーとバウンス問題を修正

作成日時: 2025年06月23日 12:00:00
修正内容:
1. 変数置換処理の強化とデバッグ
2. バウンスメール対策
3. エラーハンドリング強化
"""

import smtplib
import configparser
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate

def read_config():
    """設定ファイル読み込み"""
    config = configparser.ConfigParser()
    config.read('config/huganjob_email_config.ini', encoding='utf-8')
    return config

def read_html_template():
    """HTMLテンプレート読み込み"""
    try:
        with open('corporate-email-newsletter.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ HTMLテンプレート読み込みエラー: {e}")
        return None

def create_email_with_debug(recipient_email, company_name, job_position, html_content, config):
    """デバッグ強化版メール作成"""
    try:
        print(f"\n🔧 メール作成デバッグ情報:")
        print(f"   企業名: {company_name}")
        print(f"   職種: {job_position} (型: {type(job_position)})")
        print(f"   宛先: {recipient_email}")
        
        # HTMLテンプレート内の変数を置換
        print(f"   🔧 HTML変数置換前: {{{{company_name}}}} と {{{{job_position}}}} を検索中...")
        personalized_content = html_content.replace('{{company_name}}', str(company_name))
        personalized_content = personalized_content.replace('{{job_position}}', str(job_position))
        print(f"   ✅ HTML変数置換完了")
        
        # 件名作成（強化版）
        subject_template = config.get('EMAIL_CONTENT', 'subject')
        print(f"   🔧 件名テンプレート: '{subject_template}'")
        print(f"   🔧 置換対象: '{{job_position}}' -> '{job_position}'")
        
        # 複数の置換方法を試行
        subject_v1 = subject_template.replace('{job_position}', str(job_position))
        subject_v2 = subject_template.replace('{{job_position}}', str(job_position))
        
        print(f"   🔧 置換結果v1: '{subject_v1}'")
        print(f"   🔧 置換結果v2: '{subject_v2}'")
        
        # 最終的な件名を決定
        if '{job_position}' not in subject_v1:
            final_subject = subject_v1
            print(f"   ✅ v1置換成功を採用")
        elif '{{job_position}}' not in subject_v2:
            final_subject = subject_v2
            print(f"   ✅ v2置換成功を採用")
        else:
            # 手動で確実な置換を実行
            final_subject = f"【{job_position}の人材採用を強化しませんか？】株式会社HUGANからのご提案"
            print(f"   ⚠️ 手動置換を実行: '{final_subject}'")
        
        print(f"   🎯 最終件名: '{final_subject}'")
        
        # メール作成
        msg = MIMEMultipart('alternative')
        msg['Subject'] = Header(final_subject, 'utf-8')
        msg['From'] = formataddr((config.get('SMTP', 'sender_name'), config.get('SMTP', 'from_email')))
        msg['To'] = recipient_email
        msg['Reply-To'] = config.get('SMTP', 'reply_to')
        msg['Date'] = formatdate(localtime=True)
        
        # HTMLパート追加
        html_part = MIMEText(personalized_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        print(f"   ✅ メール作成完了")
        return msg
        
    except Exception as e:
        print(f"❌ メール作成エラー: {e}")
        return None

def send_email_with_validation(config, recipient_email, company_name, job_position, html_content):
    """バリデーション強化版メール送信"""
    try:
        print(f"\n📤 送信開始: {company_name}")
        print(f"   📧 宛先: {recipient_email}")
        print(f"   💼 職種: {job_position}")
        
        # バウンス対策: 特定のメールアドレスをスキップ
        bounce_addresses = ['info@sincere.co.jp']  # バウンス報告があったアドレス
        
        if recipient_email in bounce_addresses:
            print(f"   ⚠️ バウンス履歴あり: {recipient_email} - 送信をスキップします")
            return False
        
        # SMTP設定取得
        smtp_server = config.get('SMTP', 'server')
        smtp_port = int(config.get('SMTP', 'port'))
        smtp_user = config.get('SMTP', 'user')
        smtp_password = config.get('SMTP', 'password')
        
        print(f"   🔧 SMTP: {smtp_server}:{smtp_port}")
        
        # メール作成
        msg = create_email_with_debug(recipient_email, company_name, job_position, html_content, config)
        if not msg:
            return False
        
        # SMTP接続
        print(f"   🔗 SMTP接続中...")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=int(config.get('SECURITY', 'timeout')))
        
        if config.getboolean('SECURITY', 'use_tls'):
            print(f"   🔒 STARTTLS開始...")
            server.starttls()
        
        if config.getboolean('SECURITY', 'require_auth'):
            print(f"   🔑 認証中...")
            server.login(smtp_user, smtp_password)
        
        # メール送信
        print(f"   📤 メール送信中...")
        server.send_message(msg)
        server.quit()
        
        print(f"   ✅ 送信成功: {recipient_email}")
        return True
        
    except Exception as e:
        print(f"   ❌ 送信失敗: {recipient_email} - {e}")
        return False

def main():
    """メイン処理"""
    print("=" * 60)
    print("📧 HUGAN JOB 修正版営業メール送信")
    print("=" * 60)
    
    # 設定読み込み
    config = read_config()
    print("✅ 設定ファイル読み込み完了")
    
    # HTMLテンプレート読み込み
    html_content = read_html_template()
    if not html_content:
        return False
    print("✅ HTMLテンプレート読み込み完了")
    
    # 設定確認
    print(f"\n📋 送信設定:")
    print(f"  SMTPサーバー: {config.get('SMTP', 'server')}")
    print(f"  認証ユーザー: {config.get('SMTP', 'user')}")
    print(f"  送信者表示: {config.get('SMTP', 'sender_name')} <{config.get('SMTP', 'from_email')}>")
    
    # ID 1-5の企業データ（バウンス対策版）
    companies = [
        {
            "id": 1,
            "name": "エスケー化研株式会社",
            "email": "info@sk-kaken.co.jp",
            "job_position": "事務スタッフ"
        },
        {
            "id": 2,
            "name": "ラ・シンシア株式会社",
            "email": "info@sincere.co.jp",  # バウンス履歴あり
            "job_position": "製造スタッフ"
        },
        {
            "id": 3,
            "name": "日本セロンパック株式会社",
            "email": "info@cellonpack.com",
            "job_position": "事務スタッフ"
        },
        {
            "id": 4,
            "name": "西日本旅客鉄道株式会社",
            "email": "info@westjr.co.jp",
            "job_position": "技術職"
        },
        {
            "id": 5,
            "name": "クルーズカンパニー株式会社",
            "email": "info@crewz.co.jp",
            "job_position": "事務系総合職"
        }
    ]
    
    print(f"\n📋 送信対象企業: {len(companies)}社")
    for company in companies:
        print(f"  ID {company['id']}: {company['name']} - {company['email']} ({company['job_position']})")
    
    # 送信開始
    print(f"\n📤 営業メール送信開始...")
    print("-" * 60)
    
    success_count = 0
    skip_count = 0
    total_count = len(companies)
    
    for company in companies:
        result = send_email_with_validation(config, company['email'], company['name'], company['job_position'], html_content)
        if result:
            success_count += 1
        elif company['email'] == 'info@sincere.co.jp':
            skip_count += 1
            print(f"   📝 バウンス対策によりスキップ")
        
        # 送信間隔
        if company != companies[-1]:  # 最後の企業以外
            interval = int(config.get('SENDING', 'interval'))
            print(f"   ⏳ 送信間隔待機中（{interval}秒）...")
            time.sleep(interval)
    
    # 結果表示
    print("\n" + "=" * 60)
    print("📊 営業メール送信結果")
    print("=" * 60)
    print(f"✅ 成功: {success_count}/{total_count}")
    print(f"⚠️ スキップ: {skip_count}/{total_count} (バウンス対策)")
    print(f"❌ 失敗: {total_count - success_count - skip_count}/{total_count}")
    
    if success_count > 0:
        print(f"\n🎉 {success_count}社への営業メール送信が完了しました！")
        print("📧 各企業の受信ボックスを確認してください")
        
        print(f"\n📋 送信内容:")
        print("  • 件名: 【○○（募集職種）の人材採用を強化しませんか？】株式会社HUGANからのご提案")
        print("  • 送信者: 竹下隼平【株式会社HUGAN】 <contact@huganjob.jp>")
        print("  • 内容: 企業名と募集職種を動的に挿入したHTML形式のメール")
        
        return True
    else:
        print(f"\n⚠️ 送信に成功した企業がありませんでした")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
