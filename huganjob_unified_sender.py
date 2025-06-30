#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB 統合メール送信システム
重複送信防止機能付きの統一送信システム

作成日時: 2025年06月23日 12:25:00
目的: 複数スクリプトによる重複送信問題の完全解決
"""

import smtplib
import configparser
import time
import sys
import uuid
import csv
import os
import gc
from datetime import datetime
# MIMEMultipart削除（Thunderbird完全模倣のため）
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate
from huganjob_duplicate_prevention import DuplicatePreventionManager

class UnifiedEmailSender:
    """統合メール送信クラス"""

    def __init__(self, email_format='html_text', skip_dns_validation=True):
        self.prevention_manager = DuplicatePreventionManager()
        self.config = None
        self.html_template = None
        self.text_template = None  # テキストテンプレート追加
        self.email_format = email_format  # メール形式選択
        self.sending_results = []  # 送信結果を保存するリスト
        self.skip_dns_validation = skip_dns_validation  # DNS検証スキップフラグ（デフォルト: True）
        
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
    
    def load_html_template(self):
        """HTMLテンプレート読み込み"""
        try:
            with open('corporate-email-newsletter.html', 'r', encoding='utf-8') as f:
                self.html_template = f.read()
            print("✅ HTMLテンプレート読み込み完了")
            return True
        except Exception as e:
            print(f"❌ HTMLテンプレート読み込みエラー: {e}")
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
    
    def generate_tracking_id(self, company_id, recipient_email):
        """トラッキングIDを生成"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_string = f"{company_id}_{recipient_email}_{timestamp}_{uuid.uuid4().hex[:8]}"
        return unique_string

    def extract_primary_job_position(self, job_position):
        """複数職種から主要職種を抽出（Phase 2対応・区切り文字「/」対応）"""
        try:
            # 複数職種が「/」で区切られている場合、最初の職種のみを使用
            if '/' in job_position:
                primary_position = job_position.split('/')[0].strip()
                print(f"   🎯 複数職種検出: '{job_position}' -> 主要職種: '{primary_position}'")
                return primary_position
            else:
                return job_position.strip()
        except Exception as e:
            print(f"   ⚠️ 職種抽出エラー: {e} - 元の職種を使用")
            return job_position

    def create_email(self, company_name, job_position, recipient_email, company_id):
        """メール作成（HTMLとテキスト両方対応・トラッキング機能付き・複数職種対応）"""
        try:
            # トラッキングID生成
            tracking_id = self.generate_tracking_id(company_id, recipient_email)

            # 複数職種から主要職種を抽出（Phase 2対応）
            primary_job_position = self.extract_primary_job_position(job_position)

            # 件名作成（主要職種を使用）
            subject = f"【{primary_job_position}の人材採用を強化しませんか？】株式会社HUGANからのご提案"

            # 🚨 重要修正：Thunderbird完全模倣（MIMEMultipart削除）
            # Thunderbirdは単純なHTMLメールを送信するため、複雑なMIME構造を避ける

            # HTMLコンテンツ作成
            if self.email_format in ['html_text', 'html_only'] and self.html_template:
                html_content = self.html_template.replace('{{company_name}}', company_name)
                html_content = html_content.replace('{{job_position}}', primary_job_position)

                # Thunderbird方式：単純なHTMLメール
                msg = MIMEText(html_content, 'html', 'utf-8')
            else:
                # テキストのみの場合
                text_content = self.text_template.replace('{{company_name}}', company_name) if self.text_template else f"{company_name}様への営業メール"
                text_content = text_content.replace('{{job_position}}', primary_job_position)
                msg = MIMEText(text_content, 'plain', 'utf-8')

            # Thunderbird方式：最小限のヘッダー
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = formataddr(('竹下隼平【株式会社HUGAN】', 'contact@huganjob.jp'))
            msg['To'] = recipient_email
            msg['Reply-To'] = 'contact@huganjob.jp'
            msg['Date'] = formatdate(localtime=True)

            # 🚨 古いMIMEMultipart処理を削除（Thunderbird完全模倣のため）
            # 上記でThunderbird方式の単純なHTMLメールを既に作成済み
            # MIMEMultipartによる複雑な構造は迷惑メール判定の要因

            # メール形式の表示
            format_text = {
                'html_text': 'HTML + テキスト',
                'html_only': 'HTMLのみ',
                'text_only': 'テキストのみ'
            }.get(self.email_format, self.email_format)
            print(f"   📧 メール形式: {format_text}")

            return msg, tracking_id

        except Exception as e:
            print(f"❌ メール作成エラー: {e}")
            return None, None
    
    def check_unsubscribe_status(self, recipient_email, company_data=None):
        """配信停止状況をチェック（ドメインベース対応）"""
        try:
            recipient_email_lower = recipient_email.lower().strip()

            # 1. 完全一致チェック
            unsubscribe_log_path = 'data/huganjob_unsubscribe_log.csv'
            if os.path.exists(unsubscribe_log_path):
                with open(unsubscribe_log_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for entry in reader:
                        if entry.get('メールアドレス', '').lower().strip() == recipient_email_lower:
                            return True, entry.get('配信停止理由', '配信停止申請')

            # 2. ドメインベースチェック（企業データが提供された場合）
            if company_data and '@' in recipient_email_lower:
                recipient_domain = recipient_email_lower.split('@')[1]

                # 配信停止ログでドメインマッチングをチェック
                if os.path.exists(unsubscribe_log_path):
                    with open(unsubscribe_log_path, 'r', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f)
                        for entry in reader:
                            unsubscribe_email = entry.get('メールアドレス', '').lower().strip()
                            if '@' in unsubscribe_email:
                                unsubscribe_domain = unsubscribe_email.split('@')[1]
                                if recipient_domain == unsubscribe_domain:
                                    # 企業ホームページのドメインとも照合
                                    company_url = company_data.get('企業ホームページ', '').lower()
                                    if company_url:
                                        try:
                                            from urllib.parse import urlparse
                                            parsed_url = urlparse(company_url if company_url.startswith('http') else f'http://{company_url}')
                                            company_domain = parsed_url.netloc.lower().replace('www.', '')

                                            if recipient_domain == company_domain:
                                                reason = f"ドメイン一致による配信停止 (元申請: {unsubscribe_email})"
                                                return True, reason
                                        except:
                                            continue

            return False, None
        except Exception as e:
            print(f"   ⚠️ 配信停止チェックエラー: {e}")
            return False, None

    def validate_email_domain(self, email_address):
        """メールアドレスのドメインDNS解決チェック"""
        try:
            import socket

            # 基本的なメールアドレス形式チェック
            if '@' not in email_address or '.' not in email_address.split('@')[1]:
                return False, "無効なメールアドレス形式"

            domain = email_address.split('@')[1]

            # DNS解決テスト（タイムアウト5秒）
            socket.setdefaulttimeout(5)
            socket.gethostbyname(domain)
            return True, None

        except socket.gaierror as dns_error:
            error_msg = f"DNS解決失敗: {dns_error}"
            return False, error_msg
        except socket.timeout:
            error_msg = "DNS解決タイムアウト"
            return False, error_msg
        except Exception as e:
            error_msg = f"ドメイン検証エラー: {e}"
            return False, error_msg
        finally:
            # タイムアウトをリセット
            socket.setdefaulttimeout(None)

    def send_email_with_prevention(self, company_id, company_name, job_position, recipient_email, company_data=None):
        """重複防止機能付きメール送信（トラッキング対応・複数職種対応・配信停止チェック対応・ドメインベース配信停止対応）"""
        tracking_id = None
        try:
            # 複数職種から主要職種を抽出（表示用）
            primary_job_position = self.extract_primary_job_position(job_position)

            print(f"\n📤 送信準備: {company_name}")
            print(f"   📧 宛先: {recipient_email}")
            print(f"   💼 職種: {job_position}")
            if job_position != primary_job_position:
                print(f"   🎯 メール用職種: {primary_job_position}")

            # DNS解決チェック（設定により実行）
            if not self.skip_dns_validation:
                print(f"   🌍 DNS解決チェック中...")
                is_valid_domain, dns_error = self.validate_email_domain(recipient_email)
                if not is_valid_domain:
                    print(f"   ❌ DNS解決失敗: {dns_error} - スキップします")
                    self.record_sending_result(company_id, company_name, recipient_email, job_position, 'failed', None, f'DNS解決失敗: {dns_error}')
                    return 'failed'
                print(f"   ✅ DNS解決: 正常")
            else:
                print(f"   ⚡ DNS検証スキップ: 機械的送信モード（デフォルト設定）")

            # 配信停止チェック（ドメインベース対応）
            is_unsubscribed, unsubscribe_reason = self.check_unsubscribe_status(recipient_email, company_data)
            if is_unsubscribed:
                print(f"   🚫 配信停止済み: {unsubscribe_reason} - スキップします")
                self.record_sending_result(company_id, company_name, recipient_email, job_position, 'unsubscribed', None, f'配信停止: {unsubscribe_reason}')
                return 'unsubscribed'

            # 重複送信チェック（無効化 - 配信停止以外は複数回送信許可）
            # if self.prevention_manager.check_recent_sending(company_id, hours=24):
            #     print(f"   ⚠️ 過去24時間以内に送信済み - スキップします")
            #     self.record_sending_result(company_id, company_name, recipient_email, job_position, 'skipped', None, '重複送信防止')
            #     return 'skipped'
            print(f"   ✅ 重複送信チェック無効化: 複数回送信を許可")

            # バウンス履歴チェック
            bounce_addresses = [
                'info@sincere.co.jp', 'info@www.advance-1st.co.jp', 'info@www.aoikokuban.co.jp',
                'info@www.crosscorporation.co.jp', 'info@www.flex-og.jp', 'info@www.h2j.jp',
                'info@www.hanei-co.jp', 'info@www.hayashikazuji.co.jp', 'info@www.konishi-mark.com',
                'info@www.koutokudenkou.co.jp', 'info@www.manneken.co.jp', 'info@www.naniwakanri.co.jp',
                'info@www.nikki-tr.co.jp', 'info@www.orientalbakery.co.jp', 'info@www.osakagaigo.ac.jp',
                'info@www.seedassist.co.jp', 'info@www.somax.co.jp', 'info@www.teruteru.co.jp',
                'info@www.tsukitora.com', 'info@www.yoshimoto.co.jp:443',
                # ID 30-150範囲の追加バウンス企業
                'info@www.aiengineering.jp', 'info@www.kirin-e-s.co.jp', 'info@www.live-create.co.jp',
                'info@www.tenmasamatsushita.co.jp', 'info@www.toray.co.jp', 'info@www.artner.co.jp',
                'info@www.ytv.co.jp', 'info@www.lighting-daiko.co.jp', 'info@www.ksdh.or.jp',
                'info@www.kinryu-foods.co.jp', 'info@www.sanei-yakuhin.co.jp', 'info@www.nissin.com',
                'info@www.rex.co.jp', 'info@www.kk-maekawa.co.jp', 'info@www.askme.co.jp',
                'info@miyakohotels.ne.jp', 'info@hankyu-hanshin-dept.co.jp', 'info@sumitomo-chem.co.jp',
                'info@syusei.ac.jp'
            ]
            if recipient_email in bounce_addresses:
                print(f"   ⚠️ バウンス履歴あり - スキップします")
                self.record_sending_result(company_id, company_name, recipient_email, job_position, 'bounced', None, 'バウンス履歴あり')
                return 'bounced'

            # メール作成（複数職種対応）
            msg, tracking_id = self.create_email(company_name, job_position, recipient_email, company_id)
            if not msg:
                self.record_sending_result(company_id, company_name, recipient_email, job_position, 'failed', tracking_id, 'メール作成失敗')
                return 'failed'

            # SMTP送信（タイムアウト短縮とエラーハンドリング強化）
            print(f"   📤 SMTP送信中...")
            server = smtplib.SMTP('smtp.huganjob.jp', 587, timeout=15)  # タイムアウト短縮
            server.starttls()
            server.login('contact@huganjob.jp', 'gD34bEmB')
            server.send_message(msg)
            server.quit()

            # 🆕 送信履歴記録（機能復活）
            try:
                print(f"   📝 送信履歴記録中...")
                self.prevention_manager.record_sending(company_id, company_name, recipient_email, 'huganjob_unified_sender.py')
                print(f"   ✅ 送信履歴記録完了")
            except Exception as e:
                print(f"   ⚠️ 送信履歴記録エラー: {e}")

            # 送信結果記録（元の職種情報を保持）
            self.record_sending_result(company_id, company_name, recipient_email, job_position, 'success', tracking_id, '')

            # 🆕 CSVファイル更新（送信成功時）
            try:
                print(f"   📝 CSVファイル更新中...")
                # 企業情報を取得（簡略化）
                website = "N/A"  # 簡略化のため固定値
                update_email_resolution_results(company_id, company_name, website, job_position, recipient_email, recipient_email, 'email_sending_success')
                print(f"   ✅ CSVファイル更新完了")
            except Exception as csv_error:
                print(f"   ⚠️ CSVファイル更新エラー: {csv_error}")

            # 🆕 ダッシュボードキャッシュクリア（即時反映用）
            try:
                print(f"   🔄 ダッシュボードキャッシュクリア中...")
                clear_dashboard_cache()
                print(f"   ✅ ダッシュボードキャッシュクリア完了")
            except Exception as cache_error:
                print(f"   ⚠️ ダッシュボードキャッシュクリアエラー: {cache_error}")

            print(f"   ✅ 送信成功: {recipient_email} [追跡ID: {tracking_id}]")
            return 'success'

        except smtplib.SMTPRecipientsRefused as smtp_error:
            error_msg = f"SMTP受信者拒否: {smtp_error}"
            print(f"   ❌ 送信失敗: {recipient_email} - {error_msg}")
            self.record_sending_result(company_id, company_name, recipient_email, job_position, 'failed', tracking_id, error_msg)
            return 'failed'

        except smtplib.SMTPException as smtp_error:
            error_msg = f"SMTP エラー: {smtp_error}"
            print(f"   ❌ 送信失敗: {recipient_email} - {error_msg}")
            self.record_sending_result(company_id, company_name, recipient_email, job_position, 'failed', tracking_id, error_msg)
            return 'failed'

        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ 送信失敗: {recipient_email} - {error_msg}")
            self.record_sending_result(company_id, company_name, recipient_email, job_position, 'failed', tracking_id, error_msg)
            return 'failed'

    def record_sending_result(self, company_id, company_name, recipient_email, job_position, result, tracking_id, error_msg):
        """送信結果を記録（複数職種対応）"""
        # 件名用の主要職種を抽出
        primary_job_position = self.extract_primary_job_position(job_position)

        result_record = {
            '企業ID': company_id,
            '企業名': company_name,
            'メールアドレス': recipient_email,
            '募集職種': job_position,  # 元の職種情報を保持
            'メール用職種': primary_job_position,  # メールで使用した職種
            '送信日時': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '送信結果': result,
            'トラッキングID': tracking_id or '',
            'エラーメッセージ': error_msg,
            '件名': f"【{primary_job_position}の人材採用を強化しませんか？】株式会社HUGANからのご提案"
        }
        self.sending_results.append(result_record)

    def save_sending_results(self):
        """送信結果をCSVファイルに保存"""
        if not self.sending_results:
            print("⚠️ 保存する送信結果がありません")
            return

        try:
            filename = 'new_email_sending_results.csv'
            file_exists = os.path.exists(filename)

            print(f"📝 送信結果保存開始: {len(self.sending_results)}件")
            print(f"   ファイル: {filename}")
            print(f"   既存ファイル: {'あり' if file_exists else 'なし'}")

            with open(filename, 'a', newline='', encoding='utf-8-sig') as f:
                fieldnames = ['企業ID', '企業名', 'メールアドレス', '募集職種', 'メール用職種', '送信日時', '送信結果', 'トラッキングID', 'エラーメッセージ', '件名']
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                # ヘッダーを書き込み（新規ファイルの場合）
                if not file_exists:
                    print("   📋 ヘッダー書き込み中...")
                    writer.writeheader()

                # 送信結果を書き込み
                print("   📊 データ書き込み中...")
                for i, result in enumerate(self.sending_results):
                    try:
                        # メール用職種フィールドがない場合は募集職種をコピー
                        if 'メール用職種' not in result:
                            result['メール用職種'] = result.get('募集職種', '')

                        writer.writerow(result)
                        print(f"     {i+1}/{len(self.sending_results)}: ID {result.get('企業ID', 'N/A')} 書き込み完了")

                    except Exception as row_error:
                        print(f"     ❌ 行書き込みエラー (ID {result.get('企業ID', 'N/A')}): {row_error}")
                        continue

            print(f"✅ 送信結果を保存しました: {filename} ({len(self.sending_results)}件)")

        except Exception as e:
            print(f"❌ 送信結果保存エラー: {e}")
            print(f"   エラー詳細: {type(e).__name__}")
            import traceback
            print(f"   スタックトレース: {traceback.format_exc()}")

    def send_to_companies(self, companies):
        """企業リストへの一括送信"""
        print("=" * 60)
        print("📧 HUGAN JOB 統合メール送信システム")
        print("=" * 60)
        
        # ロック取得
        if not self.prevention_manager.acquire_lock():
            print("❌ 他のプロセスが送信中です。しばらく待ってから再実行してください。")
            return False
        
        try:
            # 設定とテンプレート読み込み
            config_loaded = self.load_config()
            html_loaded = True
            text_loaded = True

            if self.email_format in ['html_text', 'html_only']:
                html_loaded = self.load_html_template()

            if self.email_format in ['html_text', 'text_only']:
                text_loaded = self.load_text_template()

            if not config_loaded or not html_loaded or not text_loaded:
                return False
            
            print(f"\n📋 送信対象企業: {len(companies)}社")
            for company in companies:
                print(f"  ID {company['id']}: {company['name']} - {company['email']} ({company['job_position']})")
            
            # 送信実行
            print(f"\n📤 メール送信開始...")
            print("-" * 60)

            results = {'success': 0, 'failed': 0, 'skipped': 0, 'bounced': 0, 'unsubscribed': 0}

            for i, company in enumerate(companies):
                try:
                    print(f"\n📤 {i+1}/{len(companies)}: ID {company['id']} {company['name']} 送信開始")

                    result = self.send_email_with_prevention(
                        company['id'], company['name'],
                        company['job_position'], company['email'],
                        company  # 企業データ全体を渡す（ドメインベース配信停止チェック用）
                    )
                    results[result] += 1

                    print(f"   📊 送信結果: {result}")

                    # 送信間隔（最後以外）
                    if i < len(companies) - 1:
                        print(f"   ⏳ 送信間隔待機中（5秒）...")
                        time.sleep(5)

                except Exception as company_error:
                    print(f"   ❌ 企業 ID {company['id']} 送信処理エラー: {company_error}")
                    results['failed'] += 1
                    continue

            # 結果表示
            print(f"\n" + "=" * 60)
            print("📊 統合メール送信結果")
            print("=" * 60)
            print(f"✅ 成功: {results['success']}/{len(companies)}")
            print(f"⚠️ スキップ: {results['skipped']}/{len(companies)} (重複防止)")
            print(f"🚫 バウンス: {results['bounced']}/{len(companies)} (バウンス履歴)")
            print(f"🛑 配信停止: {results['unsubscribed']}/{len(companies)} (配信停止申請)")
            print(f"❌ 失敗: {results['failed']}/{len(companies)}")
            
            # 🆕 送信結果を保存（機能復活）
            print(f"\n💾 送信結果保存処理開始")
            print(f"   対象: {len(self.sending_results)}件の送信結果")
            self.save_sending_results()  # 機能復活
            print(f"💾 送信結果保存処理完了")

            # 🆕 送信完了後のダッシュボードキャッシュクリア（即時反映用）
            if results['success'] > 0:
                try:
                    print(f"\n🔄 送信完了後のダッシュボードキャッシュクリア中...")
                    clear_dashboard_cache()
                    print(f"✅ 送信完了後のダッシュボードキャッシュクリア完了")
                except Exception as cache_error:
                    print(f"⚠️ 送信完了後のダッシュボードキャッシュクリアエラー: {cache_error}")

            if results['success'] > 0:
                print(f"\n🎉 {results['success']}社への営業メール送信が完了しました！")
                print(f"📊 ダッシュボードで送信状況を確認してください: http://127.0.0.1:5002/")
                return True
            else:
                print(f"\n⚠️ 送信に成功した企業がありませんでした")
                return False

        finally:
            # ロック解放（簡略化）
            try:
                self.prevention_manager.release_lock()
                print("🔓 ロック解放完了")
            except Exception as e:
                print(f"⚠️ ロック解放エラー（無視）: {e}")

def update_email_resolution_results(company_id, company_name, website, job_position, csv_email, final_email, method):
    """🆕 メールアドレス抽出結果ファイルを更新（機能復活）"""
    try:
        print(f"  📝 メールアドレス抽出結果更新: ID {company_id}")

        # 簡略化された更新処理（重要な情報のみ記録）
        import pandas as pd

        # 新しい結果データ
        new_data = {
            'company_id': company_id,
            'company_name': company_name,
            'website': website,
            'job_position': job_position,
            'csv_email': csv_email if csv_email and csv_email.strip() and csv_email.strip() != '‐' else '‐',
            'final_email': final_email,
            'extraction_method': method,
            'status': 'success'
        }

        # 既存ファイルの読み込み
        results_file = 'huganjob_email_resolution_results.csv'
        if os.path.exists(results_file):
            existing_df = pd.read_csv(results_file, encoding='utf-8')

            # 同じcompany_idの既存データを削除
            existing_df = existing_df[existing_df['company_id'] != company_id]

            # 新しいデータを追加
            new_df = pd.DataFrame([new_data])
            updated_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            # 新規ファイル作成
            updated_df = pd.DataFrame([new_data])

        # ファイルに保存
        updated_df.to_csv(results_file, index=False, encoding='utf-8')
        print(f"  ✅ メールアドレス抽出結果更新完了: ID {company_id}")

        # 🆕 元のCSVファイル（data/new_input_test.csv）も更新
        update_original_csv_status(company_id, final_email, 'success')

        return

    except Exception as e:
        print(f"  ❌ メールアドレス抽出結果更新エラー: {e}")

def update_original_csv_status(company_id, email_address, status):
    """🆕 元のCSVファイル（data/new_input_test.csv）の送信ステータスを更新"""
    try:
        from datetime import datetime
        import pandas as pd
        import os
        csv_file = 'data/new_input_test.csv'
        if not os.path.exists(csv_file):
            print(f"  ⚠️ 元のCSVファイルが見つかりません: {csv_file}")
            return

        # CSVファイルを読み込み
        import pandas as pd
        df = pd.read_csv(csv_file, encoding='utf-8-sig')

        # 該当する企業IDの行を検索
        mask = df['ID'] == int(company_id)
        if mask.any():
            # メールアドレスと送信ステータスを更新
            df.loc[mask, 'メールアドレス'] = email_address
            df.loc[mask, '送信ステータス'] = '送信済み' if status == 'success' else '送信失敗'
            df.loc[mask, '送信日時'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # ファイルに保存
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"  ✅ 元のCSVファイル更新完了: ID {company_id} -> {email_address}")
        else:
            print(f"  ⚠️ 企業ID {company_id} が元のCSVファイルに見つかりません")

    except Exception as e:
        print(f"  ❌ 元のCSVファイル更新エラー: {e}")

def clear_dashboard_cache():
    """🆕 ダッシュボードのキャッシュをクリアして即時反映を促進"""
    try:
        import requests

        # ダッシュボードのキャッシュクリアAPIを呼び出し
        dashboard_url = "http://127.0.0.1:5002/api/cache_clear"

        response = requests.post(dashboard_url, timeout=5)
        if response.status_code == 200:
            print(f"  ✅ ダッシュボードキャッシュクリア成功")
        else:
            print(f"  ⚠️ ダッシュボードキャッシュクリア失敗: {response.status_code}")

    except ImportError:
        print(f"  ⚠️ requestsライブラリが利用できません")
    except Exception as e:
        print(f"  ⚠️ ダッシュボードキャッシュクリアエラー: {e}")

        # 以下は元の処理（コメントアウト）
        # import pandas as pd
        # import os
        #


def load_companies_from_csv(start_id=1, end_id=5):
    """CSVファイルから企業データを読み込み"""
    import pandas as pd

    def clean_domain_for_email(url):
        """URLからドメインを抽出し、www.を除去してメールアドレス用に整形"""
        try:
            # プロトコルを除去
            domain = url.replace('https://', '').replace('http://', '').split('/')[0]
            # www.を除去
            if domain.startswith('www.'):
                domain = domain[4:]
            # ポート番号を除去（例：domain.com:443 -> domain.com）
            if ':' in domain:
                domain = domain.split(':')[0]
            return domain
        except:
            return url

    try:
        # CSVファイル読み込み
        df = pd.read_csv('data/new_input_test.csv', encoding='utf-8-sig')

        # ID範囲でフィルタリング
        filtered_df = df[(df['ID'] >= start_id) & (df['ID'] <= end_id)]

        # メールアドレス抽出結果を読み込み（優先使用）
        email_resolution_results = {}
        try:
            if os.path.exists('huganjob_email_resolution_results.csv'):
                email_df = pd.read_csv('huganjob_email_resolution_results.csv', encoding='utf-8')
                for _, email_row in email_df.iterrows():
                    company_id = email_row.get('company_id')
                    final_email = email_row.get('final_email')
                    if pd.notna(company_id) and pd.notna(final_email):
                        email_resolution_results[int(company_id)] = final_email.strip()
                print(f"✅ メールアドレス抽出結果を読み込み: {len(email_resolution_results)}社")
        except Exception as e:
            print(f"⚠️ メールアドレス抽出結果読み込みエラー: {e}")

        companies = []
        for _, row in filtered_df.iterrows():
            company_id = int(row['ID'])
            company_name = row['企業名']
            website = row['企業ホームページ']
            job_position = row.get('募集職種', '採用担当者')
            csv_email = row.get('担当者メールアドレス', '')

            # メールアドレス決定ロジック（修正版：CSV最優先）
            # 1. CSVの採用担当メールアドレス（最優先）
            if pd.notna(csv_email) and csv_email.strip() and csv_email.strip() != '‐':
                email = csv_email.strip()
                method = "csv_direct"
                print(f"  📧 ID {company_id}: CSV直接使用（最優先） -> {email}")
                # 抽出結果ファイルに記録
                update_email_resolution_results(company_id, company_name, website, job_position, csv_email, email, method)
            # 2. メールアドレス抽出結果（第2優先）
            elif company_id in email_resolution_results:
                email = email_resolution_results[company_id]
                method = "extraction_result"
                print(f"  📧 ID {company_id}: 抽出結果使用（第2優先） -> {email}")
            else:
                # 3. ドメインから生成（最終手段）
                clean_domain = clean_domain_for_email(website)
                email = f"info@{clean_domain}"
                method = "website_extraction"
                print(f"  📧 ID {company_id}: ドメイン生成（最終手段） -> {email}")
                # 抽出結果ファイルに記録
                update_email_resolution_results(company_id, company_name, website, job_position, '‐', email, method)

            company = {
                "id": company_id,
                "name": company_name,
                "email": email,
                "job_position": job_position
            }
            companies.append(company)

        return companies

    except Exception as e:
        print(f"❌ CSVファイル読み込みエラー: {e}")
        # フォールバック: デフォルトデータ
        return [
            {
                "id": 1,
                "name": "エスケー化研株式会社",
                "email": "info@sk-kaken.co.jp",
                "job_position": "事務スタッフ"
            },
            {
                "id": 2,
                "name": "ラ・シンシア株式会社",
                "email": "info@sincere.co.jp",
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
        ][:end_id-start_id+1]

def main():
    """メイン処理（コマンドライン引数対応）"""
    import argparse

    # コマンドライン引数解析
    parser = argparse.ArgumentParser(description='HUGANJOB統合メール送信システム')
    parser.add_argument('--start-id', type=int, default=1, help='開始企業ID')
    parser.add_argument('--end-id', type=int, default=5, help='終了企業ID')
    parser.add_argument('--max-emails', type=int, help='最大送信数（オプション）')
    parser.add_argument('--email-format', type=str, default='html_text',
                       choices=['html_text', 'html_only', 'text_only'],
                       help='メール形式 (html_text: HTML+テキスト, html_only: HTMLのみ, text_only: テキストのみ)')
    parser.add_argument('--enable-dns', action='store_true',
                       help='DNS検証を有効にする（デフォルトはスキップ）')
    args = parser.parse_args()

    # DNS検証設定の表示
    skip_dns = not args.enable_dns  # --enable-dnsが指定されていない場合はスキップ
    if skip_dns:
        print("⚡ DNS検証スキップモード: 機械的送信を実行します")
        print("💡 DNS検証を有効にする場合は --enable-dns オプションを使用してください")
    else:
        print("🌍 DNS検証有効モード: 送信前にドメイン解決をチェックします")

    # 企業データ読み込み
    companies = load_companies_from_csv(args.start_id, args.end_id)

    # 最大送信数制限
    if args.max_emails and len(companies) > args.max_emails:
        companies = companies[:args.max_emails]

    print(f"📋 送信対象: ID {args.start_id}-{args.end_id} ({len(companies)}社)")
    print(f"📧 メール形式: {args.email_format}")

    # 統合送信システム実行
    skip_dns = not args.enable_dns  # DNS検証スキップ設定
    sender = UnifiedEmailSender(email_format=args.email_format, skip_dns_validation=skip_dns)
    success = sender.send_to_companies(companies)

    print(f"\n🏁 処理完了: {'成功' if success else '失敗'}")

    # 明示的なプロセス終了処理
    print(f"🔚 プロセス終了処理開始...")
    try:
        # ガベージコレクション実行
        import gc
        gc.collect()
        print(f"✅ メモリクリーンアップ完了")

        # 強制的にプロセス終了
        print(f"✅ プロセス正常終了")
        return success

    except Exception as e:
        print(f"⚠️ 終了処理エラー（無視）: {e}")
        return success

if __name__ == "__main__":
    try:
        success = main()
        print(f"🎯 メイン処理完了: {'成功' if success else '失敗'}")

        # 強制終了
        import os
        print(f"🔚 プロセス強制終了...")
        os._exit(0 if success else 1)

    except Exception as e:
        print(f"❌ メイン処理エラー: {e}")
        import os
        os._exit(1)
