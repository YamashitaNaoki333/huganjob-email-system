#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGANJOB 軽量メール送信システム
プロセスハング問題の根本解決版

特徴:
- 重いファイル処理を完全排除
- 最小限の処理のみ実行
- 確実なプロセス終了
"""

import smtplib
import csv
import os
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate
from email.header import Header

class LightweightEmailSender:
    """軽量メール送信クラス"""
    
    def __init__(self):
        self.results = []
    
    def load_company_data(self, start_id, end_id):
        """企業データ読み込み（軽量版）"""
        companies = []
        csv_file = 'data/new_input_test.csv'
        
        print(f"📂 企業データ読み込み: {csv_file}")
        
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        company_id = int(row.get('ID', 0))
                        if start_id <= company_id <= end_id:
                            # メールアドレス取得
                            email = row.get('採用担当メールアドレス', '').strip()
                            if not email or email == '-':
                                # メール抽出結果から取得
                                email = self.get_extracted_email(company_id)
                            
                            if email and email != '-':
                                companies.append({
                                    'id': company_id,
                                    'name': row.get('企業名', ''),
                                    'email': email,
                                    'job_position': row.get('募集職種', '営業')
                                })
                    except ValueError:
                        continue
            
            print(f"✅ 読み込み完了: {len(companies)}社")
            return companies
            
        except Exception as e:
            print(f"❌ データ読み込みエラー: {e}")
            return []
    
    def get_extracted_email(self, company_id):
        """抽出済みメールアドレス取得"""
        try:
            extraction_file = 'huganjob_email_resolution_results.csv'
            if os.path.exists(extraction_file):
                with open(extraction_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get('企業ID') == str(company_id):
                            return row.get('抽出メールアドレス', '')
        except:
            pass
        return ''
    
    def create_email(self, company_name, job_position, recipient_email):
        """メール作成（軽量版）"""
        try:
            # 件名作成
            subject = f"【{job_position}の人材採用を強化しませんか？】株式会社HUGANからのご提案"
            
            # メール作成
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = formataddr(('竹下隼平【株式会社HUGAN】', 'contact@huganjob.jp'))
            msg['To'] = recipient_email
            msg['Reply-To'] = 'contact@huganjob.jp'
            msg['Date'] = formatdate(localtime=True)
            
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
            
            return msg
            
        except Exception as e:
            print(f"   ❌ メール作成エラー: {e}")
            return None
    
    def send_email(self, company_id, company_name, job_position, recipient_email):
        """メール送信（軽量版）"""
        try:
            print(f"\n📤 送信準備: {company_name}")
            print(f"   📧 宛先: {recipient_email}")
            print(f"   💼 職種: {job_position}")
            
            # メール作成
            msg = self.create_email(company_name, job_position, recipient_email)
            if not msg:
                print(f"   ❌ メール作成失敗")
                return 'failed'
            
            # SMTP送信
            print(f"   📤 SMTP送信中...")
            server = smtplib.SMTP('smtp.huganjob.jp', 587, timeout=10)
            server.starttls()
            server.login('contact@huganjob.jp', 'gD34bEmB')
            server.send_message(msg)
            server.quit()
            
            print(f"   ✅ 送信成功: {recipient_email}")
            
            # 結果記録（メモリのみ）
            self.results.append({
                'id': company_id,
                'name': company_name,
                'email': recipient_email,
                'result': 'success',
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            return 'success'
            
        except Exception as e:
            print(f"   ❌ 送信失敗: {recipient_email} - {e}")
            
            # 結果記録（メモリのみ）
            self.results.append({
                'id': company_id,
                'name': company_name,
                'email': recipient_email,
                'result': 'failed',
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error': str(e)
            })
            
            return 'failed'
    
    def send_to_companies(self, companies):
        """企業リストへの送信実行"""
        print("=" * 60)
        print("📧 HUGANJOB 軽量メール送信システム")
        print("=" * 60)
        
        results = {'success': 0, 'failed': 0}
        
        for i, company in enumerate(companies):
            print(f"\n📤 {i+1}/{len(companies)}: ID {company['id']} 送信開始")
            
            result = self.send_email(
                company['id'], company['name'],
                company['job_position'], company['email']
            )
            
            results[result] += 1
            print(f"   📊 送信結果: {result}")
            
            # 送信間隔（最後以外）
            if i < len(companies) - 1:
                print(f"   ⏳ 送信間隔待機中（3秒）...")
                import time
                time.sleep(3)
        
        # 結果表示
        print(f"\n" + "=" * 60)
        print("📊 軽量メール送信結果")
        print("=" * 60)
        print(f"✅ 成功: {results['success']}/{len(companies)}")
        print(f"❌ 失敗: {results['failed']}/{len(companies)}")
        
        # 結果サマリー（ファイル保存なし）
        print(f"\n📋 送信結果サマリー:")
        for result in self.results:
            status = "✅" if result['result'] == 'success' else "❌"
            print(f"  {status} ID {result['id']}: {result['name']} - {result['result']}")
        
        return results['success'] > 0

def main():
    """メイン処理"""
    import argparse
    
    print(f"🚀 HUGANJOB軽量メール送信システム開始")
    print(f"⏰ 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # コマンドライン引数解析
    parser = argparse.ArgumentParser(description='HUGANJOB軽量メール送信システム')
    parser.add_argument('--start-id', type=int, required=True, help='送信開始ID')
    parser.add_argument('--end-id', type=int, required=True, help='送信終了ID')
    args = parser.parse_args()
    
    try:
        # 送信システム初期化
        sender = LightweightEmailSender()
        
        # 企業データ読み込み
        companies = sender.load_company_data(args.start_id, args.end_id)
        
        if not companies:
            print("❌ 送信対象企業が見つかりません")
            return False
        
        print(f"📋 送信対象: ID {args.start_id}-{args.end_id} ({len(companies)}社)")
        
        # 送信実行
        success = sender.send_to_companies(companies)
        
        print(f"\n🏁 処理完了: {'成功' if success else '失敗'}")
        print(f"⏰ 終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success
        
    except KeyboardInterrupt:
        print("\n❌ 送信がキャンセルされました")
        return False
    except Exception as e:
        print(f"\n❌ システムエラー: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        print(f"🎯 軽量送信システム完了: {'成功' if success else '失敗'}")
        
        # 即座にプロセス終了
        exit_code = 0 if success else 1
        print(f"🔚 プロセス終了 (コード: {exit_code})")
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"❌ 致命的エラー: {e}")
        sys.exit(1)
