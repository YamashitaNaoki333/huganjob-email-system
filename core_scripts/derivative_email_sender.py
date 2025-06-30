#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
新しいダッシュボード専用メール送信スクリプト
- 新しいファイル命名規則を使用: new_email_sending_results.csv
- new_input_utf8.csv を入力ファイルとして使用
- 過去のダッシュボードとの干渉を回避
"""

import csv
import sys
import os
import logging
import argparse
import smtplib
import time
import uuid
import base64
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import configparser
from csv_utils import safe_csv_save, get_company_id_sort_key

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("new_email_sending.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('new_email_sender')

# 新しいダッシュボード用の設定
INPUT_FILE = 'new_input_utf8.csv'
EMAIL_EXTRACTION_PREFIX = 'new_email_extraction_results'
WEBSITE_ANALYSIS_PREFIX = 'derivative_website_analysis_results'
EMAIL_SENDING_RESULTS = 'data/derivative_email_sending_results.csv'
EMAIL_TRACKING_RESULTS = 'data/derivative_email_tracking_results.csv'  # トラッキング情報保存用
EMAIL_CONFIG_FILE = 'config/derivative_email_config.ini'

# 派生版ダッシュボードのベースURL（開封追跡用）
DASHBOARD_BASE_URL = 'http://127.0.0.1:5002'

class EmailSender:
    """メール送信クラス"""

    def __init__(self, config_file=EMAIL_CONFIG_FILE):
        self.config = configparser.ConfigParser()
        self.config.read(config_file, encoding='utf-8')

        # SMTP設定を読み込み
        self.smtp_server = self.config.get('SMTP', 'server', fallback='smtp.gmail.com')
        self.smtp_port = self.config.getint('SMTP', 'port', fallback=587)
        self.smtp_user = self.config.get('SMTP', 'user', fallback='')
        self.smtp_password = self.config.get('SMTP', 'password', fallback='')
        self.sender_name = self.config.get('SMTP', 'sender_name', fallback='山下直輝')

        logger.info(f"メール送信設定を読み込みました: {self.smtp_server}:{self.smtp_port}")

    def send_email(self, to_email, subject, html_content, company_name, rank, company_id=None):
        """HTMLメールを送信（開封追跡機能付き）"""
        try:
            # トラッキングIDを生成
            tracking_id = self.generate_tracking_id(company_id or '0', to_email)

            # HTMLコンテンツにトラッキングピクセルを追加
            html_with_tracking = self.add_tracking_pixel(html_content, tracking_id)

            # メッセージを作成
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.sender_name} <{self.smtp_user}>"
            msg['To'] = to_email
            msg['Subject'] = Header(subject, 'utf-8')

            # HTMLパートを追加
            html_part = MIMEText(html_with_tracking, 'html', 'utf-8')
            msg.attach(html_part)

            # SMTP接続してメール送信（タイムアウトとリトライ機能付き）
            max_retries = 5
            retry_delay = 10
            timeout_seconds = 60  # タイムアウトを延長

            for attempt in range(max_retries):
                try:
                    logger.info(f"SMTP接続試行 {attempt + 1}/{max_retries}: {self.smtp_server}:{self.smtp_port}")
                    with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=timeout_seconds) as server:
                        logger.info("STARTTLS開始...")
                        server.starttls()
                        logger.info("ログイン中...")
                        server.login(self.smtp_user, self.smtp_password)
                        logger.info("メール送信中...")
                        server.send_message(msg)
                        logger.info("メール送信完了")
                    break  # 成功した場合はループを抜ける
                except (smtplib.SMTPException, TimeoutError, OSError) as smtp_error:
                    if attempt < max_retries - 1:
                        logger.warning(f"SMTP接続失敗 (試行 {attempt + 1}/{max_retries}): {smtp_error}")
                        logger.info(f"{retry_delay}秒後に再試行します...")
                        time.sleep(retry_delay)
                        retry_delay += 5  # 再試行のたびに待機時間を延長
                    else:
                        logger.error(f"全ての再試行が失敗しました: {smtp_error}")
                        raise smtp_error  # 最後の試行で失敗した場合は例外を再発生

            # トラッキング情報を保存
            self.save_tracking_info(tracking_id, company_id or '0', company_name, to_email, rank)

            logger.info(f"メール送信成功: {company_name} ({rank}ランク) -> {to_email} [追跡ID: {tracking_id}]")
            return True, tracking_id

        except Exception as e:
            logger.error(f"メール送信失敗: {company_name} -> {to_email}: {e}")
            return False, None

    def generate_tracking_id(self, company_id, email_address):
        """トラッキングIDを生成"""
        # 企業IDとメールアドレスとタイムスタンプを組み合わせてユニークなIDを生成
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_string = f"{company_id}_{email_address}_{timestamp}_{uuid.uuid4().hex[:8]}"

        # Base64エンコードして短縮
        tracking_id = base64.urlsafe_b64encode(unique_string.encode()).decode().rstrip('=')

        return tracking_id

    def add_tracking_pixel(self, html_content, tracking_id):
        """HTMLコンテンツに多重追跡機能を追加（改善版）"""
        # 1. 基本のトラッキングピクセル
        tracking_pixel = f'<img src="{DASHBOARD_BASE_URL}/track-open/{tracking_id}" width="1" height="1" style="display:none;" alt="">'

        # 2. JavaScript追跡（フォールバック）
        js_tracking = f'''
        <script type="text/javascript">
        (function() {{
            try {{
                // 画像追跡（メイン）
                var img = new Image();
                img.src = '{DASHBOARD_BASE_URL}/track-open/{tracking_id}?method=js';

                // フォールバック追跡（1秒後）
                setTimeout(function() {{
                    try {{
                        fetch('{DASHBOARD_BASE_URL}/track-open/{tracking_id}?method=fetch', {{
                            method: 'GET',
                            mode: 'no-cors'
                        }}).catch(function() {{
                            // 最後の手段: ビーコンAPI
                            if (navigator.sendBeacon) {{
                                navigator.sendBeacon('{DASHBOARD_BASE_URL}/track-beacon/{tracking_id}');
                            }}
                        }});
                    }} catch(e) {{
                        // JavaScript無効環境でのフォールバック
                        var fallbackImg = new Image();
                        fallbackImg.src = '{DASHBOARD_BASE_URL}/track-open/{tracking_id}?method=fallback';
                    }}
                }}, 1000);
            }} catch(e) {{
                // エラー時のフォールバック
                console.log('Tracking error:', e);
            }}
        }})();
        </script>
        '''

        # 3. CSS追跡（background-image）
        css_tracking = f'''
        <style type="text/css">
        .email-tracking {{
            background-image: url('{DASHBOARD_BASE_URL}/track-open/{tracking_id}?method=css');
            background-repeat: no-repeat;
            background-position: -9999px -9999px;
            width: 1px;
            height: 1px;
            display: block;
        }}
        </style>
        <div class="email-tracking"></div>
        '''

        # 追跡要素を組み合わせ
        all_tracking = tracking_pixel + css_tracking + js_tracking

        # {{tracking_pixel}}プレースホルダーがある場合はそれを置換
        if '{{tracking_pixel}}' in html_content:
            html_content = html_content.replace('{{tracking_pixel}}', all_tracking)
        # </body>タグの直前に追跡要素を挿入
        elif '</body>' in html_content:
            html_content = html_content.replace('</body>', f'{all_tracking}</body>')
        else:
            # </body>タグがない場合は最後に追加
            html_content += all_tracking

        return html_content

    def save_tracking_info(self, tracking_id, company_id, company_name, email_address, rank):
        """トラッキング情報を保存"""
        try:
            # ファイルが存在しない場合はヘッダーを作成
            file_exists = os.path.exists(EMAIL_TRACKING_RESULTS)

            with open(EMAIL_TRACKING_RESULTS, 'a', newline='', encoding='utf-8-sig') as f:
                fieldnames = [
                    'tracking_id', 'company_id', 'company_name', 'email_address',
                    'rank', 'sent_at', 'opened', 'opened_at'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                # ヘッダーを書き込み（新規ファイルの場合）
                if not file_exists:
                    writer.writeheader()

                # トラッキング情報を書き込み
                writer.writerow({
                    'tracking_id': tracking_id,
                    'company_id': company_id,
                    'company_name': company_name,
                    'email_address': email_address,
                    'rank': rank,
                    'sent_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'opened': 'No',
                    'opened_at': ''
                })

        except Exception as e:
            logger.error(f"トラッキング情報の保存エラー: {e}")

    def get_subject_by_rank(self, rank, company_name):
        """ランク別の件名を取得（旧システムと同じ形式）"""
        if rank == 'A':
            return f"【無料相談】30分で{company_name}様サイトの成果を2倍に！専門家が最新トレンドをご紹介"
        elif rank == 'B':
            return f"【無料診断】3つの改善ポイントで{company_name}様サイトの成果が劇的に向上します！"
        else:  # rank == 'C'
            return f"【業界最安値】1万円～でプロ品質のウェブサイトが手に入る！初期費用も格安"

    def get_html_content_by_rank(self, company_name, rank, score):
        """ランク別のHTMLメール内容を取得（旧システムのテンプレートファイルを使用）"""
        # テンプレートファイルのマッピング
        template_files = {
            'A': 'email-a.txt',
            'B': 'email-b.txt',
            'C': 'email-c.txt'
        }

        template_file = template_files.get(rank, 'email-c.txt')

        try:
            # テンプレートファイルを読み込み（email_generation/templatesディレクトリから）
            template_path = os.path.join('email_generation', 'templates', template_file)
            with open(template_path, 'r', encoding='utf-8-sig') as f:
                template = f.read()

            # 日程を生成
            from datetime import datetime, timedelta
            today = datetime.now()
            date1 = (today + timedelta(days=2)).strftime('%m月%d日(%a)')
            date2 = (today + timedelta(days=4)).strftime('%m月%d日(%a)')
            date3 = (today + timedelta(days=7)).strftime('%m月%d日(%a)')

            # テンプレートの置換
            html = template.replace('{{会社名}}', company_name)
            html = html.replace('{{担当者名}}', '山下直輝')
            html = html.replace('{{日程1}}', date1)
            html = html.replace('{{日程2}}', date2)
            html = html.replace('{{日程3}}', date3)

            # Cランク用の追加置換
            if rank == 'C':
                current_issues = "サイトの見た目が古く、競合他社に劣る印象を与えている"
                improved_benefits = "最新のデザインで信頼性が向上し、お問い合わせが増加"
                html = html.replace('{{現状の問題点}}', current_issues)
                html = html.replace('{{改善後のメリット}}', improved_benefits)

            return html

        except Exception as e:
            logger.error(f"テンプレートファイル読み込みエラー ({template_file}): {e}")
            # フォールバック用の簡単なHTMLを返す
            return f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8"><title>ウェブサイト改善のご提案</title></head>
            <body>
                <p>{company_name}様</p>
                <p>ウェブサイト改善のご提案をさせていただきます。</p>
                <p>株式会社フォーティファイヴ<br>山下直輝</p>
            </body>
            </html>
            """

def load_companies_with_email_and_analysis():
    """メール抽出結果とウェブサイト分析結果を統合した企業データを読み込む"""
    companies = {}

    # 基本企業データを読み込み
    if not os.path.exists(INPUT_FILE):
        logger.error(f"入力ファイルが見つかりません: {INPUT_FILE}")
        return []

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 1):
                companies[str(i)] = {
                    'id': i,
                    'name': row.get('企業名', '').strip(),
                    'url': row.get('企業URL', '').strip(),
                    'email': None,
                    'rank': None,
                    'score': None
                }
    except Exception as e:
        logger.error(f"基本企業データの読み込みエラー: {e}")
        return []

    # メール抽出結果を統合（新旧両方のファイル命名規則に対応）
    import glob
    email_files = []

    # 新しい命名規則のファイルを検索
    new_files = glob.glob(f'{EMAIL_EXTRACTION_PREFIX}_*.csv')
    email_files.extend(new_files)

    # 旧い命名規則のファイルも検索（email_extraction_results_id*）
    old_files = glob.glob('email_extraction_results_id*.csv')
    email_files.extend(old_files)

    # 重複を除去
    email_files = list(set(email_files))

    logger.info(f"メール抽出結果ファイル検索: {len(email_files)}件")
    for file_path in email_files:
        logger.debug(f"メール抽出ファイル: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    company_id = row.get('企業ID', '').strip()
                    email = row.get('メールアドレス', '').strip()
                    if company_id in companies and email:
                        companies[company_id]['email'] = email
                        logger.debug(f"メール統合: ID {company_id} -> {email}")
        except Exception as e:
            logger.error(f"メール抽出結果の読み込みエラー ({file_path}): {e}")

    # ウェブサイト分析結果を統合（最新ファイルを優先的に使用）
    analysis_files = []

    # 最新の統合ファイルを最優先で確認
    latest_file = 'new_website_analysis_results_latest.csv'
    if os.path.exists(latest_file):
        analysis_files.append(latest_file)
        logger.info(f"最新の統合ファイルを発見: {latest_file}")

    # その他の分析結果ファイルも検索
    other_files = glob.glob(f'{WEBSITE_ANALYSIS_PREFIX}_*.csv')
    analysis_files.extend([f for f in other_files if f != latest_file])

    if analysis_files:
        # 最初のファイル（最新ファイル）を使用
        latest_analysis_file = analysis_files[0]
        try:
            with open(latest_analysis_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                analysis_count = 0
                for row in reader:
                    company_id = row.get('企業ID', '').strip()
                    rank = row.get('ランク', '').strip()
                    score = row.get('総合スコア', '').strip()

                    # デバッグ情報を追加
                    if company_id in ['201', '202', '203', '204', '205', '206', '207', '208', '209', '210']:
                        logger.debug(f"分析結果読み込み: ID {company_id}, ランク {rank}, スコア {score}")

                    if company_id in companies:
                        companies[company_id]['rank'] = rank
                        try:
                            companies[company_id]['score'] = float(score) if score else 0.0
                        except ValueError:
                            companies[company_id]['score'] = 0.0
                        analysis_count += 1
                        logger.debug(f"分析結果統合: ID {company_id} -> ランク {rank}, スコア {score}")

            logger.info(f"ウェブサイト分析結果を読み込みました: {latest_analysis_file}")
            logger.info(f"分析結果統合数: {analysis_count}社")
        except Exception as e:
            logger.error(f"ウェブサイト分析結果の読み込みエラー ({latest_analysis_file}): {e}")
    else:
        logger.error(f"ウェブサイト分析結果ファイルが見つかりません: {WEBSITE_ANALYSIS_PREFIX}_*.csv")

    # メールアドレスとランクの両方がある企業のみを返す
    result = []
    for company in companies.values():
        if company['email'] and company['rank']:
            result.append(company)

    logger.info(f"メール送信対象企業: {len(result)}社")
    return result

def save_sending_results(results):
    """メール送信結果を保存（既存データを保持、フィールド自動調整）"""
    try:
        # 基本フィールド定義（優先順序）
        base_fieldnames = [
            '企業ID', '企業名', 'メールアドレス', 'ランク', 'スコア',
            '送信日時', '送信結果', '件名', 'トラッキングID',
            '送信・バウンス履歴', '最終ステータス', 'バウンス履歴コード', 'バウンス履歴詳細'
        ]

        # 汎用CSV保存関数を使用
        success = safe_csv_save(
            filename=EMAIL_SENDING_RESULTS,
            data_list=results,
            base_fieldnames=base_fieldnames,
            encoding='utf-8-sig',
            sort_key=get_company_id_sort_key
        )

        if success:
            logger.info(f"送信結果を保存しました: {EMAIL_SENDING_RESULTS}")
            logger.info(f"トラッキング情報を保存しました: {EMAIL_TRACKING_RESULTS}")

        return success

    except Exception as e:
        logger.error(f"送信結果の保存エラー: {e}")
        logger.error(f"エラー詳細: {type(e).__name__}: {str(e)}")
        return False

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='新しいダッシュボード専用メール送信')
    parser.add_argument('--test', action='store_true', help='テストモード（送信せずに確認のみ）')
    parser.add_argument('--rank', choices=['A', 'B', 'C'], help='指定ランクのみ送信')
    parser.add_argument('--start-id', type=int, help='開始企業ID')
    parser.add_argument('--end-id', type=int, help='終了企業ID')

    args = parser.parse_args()

    # 企業データを読み込み
    companies = load_companies_with_email_and_analysis()

    if not companies:
        logger.error("メール送信対象の企業データがありません")
        logger.info("メール抽出とウェブサイト分析を先に実行してください")
        sys.exit(1)

    # 企業IDフィルタリング
    if args.start_id and args.end_id:
        original_count = len(companies)
        original_companies = companies.copy()  # フィルタリング前のリストを保存

        # 企業ID 2001の特別処理：最新のメール抽出結果から直接読み込み
        if args.start_id == 2001 and args.end_id == 2001:
            logger.info("企業ID 2001の特別処理を実行します")

            # 最新のメール抽出結果ファイルから企業ID 2001を検索
            latest_email_file = 'new_email_extraction_results_latest.csv'
            if os.path.exists(latest_email_file):
                try:
                    with open(latest_email_file, 'r', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            company_id_str = row.get('企業ID', '').strip()
                            if company_id_str == '2001':
                                # 企業ID 2001のデータを手動で追加
                                company_2001 = {
                                    'id': 2001,
                                    'name': row.get('企業名', '株式会社大清'),
                                    'email': row.get('メールアドレス', 'info@k-daisei.co.jp'),
                                    'rank': 'B',  # デフォルトランク
                                    'score': 60.0  # デフォルトスコア
                                }
                                companies.append(company_2001)
                                logger.info(f"企業ID 2001を追加: {company_2001}")
                                break
                except Exception as e:
                    logger.error(f"企業ID 2001の特別処理エラー: {e}")
                    # フォールバック：手動でデータを作成
                    company_2001 = {
                        'id': 2001,
                        'name': '株式会社大清',
                        'email': 'info@k-daisei.co.jp',
                        'rank': 'B',
                        'score': 60.0
                    }
                    companies.append(company_2001)
                    logger.info(f"フォールバック: 企業ID 2001を手動追加: {company_2001}")

        # 通常のフィルタリング
        companies = [c for c in companies if args.start_id <= c['id'] <= args.end_id]
        logger.info(f"企業ID {args.start_id}-{args.end_id} の企業のみ処理します: {len(companies)}社 (元: {original_count}社)")

        # デバッグ情報を追加
        if len(companies) == 0:
            logger.error(f"指定範囲 {args.start_id}-{args.end_id} に該当する企業が見つかりません")
            logger.info("利用可能な企業IDの範囲を確認中...")
            all_ids = [c['id'] for c in original_companies if c.get('id')]  # 元のリストを使用
            if all_ids:
                logger.info(f"利用可能な企業ID範囲: {min(all_ids)} - {max(all_ids)}")
                # 指定範囲に近い企業IDを表示
                nearby_ids = [id for id in all_ids if abs(id - args.start_id) <= 10 or abs(id - args.end_id) <= 10]
                if nearby_ids:
                    logger.info(f"指定範囲付近の企業ID: {sorted(nearby_ids)}")
                # 指定範囲内の企業IDを詳細表示
                target_ids = [id for id in all_ids if args.start_id <= id <= args.end_id]
                if target_ids:
                    logger.info(f"指定範囲内の企業ID: {sorted(target_ids)}")
                else:
                    logger.error(f"指定範囲 {args.start_id}-{args.end_id} 内に企業IDが存在しません")
            else:
                logger.error("企業IDが見つかりません")

    # ランクフィルタリング
    if args.rank:
        companies = [c for c in companies if c['rank'] == args.rank]
        logger.info(f"{args.rank}ランクの企業のみ処理します: {len(companies)}社")

    if not companies:
        logger.error("指定条件に該当する企業がありません")
        sys.exit(1)

    # メール送信を実行
    email_sender = EmailSender()
    results = []

    for i, company in enumerate(companies, 1):
        logger.info(f"進捗: {i}/{len(companies)} - 企業ID {company['id']}: {company['name']}")

        # 件名とHTML内容を生成
        subject = email_sender.get_subject_by_rank(company['rank'], company['name'])
        html_content = email_sender.get_html_content_by_rank(
            company['name'],
            company['rank'],
            company['score']
        )

        # テストモードの場合は送信せずに確認のみ
        if args.test:
            logger.info(f"テストモード - 送信予定: {company['name']} ({company['rank']}ランク) -> {company['email']}")
            success = True
            tracking_id = None
        else:
            # 実際にメール送信（トラッキング機能付き）
            success, tracking_id = email_sender.send_email(
                company['email'],
                subject,
                html_content,
                company['name'],
                company['rank'],
                company['id']  # 企業IDを追加
            )

            # 送信間隔を設ける（サーバー負荷軽減）
            if i < len(companies):  # 最後の企業でない場合
                logger.info("送信間隔: 3秒待機中...")
                time.sleep(3)

        # 結果を記録
        result = {
            '企業ID': company['id'],
            '企業名': company['name'],
            'メールアドレス': company['email'],
            'ランク': company['rank'],
            'スコア': company['score'],
            '送信日時': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '送信結果': 'success' if success else 'failure',
            '件名': subject,
            'トラッキングID': tracking_id or ''  # トラッキングIDを追加
        }
        results.append(result)

        # サーバーに負荷をかけないよう少し待機
        if not args.test and i < len(companies):
            time.sleep(2)

    # 結果を保存
    if save_sending_results(results):
        # 統計情報を表示
        success_count = sum(1 for r in results if r['送信結果'] == 'success')
        failure_count = len(results) - success_count

        logger.info(f"処理完了:")
        logger.info(f"  - 処理企業数: {len(results)}社")
        logger.info(f"  - 送信成功: {success_count}社")
        logger.info(f"  - 送信失敗: {failure_count}社")
        logger.info(f"  - 結果ファイル: {EMAIL_SENDING_RESULTS}")
    else:
        logger.error("結果の保存に失敗しました")
        sys.exit(1)

if __name__ == '__main__':
    main()
