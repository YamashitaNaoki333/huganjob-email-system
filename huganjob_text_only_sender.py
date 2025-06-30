#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB テキストメール専用送信システム
HTMLメールが表示されない環境向けのテキストメール送信システム

作成日時: 2025年06月25日 10:00:00
目的: HTMLメール表示問題の解決とテキストメールでのアプローチ
"""

import smtplib
import configparser
import time
import csv
import os
import sys
import argparse
from datetime import datetime
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate
from huganjob_duplicate_prevention import DuplicatePreventionManager
from huganjob_unsubscribe_manager import HUGANJOBUnsubscribeManager

# プロセス制限設定
MAX_EXECUTION_TIME = 1800  # 30分でタイムアウト
MAX_COMPANIES_PER_BATCH = 200  # 一度に処理する最大企業数

def check_timeout(start_time, max_time):
    """タイムアウトチェック（Windows対応）"""
    elapsed = (datetime.now() - start_time).total_seconds()
    if elapsed > max_time:
        print(f"\n❌ プロセスタイムアウト: {max_time//60}分を超過しました")
        print("🛑 プロセスを強制終了します")
        return True
    return False

class TextOnlyEmailSender:
    """テキストメール専用送信クラス"""

    def __init__(self):
        self.prevention_manager = DuplicatePreventionManager()
        self.unsubscribe_manager = HUGANJOBUnsubscribeManager()
        self.config = None
        self.text_template = None
        self.sending_results = []  # 送信結果を保存するリスト
        self.start_time = None  # 実行開始時刻
        
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
    
    def load_text_template(self):
        """テキストテンプレート読み込み"""
        try:
            with open('templates/corporate-email-newsletter-text.txt', 'r', encoding='utf-8') as f:
                self.text_template = f.read()
            print("✅ テキストテンプレート読み込み完了")
            return True
        except Exception as e:
            print(f"❌ テキストテンプレート読み込みエラー: {e}")
            return False

    def extract_primary_job_position(self, job_position):
        """複数職種から主要職種を抽出（Phase 2対応）"""
        try:
            if '/' in job_position:
                # '/'で分割された複数職種の場合、最初の職種を使用
                primary = job_position.split('/')[0].strip()
                print(f"   🎯 複数職種検出: '{job_position}' → 主要職種: '{primary}'")
                return primary
            else:
                return job_position.strip()
        except Exception as e:
            print(f"   ⚠️ 職種抽出エラー: {e} - 元の職種を使用")
            return job_position

    def create_text_email(self, company_name, job_position, recipient_email):
        """テキストメール作成（シンプル版）"""
        try:
            # 複数職種から主要職種を抽出
            primary_job_position = self.extract_primary_job_position(job_position)

            # テキスト変数置換
            text_content = self.text_template.replace('{{company_name}}', company_name)
            text_content = text_content.replace('{{job_position}}', primary_job_position)

            # 件名作成（主要職種を使用）
            subject = f"【{primary_job_position}の人材採用を強化しませんか？】株式会社HUGANからのご提案"

            # メール作成
            msg = MIMEText(text_content, 'plain', 'utf-8')
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = formataddr(('竹下隼平【株式会社HUGAN】', 'contact@huganjob.jp'))
            msg['To'] = recipient_email
            msg['Reply-To'] = 'contact@huganjob.jp'
            msg['Date'] = formatdate(localtime=True)

            print(f"   📝 テキストメール作成完了")
            return msg

        except Exception as e:
            print(f"❌ メール作成エラー: {e}")
            return None
    
    def check_unsubscribe_status(self, recipient_email):
        """配信停止状況をチェック"""
        try:
            unsubscribe_file = 'data/huganjob_unsubscribe_log.csv'
            if not os.path.exists(unsubscribe_file):
                return False

            with open(unsubscribe_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 正しい列名を使用
                    if row.get('メールアドレス', '').lower() == recipient_email.lower():
                        print(f"   🚫 配信停止確認: {recipient_email} (企業: {row.get('企業名', 'N/A')})")
                        return True
            return False
        except Exception as e:
            print(f"   ⚠️ 配信停止チェックエラー: {e}")
            return False

    def check_bounce_status(self, recipient_email):
        """バウンス状況をチェック（CSVファイルベース）"""
        try:
            # 企業データベースからバウンス状況をチェック
            csv_file = 'data/new_input_test.csv'
            if not os.path.exists(csv_file):
                return False

            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                next(reader, None)  # ヘッダー行をスキップ

                for row in reader:
                    if len(row) >= 8:  # バウンス状態列まで存在する場合
                        csv_email = row[3].strip() if row[3].strip() else None
                        bounce_status = row[5].strip() if len(row) > 5 and row[5].strip() else None

                        if csv_email and csv_email.lower() == recipient_email.lower():
                            return bounce_status == 'permanent'

            return False
        except Exception as e:
            print(f"   ⚠️ バウンスチェックエラー: {e}")
            return False

    def send_text_email_with_prevention(self, company_id, company_name, job_position, recipient_email):
        """重複防止機能付きテキストメール送信"""
        try:
            # 複数職種から主要職種を抽出（表示用）
            primary_job_position = self.extract_primary_job_position(job_position)

            print(f"\n📤 送信準備: {company_name}")
            print(f"   📧 宛先: {recipient_email}")
            print(f"   💼 職種: {job_position}")
            if job_position != primary_job_position:
                print(f"   🎯 メール用職種: {primary_job_position}")

            # 配信停止チェック（最優先）
            if self.check_unsubscribe_status(recipient_email):
                print(f"   🚫 配信停止済み: {recipient_email} - 送信をスキップします")
                self.record_sending_result(company_id, company_name, recipient_email, job_position, 'unsubscribed', '', '配信停止済み')
                return 'unsubscribed'

            # 重複送信チェック（無効化 - 配信停止以外は複数回送信許可）
            # if self.prevention_manager.check_recent_sending(company_id, hours=24):
            #     print(f"   ⚠️ 重複送信防止: {recipient_email} - 24時間以内に送信済み")
            #     self.record_sending_result(company_id, company_name, recipient_email, job_position, 'skipped', '', '重複送信防止')
            #     return 'skipped'
            print(f"   ✅ 重複送信チェック無効化: 複数回送信を許可")

            # バウンス履歴チェック（簡易版 - CSVファイルベース）
            if self.check_bounce_status(recipient_email):
                print(f"   ⚠️ バウンス履歴あり: {recipient_email} - 送信をスキップします")
                self.record_sending_result(company_id, company_name, recipient_email, job_position, 'bounced', '', 'バウンス履歴')
                return 'bounced'

            # メール作成
            msg = self.create_text_email(company_name, job_position, recipient_email)
            if not msg:
                self.record_sending_result(company_id, company_name, recipient_email, job_position, 'failed', '', 'メール作成失敗')
                return 'failed'

            # SMTP送信
            server = smtplib.SMTP('smtp.huganjob.jp', 587, timeout=30)
            server.starttls()
            server.login('contact@huganjob.jp', 'gD34bEmB')
            server.send_message(msg)
            server.quit()

            # 送信履歴記録
            self.prevention_manager.record_sending(company_id, company_name, recipient_email)

            # 送信結果記録
            self.record_sending_result(company_id, company_name, recipient_email, job_position, 'success', '', '')

            print(f"   ✅ テキストメール送信成功: {recipient_email}")
            return 'success'

        except Exception as e:
            print(f"❌ 送信エラー: {e}")
            self.record_sending_result(company_id, company_name, recipient_email, job_position, 'failed', '', str(e))
            return 'failed'

    def record_sending_result(self, company_id, company_name, recipient_email, job_position, result, tracking_id, error_message):
        """送信結果記録"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            subject = f"【{self.extract_primary_job_position(job_position)}の人材採用を強化しませんか？】株式会社HUGANからのご提案"
            
            result_data = {
                'company_id': company_id,
                'company_name': company_name,
                'recipient_email': recipient_email,
                'job_position': job_position,
                'timestamp': timestamp,
                'result': result,
                'tracking_id': tracking_id,
                'error_message': error_message,
                'subject': subject
            }
            
            self.sending_results.append(result_data)
            
        except Exception as e:
            print(f"❌ 送信結果記録エラー: {e}")

    def save_sending_results(self):
        """送信結果をCSVファイルに保存"""
        try:
            csv_file = 'huganjob_text_email_results.csv'
            file_exists = os.path.exists(csv_file)
            
            with open(csv_file, 'a', newline='', encoding='utf-8-sig') as f:
                fieldnames = ['企業ID', '企業名', 'メールアドレス', '募集職種', '送信日時', '送信結果', 'トラッキングID', 'エラーメッセージ', '件名']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                for result in self.sending_results:
                    writer.writerow({
                        '企業ID': result['company_id'],
                        '企業名': result['company_name'],
                        'メールアドレス': result['recipient_email'],
                        '募集職種': result['job_position'],
                        '送信日時': result['timestamp'],
                        '送信結果': result['result'],
                        'トラッキングID': result['tracking_id'],
                        'エラーメッセージ': result['error_message'],
                        '件名': result['subject']
                    })
            
            print(f"✅ 送信結果保存完了: {csv_file}")
            
        except Exception as e:
            print(f"❌ 送信結果保存エラー: {e}")

    def send_to_companies(self, companies):
        """企業リストに対してテキストメール送信実行"""
        print("📧 HUGAN JOB テキストメール専用送信システム")
        print("=" * 60)

        # タイムアウト設定（Windows対応）
        # signalの代わりに実行時間チェックを使用

        # 送信開始時刻記録
        self.start_time = datetime.now()
        print(f"⏰ 開始時刻: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 企業数制限チェック
        if len(companies) > MAX_COMPANIES_PER_BATCH:
            print(f"⚠️ 企業数が制限を超えています: {len(companies)} > {MAX_COMPANIES_PER_BATCH}")
            print(f"🔄 最初の{MAX_COMPANIES_PER_BATCH}社のみ処理します")
            companies = companies[:MAX_COMPANIES_PER_BATCH]

        # ロック取得
        if not self.prevention_manager.acquire_lock():
            print("❌ 他のプロセスが送信中です。しばらく待ってから再実行してください。")
            return False

        try:
            # 設定とテンプレート読み込み
            if not self.load_config() or not self.load_text_template():
                return False

            print(f"\n📋 送信対象企業: {len(companies)}社")

            # 予想実行時間計算
            estimated_time = len(companies) * 5  # 5秒間隔
            print(f"⏱️ 予想実行時間: 約{estimated_time//60}分{estimated_time%60}秒")

            # 送信実行
            print(f"\n📤 テキストメール送信開始...")
            print("-" * 60)

            results = {'success': 0, 'failed': 0, 'skipped': 0, 'bounced': 0, 'unsubscribed': 0}

            for i, company in enumerate(companies):
                # 実行時間チェック（Windows対応）
                if check_timeout(self.start_time, MAX_EXECUTION_TIME - 60):  # 1分前に警告
                    print(f"⚠️ タイムアウト間近です。処理を中断します。")
                    break

                # 進捗表示（簡潔に）
                if i % 10 == 0 or i == len(companies) - 1:
                    progress = (i + 1) / len(companies) * 100
                    print(f"📤 進捗: [{i+1}/{len(companies)}] ({progress:.1f}%)")

                result = self.send_text_email_with_prevention(
                    company['id'], company['name'],
                    company['job_position'], company['email']
                )
                results[result] += 1

                # 送信間隔（最後以外）
                if i < len(companies) - 1:
                    time.sleep(5)

            # 結果表示
            print(f"\n" + "=" * 60)
            print("📊 テキストメール送信結果")
            print("=" * 60)
            print(f"✅ 成功: {results['success']}/{len(companies)}")
            print(f"⚠️ スキップ: {results['skipped']}/{len(companies)} (重複防止)")
            print(f"🚫 配信停止: {results['unsubscribed']}/{len(companies)}")
            print(f"📧 バウンス: {results['bounced']}/{len(companies)}")
            print(f"❌ 失敗: {results['failed']}/{len(companies)}")

            # 実行時間表示
            end_time = datetime.now()
            execution_time = end_time - self.start_time
            print(f"⏱️ 実際の実行時間: {execution_time}")

            # 送信結果保存（簡潔に）
            print(f"\n💾 送信結果保存中...")
            self.save_sending_results()
            print(f"✅ 送信結果保存完了")

            return True

        except Exception as e:
            print(f"❌ 送信処理エラー: {e}")
            return False

        finally:
            # ロック解放
            self.prevention_manager.release_lock()

def load_companies_from_csv(start_id=None, end_id=None):
    """CSVファイルから企業データを読み込み"""
    try:
        companies = []
        csv_file = 'data/new_input_test.csv'

        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader, None)  # ヘッダー行をスキップ

            for row in reader:
                if len(row) >= 5:
                    company_id = int(row[0])

                    # ID範囲フィルタ
                    if start_id and company_id < start_id:
                        continue
                    if end_id and company_id > end_id:
                        continue

                    company_name = row[1]
                    website = row[2]
                    csv_email = row[3].strip() if row[3].strip() else None
                    job_position = row[4]

                    # メールアドレス決定（CSV優先）
                    email_address = csv_email
                    if not email_address or email_address == '‐':
                        # CSVにメールアドレスがない場合は抽出結果を確認
                        email_address = get_extracted_email(company_id)
                    if not email_address:
                        # 抽出結果もない場合はドメインベース生成
                        email_address = generate_domain_email(website)

                    if email_address:
                        companies.append({
                            'id': company_id,
                            'name': company_name,
                            'email': email_address,
                            'job_position': job_position,
                            'website': website
                        })

        return companies

    except Exception as e:
        print(f"❌ 企業データ読み込みエラー: {e}")
        return []

def get_extracted_email(company_id):
    """抽出結果ファイルからメールアドレスを取得"""
    try:
        results_file = 'huganjob_email_resolution_results.csv'
        if not os.path.exists(results_file):
            return None

        with open(results_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if int(row.get('company_id', 0)) == company_id:
                    return row.get('final_email', '').strip()
        return None

    except Exception as e:
        print(f"   ⚠️ 抽出結果取得エラー: {e}")
        return None

def generate_domain_email(website):
    """ウェブサイトからドメインベースメールアドレス生成"""
    try:
        if not website:
            return None

        # URLからドメイン抽出
        domain = website.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]
        if domain:
            return f"info@{domain}"
        return None

    except Exception:
        return None

def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description='HUGAN JOB テキストメール専用送信システム')
    parser.add_argument('--start-id', type=int, help='送信開始企業ID')
    parser.add_argument('--end-id', type=int, help='送信終了企業ID')

    args = parser.parse_args()

    print(f"🚀 HUGANJOB テキストメール送信開始")
    print(f"📋 送信範囲: ID {args.start_id} - {args.end_id}")
    start_time = datetime.now()
    print(f"⏰ 開始時刻: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 企業データ読み込み
    companies = load_companies_from_csv(args.start_id, args.end_id)

    if not companies:
        print("❌ 送信対象企業が見つかりません")
        return

    print(f"✅ 送信対象企業: {len(companies)}社")

    # 送信実行
    sender = TextOnlyEmailSender()
    success = sender.send_to_companies(companies)

    # 実行時間表示
    end_time = datetime.now()
    execution_time = end_time - start_time
    print(f"\n⏰ 終了時刻: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️ 実行時間: {execution_time}")

    if success:
        print("✅ テキストメール送信処理が正常に完了しました")
    else:
        print("❌ テキストメール送信処理でエラーが発生しました")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 送信がキャンセルされました")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ システムエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
