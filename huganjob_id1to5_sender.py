#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB ID 1-5企業向け営業メール送信スクリプト
既存のメールアドレス抽出結果を使用してID 1-5の企業に営業メールを送信

作成日時: 2025年06月23日 11:55:00
作成者: AI Assistant
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

def create_email(recipient_email, recipient_name, company_name, job_position, html_content, config):
    """メール作成"""
    try:
        # テンプレート内の変数を置換
        personalized_content = html_content.replace('{{company_name}}', company_name)
        personalized_content = personalized_content.replace('{{job_position}}', job_position)
        
        # 件名作成（デバッグ情報付き）
        subject_template = config.get('EMAIL_CONTENT', 'subject')
        print(f"   🔧 件名テンプレート: {subject_template}")
        print(f"   🔧 職種: {job_position}")
        subject = subject_template.replace('{job_position}', str(job_position))
        print(f"   🔧 置換後件名: {subject}")
        
        # メール作成
        msg = MIMEMultipart('alternative')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = formataddr((config.get('SMTP', 'sender_name'), config.get('SMTP', 'from_email')))
        msg['To'] = recipient_email
        msg['Reply-To'] = config.get('SMTP', 'reply_to')
        msg['Date'] = formatdate(localtime=True)
        
        # HTMLパート追加
        html_part = MIMEText(personalized_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        return msg
        
    except Exception as e:
        print(f"❌ メール作成エラー: {e}")
        return None

def send_email(config, recipient_email, recipient_name, company_name, job_position, html_content):
    """メール送信"""
    try:
        print(f"\n📤 送信中: {company_name} ({recipient_email})")
        print(f"   💼 職種: {job_position}")
        
        # SMTP設定取得
        smtp_server = config.get('SMTP', 'server')
        smtp_port = int(config.get('SMTP', 'port'))
        smtp_user = config.get('SMTP', 'user')
        smtp_password = config.get('SMTP', 'password')
        
        # メール作成
        msg = create_email(recipient_email, recipient_name, company_name, job_position, html_content, config)
        if not msg:
            return False
        
        # SMTP接続
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=int(config.get('SECURITY', 'timeout')))
        
        if config.getboolean('SECURITY', 'use_tls'):
            server.starttls()
        
        if config.getboolean('SECURITY', 'require_auth'):
            server.login(smtp_user, smtp_password)
        
        # メール送信
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
    print("📧 HUGAN JOB ID 1-5企業向け営業メール送信")
    print("=" * 60)
    
    # 設定読み込み
    config = read_config()
    if not config:
        print("❌ 設定ファイル読み込み失敗")
        return False
    
    print("✅ 設定ファイル読み込み完了")
    
    # HTMLテンプレート読み込み
    html_content = read_html_template()
    if not html_content:
        return False
    
    print("✅ HTMLテンプレート読み込み完了")
    
    # 設定確認
    print("\n📋 送信設定:")
    print(f"  SMTPサーバー: {config.get('SMTP', 'server')}")
    print(f"  認証ユーザー: {config.get('SMTP', 'user')}")
    print(f"  送信者表示: {config.get('SMTP', 'sender_name')} <{config.get('SMTP', 'from_email')}>")
    
    # ID 1-5の企業データ（huganjob_email_resolution_results.csvから取得）
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
            "email": "info@sincere.co.jp",  # バウンス報告あり - 要検証
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
    print("\n📤 営業メール送信開始...")
    print("-" * 40)
    
    success_count = 0
    total_count = len(companies)
    
    for company in companies:
        if send_email(config, company['email'], "", company['name'], company['job_position'], html_content):
            success_count += 1
        
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
    print(f"❌ 失敗: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 全ての営業メール送信が完了しました！")
        print("📧 各企業の受信ボックスを確認してください")
        
        print("\n📋 送信内容:")
        print("  • 件名: 【○○（募集職種）の人材採用を強化しませんか？】株式会社HUGANからのご提案")
        print("  • 送信者: 竹下隼平【株式会社HUGAN】 <contact@huganjob.jp>")
        print("  • 内容: 企業名と募集職種を動的に挿入したHTML形式のメール")
        
        return True
    else:
        print("\n⚠️  一部の送信に失敗しました")
        print("🔧 設定やネットワーク接続を確認してください")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
