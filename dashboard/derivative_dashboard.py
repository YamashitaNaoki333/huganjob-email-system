#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HUGANJOB営業メール送信システム専用ダッシュボード
- HUGANJOB採用営業メール送信に特化
- 企業データ管理と一括メール送信制御
- 送信状況追跡と結果分析
"""

import os
import json
import logging
import datetime
import time  # キャッシュ用
import sys
import csv
import uuid
import base64
import subprocess
import threading
import gc  # ガベージコレクション用
import json  # HUGANJOB送信履歴読み込み用
import pandas as pd
import csv  # CSV操作用
import re   # 正規表現用
import tempfile  # 一時ファイル用
import shutil    # ファイル操作用
from werkzeug.utils import secure_filename  # ファイル名セキュリティ用
from flask import Flask, render_template, request, jsonify, abort, Response, redirect

# HUGANJOB専用ロギング設定
os.makedirs("logs/huganjob_dashboard", exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/huganjob_dashboard/huganjob_dashboard.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Flask アプリケーション設定（HUGANJOB専用）
# templatesディレクトリとstaticディレクトリのパスを明示的に指定
app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['SECRET_KEY'] = 'huganjob_dashboard_secret_key_2025'
app.config['JSON_AS_ASCII'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'temp_uploads'

# HUGANJOB専用ダッシュボード設定
INPUT_FILE = 'data/new_input_test.csv'
PROGRESS_FILE = 'data/huganjob_workflow_progress.json'
SENT_EMAILS_FILE = 'data/huganjob_sent_emails_record.csv'
PROCESS_HISTORY_FILE = 'data/huganjob_consolidated/process_history.json'
CONSOLIDATED_DIR = 'data/huganjob_consolidated'
DASHBOARD_CONFIG_FILE = 'config/huganjob_dashboard_config.json'

# 派生版専用ファイル命名規則
DERIVATIVE_EMAIL_SENDING_RESULTS = 'data/derivative_email_sending_results.csv'
DERIVATIVE_BOUNCE_TRACKING = 'data/derivative_bounce_tracking_results.csv'
DERIVATIVE_UNSUBSCRIBE_TRACKING = 'data/derivative_unsubscribe_tracking.csv'
DERIVATIVE_EMAIL_OPEN_TRACKING = 'data/derivative_email_open_tracking.csv'

# HUGANJOB統合システム用ファイル（ルートディレクトリ）
HUGANJOB_EMAIL_SENDING_RESULTS = 'new_email_sending_results.csv'

# 互換性のための別名定義（HUGANJOBファイルを優先）
NEW_EMAIL_SENDING_RESULTS = HUGANJOB_EMAIL_SENDING_RESULTS
NEW_BOUNCE_TRACKING = DERIVATIVE_BOUNCE_TRACKING
NEW_EMAIL_OPEN_TRACKING = DERIVATIVE_EMAIL_OPEN_TRACKING
DERIVATIVE_WEBSITE_ANALYSIS_PREFIX = 'derivative_website_analysis_results'
DERIVATIVE_EMAIL_EXTRACTION_PREFIX = 'derivative_email_extraction_results'
DERIVATIVE_WORK_RECORD_PREFIX = 'derivative_work_record'
DERIVATIVE_EMAIL_CONTENT_PREFIX = 'derivative_email_content'
DERIVATIVE_ANALYTICS_PREFIX = 'derivative_analytics_report'

# ログファイル設定
LOG_FILES = {
    'integrated': 'new_integrated_workflow_*.log',
    'extraction': 'new_prioritized_extraction.log',
    'bounce': 'new_bounce_processing.log',
    'email_sending': 'new_email_sending.log',
    'dashboard': 'new_dashboard.log'
}

# 実行中のプロセス
running_processes = {}

# 過去のプロセス履歴
process_history = []
process_history_max_size = 100

# 🆕 プロセス監視強化用グローバル変数
process_sync_enabled = True
last_process_sync_time = 0
process_sync_interval = 30  # 30秒間隔でプロセス状態同期

def load_process_history():
    """プロセス履歴を読み込む"""
    global process_history

    try:
        if os.path.exists(PROCESS_HISTORY_FILE):
            with open(PROCESS_HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    process_history = data
                    logger.info(f"プロセス履歴を読み込みました: {len(process_history)}件")
                    return process_history
                else:
                    logger.error(f"プロセス履歴ファイルの形式が不正です")
    except Exception as e:
        logger.error(f"プロセス履歴の読み込み中にエラーが発生しました: {e}")
        import traceback
        logger.error(traceback.format_exc())

    # 履歴が空の場合や読み込みに失敗した場合は空のリストを返す
    process_history = []
    return process_history

def sync_process_states():
    """🆕 実際のシステムプロセス状態とダッシュボード状態を同期"""
    global running_processes, last_process_sync_time, process_sync_enabled

    if not process_sync_enabled:
        return

    current_time = time.time()
    if current_time - last_process_sync_time < process_sync_interval:
        return

    try:
        import psutil

        # 実行中プロセスの状態をチェック
        processes_to_remove = []

        for process_id, process_info in running_processes.items():
            try:
                process = process_info.get('process')
                if process:
                    # プロセスが実際に終了しているかチェック
                    poll_result = process.poll()
                    if poll_result is not None:
                        logger.info(f"同期チェック: プロセス {process_id} が終了済み（終了コード: {poll_result}）")

                        # プロセス情報を更新
                        process_info['status'] = 'completed' if poll_result == 0 else 'failed'
                        process_info['end_time'] = datetime.datetime.now()
                        process_info['return_code'] = poll_result

                        # 履歴に追加
                        add_process_to_history(process_info.copy())

                        # 削除対象に追加
                        processes_to_remove.append(process_id)

            except Exception as e:
                logger.warning(f"プロセス {process_id} 同期チェックエラー: {e}")

        # 終了済みプロセスを削除
        for process_id in processes_to_remove:
            if process_id in running_processes:
                logger.info(f"同期処理: 終了済みプロセス {process_id} を削除")
                del running_processes[process_id]

        last_process_sync_time = current_time

        if processes_to_remove:
            logger.info(f"プロセス状態同期完了: {len(processes_to_remove)}件のプロセスを更新")

    except ImportError:
        logger.warning("psutilが利用できません。プロセス状態同期を無効化します")
        process_sync_enabled = False
    except Exception as e:
        logger.error(f"プロセス状態同期エラー: {e}")

def fix_unmonitored_processes():
    """🆕 監視されていないプロセスに監視を追加"""
    global running_processes

    try:
        processes_to_monitor = []

        for process_id, process_info in running_processes.items():
            process = process_info.get('process')
            if process:
                # プロセスが実際に終了しているかチェック
                poll_result = process.poll()
                if poll_result is not None:
                    # プロセスが終了している場合、ステータスを更新
                    logger.info(f"未監視プロセス {process_id} が終了済み（終了コード: {poll_result}）")

                    process_info['status'] = 'completed' if poll_result == 0 else 'failed'
                    process_info['end_time'] = datetime.datetime.now()
                    process_info['return_code'] = poll_result

                    # 履歴に追加
                    add_process_to_history(process_info.copy())

                    # 完了ログに記録
                    try:
                        completion_log = {
                            'process_id': process_id,
                            'command': process_info.get('command', 'unknown'),
                            'status': process_info['status'],
                            'return_code': poll_result,
                            'end_time': process_info['end_time'].isoformat(),
                            'duration': str(datetime.datetime.now() - process_info.get('start_time', datetime.datetime.now()))
                        }

                        completion_log_file = 'logs/process_completion.log'
                        os.makedirs('logs', exist_ok=True)
                        with open(completion_log_file, 'a', encoding='utf-8') as f:
                            f.write(f"{datetime.datetime.now().isoformat()}: {json.dumps(completion_log, ensure_ascii=False)}\n")
                    except Exception as log_error:
                        logger.warning(f"未監視プロセス完了ログ記録エラー: {log_error}")

                    # 削除対象に追加
                    processes_to_monitor.append(process_id)

        # 終了済みプロセスを削除
        for process_id in processes_to_monitor:
            if process_id in running_processes:
                logger.info(f"未監視プロセス修正: 終了済みプロセス {process_id} を削除")
                del running_processes[process_id]

        if processes_to_monitor:
            logger.info(f"未監視プロセス修正完了: {len(processes_to_monitor)}件のプロセスを更新")

    except Exception as e:
        logger.error(f"未監視プロセス修正エラー: {e}")

def save_process_history():
    """プロセス履歴を保存する"""
    global process_history

    try:
        # 最大保存数を超えた場合は古いものから削除
        if len(process_history) > process_history_max_size:
            process_history = process_history[-process_history_max_size:]

        with open(PROCESS_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(process_history, f, ensure_ascii=False, indent=2)

        logger.info(f"プロセス履歴を保存しました: {len(process_history)}件")
        return True
    except Exception as e:
        logger.error(f"プロセス履歴の保存中にエラーが発生しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def add_process_to_history(process_info):
    """プロセス情報を履歴に追加する"""
    global process_history

    try:
        # プロセスオブジェクトは保存できないので除外
        history_entry = {k: v for k, v in process_info.items() if k != 'process'}

        # 日時オブジェクトを文字列に変換
        if 'start_time' in history_entry and isinstance(history_entry['start_time'], datetime.datetime):
            history_entry['start_time'] = history_entry['start_time'].strftime('%Y-%m-%d %H:%M:%S')
        if 'end_time' in history_entry and isinstance(history_entry['end_time'], datetime.datetime):
            history_entry['end_time'] = history_entry['end_time'].strftime('%Y-%m-%d %H:%M:%S')

        # 履歴に追加
        process_history.append(history_entry)

        # 履歴を保存
        save_process_history()

        return True
    except Exception as e:
        logger.error(f"プロセス履歴への追加中にエラーが発生しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# 企業データキャッシュ
company_data_cache = None
company_data_last_updated = None
company_stats_cache = None
company_stats_last_updated = None

# 統計情報キャッシュ
stats_cache = None
stats_last_updated = None

# 日別統計キャッシュ
daily_stats_cache = None
daily_stats_last_updated = None

# 開封率分析キャッシュ
open_rate_cache = None
open_rate_last_updated = None

# 作業記録キャッシュ
work_logs_cache = None
work_logs_last_updated = None

# フィルター対応企業データキャッシュ
filtered_companies_cache = {}
filtered_companies_last_updated = {}

# パフォーマンス改善用の設定（2025-06-26 最適化・即時反映対応）
CACHE_TIMEOUT_SECONDS = 60  # キャッシュ時間を1分に短縮（即時反映優先）
STATS_CACHE_TIMEOUT_SECONDS = 30  # 統計キャッシュ時間を30秒に短縮
DAILY_STATS_CACHE_TIMEOUT = 300  # 日別統計キャッシュ時間（5分）
OPEN_RATE_CACHE_TIMEOUT = 300  # 開封率分析キャッシュ時間（5分）
ENABLE_PERFORMANCE_LOGGING = False  # パフォーマンス重視でログ削減
ENABLE_DEBUG_LOGGING = False  # デバッグログを無効化
LAZY_LOADING_ENABLED = True
STARTUP_LAZY_LOADING = True  # 起動時の遅延読み込み有効化
MAX_COMPANIES_PER_PAGE = 50  # ページサイズ縮小（推奨設定）
PERFORMANCE_MODE = True  # パフォーマンス重視モード有効化

# 日時解析キャッシュ（パフォーマンス向上）
_datetime_cache = {}

def parse_datetime_optimized(date_str):
    """最適化された日時解析関数（キャッシュ付き）"""
    if not date_str or not date_str.strip():
        return None

    date_str = date_str.strip()

    # キャッシュチェック
    if date_str in _datetime_cache:
        return _datetime_cache[date_str]

    # 複数の日時形式に対応（マイクロ秒付きも含む）
    date_formats = [
        '%Y-%m-%d %H:%M:%S.%f',  # マイクロ秒付き
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d'
    ]

    for date_format in date_formats:
        try:
            result = datetime.datetime.strptime(date_str, date_format)
            # キャッシュに保存（最大1000件まで）
            if len(_datetime_cache) < 1000:
                _datetime_cache[date_str] = result
            return result
        except ValueError:
            continue

    return None

def ensure_directories():
    """必要なディレクトリを作成"""
    directories = [CONSOLIDATED_DIR, 'new_logs', 'new_archives']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"ディレクトリを作成しました: {directory}")

def initialize_config_files():
    """設定ファイルを初期化"""
    # ダッシュボード設定ファイル
    if not os.path.exists(DASHBOARD_CONFIG_FILE):
        config = {
            "last_updated": datetime.datetime.now().isoformat(),
            "primary_files": {
                "email_extraction": f"{CONSOLIDATED_DIR}/new_email_extraction_results_consolidated.csv",
                "prioritized_extraction": f"{CONSOLIDATED_DIR}/new_email_extraction_results_consolidated.csv",
                "website_analysis": f"{CONSOLIDATED_DIR}/new_website_analysis_results_consolidated.csv",
                "email_sending": f"{CONSOLIDATED_DIR}/new_sent_emails_record_consolidated.csv"
            },
            "file_locations": {
                "consolidated_dir": CONSOLIDATED_DIR,
                "archive_dir": "new_archives"
            }
        }
        with open(DASHBOARD_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info(f"ダッシュボード設定ファイルを作成しました: {DASHBOARD_CONFIG_FILE}")

    # 進捗ファイル
    if not os.path.exists(PROGRESS_FILE):
        progress = {
            "extract_emails": {"status": "not_started", "progress": 0, "last_updated": None},
            "analyze_websites": {"status": "not_started", "progress": 0, "last_updated": None},
            "prepare_email_content": {"status": "not_started", "progress": 0, "last_updated": None},
            "send_emails": {"status": "not_started", "progress": 0, "last_updated": None},
            "process_bounces": {"status": "not_started", "progress": 0, "last_updated": None},
            "analyze_results": {"status": "not_started", "progress": 0, "last_updated": None}
        }
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        logger.info(f"進捗ファイルを作成しました: {PROGRESS_FILE}")

def check_input_file():
    """入力ファイルの存在と内容を確認"""
    if not os.path.exists(INPUT_FILE):
        logger.error(f"入力ファイルが見つかりません: {INPUT_FILE}")
        return False

    # 複数のエンコーディングを試す
    encodings = ['utf-8-sig', 'utf-8', 'shift_jis', 'cp932', 'iso-2022-jp']

    for encoding in encodings:
        try:
            with open(INPUT_FILE, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                logger.info(f"入力ファイル {INPUT_FILE} を確認しました: {len(rows)}社のデータ (エンコーディング: {encoding})")
                return True
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.error(f"入力ファイルの読み込みエラー ({encoding}): {e}")
            continue

    logger.error("入力ファイルを読み込めませんでした。サポートされているエンコーディングで保存してください。")
    return False

def load_progress():
    """進捗情報を読み込む"""
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # デフォルトの進捗情報を返す
            return {
                "extract_emails": {"status": "not_started", "progress": 0, "last_updated": None},
                "analyze_websites": {"status": "not_started", "progress": 0, "last_updated": None},
                "prepare_email_content": {"status": "not_started", "progress": 0, "last_updated": None},
                "send_emails": {"status": "not_started", "progress": 0, "last_updated": None},
                "process_bounces": {"status": "not_started", "progress": 0, "last_updated": None},
                "analyze_results": {"status": "not_started", "progress": 0, "last_updated": None}
            }
    except Exception as e:
        logger.error(f"進捗情報の読み込み中にエラーが発生しました: {e}")
        return {}

def get_step_display_name(step):
    """HUGANJOB営業メール送信ステップの表示名を取得"""
    step_names = {
        'huganjob_email_resolution': 'メールアドレス決定',
        'huganjob_email_preparation': 'メール内容準備',
        'huganjob_bulk_sending': '一括メール送信',
        'huganjob_delivery_tracking': '配信状況追跡',
        'huganjob_results_analysis': '送信結果分析'
    }
    return step_names.get(step, step)

def get_step_info(step, progress_data):
    """ステップの詳細情報を取得"""
    step_data = progress_data.get(step, {})
    return {
        'name': step,
        'display_name': get_step_display_name(step),
        'status': step_data.get('status', 'not_started'),
        'progress': step_data.get('progress', 0),
        'last_updated': step_data.get('last_updated'),
        'description': get_step_description(step)
    }

def get_step_description(step):
    """HUGANJOB営業メール送信ステップの説明を取得"""
    descriptions = {
        'huganjob_email_resolution': 'CSVデータとウェブスクレイピングでメールアドレスを決定します',
        'huganjob_email_preparation': '企業名・募集職種を動的挿入したHTMLメールを準備します',
        'huganjob_bulk_sending': 'HUGANJOB採用営業メールを一括送信します',
        'huganjob_delivery_tracking': 'メール配信状況とバウンスを追跡します',
        'huganjob_results_analysis': '送信結果を分析してレポートを生成します'
    }
    return descriptions.get(step, '')

@app.route('/')
def index():
    """メインページ - 制御パネル機能統合版"""
    try:
        progress_data = load_progress()

        # HUGANJOB営業メール送信ステップ
        steps = [
            'huganjob_email_resolution',
            'huganjob_email_preparation',
            'huganjob_bulk_sending',
            'huganjob_delivery_tracking',
            'huganjob_results_analysis'
        ]

        steps_info = [get_step_info(step, progress_data) for step in steps]

        # 基本統計情報（軽量版）
        stats = get_basic_stats_lightweight()

        # 実行中のプロセス情報を取得（最大5件まで）
        active_processes = []
        process_count = 0
        for pid, info in running_processes.items():
            if info['status'] == 'running' and process_count < 5:
                active_processes.append({
                    'id': pid,
                    'command': info['command'][:50] + '...' if len(info['command']) > 50 else info['command'],
                    'start_time': info['start_time'].strftime('%H:%M:%S'),
                    'status': info['status'],
                    'duration': str(datetime.datetime.now() - info['start_time']).split('.')[0],
                    'description': info.get('description', info['command'])
                })
                process_count += 1

        # 直近のプロセス履歴を取得（3件）
        recent_process_history = load_process_history_lightweight(3)

        return render_template(
            'index.html',
            progress=progress_data,
            steps=steps_info,
            email_stats=stats,
            processes=active_processes,
            recent_history=recent_process_history,
            last_updated=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            get_step_display_name=get_step_display_name,
            lazy_loading=STARTUP_LAZY_LOADING
        )
    except Exception as e:
        logger.error(f"メインページ読み込みエラー: {e}")
        # エラー時は最小限の情報で表示
        return render_template(
            'index.html',
            progress={'current_step': 'huganjob_email_resolution', 'completed_steps': []},
            steps=[],
            email_stats={'total_companies': 0, 'sent_emails': 0},
            processes=[],
            recent_history=[],
            last_updated=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            get_step_display_name=get_step_display_name,
            lazy_loading=False
        )

def get_basic_stats_lightweight():
    """軽量版基本統計情報を取得（起動時間短縮用）"""
    global stats_cache, stats_last_updated

    # キャッシュチェック
    if (stats_cache is not None and
        stats_last_updated is not None and
        (datetime.datetime.now() - stats_last_updated).seconds < STATS_CACHE_TIMEOUT_SECONDS):
        return stats_cache

    try:
        # 軽量版統計（ファイル存在チェックのみ）
        stats = {
            'total_companies': 0,
            'extracted_emails': 0,
            'analyzed_websites': 0,
            'sent_emails': 0,
            'bounced_emails': 0,
            'files_status': {}
        }

        # ファイル存在チェック（読み込みなし）
        files_to_check = {
            'input': INPUT_FILE,
            'email_extraction': f"{CONSOLIDATED_DIR}/new_email_extraction_results_consolidated.csv",
            'website_analysis': f"{CONSOLIDATED_DIR}/new_website_analysis_results_consolidated.csv",
            'email_sending': f"{CONSOLIDATED_DIR}/new_sent_emails_record_consolidated.csv",
            'bounce_tracking': 'comprehensive_bounce_tracking_results.csv'
        }

        for key, file_path in files_to_check.items():
            stats['files_status'][key] = os.path.exists(file_path)
            if os.path.exists(file_path):
                try:
                    # ファイルサイズのみ取得（高速）
                    file_size = os.path.getsize(file_path)
                    stats[f'{key}_size'] = file_size
                except:
                    stats[f'{key}_size'] = 0

        # 基本的な行数のみ取得（最小限）
        if os.path.exists(INPUT_FILE):
            try:
                with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
                    stats['total_companies'] = sum(1 for line in f) - 1  # ヘッダー除く
            except:
                stats['total_companies'] = 4006  # デフォルト値

        # キャッシュ更新
        stats_cache = stats
        stats_last_updated = datetime.datetime.now()

        return stats

    except Exception as e:
        logger.warning(f"軽量版統計取得エラー: {e}")
        return {
            'total_companies': 4006,
            'extracted_emails': 0,
            'analyzed_websites': 0,
            'sent_emails': 0,
            'bounced_emails': 0,
            'files_status': {}
        }

# get_bounce_detailed_stats 関数は削除されました（bounce-analysis ページが不要なため）

def get_basic_stats():
    """基本統計情報を取得"""
    try:
        companies = load_company_data()

        total_companies = len(companies)
        email_extracted = sum(1 for c in companies if c.get('email_extracted', False))
        analyzed = sum(1 for c in companies if c.get('rank'))
        email_sent = sum(1 for c in companies if c.get('email_sent', False))
        bounced = sum(1 for c in companies if c.get('bounced', False))

        # 開封統計を取得（新しい開封率管理機能、バウンス企業を除外）
        try:
            open_rate_stats = get_comprehensive_open_rate_stats()
            opened = open_rate_stats['unique_opens']
            open_rate = open_rate_stats['open_rate']
            valid_sent_count = open_rate_stats.get('valid_sent_count', email_sent)
            bounced_count = open_rate_stats.get('bounced_count', bounced)
            bounce_rate_corrected = open_rate_stats.get('bounce_rate', 0.0)
        except Exception as e:
            logger.error(f"開封率統計取得エラー: {e}")
            opened = 0
            open_rate = 0.0
            valid_sent_count = email_sent
            bounced_count = bounced
            bounce_rate_corrected = round((bounced / email_sent * 100) if email_sent > 0 else 0, 2)

        # バウンス詳細統計を取得（簡略化）
        bounce_details = {'total_candidates': 0, 'valid_bounces': 0, 'csv_records': 0}

        # データ整合性サマリーを取得
        try:
            integrity_summary = get_bounce_open_inconsistency_summary()
        except Exception as e:
            logger.error(f"データ整合性サマリー取得エラー: {e}")
            integrity_summary = {'has_issues': False, 'total_issues': 0, 'integrity_rate': 100.0}

        return {
            'total': total_companies,
            'email_extracted': email_extracted,
            'analyzed': analyzed,
            'email_sent': email_sent,
            'bounced': bounced_count,  # 修正されたバウンス数
            'success': valid_sent_count,  # バウンス除外後の有効送信数
            'pending': email_extracted - email_sent,
            'opened': opened,
            'open_rate': open_rate,  # バウンス除外後の開封率
            'bounce_rate': bounce_rate_corrected,  # 修正されたバウンス率
            'success_rate': round(((valid_sent_count) / email_sent * 100) if email_sent > 0 else 0, 2),
            'bounce_details': bounce_details,
            'integrity_summary': integrity_summary  # データ整合性情報を追加
        }
    except Exception as e:
        logger.error(f"統計情報の取得中にエラーが発生しました: {e}")
        return {
            'total': 0,
            'email_extracted': 0,
            'analyzed': 0,
            'email_sent': 0,
            'bounced': 0,
            'opened': 0,
            'open_rate': 0.0,
            'bounce_details': {}
        }

@app.route('/companies')
def companies():
    """企業一覧ページ - ページネーション対応"""
    try:
        # パラメータ取得
        page = request.args.get('page', 1, type=int)
        filter_type = request.args.get('filter', 'all')
        search_query = request.args.get('search', '')
        per_page = min(request.args.get('per_page', MAX_COMPANIES_PER_PAGE, type=int), MAX_COMPANIES_PER_PAGE)

        # 遅延読み込み対応（パフォーマンス最適化を維持しつつ全データを読み込み）
        if STARTUP_LAZY_LOADING:
            all_companies = load_company_data_lazy()
        else:
            all_companies = load_company_data()

        total_count = len(all_companies)

        # フィルタリング（効率化）
        filtered_companies = all_companies
        if filter_type != 'all':
            if filter_type == 'email-success':
                filtered_companies = [c for c in all_companies if c.get('email')]
            elif filter_type == 'email-failure':
                filtered_companies = [c for c in all_companies if not c.get('email')]
            elif filter_type == 'sent':
                filtered_companies = [c for c in all_companies if c.get('email_sent')]
            elif filter_type == 'bounced':
                # バウンス状態の判定を強化
                filtered_companies = []
                for c in all_companies:
                    # 複数の方法でバウンス状態をチェック
                    is_bounced = (
                        c.get('bounced') == True or
                        c.get('bounce_status') == 'permanent' or
                        str(c.get('bounce_status', '')).strip().lower() == 'permanent' or
                        str(c.get('csv_bounce_status', '')).strip().lower() == 'permanent'
                    )
                    if is_bounced:
                        filtered_companies.append(c)

                # デバッグ: バウンス企業フィルタリング結果をログ出力
                if not PERFORMANCE_MODE:
                    logger.info(f"バウンス企業フィルタリング結果: {len(filtered_companies)}社が検出されました")
                    if len(filtered_companies) > 0:
                        # 最初の5社の詳細をログ出力
                        for i, c in enumerate(filtered_companies[:5]):
                            logger.info(f"バウンス企業 {i+1}: ID={c.get('id')}, 企業名={c.get('name')}, "
                                      f"bounced={c.get('bounced')}, bounce_status={c.get('bounce_status')}, "
                                      f"csv_bounce_status={c.get('csv_bounce_status')}")

        # 検索（効率化）
        if search_query:
            search_lower = search_query.lower()
            filtered_companies = [c for c in filtered_companies
                                if search_lower in c.get('name', '').lower() or
                                   search_lower in c.get('website', '').lower()]

        # ページネーション
        total_companies = len(filtered_companies)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_companies = filtered_companies[start:end]

        # ページネーション情報
        total_pages = (total_companies + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages

        total_pages = (len(filtered_companies) + per_page - 1) // per_page

        # ページネーション情報
        has_prev = page > 1
        has_next = page < total_pages
        prev_num = page - 1 if has_prev else None
        next_num = page + 1 if has_next else None

        # 統計情報（簡易版）- バウンス判定を強化
        def is_company_bounced(c):
            """企業のバウンス状態を正確に判定"""
            is_bounced = (
                c.get('bounced') == True or
                c.get('bounce_status') == 'permanent' or
                str(c.get('bounce_status', '')).strip().lower() == 'permanent' or
                str(c.get('csv_bounce_status', '')).strip().lower() == 'permanent'
            )
            return is_bounced

        # 統計情報を計算（統一送信数を使用）
        bounced_companies = [c for c in all_companies if is_company_bounced(c)]

        # 統一された送信数を取得
        unified_sent_count = get_unified_sent_email_count()

        stats = {
            'email_extracted': len([c for c in all_companies if c.get('email')]),
            'email_not_extracted': len([c for c in all_companies if not c.get('email')]),
            'rank_a': len([c for c in all_companies if c.get('rank') == 'A']),
            'rank_b': len([c for c in all_companies if c.get('rank') == 'B']),
            'rank_c': len([c for c in all_companies if c.get('rank') == 'C']),
            'not_analyzed': len([c for c in all_companies if not c.get('rank')]),
            'email_sent': unified_sent_count,  # 統一された送信数を使用
            'email_not_sent': len(all_companies) - unified_sent_count,
            'delivered': unified_sent_count - len(bounced_companies),  # 送信数からバウンス数を引く
            'bounced': len(bounced_companies)
        }

        # デバッグ: 統計情報をログ出力
        logger.info(f"統計情報計算: 総企業数={len(all_companies)}, メール抽出済み={stats['email_extracted']}, "
                  f"メール送信済み={stats['email_sent']}（統一送信数）, バウンス企業={stats['bounced']}")

        # バウンス企業の詳細確認（最初の5社）
        if len(bounced_companies) > 0:
            logger.info(f"バウンス企業詳細（最初の5社）:")
            for i, c in enumerate(bounced_companies[:5]):
                logger.info(f"  {i+1}. ID={c.get('id')}, 企業名={c.get('name')}, "
                          f"bounced={c.get('bounced')}, bounce_status={c.get('bounce_status')}, "
                          f"csv_bounce_status={c.get('csv_bounce_status')}")

        return render_template(
            'companies.html',
            companies=paginated_companies,
            current_page=page,
            page=page,
            total_pages=total_pages,
            total_companies=len(all_companies),
            total_filtered_companies=len(filtered_companies),
            per_page=per_page,
            has_prev=has_prev,
            has_next=has_next,
            prev_num=prev_num,
            next_num=next_num,
            current_filter=filter_type,
            current_search=search_query,
            stats=stats,
            last_updated=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
    except Exception as e:
        logger.error(f"企業一覧の表示中にエラーが発生しました: {e}")
        import traceback
        logger.error(f"詳細なエラー情報: {traceback.format_exc()}")

        # シンプルなエラーページを返す
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>エラー - 新しいダッシュボード</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>エラーが発生しました</h1>
            <p>企業一覧の表示中にエラーが発生しました。</p>
            <p>エラー詳細: {str(e)}</p>
            <p><a href="/">トップページに戻る</a></p>
        </body>
        </html>
        """
        return error_html, 500

# グローバル変数（キャッシュ）
company_data_cache = None
company_data_last_updated = None

def clear_cache():
    """キャッシュをクリア"""
    global company_data_cache, company_data_last_updated
    company_data_cache = None
    company_data_last_updated = None
    logger.info("キャッシュをクリアしました")
stats_cache = None
stats_last_updated = None

def clear_all_caches():
    """全てのキャッシュをクリア"""
    global company_data_cache, company_data_last_updated, stats_cache, stats_last_updated
    global company_stats_cache, company_stats_last_updated, work_logs_cache, work_logs_last_updated
    global filtered_companies_cache, filtered_companies_last_updated

    company_data_cache = None
    company_data_last_updated = None
    stats_cache = None
    stats_last_updated = None
    company_stats_cache = None
    company_stats_last_updated = None
    work_logs_cache = None
    work_logs_last_updated = None
    filtered_companies_cache.clear()
    filtered_companies_last_updated.clear()

    # ガベージコレクション実行
    gc.collect()

    logger.info("全てのキャッシュをクリアし、ガベージコレクションを実行しました")

def optimize_memory():
    """メモリ使用量を最適化"""
    try:
        # 古いキャッシュをクリア
        current_time = datetime.datetime.now()

        # 期限切れキャッシュの削除
        expired_filters = []
        for key, last_updated in filtered_companies_last_updated.items():
            if (current_time - last_updated).seconds > CACHE_TIMEOUT_SECONDS * 2:
                expired_filters.append(key)

        for key in expired_filters:
            if key in filtered_companies_cache:
                del filtered_companies_cache[key]
            if key in filtered_companies_last_updated:
                del filtered_companies_last_updated[key]

        # ガベージコレクション実行
        collected = gc.collect()

        if collected > 0:
            logger.info(f"メモリ最適化完了: {collected}個のオブジェクトを回収")

        return collected

    except Exception as e:
        logger.warning(f"メモリ最適化エラー: {e}")
        return 0

def load_csv_optimized(file_path, max_rows=None, columns=None):
    """最適化されたCSV読み込み"""
    try:
        start_time = datetime.datetime.now()

        # ファイル存在チェック
        if not os.path.exists(file_path):
            logger.warning(f"ファイルが見つかりません: {file_path}")
            return None

        # ファイルサイズチェック
        file_size = os.path.getsize(file_path) / 1024 / 1024  # MB

        # 大きなファイルの場合はチャンク読み込み
        if file_size > 10:  # 10MB以上
            logger.info(f"大容量ファイル検出 ({file_size:.1f}MB): チャンク読み込みを使用")

            chunks = []
            chunk_size = 1000  # 1000行ずつ読み込み

            for chunk in pd.read_csv(file_path, encoding='utf-8-sig', chunksize=chunk_size):
                if columns:
                    # 必要な列のみ選択
                    available_columns = [col for col in columns if col in chunk.columns]
                    if available_columns:
                        chunk = chunk[available_columns]

                chunks.append(chunk)

                # 最大行数制限
                if max_rows and len(chunks) * chunk_size >= max_rows:
                    break

            if chunks:
                df = pd.concat(chunks, ignore_index=True)
                if max_rows:
                    df = df.head(max_rows)
            else:
                df = pd.DataFrame()
        else:
            # 通常の読み込み
            df = pd.read_csv(file_path, encoding='utf-8-sig')

            if columns:
                available_columns = [col for col in columns if col in df.columns]
                if available_columns:
                    df = df[available_columns]

            if max_rows:
                df = df.head(max_rows)

        load_time = (datetime.datetime.now() - start_time).total_seconds()
        logger.info(f"CSV読み込み完了: {file_path} ({len(df)}行, {load_time:.2f}秒)")

        return df

    except Exception as e:
        logger.error(f"CSV読み込みエラー {file_path}: {e}")
        return None

def get_csv_info_fast(file_path):
    """CSVファイル情報を高速取得（行数とサイズのみ）"""
    try:
        if not os.path.exists(file_path):
            return None

        file_size = os.path.getsize(file_path) / 1024 / 1024  # MB

        # 行数を高速カウント
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            row_count = sum(1 for line in f) - 1  # ヘッダー除く

        return {
            'file_path': file_path,
            'size_mb': file_size,
            'rows': row_count,
            'exists': True
        }

    except Exception as e:
        logger.warning(f"ファイル情報取得エラー {file_path}: {e}")
        return {
            'file_path': file_path,
            'size_mb': 0,
            'rows': 0,
            'exists': False,
            'error': str(e)
        }

def load_company_data_lazy():
    """企業データを遅延読み込み（必要時のみ）"""
    global company_data_cache, company_data_last_updated

    # キャッシュが有効な場合は返す
    if (company_data_cache is not None and
        company_data_last_updated is not None and
        (datetime.datetime.now() - company_data_last_updated).seconds < CACHE_TIMEOUT_SECONDS):
        return company_data_cache

    # 実際のデータ読み込みは必要時のみ
    return load_company_data()

def load_company_data():
    """企業データを読み込む（標準データと広告営業データの両方）"""
    global company_data_cache, company_data_last_updated

    logger.info("企業データの読み込みを開始します")

    # 既存のキャッシュを保存（送信履歴やステータスを保持するため）
    existing_cache = {}
    if company_data_cache is not None:
        # 企業IDをキーとして既存のデータを保存
        for company in company_data_cache:
            if company.get('id'):
                company_id = int(company['id'])
                # 重要なステータス情報を保存
                existing_cache[company_id] = {
                    'email_sent': company.get('email_sent', False),
                    'sent_date': company.get('sent_date'),
                    'email_subject': company.get('email_subject'),
                    'email_content': company.get('email_content'),
                    'bounced': company.get('bounced', False),
                    'bounce_reason': company.get('bounce_reason'),
                    'history': company.get('history', []),
                    'email_extracted': company.get('email_extracted', False),
                    'email_confidence': company.get('email_confidence'),
                    'extraction_method': company.get('extraction_method'),
                    'rank': company.get('rank'),
                    'analysis_completed': company.get('analysis_completed', False)
                }
        logger.info(f"{len(existing_cache)}社の既存ステータス情報をキャッシュから保存しました")

    # デバッグ: 常に最新データを読み込み
    logger.info("キャッシュを無効化して最新データを読み込みます")

    try:
        companies = []

        # 🆕 HUGANJOB メールアドレス抽出結果を読み込み（修復版）
        huganjob_results = {}
        huganjob_results_file = 'huganjob_email_resolution_results.csv'

        # ファイル存在確認を強化
        if os.path.exists(huganjob_results_file):
            logger.info(f"HUGANJOB メールアドレス抽出結果を読み込み中: {huganjob_results_file}")
            try:
                # エンコーディングを明示的に指定
                results_df = pd.read_csv(huganjob_results_file, encoding='utf-8')
                if results_df is not None and not results_df.empty:
                    logger.info(f"メールアドレス抽出結果から{len(results_df)}行のデータを読み込みました")

                    # データ処理を強化
                    for idx, row in results_df.iterrows():
                        try:
                            company_id = row.get('company_id')
                            if pd.notna(company_id) and str(company_id).strip():
                                company_id_int = int(float(company_id))  # float経由でintに変換
                                huganjob_results[company_id_int] = {
                                    'final_email': str(row.get('final_email', '')).strip() if pd.notna(row.get('final_email')) else '',
                                    'email_source': str(row.get('extraction_method', '')).strip() if pd.notna(row.get('extraction_method')) else '',
                                    'status': str(row.get('status', '')).strip() if pd.notna(row.get('status')) else ''
                                }
                        except (ValueError, TypeError) as e:
                            logger.debug(f"行スキップ（ID変換エラー）: {e}")
                            continue

                    logger.info(f"HUGANJOB メールアドレス抽出結果: {len(huganjob_results)}社")
                else:
                    logger.warning("HUGANJOB メールアドレス抽出結果ファイルが空です")
            except Exception as e:
                logger.error(f"HUGANJOB メールアドレス抽出結果読み込みエラー: {e}")
                # エラー時は空の辞書を使用して処理を継続
                huganjob_results = {}
        else:
            logger.warning(f"HUGANJOB メールアドレス抽出結果ファイルが見つかりません: {huganjob_results_file}")
            # ファイルが見つからない場合も空の辞書で処理を継続
            huganjob_results = {}

        # 新しい採用データファイルを優先的に読み込み
        new_input_file = 'data/new_input_test.csv'
        if os.path.exists(new_input_file):
            logger.info(f"新しい採用データファイルを読み込み中: {new_input_file}")
            try:
                # CSVファイルを手動で読み込み、問題を回避
                import csv

                companies_data = []
                with open(new_input_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        companies_data.append(row)

                # DataFrameに変換
                df = pd.DataFrame(companies_data)

                if df is not None and not df.empty:
                    logger.info(f"CSVファイルから{len(df)}行のデータを読み込みました")
                    logger.info(f"CSVファイルの列名: {list(df.columns)}")
                    # 最初の数行をデバッグ出力
                    if len(df) > 0:
                        logger.info(f"最初の行のデータ: {dict(df.iloc[0])}")

                    # 必要な列が存在するかチェック
                    required_columns = ['ID', '企業名', '企業ホームページ', '担当者メールアドレス', '募集職種']
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    if missing_columns:
                        logger.error(f"必要な列が見つかりません: {missing_columns}")
                        logger.error(f"利用可能な列: {list(df.columns)}")
                        return companies
                    companies_added = 0
                    for idx, row in df.iterrows():
                        # メールアドレスの処理（"‐"は空として扱う）
                        # CSVファイルの実際の列名は「担当者メールアドレス」
                        email_address = row.get('担当者メールアドレス', '').strip() if pd.notna(row.get('担当者メールアドレス')) else ''
                        if email_address == '‐':
                            email_address = ''

                        # IDの安全な取得
                        try:
                            company_id_raw = row.get('ID', len(companies) + 1)
                            company_id = int(company_id_raw)
                        except (ValueError, TypeError) as e:
                            logger.error(f"ID変換エラー: '{company_id_raw}' -> {e}")
                            continue
                        company_name = row.get('企業名', '').strip() if pd.notna(row.get('企業名')) else ''
                        # パフォーマンス重視モードではログ出力を最小化
                        if not PERFORMANCE_MODE and (idx < 5 or idx >= len(df) - 5):
                            logger.info(f"行{idx+1}を処理中: ID={company_id}, 企業名={company_name}")

                        # HUGANJOB抽出結果があるかチェック
                        huganjob_result = huganjob_results.get(company_id, {})
                        final_email = huganjob_result.get('final_email', '')
                        email_source = huganjob_result.get('email_source', '')
                        extraction_status = huganjob_result.get('status', '')

                        # 最終的なメールアドレスを決定（HUGANJOB結果を優先）
                        if final_email:
                            effective_email = final_email
                            extraction_method = email_source
                            email_extracted = True
                            extraction_source = 'huganjob_extraction'
                            confidence = 0.9 if email_source == 'web_extraction' else 1.0
                        elif email_address:
                            effective_email = email_address
                            extraction_method = 'csv_import'
                            email_extracted = True
                            extraction_source = 'recruitment_csv'
                            confidence = 1.0
                        else:
                            effective_email = ''
                            extraction_method = None
                            email_extracted = False
                            extraction_source = None
                            confidence = None

                        # バウンス状態をCSVから読み取り（既存データがない場合のみ）
                        # CSVファイルの列名に基づいてデータを取得
                        csv_bounce_status = row.get('バウンス状態', '').strip() if pd.notna(row.get('バウンス状態')) else ''
                        csv_bounce_date = row.get('バウンス日時', '').strip() if pd.notna(row.get('バウンス日時')) else ''
                        csv_bounce_reason = row.get('バウンス理由', '').strip() if pd.notna(row.get('バウンス理由')) else ''

                        # 文字列として処理
                        csv_bounce_status = str(csv_bounce_status).strip() if csv_bounce_status else ''
                        csv_bounce_date = str(csv_bounce_date).strip() if csv_bounce_date else ''
                        csv_bounce_reason = str(csv_bounce_reason).strip() if csv_bounce_reason else ''

                        # 既存キャッシュからバウンス状態を確認
                        existing_bounce_status = None
                        existing_bounce_date = None
                        existing_bounce_reason = None
                        existing_is_bounced = False

                        if existing_cache and int(company_id) in existing_cache:
                            cached_data = existing_cache[int(company_id)]
                            existing_bounce_status = cached_data.get('bounce_status', '')
                            existing_bounce_date = cached_data.get('bounce_date', '')
                            existing_bounce_reason = cached_data.get('bounce_reason', '')
                            existing_is_bounced = cached_data.get('bounced', False)

                        # バウンス状態の優先順位: 既存キャッシュ > CSV
                        if existing_bounce_status:
                            # 既存のバウンス状態を優先
                            bounce_status = existing_bounce_status
                            bounce_date = existing_bounce_date
                            bounce_reason = existing_bounce_reason
                            is_bounced = existing_is_bounced
                            logger.info(f"ID {company_id}: 既存バウンス状態を保持 - {bounce_status}")
                        else:
                            # CSVのバウンス状態を使用
                            bounce_status = csv_bounce_status
                            bounce_date = csv_bounce_date
                            bounce_reason = csv_bounce_reason
                            is_bounced = bounce_status == 'permanent'
                            if is_bounced:
                                logger.info(f"ID {company_id}: CSVからバウンス状態を設定 - {bounce_status}")

                        # パフォーマンス重視モードではバウンス状態ログを最小化
                        if not PERFORMANCE_MODE and (idx < 3 or idx >= len(df) - 3 or is_bounced):
                            logger.info(f"バウンス状態チェック: ID={company_id}, 企業名={company_name}, "
                                      f"バウンス状態='{bounce_status}', is_bounced={is_bounced}")
                            if is_bounced:
                                logger.info(f"バウンス企業検出: ID={company_id}, 理由={bounce_reason}, 日時={bounce_date}")

                        # CSVファイルの列名に基づいてデータを取得
                        website = row.get('企業ホームページ', '').strip() if pd.notna(row.get('企業ホームページ')) else ''
                        job_position = row.get('募集職種', '').strip() if pd.notna(row.get('募集職種')) else ''

                        # 文字列として処理
                        website = str(website).strip() if website else ''
                        job_position = str(job_position).strip() if job_position else ''

                        company = {
                            'id': str(company_id),  # IDは文字列として保存
                            'name': company_name,
                            'website': website,
                            'recruitment_email': email_address,  # 元のCSVのメールアドレス
                            'job_position': job_position,
                            'industry': '',  # 新しいCSVには含まれていない
                            'location': '',  # 新しいCSVには含まれていない
                            # HUGANJOB専用システム - campaign_type削除済み
                            'email_extracted': email_extracted,
                            'email': effective_email,  # 最終的なメールアドレス（HUGANJOB結果を優先）
                            'extraction_method': extraction_method,
                            'confidence': confidence,
                            'email_confidence': confidence,
                            'smtp_verified': False,
                            'extraction_source': extraction_source,
                            'huganjob_status': extraction_status,  # HUGANJOB抽出ステータス
                            'huganjob_email_source': email_source,  # HUGANJOB抽出ソース
                            'email_sent': False,
                            'sent_date': None,
                            'email_subject': None,    # メール件名
                            'email_content': None,    # メール内容
                            'bounced': is_bounced,    # CSVのバウンス状態を最優先で反映
                            'bounce_reason': bounce_reason if bounce_reason else None,
                            'bounce_date': bounce_date if bounce_date else None,
                            'bounce_status': bounce_status if bounce_status else None,
                            'csv_bounce_status': bounce_status,  # デバッグ用：元のCSV値を保持
                            'is_bounced': is_bounced,  # テンプレート用：確実なバウンス判定フラグ
                            'unsubscribed': False,
                            'history': []             # 処理履歴
                        }
                        companies.append(company)
                        companies_added += 1
                        # パフォーマンス重視モードでは詳細ログを削減
                        if not PERFORMANCE_MODE and (idx < 3 or idx >= len(df) - 3):
                            logger.info(f"企業を追加しました: ID={company_id}, 企業名={company_name}, 現在の企業数={len(companies)}")
                    logger.info(f"新しい採用データから{companies_added}社を読み込みました（合計: {len(companies)}社）")
            except Exception as e:
                logger.error(f"新しい採用データファイルの読み込みエラー: {e}")
                import traceback
                logger.error(f"詳細なエラー情報: {traceback.format_exc()}")

        # 標準データファイルを読み込み（新しいファイルがない場合のフォールバック）
        elif os.path.exists(INPUT_FILE):
            # 最適化されたCSV読み込みを使用（英語カラム名に対応）
            df = load_csv_optimized(INPUT_FILE, columns=['company_name', 'website_url', 'industry', 'location'])

            if df is not None and not df.empty:
                for i, row in df.iterrows():
                    company = {
                        'id': str(i + 1),
                        'name': row.get('company_name', '').strip() if pd.notna(row.get('company_name')) else '',
                        'website': row.get('website_url', '').strip() if pd.notna(row.get('website_url')) else '',
                        'industry': row.get('industry', '').strip() if pd.notna(row.get('industry')) else '',
                        'location': row.get('location', '').strip() if pd.notna(row.get('location')) else '',
                        'recruitment_email': '',  # 新しいフィールド（空）
                        'job_position': '',       # 新しいフィールド（空）
                        # HUGANJOB専用システム - campaign_type削除済み
                        'email_extracted': False,
                        'email': None,
                        'extraction_method': None,
                        'confidence': None,
                        'email_confidence': None,  # テンプレート用
                        'smtp_verified': False,    # テンプレート用
                        'extraction_source': None, # テンプレート用
                        'rank': None,
                        'score': None,
                        'ux_score': None,          # ウェブサイト分析用
                        'design_score': None,      # ウェブサイト分析用
                        'tech_score': None,        # ウェブサイト分析用
                        'accessibility_score': None,    # アクセシビリティスコア
                        'content_score': None,          # コンテンツ品質スコア
                        'visual_hierarchy_score': None, # 視覚的階層スコア
                        'brand_consistency_score': None, # ブランド一貫性スコア
                        'performance_score': None,      # パフォーマンススコア
                        'security_score': None,         # セキュリティスコア
                        'email_sent': False,
                        'sent_date': None,
                        'email_subject': None,    # メール件名
                        'email_content': None,    # メール内容
                        'bounced': False,
                        'unsubscribed': False,
                        'history': []             # 処理履歴
                    }
                    companies.append(company)
            else:
                logger.warning("標準企業データの読み込みに失敗しました")

        # 広告営業データファイルも読み込み
        ad_input_file = 'data/derivative_ad_input.csv'
        if os.path.exists(ad_input_file):
            logger.info(f"広告営業データファイルを読み込み中: {ad_input_file}")
            try:
                ad_df = pd.read_csv(ad_input_file, encoding='utf-8-sig')
                if ad_df is not None and not ad_df.empty:
                    for _, row in ad_df.iterrows():
                        company = {
                            'id': str(row.get('id', len(companies) + 1)),
                            'name': row.get('company_name', '').strip() if pd.notna(row.get('company_name')) else '',
                            'website': row.get('website_url', '').strip() if pd.notna(row.get('website_url')) else '',
                            'industry': row.get('industry', '').strip() if pd.notna(row.get('industry')) else '',
                            'location': row.get('location', '').strip() if pd.notna(row.get('location')) else '',
                            # HUGANJOB専用システム - campaign_type削除済み
                            'email_extracted': False,
                            'email': None,
                            'extraction_method': None,
                            'confidence': None,
                            'email_confidence': None,
                            'smtp_verified': False,
                            'extraction_source': None,
                            'rank': None,
                            'score': None,
                            'ux_score': None,
                            'design_score': None,
                            'tech_score': None,
                            'accessibility_score': None,
                            'content_score': None,
                            'visual_hierarchy_score': None,
                            'brand_consistency_score': None,
                            'performance_score': None,
                            'security_score': None,
                            'email_sent': False,
                            'sent_date': None,
                            'email_subject': None,
                            'email_content': None,
                            'bounced': False,
                            'unsubscribed': False,
                            'history': []
                        }
                        companies.append(company)
                    logger.info(f"広告営業データを読み込みました: {len(ad_df)}社")
                else:
                    logger.warning("広告営業データの読み込みに失敗しました")
            except Exception as e:
                logger.error(f"広告営業データの読み込み中にエラー: {e}")
        else:
            logger.info("広告営業データファイルが見つかりません")

        # データ統合処理（送信履歴を確実に表示するため完全版を使用）
        companies = integrate_email_extraction_results(companies)
        companies = integrate_email_sending_results(companies)
        companies = integrate_bounce_tracking_results(companies)

        # パフォーマンス重視モードでは一部の重い処理をスキップ
        if not PERFORMANCE_MODE:
            companies = generate_email_content(companies)
            validate_data_integrity(companies)

        # 既存ステータスを復元（送信・バウンス状態の最終確認）
        if existing_cache:
            restored_count = 0
            for company in companies:
                company_id = int(company['id'])
                if company_id in existing_cache:
                    cached_data = existing_cache[company_id]
                    # 既存のステータス情報を復元（新しいデータを上書きしない）
                    for key, value in cached_data.items():
                        # 送信状態は既存の値を優先（送信済みの場合は保持）
                        if key in ['email_sent', 'sent_date', 'email_subject', 'email_content']:
                            if value and not company.get(key):  # 既存の値があり、新しい値がない場合のみ復元
                                company[key] = value
                        # バウンス状態は最新のバウンス処理結果を優先（delivery_statusがある場合）
                        elif key in ['bounced', 'bounce_reason', 'bounce_date', 'bounce_status']:
                            if not company.get('delivery_status') and value:  # 最新のバウンス処理結果がない場合のみ復元
                                company[key] = value
                        # 履歴は常に復元
                        elif key == 'history':
                            if value:
                                company[key] = value
                        elif key not in company or not company[key]:
                            # その他の情報は新しいデータがない場合のみ復元
                            company[key] = value
                    restored_count += 1
            logger.info(f"{restored_count}社の既存ステータス情報を復元しました")

        # キャッシュを更新
        company_data_cache = companies
        company_data_last_updated = datetime.datetime.now()

        logger.info(f"{len(companies)}社の企業データを読み込みました")
        return companies

    except Exception as e:
        logger.error(f"企業データの読み込み中にエラーが発生しました: {e}")
        return []

def validate_data_integrity(companies):
    """データ整合性をチェックし、問題があれば警告を出力"""
    total_companies = len(companies)
    companies_with_email = sum(1 for c in companies if c.get('email_extracted'))
    companies_with_analysis = sum(1 for c in companies if c.get('rank'))
    companies_with_sending = sum(1 for c in companies if c.get('email_sent'))

    logger.info(f"データ整合性チェック:")
    logger.info(f"  総企業数: {total_companies}")
    logger.info(f"  メール抽出済み: {companies_with_email}")
    logger.info(f"  ウェブサイト分析済み: {companies_with_analysis}")
    logger.info(f"  メール送信済み: {companies_with_sending}")

    # ID 1-5の特別チェック
    for company_id in ['1', '2', '3', '4', '5']:
        company = next((c for c in companies if c.get('id') == company_id), None)
        if company:
            logger.info(f"ID {company_id} ({company.get('name', 'N/A')}): "
                      f"メール={company.get('email_extracted', False)}, "
                      f"分析={bool(company.get('rank'))}, "
                      f"送信={company.get('email_sent', False)}")
        else:
            logger.warning(f"ID {company_id} の企業データが見つかりません")

def get_max_company_id_from_file(file_path):
    """CSVファイルから最大の企業IDを取得"""
    try:
        import pandas as pd
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        if '企業ID' in df.columns and not df.empty:
            return df['企業ID'].max()
        return 0
    except Exception as e:
        logger.warning(f"ファイル {file_path} から最大IDを取得できませんでした: {e}")
        return 0

def get_min_company_id_from_file(file_path):
    """CSVファイルから最小の企業IDを取得"""
    try:
        import pandas as pd
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        if '企業ID' in df.columns and not df.empty:
            return df['企業ID'].min()
        return None
    except Exception as e:
        logger.warning(f"ファイル {file_path} から最小IDを取得できませんでした: {e}")
        return None

def integrate_email_extraction_results_light(companies):
    """メール抽出結果を企業データに統合（軽量版）"""
    try:
        # HUGANJOB専用の抽出結果のみ処理
        huganjob_results_file = 'huganjob_email_resolution_results.csv'
        if not os.path.exists(huganjob_results_file):
            return companies

        # 最小限のデータのみ読み込み
        df = pd.read_csv(huganjob_results_file, encoding='utf-8-sig',
                        usecols=['company_id', 'final_email', 'email_source', 'status'])

        if df.empty:
            return companies

        # 企業IDでインデックスを作成
        company_by_id = {c['id']: c for c in companies}

        # 抽出結果を統合（最小限の処理）
        for _, row in df.iterrows():
            company_id = str(row.get('company_id', ''))
            if company_id in company_by_id:
                company = company_by_id[company_id]
                final_email = row.get('final_email', '')
                if final_email:
                    company['email_extracted'] = True
                    company['email'] = final_email
                    company['extraction_method'] = row.get('email_source', '')
                    company['confidence'] = 0.9

        return companies

    except Exception as e:
        logger.error(f"軽量版メール抽出結果統合エラー: {e}")
        return companies

def integrate_email_sending_results_light(companies):
    """メール送信結果を企業データに統合（軽量版）"""
    try:
        # HUGANJOB送信履歴のみ処理
        huganjob_history_file = 'huganjob_sending_history.json'
        if not os.path.exists(huganjob_history_file):
            return companies

        # 企業IDでインデックスを作成
        company_by_id = {c['id']: c for c in companies}

        # JSON履歴を読み込み（最小限の処理）
        with open(huganjob_history_file, 'r', encoding='utf-8') as f:
            history_data = json.load(f)

        # 送信結果を統合
        for record in history_data:
            company_id = str(record.get('company_id', ''))
            if company_id in company_by_id:
                company = company_by_id[company_id]
                company['email_sent'] = True
                company['sent_date'] = record.get('sent_date', '')

        return companies

    except Exception as e:
        logger.error(f"軽量版メール送信結果統合エラー: {e}")
        return companies

def integrate_bounce_tracking_results_light(companies):
    """バウンス追跡結果を企業データに統合（軽量版）"""
    try:
        # CSVファイルのバウンス状態のみ使用（既に読み込み済み）
        # 追加の処理は不要
        return companies

    except Exception as e:
        logger.error(f"軽量版バウンス結果統合エラー: {e}")
        return companies

def integrate_bounce_reports_to_daily_stats_light(daily_stats, start_date, end_date):
    """軽量版日別統計統合（基本的な集計のみ）"""
    try:
        # HUGANJOB送信履歴から基本統計を取得
        huganjob_history_file = 'huganjob_sending_history.json'
        if os.path.exists(huganjob_history_file):
            with open(huganjob_history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)

            # データが正しい形式かチェック
            if not isinstance(history_data, list):
                logger.warning("HUGANJOB送信履歴の形式が正しくありません")
                return daily_stats

            # 日付別に集計
            for record in history_data:
                if not isinstance(record, dict):
                    continue  # 辞書でない場合はスキップ

                sent_date = record.get('sent_date', '')
                if sent_date and sent_date in daily_stats:
                    daily_stats[sent_date]['total'] += 1
                    if record.get('sent_result') == 'success':
                        daily_stats[sent_date]['success'] += 1
                    elif 'bounce' in str(record.get('error_message', '')).lower():
                        daily_stats[sent_date]['bounce'] += 1

        return daily_stats

    except Exception as e:
        logger.error(f"軽量版日別統計統合エラー: {e}")
        return daily_stats

def get_lightweight_stats():
    """軽量版統計情報を取得（ファイルベース）"""
    try:
        stats = {
            'total': 0,
            'email_extracted': 0,
            'analyzed': 0,
            'email_sent': 0,
            'bounced': 0,
            'success': 0,
            'pending': 0,
            'opened': 0,
            'open_rate': 0.0,
            'bounce_rate': 0.0,
            'success_rate': 0.0,
            'bounce_details': {},
            'integrity_summary': {}
        }

        # 企業総数を高速取得
        if os.path.exists(INPUT_FILE):
            with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
                stats['total'] = sum(1 for line in f) - 1  # ヘッダー除く

        # HUGANJOB抽出結果から統計取得
        huganjob_results_file = 'huganjob_email_resolution_results.csv'
        if os.path.exists(huganjob_results_file):
            with open(huganjob_results_file, 'r', encoding='utf-8-sig') as f:
                stats['email_extracted'] = sum(1 for line in f) - 1  # ヘッダー除く

        # HUGANJOB送信履歴から統計取得
        huganjob_history_file = 'huganjob_sending_history.json'
        if os.path.exists(huganjob_history_file):
            try:
                with open(huganjob_history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    stats['email_sent'] = len(history_data)
            except:
                stats['email_sent'] = 0

        # 基本的な計算
        stats['pending'] = max(0, stats['email_extracted'] - stats['email_sent'])
        stats['success'] = stats['email_sent'] - stats['bounced']

        if stats['email_sent'] > 0:
            stats['bounce_rate'] = round((stats['bounced'] / stats['email_sent']) * 100, 2)
            stats['success_rate'] = round((stats['success'] / stats['email_sent']) * 100, 2)

        return stats

    except Exception as e:
        logger.error(f"軽量版統計取得エラー: {e}")
        return {
            'total': 0,
            'email_extracted': 0,
            'analyzed': 0,
            'email_sent': 0,
            'bounced': 0,
            'opened': 0,
            'open_rate': 0.0,
            'bounce_details': {}
        }

def get_total_companies_count():
    """企業総数を高速取得"""
    try:
        if os.path.exists(INPUT_FILE):
            with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
                return sum(1 for line in f) - 1  # ヘッダー除く
        return 0
    except Exception as e:
        logger.error(f"企業総数取得エラー: {e}")
        return 0

def load_company_data_paginated(page, per_page, filter_type='all', search_query=''):
    """ページネーション対応の企業データ読み込み（軽量版）"""
    try:
        companies = []

        # CSVファイルから必要な範囲のみ読み込み
        start_index = (page - 1) * per_page
        end_index = start_index + per_page

        if not os.path.exists(INPUT_FILE):
            return companies

        # HUGANJOB抽出結果を事前読み込み
        huganjob_results = {}
        huganjob_results_file = 'huganjob_email_resolution_results.csv'
        if os.path.exists(huganjob_results_file):
            try:
                results_df = pd.read_csv(huganjob_results_file, encoding='utf-8-sig')
                for _, row in results_df.iterrows():
                    company_id = row.get('company_id')
                    if pd.notna(company_id):
                        huganjob_results[int(company_id)] = {
                            'final_email': row.get('final_email', '').strip() if pd.notna(row.get('final_email')) else '',
                            'email_source': row.get('email_source', '').strip() if pd.notna(row.get('email_source')) else ''
                        }
            except Exception as e:
                logger.warning(f"HUGANJOB抽出結果読み込みエラー: {e}")

        # CSVファイルから指定範囲のデータを読み込み
        with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader, None)  # ヘッダーをスキップ

            current_index = 0
            for row in reader:
                if current_index >= start_index and current_index < end_index:
                    if len(row) >= 5:  # 最小限の列数チェック
                        company_id = int(row[0]) if row[0].isdigit() else current_index + 1
                        company_name = row[1].strip() if len(row) > 1 else ''
                        website = row[2].strip() if len(row) > 2 else ''
                        email_address = row[3].strip() if len(row) > 3 and row[3] != '‐' else ''
                        job_position = row[4].strip() if len(row) > 4 else ''

                        # HUGANJOB抽出結果があるかチェック
                        huganjob_result = huganjob_results.get(company_id, {})
                        final_email = huganjob_result.get('final_email', '')

                        # 最終的なメールアドレスを決定
                        effective_email = final_email if final_email else email_address

                        # 送信状況をチェック
                        email_sent = False
                        sent_date = None
                        if len(row) > 12 and row[12] == '送信済み':
                            email_sent = True
                            if len(row) > 13:
                                sent_date = row[13]

                        # バウンス状況をチェック
                        is_bounced = False
                        if len(row) > 15 and row[15] and row[15].lower() in ['permanent', 'temporary', 'unknown']:
                            is_bounced = True
                            bounce_status = row[15]

                        company = {
                            'id': str(company_id),
                            'name': company_name,
                            'website': website,
                            'recruitment_email': email_address,
                            'job_position': job_position,
                            'email_extracted': bool(effective_email),
                            'email': effective_email,
                            'extraction_method': huganjob_result.get('email_source', 'csv_import' if email_address else ''),
                            'confidence': 0.9 if final_email else (1.0 if email_address else None),
                            'email_sent': email_sent,  # CSVから送信状況を取得
                            'sent_date': sent_date,    # CSVから送信日時を取得
                            'bounced': is_bounced,     # CSVからバウンス状況を取得
                            'bounce_status': bounce_status,
                            'unsubscribed': False
                        }
                        companies.append(company)

                current_index += 1
                if current_index >= end_index:
                    break

        return companies

    except Exception as e:
        logger.error(f"ページネーション企業データ読み込みエラー: {e}")
        return []

def integrate_email_extraction_results(companies):
    """メール抽出結果を企業データに統合"""
    try:
        # 新しいダッシュボード専用のメール抽出結果ファイルを探す
        import glob

        # 最新ファイルを最優先で確認
        latest_file = 'new_email_extraction_results_latest.csv'
        extraction_files = []

        # 絶対パスで確認
        current_dir = os.getcwd()
        latest_file_path = os.path.join(current_dir, latest_file)

        logger.info(f"最新ファイルを検索中: {latest_file_path}")

        # 最新ファイルを優先し、存在しない場合はID範囲別ファイルを統合
        if os.path.exists(latest_file_path):
            extraction_files.append(latest_file_path)
            logger.info(f"✅ 最新ファイルを使用: {latest_file}")

            # 追加: ID範囲別ファイルもチェックして、最新ファイルに含まれていないデータがあれば統合
            new_files = glob.glob('new_email_extraction_results_id*.csv')
            if new_files:
                logger.info(f"ID範囲別ファイルも確認: {len(new_files)}個見つかりました")
                # 最新ファイルの最大IDを確認
                max_id_in_latest = get_max_company_id_from_file(latest_file_path)
                logger.info(f"最新ファイルの最大企業ID: {max_id_in_latest}")

                # 最新ファイルより新しいIDのファイルを追加
                for file_path in new_files:
                    min_id_in_file = get_min_company_id_from_file(file_path)
                    if min_id_in_file and min_id_in_file > max_id_in_latest:
                        extraction_files.append(file_path)
                        logger.info(f"✅ 追加ファイルを統合: {os.path.basename(file_path)} (最小ID: {min_id_in_file})")
        else:
            # 最新ファイルがない場合はID範囲別ファイルを統合（改良版を優先）
            improved_files = glob.glob('improved_email_extraction_results_id*.csv')
            new_files = glob.glob('new_email_extraction_results_id*.csv')

            logger.info(f"改良版ファイルを検索: {len(improved_files)}個見つかりました")
            logger.info(f"従来版ファイルを検索: {len(new_files)}個見つかりました")

            if improved_files:
                extraction_files = improved_files
                logger.info(f"✅ 改良版ファイルを使用: {[os.path.basename(f) for f in extraction_files]}")
            elif new_files:
                extraction_files = new_files
                logger.info(f"✅ 従来版ファイルを使用: {[os.path.basename(f) for f in extraction_files]}")
            else:
                logger.warning("メール抽出結果ファイルが見つかりません")
                return companies

        if not extraction_files:
            logger.info("新しいダッシュボード用のメール抽出結果ファイルが見つかりません")
            logger.info("メール抽出を実行してください。ファイル名は 'new_email_extraction_results_latest.csv' である必要があります")
            return companies

        # すべてのファイルを処理
        logger.info(f"見つかった新しいダッシュボード用メール抽出結果ファイル: {len(extraction_files)}個")
        logger.info(f"処理対象ファイル: {[os.path.basename(f) for f in extraction_files]}")  # すべてのファイルを表示

        # ファイルの詳細情報をログ出力
        for file_path in extraction_files:
            file_size = os.path.getsize(file_path)
            file_mtime = os.path.getmtime(file_path)
            import datetime
            mtime_str = datetime.datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"ファイル詳細: {os.path.basename(file_path)} (サイズ: {file_size}バイト, 更新日時: {mtime_str})")

        # 企業名とIDでインデックスを作成
        company_by_name = {c['name']: c for c in companies}
        company_by_id = {c['id']: c for c in companies}

        # デバッグ: 企業データの状況を確認
        logger.info(f"読み込み対象企業数: {len(companies)}")
        logger.info(f"企業IDインデックス: {list(company_by_id.keys())[:10]}...")  # 最初の10個のIDを表示

        matched_count = 0
        processed_rows = 0

        # すべてのメール抽出結果ファイルを処理
        for file_path in extraction_files:
            logger.info(f"ファイルを処理中: {os.path.basename(file_path)}")

            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    file_processed_rows = 0
                    file_matched_count = 0

                    for row in reader:
                        processed_rows += 1
                        file_processed_rows += 1
                        company_name = row.get('企業名', '').strip()
                        company_id = row.get('企業ID', '').strip()
                        email = row.get('メールアドレス', '').strip()
                        extraction_method = row.get('抽出方法', '').strip()
                        confidence = row.get('信頼度', '').strip()

                        # デバッグ: 企業ID 1-5の処理状況を詳しく表示
                        if company_id in ['1', '2', '3', '4', '5']:
                            logger.info(f"企業ID {company_id} を処理中: 名前={company_name}, メール={email}")

                        # 企業を特定（IDまたは名前で）
                        company = None
                        if company_id and company_id in company_by_id:
                            company = company_by_id[company_id]
                            if company_id in ['1', '2', '3', '4', '5']:
                                logger.info(f"企業ID {company_id} でマッチ: {company_name}")
                        elif company_name and company_name in company_by_name:
                            company = company_by_name[company_name]
                            if company_id in ['1', '2', '3', '4', '5']:
                                logger.info(f"企業名 {company_name} でマッチ")

                        if company and email:
                            company['email_extracted'] = True
                            company['email'] = email
                            company['extraction_method'] = extraction_method
                            try:
                                # テンプレートで使用される名前に合わせる
                                company['confidence'] = float(confidence) if confidence else 0.0
                                company['email_confidence'] = float(confidence) if confidence else 0.0
                            except ValueError:
                                company['confidence'] = 0.0
                                company['email_confidence'] = 0.0

                            # 改良版ファイルの場合は追加フィールドを処理
                            extraction_steps = row.get('抽出ステップ', '').strip()
                            source = row.get('抽出方法', '').strip()

                            if extraction_steps:
                                company['extraction_steps'] = extraction_steps
                            if source:
                                company['extraction_source'] = source

                            matched_count += 1
                            file_matched_count += 1
                            if company_id in ['1', '2', '3', '4', '5']:
                                logger.info(f"企業ID {company_id} のメール情報を統合: {company_name} -> {email}")

                            # デバッグ: ID 1-5の詳細ログ
                            if int(company_id) <= 5:
                                logger.info(f"[DEBUG] ID {company_id}: 企業名={company_name}, メール={email}, 抽出方法={extraction_method}, 信頼度={confidence}")
                                if extraction_steps:
                                    logger.info(f"[DEBUG] ID {company_id}: 抽出ステップ={extraction_steps}")

                    logger.info(f"ファイル {os.path.basename(file_path)}: {file_processed_rows}行処理, {file_matched_count}社マッチ")

            except Exception as e:
                logger.error(f"ファイル {file_path} の処理中にエラー: {e}")
                continue

        extracted_count = sum(1 for c in companies if c.get('email_extracted', False))
        logger.info(f"処理した行数: {processed_rows}")
        logger.info(f"マッチした企業数: {matched_count}")
        logger.info(f"メール抽出結果を統合しました: {extracted_count}社")

    except Exception as e:
        logger.error(f"メール抽出結果の統合中にエラーが発生しました: {e}")
        import traceback
        logger.error(f"詳細なエラー情報: {traceback.format_exc()}")

    return companies

def integrate_website_analysis_results(companies):
    """ウェブサイト分析結果を企業データに統合"""
    try:
        # 新しいダッシュボード専用のウェブサイト分析結果ファイルを探す
        import glob

        # 最新ファイルを最優先で確認
        latest_file = 'new_website_analysis_results_latest.csv'
        selected_file = None

        if os.path.exists(latest_file):
            selected_file = latest_file
            logger.info(f"最新ファイルを使用: {latest_file}")
        else:
            # 最新ファイルがない場合は他のファイルを探す
            analysis_files = glob.glob('new_website_analysis_results_*.csv')

            if not analysis_files:
                logger.info("新しいダッシュボード用のウェブサイト分析結果ファイルが見つかりません（まだ分析が実行されていません）")
                return companies

            # 最新のファイルを使用（更新日時でソート）
            selected_file = max(analysis_files, key=os.path.getmtime)
            logger.info(f"更新日時が最新のファイルを使用: {selected_file}")

        logger.info(f"ウェブサイト分析結果ファイルを読み込み中: {selected_file}")

        # 企業IDと企業名の両方でインデックスを作成
        company_by_id = {c['id']: c for c in companies}
        company_by_name = {c['name']: c for c in companies}

        matched_count = 0
        processed_rows = 0

        with open(selected_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed_rows += 1
                company_id = row.get('企業ID', '').strip()
                company_name = row.get('企業名', '').strip()
                rank = row.get('ランク', '').strip()
                score = row.get('総合スコア', '').strip()

                # 新しいCSVファイルの列名に対応（実際のファイル形式に合わせて修正）
                ux_score = row.get('UXスコア', '').strip()
                design_score = row.get('デザインスコア', '').strip()
                technical_score = row.get('技術スコア', '').strip()

                # 旧形式との互換性も保持
                accessibility_score = row.get('アクセシビリティ', '').strip()
                usability_score = row.get('ユーザビリティ', '').strip()
                content_score = row.get('コンテンツ品質', '').strip()
                visual_hierarchy_score = row.get('視覚的階層', '').strip()
                brand_consistency_score = row.get('ブランド一貫性', '').strip()
                seo_score = row.get('SEO最適化', '').strip()
                performance_score = row.get('パフォーマンス', '').strip()
                security_score = row.get('セキュリティ', '').strip()

                # 分析結果の詳細情報
                strengths = row.get('強み', '').strip()
                weaknesses = row.get('弱み', '').strip()
                improvements = row.get('改善提案', '').strip()

                # 企業IDまたは企業名でマッチング
                company = None
                if company_id and company_id in company_by_id:
                    company = company_by_id[company_id]
                    matched_count += 1
                elif company_name and company_name in company_by_name:
                    company = company_by_name[company_name]
                    matched_count += 1

                if company:
                    company['rank'] = rank
                    try:
                        company['score'] = float(score) if score else 0.0
                    except ValueError:
                        company['score'] = 0.0

                    # カテゴリ別スコアを計算（詳細スコアから）
                    try:
                        # UXスコア（30点満点）= (アクセシビリティ + ユーザビリティ + コンテンツ品質) / 3 * 0.3
                        if accessibility_score and usability_score and content_score:
                            ux_calc = (float(accessibility_score) + float(usability_score) + float(content_score)) / 3 * 0.3
                            company['ux_score'] = round(ux_calc, 1)
                            logger.debug(f"企業ID {company_id}: UXスコア計算 = ({accessibility_score} + {usability_score} + {content_score}) / 3 * 0.3 = {ux_calc:.1f}")
                        elif ux_score:
                            company['ux_score'] = float(ux_score)
                            logger.debug(f"企業ID {company_id}: UXスコア（既存値使用） = {ux_score}")
                        else:
                            company['ux_score'] = 0.0
                            logger.debug(f"企業ID {company_id}: UXスコア = 0.0（データなし）")
                    except (ValueError, TypeError) as e:
                        company['ux_score'] = 0.0
                        logger.warning(f"企業ID {company_id}: UXスコア計算エラー = {e}")

                    try:
                        # デザインスコア（40点満点）= (デザイン品質 + 視覚的階層 + ブランド一貫性) / 3 * 0.4
                        design_quality = row.get('デザイン品質', '').strip()
                        if design_quality and visual_hierarchy_score and brand_consistency_score:
                            design_calc = (float(design_quality) + float(visual_hierarchy_score) + float(brand_consistency_score)) / 3 * 0.4
                            company['design_score'] = round(design_calc, 1)
                            logger.debug(f"企業ID {company_id}: デザインスコア計算 = ({design_quality} + {visual_hierarchy_score} + {brand_consistency_score}) / 3 * 0.4 = {design_calc:.1f}")
                        elif design_score:
                            company['design_score'] = float(design_score)
                            logger.debug(f"企業ID {company_id}: デザインスコア（既存値使用） = {design_score}")
                        else:
                            company['design_score'] = 0.0
                            logger.debug(f"企業ID {company_id}: デザインスコア = 0.0（データなし）")
                    except (ValueError, TypeError) as e:
                        company['design_score'] = 0.0
                        logger.warning(f"企業ID {company_id}: デザインスコア計算エラー = {e}")

                    try:
                        # 技術スコア（30点満点）= (SEO最適化 + パフォーマンス + セキュリティ) / 3 * 0.3
                        if seo_score and performance_score and security_score:
                            tech_calc = (float(seo_score) + float(performance_score) + float(security_score)) / 3 * 0.3
                            company['tech_score'] = round(tech_calc, 1)
                            logger.debug(f"企業ID {company_id}: 技術スコア計算 = ({seo_score} + {performance_score} + {security_score}) / 3 * 0.3 = {tech_calc:.1f}")
                        elif technical_score:
                            company['tech_score'] = float(technical_score)
                            logger.debug(f"企業ID {company_id}: 技術スコア（既存値使用） = {technical_score}")
                        else:
                            company['tech_score'] = 0.0
                            logger.debug(f"企業ID {company_id}: 技術スコア = 0.0（データなし）")
                    except (ValueError, TypeError) as e:
                        company['tech_score'] = 0.0
                        logger.warning(f"企業ID {company_id}: 技術スコア計算エラー = {e}")

                    # 旧形式との互換性のため詳細スコアも統合
                    try:
                        company['accessibility_score'] = float(accessibility_score) if accessibility_score else 0.0
                    except ValueError:
                        company['accessibility_score'] = 0.0

                    try:
                        company['usability_score'] = float(usability_score) if usability_score else 0.0
                    except ValueError:
                        company['usability_score'] = 0.0

                    try:
                        company['content_score'] = float(content_score) if content_score else 0.0
                    except ValueError:
                        company['content_score'] = 0.0

                    try:
                        company['visual_hierarchy_score'] = float(visual_hierarchy_score) if visual_hierarchy_score else 0.0
                    except ValueError:
                        company['visual_hierarchy_score'] = 0.0

                    try:
                        company['brand_consistency_score'] = float(brand_consistency_score) if brand_consistency_score else 0.0
                    except ValueError:
                        company['brand_consistency_score'] = 0.0

                    try:
                        company['seo_score'] = float(seo_score) if seo_score else 0.0
                    except ValueError:
                        company['seo_score'] = 0.0

                    try:
                        company['performance_score'] = float(performance_score) if performance_score else 0.0
                    except ValueError:
                        company['performance_score'] = 0.0

                    try:
                        company['security_score'] = float(security_score) if security_score else 0.0
                    except ValueError:
                        company['security_score'] = 0.0

                    # 分析結果の詳細情報
                    company['analysis_strengths'] = strengths
                    company['analysis_weaknesses'] = weaknesses
                    company['analysis_improvements'] = improvements

                    logger.debug(f"企業ID {company_id} ({company_name}) の分析結果を統合: ランク {rank}, スコア {score}")

                    # デバッグ: ID 1-5の詳細ログ
                    if int(company_id) <= 5:
                        logger.info(f"[DEBUG] ウェブサイト分析 ID {company_id}: 企業名={company_name}, ランク={rank}, スコア={score}, UX={ux_score}, デザイン={design_score}, 技術={technical_score}")
                else:
                    logger.debug(f"マッチしない企業: ID={company_id}, 名前={company_name}")

                    # デバッグ: ID 1-5のマッチしない場合もログ
                    if int(company_id) <= 5:
                        logger.warning(f"[DEBUG] ウェブサイト分析でマッチしない ID {company_id}: 企業名={company_name}")

        analyzed_count = sum(1 for c in companies if c['rank'])
        logger.info(f"処理した行数: {processed_rows}")
        logger.info(f"マッチした企業数: {matched_count}")
        logger.info(f"ウェブサイト分析結果を統合しました: {analyzed_count}社")

    except Exception as e:
        logger.error(f"ウェブサイト分析結果の統合中にエラーが発生しました: {e}")

    return companies

def integrate_email_sending_results(companies):
    """メール送信結果を企業データに統合（HUGANJOB統合システム対応）"""
    try:
        # 企業IDでインデックスを作成
        company_by_id = {c['id']: c for c in companies}

        # 1. HUGANJOB統合システムの送信履歴JSONファイルを最優先で確認
        huganjob_history_file = 'huganjob_sending_history.json'
        huganjob_processed = 0

        if os.path.exists(huganjob_history_file):
            logger.info(f"HUGANJOB統合システム送信履歴を読み込み中: {huganjob_history_file}")
            try:
                with open(huganjob_history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)

                sending_records = history_data.get('sending_records', [])
                logger.info(f"HUGANJOB送信履歴: {len(sending_records)}件の記録を発見")

                for record in sending_records:
                    company_id = str(record.get('company_id', ''))
                    company_name = record.get('company_name', '')
                    email_address = record.get('email_address', '')
                    send_time = record.get('send_time', '')
                    script_name = record.get('script_name', '')

                    if company_id in company_by_id:
                        company = company_by_id[company_id]
                        company['email_sent'] = True
                        company['sent_date'] = send_time
                        company['email_subject'] = f"【{company.get('job_position', '人材')}の人材採用を強化しませんか？】株式会社HUGANからのご提案"
                        company['final_status'] = '配信成功'
                        company['sending_system'] = 'huganjob_unified'
                        company['script_name'] = script_name

                        # 送信履歴に記録を追加
                        if 'history' not in company:
                            company['history'] = []

                        company['history'].append({
                            'action': 'email_sent',
                            'timestamp': send_time,
                            'details': f'HUGANJOB統合システムで送信: {email_address}',
                            'system': 'huganjob_unified'
                        })

                        huganjob_processed += 1
                        logger.info(f"HUGANJOB送信記録を統合: ID {company_id} - {company_name}")

                logger.info(f"HUGANJOB統合システム送信結果を統合: {huganjob_processed}社")

            except Exception as e:
                logger.error(f"HUGANJOB送信履歴ファイルの読み込みエラー: {e}")

        # 2. 従来のCSVファイルも確認（フォールバック）
        import glob

        # 最優先で new_email_sending_results.csv を確認
        primary_file = 'new_email_sending_results.csv'
        selected_file = None

        if os.path.exists(primary_file):
            selected_file = primary_file
            logger.info(f"メイン送信結果ファイルを使用: {primary_file}")
        else:
            # ID範囲別ファイルを検索
            sending_files = glob.glob('sent_emails_record_id*.csv')
            if sending_files:
                # 最新のファイルを選択
                selected_file = max(sending_files, key=os.path.getmtime)
                logger.info(f"最新のメール送信結果ファイルを使用: {selected_file}")
            elif os.path.exists(NEW_EMAIL_SENDING_RESULTS):
                selected_file = NEW_EMAIL_SENDING_RESULTS
                logger.info(f"デフォルト送信結果ファイルを使用: {NEW_EMAIL_SENDING_RESULTS}")

        csv_processed = 0
        if selected_file:
            logger.info(f"従来のCSV送信結果ファイルを読み込み中: {selected_file}")
            try:
                with open(selected_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    # ヘッダー行を読み取り、構造を検証
                    header = next(reader, None)

                    # CSVファイル構造の検証とログ出力
                    if header:
                        logger.info(f"CSVヘッダー構造: {header}")
                        logger.info(f"CSVヘッダー列数: {len(header)}")
                        expected_columns = ['企業ID', '企業名', 'メールアドレス', '募集職種', 'メール用職種', '送信日時', '送信結果', 'トラッキングID', 'エラーメッセージ', '件名']
                        if len(header) != len(expected_columns):
                            logger.warning(f"CSVヘッダー列数不一致: 期待={len(expected_columns)}, 実際={len(header)}")
                            logger.warning(f"期待される列: {expected_columns}")
                            logger.warning(f"実際の列: {header}")
                            # 実際のデータ構造に合わせて処理を調整
                            logger.info("実際のデータ構造に合わせて処理を継続します")

                    # CSVファイルの実際の構造に基づいて読み込み
                    # 動的に列構造を判定（一部の行に「メール用職種」列が存在する不整合に対応）
                    for row_data in reader:
                        # 行データをリストとして取得
                        if len(row_data) < 7:  # 最低限必要な列数をチェック
                            continue

                        # 列数に基づいて動的にマッピングを決定
                        if len(row_data) == 10:  # メール用職種列が存在する場合（ID 1-5など）
                            # 列順序: 企業ID,企業名,メールアドレス,募集職種,メール用職種,送信日時,送信結果,トラッキングID,エラーメッセージ,件名
                            company_id = row_data[0].strip() if len(row_data) > 0 else ''
                            company_name = row_data[1].strip() if len(row_data) > 1 else ''
                            email_address = row_data[2].strip() if len(row_data) > 2 else ''
                            job_position = row_data[3].strip() if len(row_data) > 3 else ''
                            # row_data[4] はメール用職種（スキップ）
                            sent_date = row_data[5].strip() if len(row_data) > 5 else ''
                            sent_result = row_data[6].strip() if len(row_data) > 6 else ''
                            tracking_id = row_data[7].strip() if len(row_data) > 7 else ''
                            error_message = row_data[8].strip() if len(row_data) > 8 else ''
                            subject = row_data[9].strip() if len(row_data) > 9 else ''
                            logger.debug(f"10列形式で処理: ID={company_id}")
                        else:  # メール用職種列が存在しない場合（ID 6以降など）
                            # 列順序: 企業ID,企業名,メールアドレス,募集職種,送信日時,送信結果,トラッキングID,エラーメッセージ,件名
                            company_id = row_data[0].strip() if len(row_data) > 0 else ''
                            company_name = row_data[1].strip() if len(row_data) > 1 else ''
                            email_address = row_data[2].strip() if len(row_data) > 2 else ''
                            job_position = row_data[3].strip() if len(row_data) > 3 else ''
                            sent_date = row_data[4].strip() if len(row_data) > 4 else ''
                            sent_result = row_data[5].strip() if len(row_data) > 5 else ''
                            tracking_id = row_data[6].strip() if len(row_data) > 6 else ''
                            error_message = row_data[7].strip() if len(row_data) > 7 else ''
                            subject = row_data[8].strip() if len(row_data) > 8 else ''
                            logger.debug(f"9列形式で処理: ID={company_id}")

                        # バウンス関連の情報は、エラーメッセージから判定
                        bounce_status = ''
                        bounce_reason = ''
                        bounce_date = ''
                        final_status = ''

                        # エラーメッセージがある場合はバウンスとして扱う
                        if error_message and error_message != '':
                            bounce_status = 'permanent'
                            bounce_reason = error_message
                            bounce_date = sent_date
                            final_status = 'バウンス'
                        elif sent_result == 'success':
                            final_status = '配信成功'
                        elif sent_result == 'bounced':
                            bounce_status = 'permanent'
                            bounce_reason = 'バウンス検出'
                            bounce_date = sent_date
                            final_status = 'バウンス'
                        elif sent_result == 'skipped':
                            final_status = 'スキップ'

                        # データ整合性チェック
                        if not company_id:
                            logger.warning(f"企業IDが空の行をスキップ: {row_data}")
                            continue

                        if not sent_result:
                            logger.warning(f"送信結果が空の行: ID={company_id}")

                        logger.info(f"CSV行処理: ID={company_id}, 送信結果={sent_result}, トラッキングID={tracking_id}, エラー={error_message}")

                        if company_id in company_by_id:
                            company = company_by_id[company_id]

                            # トラッキングIDを常に更新（開封状況追跡のため）
                            if tracking_id:
                                company['tracking_id'] = tracking_id
                                logger.info(f"企業ID {company_id} にトラッキングID設定: {tracking_id}")

                            # 送信結果の統合処理を改善
                            # CSVに送信記録がある場合は、HUGANJOBシステムの記録がなくても送信済みとして扱う
                            if sent_result == 'success':
                                # メールアドレスが未登録の場合は送信済みとしない（ID欠番修正時の不整合対策）
                                company_email = company.get('email', '').strip()
                                if company_email and company_email != '‐' and company_email != '-':
                                    # 送信成功の場合は必ず送信済みとしてマーク
                                    company['email_sent'] = True
                                    company['sent_date'] = sent_date

                                    # 送信システムの情報を設定（HUGANJOB統合システムの記録がない場合）
                                    if not company.get('sending_system'):
                                        company['sending_system'] = 'legacy_csv'
                                else:
                                    # メールアドレス未登録の場合はログ出力
                                    logger.warning(f"企業ID {company_id}: メールアドレス未登録のため送信済みステータスをスキップ ({company_email})")
                                    logger.info(f"企業ID {company_id}: CSV送信結果から送信済み状態を設定")

                                # バウンス情報を追加（既存のバウンス状態がない場合のみ）
                                if not company.get('bounced') and not company.get('bounce_status'):
                                    company['bounced'] = (bounce_status == 'permanent')  # CSVでは'permanent'として記録
                                    company['bounce_reason'] = bounce_reason if bounce_reason else None
                                    company['bounce_date'] = bounce_date if bounce_date else None
                                    company['bounce_status'] = bounce_status if bounce_status else None
                                    logger.info(f"企業ID {company_id}: CSV送信結果からバウンス状態を設定 - {bounce_status}")
                                else:
                                    logger.info(f"企業ID {company_id}: 既存バウンス状態を保持")

                                company['final_status'] = final_status if final_status else '配信成功'

                            csv_processed += 1

                logger.info(f"従来のCSV送信結果を統合: {csv_processed}社")

            except Exception as e:
                logger.error(f"CSV送信結果ファイルの読み込みエラー: {e}")

        total_sent = sum(1 for c in companies if c.get('email_sent', False))
        total_bounced = sum(1 for c in companies if c.get('bounced', False))
        total_success = sum(1 for c in companies if c.get('email_sent', False) and not c.get('bounced', False))

        logger.info(f"メール送信結果統合完了: 総送信済み {total_sent}社 (HUGANJOB: {huganjob_processed}社, CSV: {csv_processed}社)")
        logger.info(f"送信結果詳細: 配信成功 {total_success}社, バウンス {total_bounced}社")

        # データ整合性の最終チェック
        inconsistent_count = 0
        for company in companies:
            if company.get('email_sent', False) and not company.get('sent_date'):
                logger.warning(f"企業ID {company.get('id')}: 送信済みだが送信日時が未設定")
                inconsistent_count += 1

        if inconsistent_count > 0:
            logger.warning(f"データ整合性の問題: {inconsistent_count}社で不整合を検出")

    except Exception as e:
        logger.error(f"メール送信結果の統合中にエラーが発生しました: {e}")

    return companies

def integrate_bounce_tracking_results(companies):
    """バウンス追跡結果を企業データに統合"""
    try:
        # 包括的バウンス検出結果ファイルを優先的に確認
        comprehensive_bounce_file = 'comprehensive_bounce_tracking_results.csv'
        selected_file = None

        if os.path.exists(comprehensive_bounce_file):
            selected_file = comprehensive_bounce_file
            logger.info(f"包括的バウンス検出結果ファイルを使用: {comprehensive_bounce_file}")
        elif os.path.exists(NEW_BOUNCE_TRACKING):
            selected_file = NEW_BOUNCE_TRACKING
            logger.info(f"標準バウンス追跡ファイルを使用: {NEW_BOUNCE_TRACKING}")
        else:
            logger.info("バウンス追跡ファイルが見つかりません（まだバウンス処理が実行されていません）")
            return companies

        logger.info(f"バウンス追跡ファイルを読み込み中: {selected_file}")

        # 企業IDでインデックスを作成
        company_by_id = {c['id']: c for c in companies}
        bounce_count = 0

        with open(selected_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                company_id = row.get('企業ID', '').strip()
                status = row.get('ステータス', '').strip()
                bounce_reason = row.get('バウンス理由', '').strip()
                bounce_date = row.get('バウンス日時', '').strip()
                bounce_type = row.get('バウンスタイプ', '').strip()

                if company_id in company_by_id:
                    company = company_by_id[company_id]
                    # バウンス追跡結果は最新の情報として優先的に適用
                    company['bounced'] = (status == 'bounced')
                    company['bounce_reason'] = bounce_reason
                    company['bounce_date'] = bounce_date
                    company['bounce_type'] = bounce_type
                    company['delivery_status'] = status
                    bounce_count += 1
                    logger.info(f"企業ID {company_id}: バウンス追跡結果を更新 - {status}")

        logger.info(f"バウンス追跡結果統合完了: {bounce_count}件のバウンス情報を統合しました")

        bounced_count = sum(1 for c in companies if c.get('bounced', False))
        delivered_count = sum(1 for c in companies if c.get('delivery_status') == 'delivered')
        logger.info(f"バウンス追跡結果を統合しました: 配信成功 {delivered_count}社, バウンス {bounced_count}社")

    except Exception as e:
        logger.error(f"バウンス追跡結果の統合中にエラーが発生しました: {e}")

    return companies

def load_email_template(rank):
    """ランクに応じたメールテンプレートを読み込む"""
    template_file = None
    if rank == 'A':
        template_file = 'email_generation/templates/email-a.txt'
    elif rank == 'B':
        template_file = 'email_generation/templates/email-b.txt'
    else:  # rank == 'C'
        template_file = 'email_generation/templates/email-c.txt'

    if template_file and os.path.exists(template_file):
        try:
            with open(template_file, 'r', encoding='utf-8-sig') as f:
                return f.read()
        except Exception as e:
            logger.error(f"テンプレートファイル {template_file} の読み込み中にエラーが発生しました: {e}")

    return None

def generate_email_content(companies):
    """企業データに基づいてメール内容を生成（HUGAN JOB採用メール用）"""
    try:
        for company in companies:
            # 企業名と募集職種を取得
            company_name = company.get('name', '企業名不明')
            job_position = company.get('job_position', '人材')

            # メール件名を設定（募集職種を含む）
            if not company.get('email_subject'):
                company['email_subject'] = f'【{job_position}の人材採用を強化しませんか？】株式会社HUGANからのご提案'

                # メール内容を設定（HUGAN JOB採用テンプレートを使用）
                if not company.get('email_content'):
                    # corporate-email-newsletter.htmlテンプレートを読み込み
                    template_file = 'corporate-email-newsletter.html'
                    if os.path.exists(template_file):
                        try:
                            with open(template_file, 'r', encoding='utf-8') as f:
                                template = f.read()

                            # テンプレート内の変数を置換
                            email_content = template.replace('{{company_name}}', company_name)
                            email_content = email_content.replace('{{job_position}}', job_position)

                            # トラッキングピクセルのプレースホルダーを追加（実際の送信時に置換される）
                            email_content = email_content.replace('{{tracking_pixel}}', '')

                            company['email_content'] = email_content
                        except Exception as e:
                            logger.error(f"テンプレートファイル {template_file} の読み込み中にエラーが発生しました: {e}")
                            company['email_content'] = None
                    else:
                        # テンプレートが読み込めない場合のフォールバック
                        company['email_content'] = f'''
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background-color: #3498db; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #777; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>HUGAN JOB</h1>
        <p>人材紹介サービス</p>
    </div>
    <div class="content">
        <p>{company_name} 様</p>

        <p>初めてご連絡いたします。<br>
        株式会社HUGANで、人材紹介サービス「HUGAN JOB」を担当しております竹下と申します。</p>

        <p>この度、貴社が募集されております「{job_position}」の求人を拝見し、弊社のサービスが貴社の採用活動に貢献できるものと考え、ご連絡いたしました。</p>

        <p>初期費用0円の完全成功報酬型で、採用工数の削減とミスマッチ防止を実現いたします。</p>
    </div>
    <div class="footer">
        <p>株式会社HUGAN<br>
        竹下隼平<br>
        Email: contact@huganjob.jp</p>
    </div>
</body>
</html>
'''

        logger.info(f"メール内容を生成しました: {len([c for c in companies if c.get('email_content')])}社")

    except Exception as e:
        logger.error(f"メール内容の生成中にエラーが発生しました: {e}")

    return companies

@app.route('/api/companies')
def api_companies():
    """企業データAPI"""
    try:
        companies = load_company_data()
        return jsonify({
            'success': True,
            'companies': companies,
            'total': len(companies),
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"企業データAPIでエラーが発生しました: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 500

@app.route('/api/stats')
def api_stats():
    """統計情報API - 軽量版対応"""
    try:
        # 軽量版統計を使用してレスポンス時間を短縮
        lightweight = request.args.get('lightweight', 'false').lower() == 'true'

        if lightweight:
            stats = get_basic_stats_lightweight()
        else:
            stats = get_basic_stats()

        return jsonify({
            'success': True,
            'stats': stats,
            'lightweight': lightweight,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"統計情報APIでエラーが発生しました: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 500

@app.route('/api/memory_optimize', methods=['POST'])
def api_memory_optimize():
    """メモリ最適化API"""
    try:
        collected = optimize_memory()
        return jsonify({
            'success': True,
            'collected_objects': collected,
            'message': f'{collected}個のオブジェクトを回収しました',
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"メモリ最適化APIでエラーが発生しました: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 500

@app.route('/api/cache_clear', methods=['POST'])
def api_cache_clear():
    """キャッシュクリアAPI"""
    try:
        clear_all_caches()
        return jsonify({
            'success': True,
            'message': 'すべてのキャッシュをクリアしました',
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"キャッシュクリアAPIでエラーが発生しました: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 500

@app.route('/api/email_open_stats')
def api_email_open_stats():
    """メール開封統計API"""
    try:
        open_stats = get_email_open_stats()
        return jsonify({
            'success': True,
            'open_stats': open_stats,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"開封統計APIでエラーが発生しました: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 500

@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    """データリフレッシュAPI（強化版）"""
    try:
        # キャッシュをクリア
        global company_data_cache, company_data_last_updated
        global company_stats_cache, company_stats_last_updated
        global stats_cache, stats_last_updated
        global filtered_companies_cache, filtered_companies_last_updated

        company_data_cache = None
        company_data_last_updated = None
        company_stats_cache = None
        company_stats_last_updated = None
        stats_cache = None
        stats_last_updated = None
        filtered_companies_cache = {}
        filtered_companies_last_updated = {}

        logger.info("全てのデータキャッシュをクリアしました")

        # データを再読み込み
        companies = load_company_data()
        logger.info(f"企業データを再読み込みしました: {len(companies)}社")

        return jsonify({
            'success': True,
            'message': f'データを更新しました（{len(companies)}社）',
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"データリフレッシュでエラーが発生しました: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 500



def analyze_huganjob_progress(process_info):
    """HUGANJOB統合送信の進行状況を解析"""
    try:
        output = process_info.get('output', '')
        command = process_info.get('command', '')

        # HUGANJOB統合送信プロセスかどうか確認
        if 'huganjob_unified_sender' not in command:
            return {'type': 'unknown', 'message': 'HUGANJOB統合送信以外のプロセス'}

        # コマンドからID範囲を抽出
        import re
        start_match = re.search(r'--start-id\s+(\d+)', command)
        end_match = re.search(r'--end-id\s+(\d+)', command)

        if not start_match or not end_match:
            return {'type': 'unknown', 'message': 'ID範囲を特定できません'}

        start_id = int(start_match.group(1))
        end_id = int(end_match.group(1))
        total_companies = end_id - start_id + 1

        # 出力から進行状況を解析
        progress_info = {
            'type': 'huganjob_unified_sender',
            'start_id': start_id,
            'end_id': end_id,
            'total_companies': total_companies,
            'processed_companies': 0,
            'success_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'bounced_count': 0,
            'unsubscribed_count': 0,
            'current_company': None,
            'progress_percent': 0.0,
            'estimated_remaining_time': 'N/A'
        }

        # 出力から処理済み企業数を解析
        lines = output.split('\n')
        for line in lines:
            # 送信開始メッセージを検索
            if '送信開始' in line and 'ID' in line:
                match = re.search(r'(\d+)/(\d+):\s*ID\s*(\d+)', line)
                if match:
                    current_index = int(match.group(1))
                    total_count = int(match.group(2))
                    current_id = int(match.group(3))

                    progress_info['processed_companies'] = current_index
                    progress_info['current_company'] = current_id
                    progress_info['progress_percent'] = round((current_index / total_count) * 100, 1)

            # 送信結果を解析
            elif '送信結果:' in line:
                if 'success' in line:
                    progress_info['success_count'] += 1
                elif 'failed' in line:
                    progress_info['failed_count'] += 1
                elif 'skipped' in line:
                    progress_info['skipped_count'] += 1
                elif 'bounced' in line:
                    progress_info['bounced_count'] += 1
                elif 'unsubscribed' in line:
                    progress_info['unsubscribed_count'] += 1

        # 残り時間を推定（5秒間隔で送信）
        remaining_companies = total_companies - progress_info['processed_companies']
        if remaining_companies > 0:
            estimated_seconds = remaining_companies * 5
            if estimated_seconds < 60:
                progress_info['estimated_remaining_time'] = f"{estimated_seconds}秒"
            elif estimated_seconds < 3600:
                minutes = estimated_seconds // 60
                progress_info['estimated_remaining_time'] = f"{minutes}分"
            else:
                hours = estimated_seconds // 3600
                minutes = (estimated_seconds % 3600) // 60
                progress_info['estimated_remaining_time'] = f"{hours}時間{minutes}分"
        else:
            progress_info['estimated_remaining_time'] = '完了'

        return progress_info

    except Exception as e:
        logger.error(f"進行状況解析エラー: {e}")
        return {'type': 'error', 'message': f'解析エラー: {e}'}

@app.route('/api/process_status/<process_id>')
def get_process_status(process_id):
    """プロセスの状態を取得（進行状況表示強化）"""
    if process_id not in running_processes:
        # 履歴から検索
        for history_process in process_history:
            if history_process.get('id') == process_id:
                return jsonify({
                    'status': history_process.get('status', 'unknown'),
                    'output': history_process.get('output', ''),
                    'error': history_process.get('error', ''),
                    'progress': history_process.get('progress', {}),
                    'duration': history_process.get('duration', 'N/A')
                })

        return jsonify({'success': False, 'message': 'プロセスが見つかりません'})

    process_info = running_processes[process_id]

    # 出力を取得
    output = process_info.get('output', '')

    # 🆕 HUGANJOB統合送信の進行状況を解析
    progress_info = analyze_huganjob_progress(process_info)

    # 状態を返す
    return jsonify({
        'status': process_info['status'],
        'output': output,
        'error': process_info.get('error', ''),
        'description': process_info.get('description', process_info['command']),
        'duration': str(datetime.datetime.now() - process_info['start_time']).split('.')[0],
        'progress': progress_info
    })



@app.route('/details/<step>')
def step_details(step):
    """ステップの詳細ページ"""
    progress_data = load_progress()
    step_info = get_step_info(step, progress_data)

    # ログファイルの内容を取得
    log_content = get_log_content_for_step(step)

    return render_template(
        'details.html',
        step=step_info,
        log_content=log_content,
        last_updated=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        get_step_display_name=get_step_display_name
    )



def get_log_content_for_step(step):
    """ステップに対応するログ内容を取得"""
    try:
        log_file = None
        if step == 'extract_emails':
            log_file = LOG_FILES['extraction']
        elif step == 'process_bounces':
            log_file = LOG_FILES['bounce']
        elif step == 'send_emails':
            log_file = LOG_FILES['email_sending']
        else:
            log_file = LOG_FILES['integrated']

        # ログファイルが存在する場合は内容を読み込み
        if log_file and os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 最新の100行を返す
                return ''.join(lines[-100:])
        else:
            return f"ログファイルが見つかりません: {log_file}"
    except Exception as e:
        return f"ログ読み込みエラー: {e}"

@app.route('/company/<int:company_id>')
def company_detail(company_id):
    """企業詳細ページ"""
    try:
        companies = load_company_data()

        # 指定されたIDの企業を検索
        company = None
        for c in companies:
            if int(c['id']) == company_id:
                company = c
                break

        if not company:
            abort(404)

        # デバッグ: 企業データの内容をログに出力
        logger.info(f"企業詳細ページ - 企業ID: {company_id}")
        logger.info(f"企業名: {company.get('name', 'N/A')}")
        logger.info(f"メールアドレス: {company.get('email', 'N/A')}")
        logger.info(f"メール抽出フラグ: {company.get('email_extracted', 'N/A')}")
        logger.info(f"信頼度: {company.get('email_confidence', 'N/A')}")
        logger.info(f"抽出方法: {company.get('extraction_method', 'N/A')}")

        # 開封状況を取得
        open_status = get_company_open_status_detail(company_id)

        return render_template(
            'company_detail.html',
            company=company,
            open_status=open_status,
            last_updated=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
    except Exception as e:
        logger.error(f"企業詳細ページでエラーが発生しました: {e}")
        return render_template('error.html', error=str(e)), 500

def run_process(command, args=None):
    """プロセスを実行"""
    try:
        # コマンドライン引数を構築
        cmd = ['python', command]

        # プロセス実行時の環境変数を設定
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONPATH'] = os.getcwd() + os.pathsep + env.get('PYTHONPATH', '')

        # analyze_websites_new_criteria.pyの場合は、適切な入力ファイルを指定
        if command == 'analyze_websites_new_criteria.py':
            # 引数を解析して、--input-fileが指定されていない場合は追加
            args_list = []
            if args:
                if isinstance(args, str):
                    args_list = args.split()
                elif isinstance(args, list):
                    args_list = args.copy()

            # --input-fileが指定されていない場合は追加
            if '--input-file' not in ' '.join(args_list):
                args_list.extend(['--input-file', INPUT_FILE])
                logger.info(f"ウェブサイト分析のため、入力ファイルパラメータを追加: {INPUT_FILE}")

            # 環境変数でエンコーディングを設定
            env['PYTHONIOENCODING'] = 'utf-8'

            cmd.extend(args_list)
        # 統合プロセス実行の場合の特別処理
        elif command == 'integrated_email_marketing_system.py':
            # 引数を文字列からリストに変換（文字列の場合）
            if isinstance(args, str):
                args_list = args.split()
            else:
                args_list = args if isinstance(args, list) else []

            # 新ダッシュボード用の統合プロセスでは、new_integrated_workflow.pyを使用
            logger.info("統合プロセス実行要求を新ダッシュボード用ワークフローに変更します")
            command = 'new_integrated_workflow.py'

            # 引数が空の場合はデフォルト引数を設定
            if not args_list:
                args_list = ['--start-id', '51', '--end-id', '60']
                logger.info(f"統合プロセスのため、デフォルト引数を設定: {args_list}")

            # new_integrated_workflow.pyは--input-fileパラメータを必要としない
            # （内部でnew_input_utf8.csvを自動使用するため）
            logger.info(f"new_integrated_workflow.pyは入力ファイルを自動検出します（--input-fileパラメータ不要）")

            cmd = ['python', command]
            cmd.extend(args_list)
        # new_integrated_workflow.pyの直接実行の場合も--input-fileを追加しない
        elif command == 'new_integrated_workflow.py':
            logger.info("new_integrated_workflow.pyの直接実行 - 入力ファイル自動検出")
            cmd = ['python', command]
            if args:
                if isinstance(args, str):
                    cmd.extend(args.split())
                elif isinstance(args, list):
                    cmd.extend(args)
        else:
            # その他のコマンドの場合は通常通り
            if args:
                if isinstance(args, str):
                    # 文字列の場合はスペースで分割
                    cmd.extend(args.split())
                elif isinstance(args, list):
                    cmd.extend(args)

        logger.info(f"プロセス実行: {' '.join(cmd)}")

        # プロセスを開始（リアルタイム出力対応）
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,  # テキストモードで実行
                encoding='utf-8',
                errors='replace',
                bufsize=1,  # 行バッファリング
                universal_newlines=True,
                cwd=os.getcwd(),
                env=env
            )
        except Exception as e:
            logger.error(f"プロセス開始エラー: {e}")
            raise

        # プロセス情報を記録
        process_id = str(process.pid)

        # 引数を文字列形式で保存（表示用）
        args_str = ""
        if args:
            if isinstance(args, list):
                args_str = " ".join(args)
            else:
                args_str = args

        # プロセス情報を記録
        running_processes[process_id] = {
            'process': process,
            'command': command,
            'args': args,
            'args_str': args_str,
            'start_time': datetime.datetime.now(),
            'status': 'running',
            'description': get_process_description(command, args),
            'output': ''
        }

        # 🆕 監視スレッドを開始（重要な修正）
        monitor_thread = threading.Thread(target=monitor_process, args=(process_id,))
        monitor_thread.daemon = True
        monitor_thread.start()

        logger.info(f"プロセス {process_id} の監視スレッドを開始しました")

        return process_id
    except Exception as e:
        logger.error(f"プロセス実行中にエラーが発生しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def get_process_description(command, args):
    """プロセスの日本語説明を生成"""
    description = ""

    # コマンドに基づいて基本説明を設定
    if command == 'prioritized_email_extractor.py':
        description = "メールアドレス抽出"
    elif command == 'new_email_extractor.py':
        description = "メールアドレス抽出"
    elif command == 'new_website_analyzer.py':
        description = "ウェブサイト分析"
    elif command == 'analyze_websites_new_criteria.py':
        description = "ウェブサイト分析"
    elif command == 'new_email_sender.py':
        description = "メール送信"
    elif command == 'enhanced_bounce_processor.py':
        description = "バウンス処理"
    elif command == 'standalone_bounce_processor.py':
        description = "HUGANJOB バウンス処理"
    elif command == 'huganjob_bounce_processor.py':
        description = "HUGANJOB バウンス処理"
    elif command == 'new_integrated_workflow.py':
        description = "統合ワークフロー実行"
    elif command == 'integrated_email_marketing_system.py':
        description = "統合プロセス実行"
    else:
        # その他のコマンドの場合はファイル名をそのまま使用
        description = command

    # 引数から企業ID範囲やバウンス処理パラメータを抽出
    start_id = None
    end_id = None
    days = None
    test_mode = False

    # 引数が文字列の場合はスペースで分割
    if isinstance(args, str):
        args_list = args.split()
    else:
        args_list = args if args else []

    # 各種パラメータを探す
    for i, arg in enumerate(args_list):
        if arg == '--start-id' and i + 1 < len(args_list):
            start_id = args_list[i + 1]
        elif arg == '--end-id' and i + 1 < len(args_list):
            end_id = args_list[i + 1]
        elif arg == '--days' and i + 1 < len(args_list):
            days = args_list[i + 1]
        elif arg == '--test-mode':
            test_mode = True

    # パラメータに応じて説明を追加
    if command == 'enhanced_bounce_processor.py' or command == 'standalone_bounce_processor.py' or command == 'huganjob_bounce_processor.py':
        if days:
            description += f" (過去{days}日間)"
        if test_mode:
            description += " [テストモード・移動なし]"
        else:
            description += " [処理済み移動あり]"
    elif start_id and end_id:
        description += f" (ID {start_id}-{end_id})"
    elif start_id:
        description += f" (ID {start_id}から)"

    return description

def monitor_process(process_id):
    """プロセスの監視（強化版）"""
    if process_id not in running_processes:
        logger.warning(f"プロセスID {process_id} が見つかりません。監視を終了します。")
        return

    process_info = running_processes[process_id]
    process = process_info['process']
    command = process_info['command']

    # 出力バッファ
    output_buffer = []

    # 🆕 プロセス監視強化: 定期的な生存確認
    last_alive_check = time.time()
    check_interval = 10  # 10秒間隔でプロセス生存確認

    try:
        logger.info(f"プロセス {process_id} ({command}) の監視を開始します")

        # 🆕 強化されたプロセス監視ループ
        process_info['status'] = 'running'

        while True:
            # 定期的なプロセス生存確認
            current_time = time.time()
            if current_time - last_alive_check >= check_interval:
                poll_result = process.poll()
                if poll_result is not None:
                    logger.info(f"プロセス {process_id} 終了検出（poll結果: {poll_result}）")
                    return_code = poll_result
                    break
                last_alive_check = current_time
                logger.debug(f"プロセス {process_id} 生存確認OK")

            # 出力読み取り（タイムアウト付き）
            try:
                line = process.stdout.readline()
                if line:
                    line = line.rstrip('\n\r')
                    if line:
                        output_buffer.append(line)
                        process_info['output'] = '\n'.join(output_buffer[-100:])
                        logger.info(f"プロセス {process_id}: {line}")
                        sys.stdout.flush()
                elif process.poll() is not None:
                    # 出力が空でプロセスが終了している
                    return_code = process.poll()
                    logger.info(f"プロセス {process_id} 出力終了で終了検出（終了コード: {return_code}）")
                    break
            except Exception as e:
                logger.warning(f"プロセス {process_id} 出力読み取りエラー: {e}")
                # エラーが発生してもプロセス終了チェックは継続
                if process.poll() is not None:
                    return_code = process.poll()
                    logger.info(f"プロセス {process_id} 例外後終了検出（終了コード: {return_code}）")
                    break

            # CPU使用率を下げるための短時間スリープ
            time.sleep(0.1)

        # プロセス完了処理
        if return_code == 0:
            process_info['status'] = 'completed'
            logger.info(f"プロセス {process_id} ({command}) が正常に完了しました")
        else:
            process_info['status'] = 'failed'
            # 実行時間が異常に短い場合は特別なエラーメッセージを追加
            duration = datetime.datetime.now() - process_info['start_time']
            if duration.total_seconds() < 5:
                error_msg = f"プロセス {process_id} ({command}) が異常に短時間で終了しました (実行時間: {duration.total_seconds():.1f}秒, 終了コード: {return_code})"
                logger.error(error_msg)
                logger.error("引数エラーまたは初期化エラーの可能性があります")
                logger.error(f"実行されたコマンド: python {command} {process_info.get('args_str', '')}")
                process_info['error'] = f"異常終了: 実行時間{duration.total_seconds():.1f}秒"
            else:
                logger.error(f"プロセス {process_id} ({command}) がエラーで終了しました (終了コード: {return_code})")

        process_info['end_time'] = datetime.datetime.now()
        process_info['return_code'] = return_code

        # 履歴に追加
        add_process_to_history(process_info.copy())

        # 🆕 即座に実行中プロセスから削除（遅延削除を廃止）
        if process_id in running_processes:
            logger.info(f"完了プロセス {process_id} を即座に削除します")
            del running_processes[process_id]

        # 🆕 プロセス終了通知（他のシステムコンポーネントへの通知）
        try:
            # プロセス終了イベントをファイルに記録（デバッグ用）
            completion_log = {
                'process_id': process_id,
                'command': command,
                'status': process_info['status'],
                'return_code': return_code,
                'end_time': process_info['end_time'].isoformat(),
                'duration': str(datetime.datetime.now() - process_info['start_time'])
            }

            # 完了ログファイルに記録
            completion_log_file = 'logs/process_completion.log'
            os.makedirs('logs', exist_ok=True)
            with open(completion_log_file, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.datetime.now().isoformat()}: {json.dumps(completion_log, ensure_ascii=False)}\n")

        except Exception as log_error:
            logger.warning(f"プロセス完了ログ記録エラー: {log_error}")

    except Exception as e:
        logger.error(f"プロセス {process_id} の監視中にエラーが発生しました: {e}")
        process_info['status'] = 'error'
        process_info['error'] = str(e)
        process_info['end_time'] = datetime.datetime.now()

        # 履歴に追加
        add_process_to_history(process_info.copy())

        # 🆕 エラープロセスも即座に削除
        if process_id in running_processes:
            logger.info(f"エラープロセス {process_id} を即座に削除します")
            del running_processes[process_id]

@app.route('/api/start_process', methods=['POST'])
def start_process():
    """プロセスを開始"""
    try:
        command = request.form.get('command')
        args = request.form.get('args', '')
        batch_mode = request.form.get('batch_mode', 'false').lower() == 'true'
        batch_size = int(request.form.get('batch_size', 20))

        if not command:
            return jsonify({'success': False, 'message': 'コマンドが指定されていません'})

        logger.info(f"プロセス開始要求: {command} {args} (バッチモード: {batch_mode})")

        # 100社以上の処理の場合、自動的にバッチモードを有効化
        if '--start-id' in args and '--end-id' in args:
            try:
                args_parts = args.split()
                start_idx = args_parts.index('--start-id') + 1
                end_idx = args_parts.index('--end-id') + 1
                start_id = int(args_parts[start_idx])
                end_id = int(args_parts[end_idx])
                range_size = end_id - start_id + 1

                if range_size >= 100:
                    batch_mode = True
                    logger.info(f"処理範囲が{range_size}社のため、自動的にバッチモードを有効化")
                elif range_size > 20 and not batch_mode:
                    logger.warning(f"処理範囲が{range_size}社です。安定性のためバッチモードを推奨します")
            except (ValueError, IndexError):
                pass

        # バッチモードが有効な場合、引数を調整
        if batch_mode and command == 'new_integrated_workflow.py':
            if '--batch-mode' not in args:
                args += ' --batch-mode'
            if '--batch-size' not in args:
                args += f' --batch-size {batch_size}'
            logger.info(f"バッチモード引数を追加: {args}")

        # プロセスを実行
        process_id = run_process(command, args)
        if not process_id:
            return jsonify({'success': False, 'message': 'プロセスの開始に失敗しました'})

        # 監視スレッドを開始
        monitor_thread = threading.Thread(target=monitor_process, args=(process_id,))
        monitor_thread.daemon = True
        monitor_thread.start()

        logger.info(f"プロセス {process_id} を開始しました: {command} {args}")

        return jsonify({
            'success': True,
            'message': f'プロセスを開始しました: {command}' + (' (バッチモード)' if batch_mode else ''),
            'process_id': process_id,
            'command': f"python {command} {args}".strip(),
            'batch_mode': batch_mode,
            'batch_size': batch_size if batch_mode else None
        })

    except Exception as e:
        logger.error(f"プロセス開始でエラーが発生しました: {e}")
        return jsonify({
            'success': False,
            'message': f'プロセス開始エラー: {e}'
        }), 500

@app.route('/api/stop_process/<process_id>', methods=['POST'])
def stop_process(process_id):
    """プロセスを停止"""
    try:
        if not process_id or process_id not in running_processes:
            return jsonify({'success': False, 'message': 'プロセスが見つかりません'})

        # 実際のプロセスを終了
        process_info = running_processes[process_id]
        if 'process' in process_info and process_info['process']:
            try:
                process_info['process'].terminate()
                logger.info(f"プロセス {process_id} を終了しました")
            except Exception as e:
                logger.warning(f"プロセス {process_id} の終了中にエラー: {e}")

        # プロセス情報を更新
        running_processes[process_id]['status'] = 'stopped'
        running_processes[process_id]['end_time'] = datetime.datetime.now()

        # 履歴を更新
        add_process_to_history(running_processes[process_id].copy())

        # 実行中プロセスから削除
        del running_processes[process_id]

        logger.info(f"プロセス {process_id} を停止しました")

        return jsonify({
            'success': True,
            'message': f'プロセス {process_id} を停止しました'
        })

    except Exception as e:
        logger.error(f"プロセス停止でエラーが発生しました: {e}")
        return jsonify({
            'success': False,
            'message': f'プロセス停止エラー: {e}'
        }), 500

@app.route('/api/update_process_status', methods=['POST'])
def update_process_status():
    """プロセス状態を手動で更新"""
    try:
        process_id = request.form.get('process_id')
        new_status = request.form.get('status', 'completed')

        if not process_id:
            return jsonify({'success': False, 'message': 'プロセスIDが指定されていません'})

        # プロセス履歴を読み込み
        global process_history
        load_process_history()

        # 該当するプロセスを検索して更新
        updated = False
        for i, process in enumerate(process_history):
            if process.get('id') == process_id:
                process_history[i]['status'] = new_status
                process_history[i]['end_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                updated = True
                break

        if updated:
            # 履歴を保存
            save_process_history()

            # 実行中プロセスからも削除
            if process_id in running_processes:
                del running_processes[process_id]

            logger.info(f"プロセス {process_id} の状態を {new_status} に更新しました")

            return jsonify({
                'success': True,
                'message': f'プロセス {process_id} の状態を更新しました'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'プロセスが見つかりませんでした'
            })

    except Exception as e:
        logger.error(f"プロセス状態更新でエラーが発生しました: {e}")
        return jsonify({
            'success': False,
            'message': f'プロセス状態更新エラー: {e}'
        }), 500

@app.route('/api/refresh_data', methods=['POST'])
def refresh_data():
    """データキャッシュをクリアして再読み込み"""
    try:
        global company_data_cache, company_data_last_updated

        # 統合プロセス実行後の自動更新かどうかを確認
        auto_refresh = request.form.get('auto_refresh', 'false').lower() == 'true'

        if auto_refresh:
            logger.info("統合プロセス完了後の自動データ更新を実行します")
        else:
            logger.info("手動データ更新を実行します")

        # キャッシュをクリア
        company_data_cache = None
        company_data_last_updated = None

        # データを再読み込み
        companies = load_company_data()

        # 統合プロセス後の場合は、ステータス統計を更新
        if auto_refresh:
            email_extracted_count = sum(1 for c in companies if c.get('email_extracted'))
            analyzed_count = sum(1 for c in companies if c.get('rank'))
            sent_count = sum(1 for c in companies if c.get('email_sent'))

            logger.info(f"統合プロセス後の状況: メール抽出={email_extracted_count}社, 分析完了={analyzed_count}社, 送信完了={sent_count}社")

        logger.info(f"データを再読み込みしました: {len(companies)}社")

        return jsonify({
            'success': True,
            'message': f'データを再読み込みしました（{len(companies)}社）',
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'auto_refresh': auto_refresh
        })

    except Exception as e:
        logger.error(f"データ再読み込み中にエラーが発生しました: {e}")
        return jsonify({
            'success': False,
            'message': f'データ再読み込みエラー: {e}'
        }), 500

@app.route('/control')
def control():
    """制御パネルページ（トップページにリダイレクト）"""
    return redirect('/')



@app.route('/api/get_process_history')
def get_process_history():
    """プロセス履歴を取得（軽量化版）"""
    try:
        limit = min(request.args.get('limit', 5, type=int), 10)  # 最大10件に制限

        # 軽量版履歴読み込み
        recent_history = load_process_history_lightweight(limit)

        return jsonify(recent_history)
    except Exception as e:
        logger.error(f"プロセス履歴取得エラー: {e}")
        return jsonify([])  # エラー時は空配列を返す

# 営業キャンペーン実行API - HUGANJOB専用システムでは削除済み
# 広告キャンペーンページ - HUGANJOB専用システムでは削除済み

def load_process_history_lightweight(limit=5):
    """軽量版プロセス履歴読み込み"""
    try:
        if not os.path.exists(PROCESS_HISTORY_FILE):
            return []

        # ファイルサイズをチェック（大きすぎる場合は末尾のみ読み込み）
        file_size = os.path.getsize(PROCESS_HISTORY_FILE)
        if file_size > 1024 * 1024:  # 1MB以上の場合
            # 末尾から読み込み
            with open(PROCESS_HISTORY_FILE, 'rb') as f:
                f.seek(-min(file_size, 50000), 2)  # 末尾50KB
                content = f.read().decode('utf-8', errors='ignore')
                lines = content.split('\n')[-limit*2:]  # 余裕を持って取得
        else:
            with open(PROCESS_HISTORY_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

        # JSON形式の行を解析
        history = []
        for line in reversed(lines):  # 新しい順
            if line.strip() and len(history) < limit:
                try:
                    entry = json.loads(line)
                    # 軽量化: 必要最小限の情報のみ
                    lightweight_entry = {
                        'id': entry.get('id', f"proc_{len(history)}"),
                        'command': entry.get('command', '不明')[:30] + '...' if len(entry.get('command', '')) > 30 else entry.get('command', '不明'),
                        'start_time': entry.get('start_time', '')[-8:] if entry.get('start_time') else '',  # 時刻のみ
                        'status': entry.get('status', '不明'),
                        'return_code': entry.get('return_code', None)
                    }
                    history.append(lightweight_entry)
                except json.JSONDecodeError:
                    continue

        return history
    except Exception as e:
        logger.error(f"軽量版履歴読み込みエラー: {e}")
        return []

@app.route('/daily_stats')
def daily_stats():
    """日別メール送信・バウンス統計ページ（キャッシュ対応）"""
    global daily_stats_cache, daily_stats_last_updated

    # クエリパラメータから期間を取得
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # デフォルトで過去30日間を表示
    if not start_date or not end_date:
        end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')

    # キャッシュキーを生成
    cache_key = f"{start_date}_{end_date}"

    # キャッシュチェック
    current_time = time.time()
    if (daily_stats_cache and
        daily_stats_last_updated and
        cache_key in daily_stats_cache and
        current_time - daily_stats_last_updated < DAILY_STATS_CACHE_TIMEOUT):

        logger.info("日別統計データをキャッシュから取得")
        cached_data = daily_stats_cache[cache_key]
        return render_template(
            'daily_stats.html',
            daily_stats=cached_data['daily_stats'],
            bounce_reason_stats=cached_data['bounce_reason_stats'],
            chart_data=cached_data['chart_data'],
            start_date=start_date,
            end_date=end_date,
            unified_total_sent=cached_data['unified_total_sent'],
            sorted_dates=cached_data.get('sorted_dates', []),
            total_stats=cached_data.get('total_stats', {}),
            actual_bounce_stats=cached_data.get('actual_bounce_stats', {})
        )

    # キャッシュがない場合は新規計算
    logger.info("日別統計データを新規計算中...")

    # 日別統計を取得（新しいダッシュボード用）
    daily_stats_data = get_daily_email_stats(start_date, end_date)

    # バウンス理由別統計を取得
    bounce_reason_stats = get_bounce_reason_statistics(start_date, end_date)

    # 日付順にソート
    sorted_dates = sorted(daily_stats_data.keys())

    # 統一された送信数を取得
    unified_total_sent = get_unified_sent_email_count()

    # チャート用データを準備
    chart_data = {
        'dates': sorted_dates,
        'total': [daily_stats_data[date]['total'] for date in sorted_dates],
        'success': [daily_stats_data[date]['success'] for date in sorted_dates],
        'bounce': [daily_stats_data[date]['bounce'] for date in sorted_dates],
        'pending': [daily_stats_data[date]['pending'] for date in sorted_dates]
    }

    # 実際のバウンス検知データを取得
    actual_bounce_stats = get_actual_bounce_statistics()

    # 合計統計を計算（統一送信数を使用）
    total_stats = {
        'total': unified_total_sent,  # 統一された送信数を使用
        'success': sum(daily_stats_data[date]['success'] for date in daily_stats_data),
        'bounce': actual_bounce_stats['total_bounces'],  # 実際のバウンス検知データを使用
        'pending': sum(daily_stats_data[date]['pending'] for date in daily_stats_data)
    }

    # キャッシュに保存
    if daily_stats_cache is None:
        daily_stats_cache = {}

    daily_stats_cache[cache_key] = {
        'daily_stats': daily_stats_data,
        'bounce_reason_stats': bounce_reason_stats,
        'chart_data': chart_data,
        'unified_total_sent': unified_total_sent,
        'sorted_dates': sorted_dates,
        'total_stats': total_stats,
        'actual_bounce_stats': actual_bounce_stats
    }
    daily_stats_last_updated = current_time

    logger.info(f"日別統計データをキャッシュに保存: {cache_key}")

    # 成功数を再計算（総送信数 - バウンス数 - 結果待ち）
    total_stats['success'] = total_stats['total'] - total_stats['bounce'] - total_stats['pending']

    # バウンス率と成功率を計算
    if total_stats['total'] > 0:
        total_stats['bounce_rate'] = round((total_stats['bounce'] / total_stats['total']) * 100, 1)
        total_stats['success_rate'] = round((total_stats['success'] / total_stats['total']) * 100, 1)
    else:
        total_stats['bounce_rate'] = 0.0
        total_stats['success_rate'] = 0.0

    # バウンス企業の詳細情報を取得
    bounce_companies = get_bounce_companies_details(start_date, end_date)

    return render_template(
        'daily_stats.html',
        daily_stats=daily_stats_data,
        sorted_dates=sorted_dates,
        chart_data=chart_data,
        total_stats=total_stats,
        bounce_reason_stats=bounce_reason_stats.get('reasons', {}),
        bounce_type_stats=bounce_reason_stats.get('types', {}),
        bounce_companies=bounce_companies,
        start_date=start_date,
        end_date=end_date,
        last_updated=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

def get_daily_email_stats(start_date, end_date):
    """日別メール送信統計を取得（新しいダッシュボード用・最適化版）"""
    try:
        daily_stats = {}

        # 日付範囲の初期化
        current_date = parse_datetime_optimized(start_date + ' 00:00:00') or datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = parse_datetime_optimized(end_date + ' 23:59:59') or datetime.datetime.strptime(end_date, '%Y-%m-%d')

        while current_date <= end_date_obj:
            date_str = current_date.strftime('%Y-%m-%d')
            daily_stats[date_str] = {
                'total': 0,
                'success': 0,
                'bounce': 0,
                'pending': 0
            }
            current_date += datetime.timedelta(days=1)

        # バウンス処理レポートファイルから統計を集計（安定版を使用）
        daily_stats = integrate_bounce_reports_to_daily_stats(daily_stats, start_date, end_date)

        # メール送信結果ファイルから統計を集計
        daily_stats = integrate_sending_results_to_daily_stats(daily_stats, start_date, end_date)

        return daily_stats

    except Exception as e:
        logger.error(f"日別統計の取得中にエラーが発生しました: {e}")
        import traceback
        logger.error(f"詳細なエラー情報: {traceback.format_exc()}")
        return {}

def integrate_bounce_reports_to_daily_stats(daily_stats, start_date, end_date):
    """バウンス処理レポートファイルから日別統計を集計"""
    try:
        import glob

        # バウンス処理レポートファイルを検索
        report_files = glob.glob('bounce_processing_report_*.json')

        if not report_files:
            logger.info("バウンス処理レポートファイルが見つかりません")
            return daily_stats

        logger.info(f"バウンス処理レポートファイル {len(report_files)}個を処理中")

        start_date_obj = parse_datetime_optimized(start_date + ' 00:00:00') or datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = parse_datetime_optimized(end_date + ' 23:59:59') or datetime.datetime.strptime(end_date, '%Y-%m-%d')

        for report_file in report_files:
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)

                # レポートの日時を解析
                timestamp_str = report_data.get('timestamp', '')
                if not timestamp_str:
                    continue

                # タイムスタンプをパース（最適化版）
                report_datetime = parse_datetime_optimized(timestamp_str)
                if report_datetime is None:
                    logger.warning(f"タイムスタンプの解析に失敗: {timestamp_str}")
                    continue

                # 指定期間内かチェック
                if not (start_date_obj <= report_datetime <= end_date_obj + datetime.timedelta(days=1)):
                    continue

                # 日付文字列を生成
                date_str = report_datetime.strftime('%Y-%m-%d')

                if date_str in daily_stats:
                    # バウンス統計を追加
                    total_bounces = report_data.get('total_bounces_detected', 0)
                    emails_moved = report_data.get('emails_moved', 0)

                    daily_stats[date_str]['bounce'] += total_bounces
                    daily_stats[date_str]['total'] += total_bounces

                    logger.debug(f"日付 {date_str}: バウンス {total_bounces}件, 移動 {emails_moved}件を追加")

            except Exception as e:
                logger.error(f"レポートファイル {report_file} の処理中にエラー: {e}")
                continue

        return daily_stats

    except Exception as e:
        logger.error(f"バウンス処理レポートの統合中にエラー: {e}")
        return daily_stats

def integrate_sending_results_to_daily_stats(daily_stats, start_date, end_date):
    """メール送信結果ファイルから日別統計を集計"""
    try:
        import glob

        # メール送信結果ファイルを検索
        sending_files = []

        # 優先順位でファイルを検索
        primary_file = 'new_email_sending_results.csv'
        if os.path.exists(primary_file):
            sending_files.append(primary_file)
        else:
            # ID範囲別ファイルを検索
            id_files = glob.glob('sent_emails_record_id*.csv')
            if id_files:
                sending_files.extend(id_files)
            elif os.path.exists(NEW_EMAIL_SENDING_RESULTS):
                sending_files.append(NEW_EMAIL_SENDING_RESULTS)

        if not sending_files:
            logger.info("メール送信結果ファイルが見つかりません")
            return daily_stats

        logger.info(f"メール送信結果ファイル {len(sending_files)}個を処理中")

        start_date_obj = parse_datetime_optimized(start_date + ' 00:00:00') or datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = parse_datetime_optimized(end_date + ' 23:59:59') or datetime.datetime.strptime(end_date, '%Y-%m-%d')

        for sending_file in sending_files:
            try:
                with open(sending_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)

                    for row in reader:
                        # 複数の列名に対応
                        sent_date_str = (row.get('送信日時', '') or
                                       row.get('send_datetime', '') or
                                       row.get('sent_date', '')).strip()
                        if not sent_date_str:
                            continue

                        # 送信日時を解析（最適化版）
                        try:
                            sent_datetime = parse_datetime_optimized(sent_date_str)
                            if sent_datetime is None:
                                if not PERFORMANCE_MODE:  # パフォーマンス重視モードでは警告を抑制
                                    logger.warning(f"送信日時の解析に失敗: {sent_date_str}")
                                continue
                        except Exception as e:
                            logger.warning(f"送信日時の解析エラー: {sent_date_str}, {e}")
                            continue

                        # 指定期間内かチェック
                        if not (start_date_obj <= sent_datetime <= end_date_obj + datetime.timedelta(days=1)):
                            continue

                        # 日付文字列を生成
                        date_str = sent_datetime.strftime('%Y-%m-%d')

                        if date_str in daily_stats:
                            # 送信結果を分類（複数の列名に対応）
                            sent_result = (row.get('送信結果', '') or
                                         row.get('success', '') or
                                         row.get('sent_result', '') or
                                         str(row.get('success', ''))).strip()
                            bounce_status = (row.get('バウンス状態', '') or
                                           row.get('bounce_status', '') or
                                           row.get('error_message', '')).strip()
                            final_status = row.get('最終ステータス', '').strip()
                            company_id = (row.get('企業ID', '') or
                                        row.get('company_id', '')).strip()

                            daily_stats[date_str]['total'] += 1

                            # 実際のバウンス検知データをチェック
                            actual_bounce_status = check_actual_bounce_status(company_id)

                            if actual_bounce_status or bounce_status == 'バウンス' or final_status == 'バウンス':
                                daily_stats[date_str]['bounce'] += 1
                            elif sent_result == 'success':
                                daily_stats[date_str]['success'] += 1
                            else:
                                daily_stats[date_str]['pending'] += 1

                            if ENABLE_DEBUG_LOGGING:
                                logger.debug(f"日付 {date_str}: 送信結果 {sent_result}, 実際のバウンス {actual_bounce_status}")

            except Exception as e:
                logger.error(f"送信結果ファイル {sending_file} の処理中にエラー: {e}")
                continue

        return daily_stats

    except Exception as e:
        logger.error(f"メール送信結果の統合中にエラー: {e}")
        return daily_stats

def get_bounce_reason_statistics(start_date, end_date):
    """バウンス理由別統計を取得"""
    try:
        import glob

        bounce_reasons = {}
        bounce_types = {'permanent': 0, 'temporary': 0, 'unknown': 0}
        start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d')

        # バウンス処理レポートファイルから理由別統計を集計
        report_files = glob.glob('huganjob_bounce_report_*.json')

        for report_file in report_files:
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)

                # レポートの日時を解析
                timestamp_str = report_data.get('timestamp', '')
                if not timestamp_str:
                    continue

                try:
                    report_datetime = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        report_datetime = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M')
                    except ValueError:
                        continue

                # 指定期間内かチェック
                if not (start_date_obj <= report_datetime <= end_date_obj + datetime.timedelta(days=1)):
                    continue

                # バウンス詳細から理由別統計を集計
                bounce_details = report_data.get('bounce_details', [])
                for detail in bounce_details:
                    reason = detail.get('reason', '不明なバウンス理由')
                    bounce_type = detail.get('bounce_type', 'unknown')

                    if reason not in bounce_reasons:
                        bounce_reasons[reason] = 0
                    bounce_reasons[reason] += 1

                    # バウンスタイプ別統計も集計
                    if bounce_type in bounce_types:
                        bounce_types[bounce_type] += 1
                    else:
                        bounce_types['unknown'] += 1

            except Exception as e:
                logger.error(f"バウンス理由統計ファイル {report_file} の処理中にエラー: {e}")
                continue

        # バウンス追跡結果ファイルからも理由を集計
        bounce_files = ['comprehensive_bounce_tracking_results.csv', NEW_BOUNCE_TRACKING]

        for bounce_file in bounce_files:
            if not os.path.exists(bounce_file):
                continue

            try:
                with open(bounce_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)

                    for row in reader:
                        bounce_date_str = row.get('バウンス日時', '').strip()
                        if not bounce_date_str:
                            continue

                        # バウンス日時を解析
                        try:
                            for date_format in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']:
                                try:
                                    bounce_datetime = datetime.datetime.strptime(bounce_date_str, date_format)
                                    break
                                except ValueError:
                                    continue
                            else:
                                continue
                        except Exception:
                            continue

                        # 指定期間内かチェック
                        if not (start_date_obj <= bounce_datetime <= end_date_obj + datetime.timedelta(days=1)):
                            continue

                        reason = row.get('バウンス理由', '不明なバウンス理由').strip()
                        bounce_type = row.get('バウンスタイプ', 'unknown').strip()

                        if not reason:
                            reason = '不明なバウンス理由'

                        if reason not in bounce_reasons:
                            bounce_reasons[reason] = 0
                        bounce_reasons[reason] += 1

                        # バウンスタイプ別統計も集計
                        if bounce_type in bounce_types:
                            bounce_types[bounce_type] += 1
                        else:
                            bounce_types['unknown'] += 1

            except Exception as e:
                logger.error(f"バウンス追跡ファイル {bounce_file} の処理中にエラー: {e}")
                continue

        # CSVファイルから直接バウンス統計を取得
        csv_bounce_stats = get_csv_bounce_statistics(start_date, end_date)

        # CSVファイルの統計をマージ
        for reason, count in csv_bounce_stats['reasons'].items():
            if reason not in bounce_reasons:
                bounce_reasons[reason] = 0
            bounce_reasons[reason] += count

        for bounce_type, count in csv_bounce_stats['types'].items():
            if bounce_type in bounce_types:
                bounce_types[bounce_type] += count

        # 結果にバウンスタイプ別統計を含める
        return {
            'reasons': bounce_reasons,
            'types': bounce_types,
            'total_bounces': sum(bounce_types.values())
        }

    except Exception as e:
        logger.error(f"バウンス理由統計の取得中にエラー: {e}")
        return {'reasons': {}, 'types': {'permanent': 0, 'temporary': 0, 'unknown': 0}, 'total_bounces': 0}

def get_csv_bounce_statistics(start_date, end_date):
    """CSVファイルから直接バウンス統計を取得"""
    try:
        bounce_reasons = {}
        bounce_types = {'permanent': 0, 'temporary': 0, 'unknown': 0}

        start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d')

        # 企業データCSVファイルからバウンス情報を読み取り
        csv_file = 'data/new_input_test.csv'
        if not os.path.exists(csv_file):
            return {'reasons': bounce_reasons, 'types': bounce_types}

        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                bounce_status = row.get('バウンス状態', '').strip()
                bounce_date_str = row.get('バウンス日時', '').strip()
                bounce_reason = row.get('バウンス理由', '').strip()

                # バウンス状態がない場合はスキップ
                if not bounce_status or bounce_status.lower() in ['', 'none', 'null']:
                    continue

                # バウンス日時がある場合は期間チェック
                if bounce_date_str:
                    try:
                        for date_format in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']:
                            try:
                                bounce_datetime = datetime.datetime.strptime(bounce_date_str, date_format)
                                break
                            except ValueError:
                                continue
                        else:
                            continue

                        # 指定期間内かチェック
                        if not (start_date_obj <= bounce_datetime <= end_date_obj + datetime.timedelta(days=1)):
                            continue
                    except Exception:
                        continue

                # バウンス理由別統計
                if not bounce_reason:
                    bounce_reason = '不明なバウンス理由'

                if bounce_reason not in bounce_reasons:
                    bounce_reasons[bounce_reason] = 0
                bounce_reasons[bounce_reason] += 1

                # バウンスタイプ別統計
                if bounce_status.lower() in ['permanent', 'temporary', 'unknown']:
                    bounce_types[bounce_status.lower()] += 1
                else:
                    bounce_types['unknown'] += 1

        return {'reasons': bounce_reasons, 'types': bounce_types}

    except Exception as e:
        logger.error(f"CSV バウンス統計の取得中にエラー: {e}")
        return {'reasons': {}, 'types': {'permanent': 0, 'temporary': 0, 'unknown': 0}}

def get_actual_bounce_statistics():
    """実際のバウンス検知データから統計を取得"""
    try:
        total_bounces = 0
        bounce_types = {'permanent': 0, 'temporary': 0, 'unknown': 0}

        # 企業データCSVファイルからバウンス情報を読み取り
        csv_file = 'data/new_input_test.csv'
        if not os.path.exists(csv_file):
            return {'total_bounces': 0, 'types': bounce_types}

        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                bounce_status = row.get('バウンス状態', '').strip()

                # バウンス状態がある場合はカウント
                if bounce_status and bounce_status.lower() not in ['', 'none', 'null']:
                    total_bounces += 1

                    # バウンスタイプ別統計
                    if bounce_status.lower() in ['permanent', 'temporary', 'unknown']:
                        bounce_types[bounce_status.lower()] += 1
                    else:
                        bounce_types['unknown'] += 1

        logger.info(f"実際のバウンス統計: 総バウンス数={total_bounces}, Permanent={bounce_types['permanent']}, Temporary={bounce_types['temporary']}, Unknown={bounce_types['unknown']}")

        return {
            'total_bounces': total_bounces,
            'types': bounce_types
        }

    except Exception as e:
        logger.error(f"実際のバウンス統計の取得中にエラー: {e}")
        return {'total_bounces': 0, 'types': {'permanent': 0, 'temporary': 0, 'unknown': 0}}

def check_actual_bounce_status(company_id):
    """指定された企業IDの実際のバウンス状態をチェック"""
    try:
        csv_file = 'data/new_input_test.csv'
        if not os.path.exists(csv_file):
            return False

        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                if row.get('ID', '').strip() == str(company_id):
                    bounce_status = row.get('バウンス状態', '').strip()
                    return bounce_status and bounce_status.lower() not in ['', 'none', 'null']

        return False

    except Exception as e:
        logger.error(f"企業ID {company_id} のバウンス状態チェック中にエラー: {e}")
        return False

def get_bounce_companies_details(start_date, end_date):
    """バウンス企業の詳細情報を取得"""
    try:
        bounce_companies = []
        start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d')

        # 企業データCSVファイルからバウンス企業を読み取り
        csv_file = 'data/new_input_test.csv'
        if not os.path.exists(csv_file):
            return bounce_companies

        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                bounce_status = row.get('バウンス状態', '').strip()
                bounce_date_str = row.get('バウンス日時', '').strip()

                # バウンス状態がない場合はスキップ
                if not bounce_status or bounce_status.lower() in ['', 'none', 'null']:
                    continue

                # バウンス日時がある場合は期間チェック
                if bounce_date_str:
                    try:
                        for date_format in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']:
                            try:
                                bounce_datetime = datetime.datetime.strptime(bounce_date_str, date_format)
                                break
                            except ValueError:
                                continue
                        else:
                            continue

                        # 指定期間内かチェック
                        if not (start_date_obj <= bounce_datetime <= end_date_obj + datetime.timedelta(days=1)):
                            continue
                    except Exception:
                        continue

                # バウンス企業情報を追加
                bounce_companies.append({
                    'id': row.get('ID', ''),
                    'company_name': row.get('企業名', ''),
                    'email': row.get('担当者メールアドレス', ''),
                    'job_position': row.get('募集職種', ''),
                    'bounce_type': bounce_status,
                    'bounce_date': bounce_date_str,
                    'bounce_reason': row.get('バウンス理由', ''),
                    'website': row.get('企業ホームページ', '')
                })

        # バウンス日時でソート（新しい順）
        bounce_companies.sort(key=lambda x: x.get('bounce_date', ''), reverse=True)

        return bounce_companies

    except Exception as e:
        logger.error(f"バウンス企業詳細の取得中にエラー: {e}")
        return []

@app.route('/api/get_daily_stats')
def get_daily_stats_api():
    """日別統計データを取得(AJAX用)"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    daily_stats = get_daily_email_stats(start_date, end_date)
    bounce_reason_stats = get_bounce_reason_statistics(start_date, end_date)

    # 日付順にソート
    sorted_dates = sorted(daily_stats.keys())

    # 実際のバウンス検知データを取得
    actual_bounce_stats = get_actual_bounce_statistics()

    # 合計統計を計算（統一送信数を使用）
    unified_total_sent = get_unified_sent_email_count()
    total_stats = {
        'total': unified_total_sent,  # 統一された送信数を使用
        'success': sum(daily_stats[date]['success'] for date in daily_stats),
        'bounce': actual_bounce_stats['total_bounces'],  # 実際のバウンス検知データを使用
        'pending': sum(daily_stats[date]['pending'] for date in daily_stats)
    }

    # 成功数を再計算（総送信数 - バウンス数 - 結果待ち）
    total_stats['success'] = total_stats['total'] - total_stats['bounce'] - total_stats['pending']

    # バウンス率と成功率を計算
    if total_stats['total'] > 0:
        total_stats['bounce_rate'] = round((total_stats['bounce'] / total_stats['total']) * 100, 1)
        total_stats['success_rate'] = round((total_stats['success'] / total_stats['total']) * 100, 1)
    else:
        total_stats['bounce_rate'] = 0.0
        total_stats['success_rate'] = 0.0

    # API用データを準備
    result = {
        'dates': sorted_dates,
        'data': [daily_stats[date] for date in sorted_dates],
        'total_stats': total_stats,
        'bounce_reason_stats': bounce_reason_stats.get('reasons', {}),
        'bounce_type_stats': bounce_reason_stats.get('types', {}),
        'total_bounces': bounce_reason_stats.get('total_bounces', 0)
    }

    return jsonify(result)

@app.route('/auto_contact_results')
def auto_contact_results():
    """自動問い合わせ結果ページ"""
    try:
        # 自動問い合わせ結果を読み込み
        results = load_auto_contact_results()

        # 統計情報を計算
        stats = calculate_auto_contact_stats(results)

        return render_template(
            'auto_contact_results.html',
            results=results,
            stats=stats,
            last_updated=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

    except Exception as e:
        logger.error(f"自動問い合わせ結果ページエラー: {e}")
        return render_template('error.html', error=str(e))

def load_auto_contact_results():
    """自動問い合わせ結果を読み込み"""
    try:
        results_file = 'auto_contact_results.csv'

        if not os.path.exists(results_file):
            return []

        results = []
        with open(results_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(row)

        # 処理日時でソート（新しい順）
        results.sort(key=lambda x: x.get('処理日時', ''), reverse=True)

        return results

    except Exception as e:
        logger.error(f"自動問い合わせ結果読み込みエラー: {e}")
        return []

def calculate_auto_contact_stats(results):
    """自動問い合わせ統計を計算"""
    try:
        if not results:
            return {
                'total_processed': 0,
                'contact_page_found': 0,
                'form_detected': 0,
                'form_filled': 0,
                'form_submitted': 0,
                'confirmation_received': 0,
                'success_rate': 0.0,
                'recent_results': []
            }

        total = len(results)
        contact_page_found = sum(1 for r in results if r.get('問い合わせページ検出') == 'True')
        form_detected = sum(1 for r in results if r.get('フォーム検出') == 'True')
        form_filled = sum(1 for r in results if r.get('フォーム入力') == 'True')
        form_submitted = sum(1 for r in results if r.get('フォーム送信') == 'True')
        confirmation_received = sum(1 for r in results if r.get('確認メール受信') == 'True')

        success_rate = (form_filled / total * 100) if total > 0 else 0.0

        # 最近の結果（最新10件）
        recent_results = results[:10]

        return {
            'total_processed': total,
            'contact_page_found': contact_page_found,
            'form_detected': form_detected,
            'form_filled': form_filled,
            'form_submitted': form_submitted,
            'confirmation_received': confirmation_received,
            'success_rate': round(success_rate, 1),
            'recent_results': recent_results
        }

    except Exception as e:
        logger.error(f"自動問い合わせ統計計算エラー: {e}")
        return {
            'total_processed': 0,
            'contact_page_found': 0,
            'form_detected': 0,
            'form_filled': 0,
            'form_submitted': 0,
            'confirmation_received': 0,
            'success_rate': 0.0,
            'recent_results': []
        }

@app.route('/api/get_progress')
def get_progress():
    """進捗情報を取得（AJAX用）"""
    try:
        progress_data = load_progress()
        return jsonify(progress_data)
    except Exception as e:
        logger.error(f"進捗情報取得エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_email_stats')
def get_email_stats():
    """メール統計情報を取得（AJAX用）"""
    try:
        stats = get_basic_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"メール統計取得エラー: {e}")
        return jsonify({'error': str(e)}), 500

# /api/bounce-details エンドポイントは削除されました（bounce-analysis ページが不要なため）

# bounce-analysis ページは削除されました（不要なため）

@app.route('/api/get_processes')
def get_processes():
    """プロセス情報を取得（AJAX用）"""
    try:
        # 🆕 プロセス状態同期を実行
        sync_process_states()

        # 🆕 監視されていないプロセスに監視を追加
        fix_unmonitored_processes()

        processes = []
        current_time = datetime.datetime.now()

        for pid, info in running_processes.items():
            # 実行中のプロセスまたは最近完了したプロセスを表示
            show_process = False

            if info['status'] == 'running':
                show_process = True
            elif info['status'] in ['completed', 'failed', 'error']:
                # 完了から5分以内のプロセスは表示を継続
                end_time = info.get('end_time')
                if end_time and (current_time - end_time).total_seconds() < 300:  # 5分 = 300秒
                    show_process = True

            if show_process:
                # プロセス説明を生成
                description = get_process_description(info['command'], info.get('args', ''))

                # 実行時間を計算
                if info['status'] == 'running':
                    duration = str(current_time - info['start_time']).split('.')[0]
                else:
                    end_time = info.get('end_time', current_time)
                    duration = str(end_time - info['start_time']).split('.')[0]

                processes.append({
                    'id': pid,
                    'command': info['command'],
                    'args': info.get('args_str', info.get('args', '')),
                    'description': description,
                    'start_time': info['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
                    'status': info['status'],
                    'duration': duration,
                    'output': info.get('output', ''),  # リアルタイム出力を追加
                    'error': info.get('error', '')  # エラー情報も追加
                })

        return jsonify(processes)
    except Exception as e:
        logger.error(f"プロセス情報取得エラー: {e}")
        return jsonify([])

@app.route('/api/get_process_output/<process_id>')
def get_process_output(process_id):
    """特定のプロセスの出力を取得"""
    try:
        if process_id in running_processes:
            process_info = running_processes[process_id]
            return jsonify({
                'success': True,
                'process_id': process_id,
                'output': process_info.get('output', ''),
                'status': process_info.get('status', 'unknown'),
                'start_time': process_info['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'duration': str(datetime.datetime.now() - process_info['start_time']).split('.')[0],
                'error': process_info.get('error', '')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'プロセスが見つかりません'
            })
    except Exception as e:
        logger.error(f"プロセス出力取得エラー: {e}")
        return jsonify({
            'success': False,
            'message': f'エラー: {e}'
        })



@app.route('/api/process_batch_range', methods=['POST'])
def process_batch_range():
    """100社単位でのバッチ処理を実行"""
    try:
        data = request.get_json() if request.is_json else request.form
        start_id = int(data.get('start_id', 1))
        end_id = int(data.get('end_id', 100))
        batch_size = int(data.get('batch_size', 20))
        process_type = data.get('process_type', 'full_workflow')  # full_workflow, email_extraction, website_analysis, email_sending

        range_size = end_id - start_id + 1
        logger.info(f"バッチ処理を開始します: ID {start_id}-{end_id} ({range_size}社), バッチサイズ: {batch_size}")

        # HUGANJOB専用プロセスタイプに応じてコマンドを構築
        if process_type == 'huganjob_email_resolution':
            command = 'huganjob_email_address_resolver.py'
            args = f'--start-id {start_id} --end-id {end_id}'
        elif process_type == 'huganjob_bulk_sending':
            command = 'huganjob_bulk_email_sender.py'
            args = f'--start-id {start_id} --end-id {end_id} --max-emails {end_id - start_id + 1}'
        elif process_type == 'huganjob_test_sending':
            command = 'huganjob_test_sender.py'
            args = f'--start-id {start_id} --end-id {end_id}'
        elif process_type == 'huganjob_full_workflow':
            command = 'huganjob_bulk_email_sender.py'
            args = f'--start-id {start_id} --end-id {end_id}'
        else:
            return jsonify({'success': False, 'message': f'不明なHUGANJOBプロセスタイプ: {process_type}'})

        # プロセスを実行
        process_id = run_process(command, args)
        if not process_id:
            return jsonify({'success': False, 'message': 'バッチ処理の開始に失敗しました'})

        # 監視スレッドを開始
        monitor_thread = threading.Thread(target=monitor_process, args=(process_id,))
        monitor_thread.daemon = True
        monitor_thread.start()

        logger.info(f"バッチ処理プロセス {process_id} を開始しました: {process_type}")

        return jsonify({
            'success': True,
            'message': f'{process_type}バッチ処理を開始しました (ID {start_id}-{end_id}, {range_size}社)',
            'process_id': process_id,
            'process_type': process_type,
            'range_size': range_size,
            'batch_size': batch_size,
            'estimated_batches': (range_size + batch_size - 1) // batch_size
        })

    except Exception as e:
        logger.error(f"バッチ処理開始でエラーが発生しました: {e}")
        return jsonify({
            'success': False,
            'message': f'バッチ処理開始エラー: {e}'
        }), 500

@app.route('/api/reset_progress', methods=['POST'])
def reset_progress():
    """進捗情報をリセット"""
    try:
        # 進捗ファイルを初期化
        progress = {
            "extract_emails": {"status": "not_started", "progress": 0, "last_updated": None},
            "analyze_websites": {"status": "not_started", "progress": 0, "last_updated": None},
            "prepare_email_content": {"status": "not_started", "progress": 0, "last_updated": None},
            "send_emails": {"status": "not_started", "progress": 0, "last_updated": None},
            "process_bounces": {"status": "not_started", "progress": 0, "last_updated": None},
            "analyze_results": {"status": "not_started", "progress": 0, "last_updated": None}
        }

        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

        logger.info("進捗情報をリセットしました")

        return jsonify({
            'success': True,
            'message': '進捗情報をリセットしました'
        })
    except Exception as e:
        logger.error(f"進捗リセットエラー: {e}")
        return jsonify({
            'success': False,
            'message': f'進捗リセットエラー: {e}'
        }), 500

@app.route('/api/refresh', methods=['POST'])
def api_refresh_data():
    """データリフレッシュ（キャッシュクリア）"""
    try:
        clear_all_caches()
        return jsonify({
            'success': True,
            'message': 'データキャッシュをクリアしました'
        })
    except Exception as e:
        logger.error(f"データリフレッシュエラー: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/consolidate_files', methods=['POST'])
def consolidate_files():
    """ウェブサイト分析結果ファイルを統合"""
    try:
        # ファイル統合処理（実装は省略）
        return jsonify({
            'success': True,
            'message': 'ファイル統合が完了しました',
            'output_file': 'new_website_analysis_results_latest.csv',
            'archived_count': 0
        })
    except Exception as e:
        logger.error(f"ファイル統合でエラーが発生しました: {e}")
        return jsonify({
            'success': False,
            'message': f'ファイル統合エラー: {e}'
        }), 500

@app.route('/api/companies')
def get_companies_api():
    """企業データを取得（API用）"""
    try:
        companies = load_company_data()
        return jsonify({
            'success': True,
            'companies': companies,
            'total': len(companies)
        })
    except Exception as e:
        logger.error(f"企業データ取得エラー: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# manual ページは削除されました（不要なため）

# ===== 問い合わせフォーム自動入力機能 =====

@app.route('/contact-form')
def contact_form_page():
    """問い合わせフォーム自動入力ページ"""
    try:
        # バウンス企業数の取得（簡略化）
        bounce_stats = {'total_candidates': 0, 'valid_bounces': 0}

        # 問い合わせフォーム処理結果の取得
        contact_form_stats = get_contact_form_stats()

        return render_template(
            'contact_form.html',
            bounce_stats=bounce_stats,
            contact_form_stats=contact_form_stats,
            last_updated=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
    except Exception as e:
        logger.error(f"問い合わせフォームページエラー: {e}")
        return f"エラーが発生しました: {str(e)}", 500

@app.route('/api/contact_form_execute', methods=['POST'])
def contact_form_execute():
    """問い合わせフォーム自動入力を実行"""
    try:
        data = request.get_json() if request.is_json else request.form
        start_id = int(data.get('start_id', 1))
        end_id = int(data.get('end_id', 10))
        max_companies = int(data.get('max_companies', 10))
        test_mode = data.get('test_mode', 'true').lower() == 'true'

        # プロセスIDの生成
        process_id = str(uuid.uuid4())

        # コマンドの構築
        command = f"python contact_form_automation.py --start-id {start_id} --end-id {end_id} --max-companies {max_companies}"
        if test_mode:
            command += " --test-mode"
        command += " --headless"

        # バックグラウンドでプロセスを開始
        def run_contact_form_process():
            try:
                logger.info(f"問い合わせフォーム処理開始: {command}")

                # プロセス情報を記録
                running_processes[process_id] = {
                    'id': process_id,
                    'command': command,
                    'description': f"問い合わせフォーム自動入力 (ID {start_id}-{end_id})",
                    'start_time': datetime.datetime.now(),
                    'status': 'running',
                    'output': [],
                    'pid': None
                }

                # 実際のプロセス実行
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    cwd=os.getcwd()
                )

                running_processes[process_id]['pid'] = process.pid

                # 出力を読み取り
                for line in iter(process.stdout.readline, ''):
                    if line:
                        running_processes[process_id]['output'].append(line.strip())
                        logger.info(f"問い合わせフォーム処理: {line.strip()}")

                # プロセス完了
                process.wait()

                if process.returncode == 0:
                    running_processes[process_id]['status'] = 'completed'
                    logger.info(f"問い合わせフォーム処理完了: {process_id}")
                else:
                    running_processes[process_id]['status'] = 'failed'
                    logger.error(f"問い合わせフォーム処理失敗: {process_id}")

                running_processes[process_id]['end_time'] = datetime.datetime.now()

                # 履歴に追加
                process_history.append(running_processes[process_id].copy())

                # 一定時間後にrunning_processesから削除
                threading.Timer(300, lambda: running_processes.pop(process_id, None)).start()

            except Exception as e:
                logger.error(f"問い合わせフォーム処理エラー: {e}")
                if process_id in running_processes:
                    running_processes[process_id]['status'] = 'failed'
                    running_processes[process_id]['error'] = str(e)

        # バックグラウンドスレッドで実行
        thread = threading.Thread(target=run_contact_form_process)
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': '問い合わせフォーム自動入力を開始しました',
            'process_id': process_id
        })

    except Exception as e:
        logger.error(f"問い合わせフォーム実行エラー: {e}")
        return jsonify({
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500

def get_contact_form_stats():
    """問い合わせフォーム処理統計を取得"""
    try:
        stats = {
            'total_processed': 0,
            'form_detected': 0,
            'form_filled': 0,
            'form_submitted': 0,
            'success_rate': 0,
            'recent_results': []
        }

        # 結果ファイルの検索
        results_dir = 'contact_form_results'
        if os.path.exists(results_dir):
            result_files = [f for f in os.listdir(results_dir) if f.endswith('.csv')]

            if result_files:
                # 最新のファイルを読み込み
                latest_file = max(result_files)
                file_path = os.path.join(results_dir, latest_file)

                df = pd.read_csv(file_path, encoding='utf-8-sig')

                stats['total_processed'] = len(df)
                stats['form_detected'] = len(df[df['フォーム検出'] == True])
                stats['form_filled'] = len(df[df['フォーム入力'] == True])
                stats['form_submitted'] = len(df[df['フォーム送信'] == True])

                if stats['total_processed'] > 0:
                    stats['success_rate'] = (stats['form_submitted'] / stats['total_processed']) * 100

                # 最新の結果（最大10件）
                stats['recent_results'] = df.tail(10).to_dict('records')

        return stats

    except Exception as e:
        logger.error(f"問い合わせフォーム統計取得エラー: {e}")
        return {
            'total_processed': 0,
            'form_detected': 0,
            'form_filled': 0,
            'form_submitted': 0,
            'success_rate': 0,
            'recent_results': []
        }



def record_email_open(tracking_id, request_obj):
    """メール開封を記録（重複チェック付き）"""
    try:
        # 既に開封記録があるかチェック
        if is_already_opened(tracking_id):
            logger.info(f"既に開封済み: {tracking_id}")
            return

        # デバイスタイプを判定
        user_agent = request_obj.environ.get('HTTP_USER_AGENT', '')
        device_type = detect_device_type(user_agent)

        # 開封情報を準備（秒まで含む正確な時刻）
        now = datetime.datetime.now()
        open_record = {
            'tracking_id': tracking_id,
            'opened_at': now.strftime('%Y-%m-%d %H:%M:%S'),
            'ip_address': request_obj.environ.get('REMOTE_ADDR', ''),
            'device_type': device_type,
            'user_agent': user_agent[:200] if user_agent else ''  # 長すぎる場合は切り詰め
        }

        # 開封追跡ファイルに記録
        save_email_open_record(open_record)

        logger.info(f"メール開封を記録しました: {tracking_id} at {now}")

    except Exception as e:
        logger.error(f"開封記録の保存エラー: {e}")

def is_already_opened(tracking_id):
    """指定されたトラッキングIDが既に開封済みかチェック"""
    try:
        if not os.path.exists(NEW_EMAIL_OPEN_TRACKING):
            return False

        with open(NEW_EMAIL_OPEN_TRACKING, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('tracking_id', '') == tracking_id:
                    return True
        return False
    except Exception as e:
        logger.error(f"開封状況チェックエラー: {e}")
        return False

def detect_device_type(user_agent):
    """User-Agentからデバイスタイプを判定"""
    if not user_agent:
        return 'Unknown'

    user_agent_lower = user_agent.lower()

    if 'mobile' in user_agent_lower or 'iphone' in user_agent_lower or 'android' in user_agent_lower:
        return 'Mobile'
    elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
        return 'Tablet'
    elif 'windows' in user_agent_lower or 'macintosh' in user_agent_lower or 'linux' in user_agent_lower:
        return 'Desktop'
    else:
        return 'Unknown'

def save_email_open_record(open_record):
    """開封記録をファイルに保存（改善版）"""
    try:
        # ファイルが存在しない場合はヘッダーを作成
        file_exists = os.path.exists(NEW_EMAIL_OPEN_TRACKING)

        with open(NEW_EMAIL_OPEN_TRACKING, 'a', newline='', encoding='utf-8-sig') as f:
            fieldnames = [
                'tracking_id', 'opened_at', 'ip_address', 'device_type', 'user_agent'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            # ヘッダーを書き込み（新規ファイルの場合）
            if not file_exists:
                writer.writeheader()

            # 開封記録を書き込み（必要なフィールドのみ）
            filtered_record = {
                'tracking_id': open_record.get('tracking_id', ''),
                'opened_at': open_record.get('opened_at', ''),
                'ip_address': open_record.get('ip_address', ''),
                'device_type': open_record.get('device_type', 'Unknown'),
                'user_agent': open_record.get('user_agent', '')
            }
            writer.writerow(filtered_record)

    except Exception as e:
        logger.error(f"開封記録ファイルの保存エラー: {e}")



def get_sent_emails_count():
    """送信済みメール数を取得"""
    try:
        if os.path.exists(NEW_EMAIL_SENDING_RESULTS):
            with open(NEW_EMAIL_SENDING_RESULTS, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                return len(list(reader))
        return 0
    except Exception as e:
        logger.error(f"送信済みメール数の取得エラー: {e}")
        return 0

# === 結果管理システム統合 ===

# 結果管理システム統合
def load_managed_results():
    """結果管理システムから統合結果を読み込み"""
    try:
        from result_management_system import ResultManager
        rm = ResultManager()

        # 統合ファイルを作成
        dashboard_files = rm.create_dashboard_files()

        # 統合結果の統計を取得
        report = rm.generate_status_report()

        return {
            "files": dashboard_files,
            "report": report,
            "success": True
        }
    except Exception as e:
        logger.error(f"管理結果読み込みエラー: {e}")
        return {"success": False, "error": str(e)}

def get_processing_status():
    """処理状況を取得"""
    try:
        from result_management_system import ResultManager
        rm = ResultManager()
        return rm.generate_status_report()
    except Exception as e:
        logger.error(f"処理状況取得エラー: {e}")
        return {}

def get_missing_ranges():
    """未処理範囲を取得"""
    try:
        from result_management_system import ResultManager
        rm = ResultManager()
        return rm.get_missing_ranges()
    except Exception as e:
        logger.error(f"未処理範囲取得エラー: {e}")
        return []

@app.route('/api/process_bounces', methods=['POST'])
def process_bounces():
    """独立したバウンス処理を実行（分離運用版）"""
    try:
        # リクエストパラメータの取得
        data = request.get_json() or {}
        days = data.get('days', 30)
        test_mode = data.get('test_mode', False)
        force_reprocess = data.get('force_reprocess', False)
        reset_tracking = data.get('reset_tracking', False)

        logger.info(f"独立バウンス処理を開始（分離運用版）: 検索期間={days}日, テストモード={test_mode}, 強制再処理={force_reprocess}, 追跡リセット={reset_tracking}")

        # 分離運用版のバウンス処理コマンドを構築
        command = "standalone_bounce_processor.py"
        args = f"--days {days}"
        if test_mode:
            args += " --test-mode"
        if force_reprocess:
            args += " --force-reprocess"
        if reset_tracking:
            args += " --reset-tracking"

        # 既存のプロセス管理システムを使用
        process_id = run_process(command, args)
        if not process_id:
            return jsonify({
                'success': False,
                'message': 'バウンス処理の開始に失敗しました'
            }), 500

        # 監視スレッドを開始
        monitor_thread = threading.Thread(target=monitor_process, args=(process_id,))
        monitor_thread.daemon = True
        monitor_thread.start()

        logger.info(f"バウンス処理プロセス {process_id} を開始しました")

        return jsonify({
            'success': True,
            'message': f"バウンス処理を開始しました（分離運用版・プロセスID: {process_id}）",
            'process_id': process_id,
            'command': f"python {command} {args}",
            'separation_mode': True
        })

    except Exception as e:
        error_msg = f"バウンス処理開始エラー: {e}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500

@app.route('/api/bounce_status', methods=['GET'])
def bounce_status():
    """バウンス処理の状況を取得"""
    try:
        # 最新のバウンス処理レポートを検索
        import glob
        report_files = glob.glob('bounce_processing_report_*.json')

        if not report_files:
            return jsonify({
                'success': True,
                'message': 'バウンス処理レポートが見つかりません',
                'has_report': False
            })

        # 最新のレポートファイルを取得
        latest_report = max(report_files, key=os.path.getctime)

        with open(latest_report, 'r', encoding='utf-8') as f:
            report_data = json.load(f)

        return jsonify({
            'success': True,
            'has_report': True,
            'report': report_data,
            'report_file': latest_report
        })

    except Exception as e:
        error_msg = f"バウンス状況取得エラー: {e}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg
        })

@app.route('/api/process_auto_contact', methods=['POST'])
def process_auto_contact():
    """独立した自動問い合わせ処理を実行（分離運用版）"""
    try:
        # リクエストパラメータの取得
        data = request.get_json() or {}
        days = data.get('days', 7)
        max_companies = data.get('max_companies', 10)
        test_mode = data.get('test_mode', True)

        logger.info(f"独立自動問い合わせ処理を開始（分離運用版）: 検索期間={days}日, 最大処理数={max_companies}, テストモード={test_mode}")

        # 分離運用版の自動問い合わせコマンドを構築
        command = "standalone_auto_contact.py"
        args = f"--days {days}"
        if max_companies:
            args += f" --max-companies {max_companies}"
        if test_mode:
            args += " --test-mode"

        # 既存のプロセス管理システムを使用
        process_id = run_process(command, args)
        if not process_id:
            return jsonify({
                'success': False,
                'message': '自動問い合わせ処理の開始に失敗しました'
            }), 500

        # 監視スレッドを開始
        monitor_thread = threading.Thread(target=monitor_process, args=(process_id,))
        monitor_thread.daemon = True
        monitor_thread.start()

        logger.info(f"自動問い合わせ処理プロセス {process_id} を開始しました")

        return jsonify({
            'success': True,
            'message': f"自動問い合わせ処理を開始しました（分離運用版・プロセスID: {process_id}）",
            'process_id': process_id,
            'command': f"python {command} {args}",
            'separation_mode': True
        })

    except Exception as e:
        error_msg = f"自動問い合わせ処理開始エラー（分離運用版）: {e}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500

@app.route('/bounce-processing')
def bounce_processing():
    """バウンス処理専用ページ（分離運用版）"""
    return render_template(
        'bounce_processing.html',
        last_updated=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        separation_mode=True
    )

@app.route('/auto-contact-processing')
def auto_contact_processing():
    """自動問い合わせ処理専用ページ（分離運用版）"""
    return render_template(
        'auto_contact_processing.html',
        last_updated=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        separation_mode=True
    )

# ===== 開封率管理機能 =====

@app.route('/track-open/<tracking_id>')
def track_email_open(tracking_id):
    """メール開封追跡エンドポイント（改善版）"""
    try:
        # 追跡方法を取得（デフォルトはpixel）
        tracking_method = request.args.get('method', 'pixel')

        # 開封情報を記録（追跡方法も記録）
        record_email_open_enhanced(tracking_id, request, tracking_method)

        # 1x1ピクセルの透明画像を返す
        from flask import Response
        import base64

        # 1x1透明GIF画像のbase64データ
        pixel_data = base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')

        return Response(
            pixel_data,
            mimetype='image/gif',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        )
    except Exception as e:
        logger.error(f"開封追跡エラー: {e}")
        # エラーでも1x1ピクセルを返す
        pixel_data = base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
        return Response(pixel_data, mimetype='image/gif')


@app.route('/track-beacon/<tracking_id>', methods=['POST'])
def track_email_beacon(tracking_id):
    """ビーコンAPI追跡エンドポイント（改善版）"""
    try:
        # ビーコンによる開封記録
        record_email_open_enhanced(tracking_id, request, 'beacon')
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"ビーコン追跡エラー: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/track/<tracking_id>')
def track_email_fallback(tracking_id):
    """フォールバック追跡エンドポイント"""
    try:
        record_email_open_enhanced(tracking_id, request, 'fallback')

        # 1x1ピクセル画像を返す
        pixel_data = base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
        return Response(
            pixel_data,
            mimetype='image/gif',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
    except Exception as e:
        logger.error(f"フォールバック追跡エラー: {e}")
        pixel_data = base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
        return Response(pixel_data, mimetype='image/gif')

@app.route('/track-css/<tracking_id>')
def track_email_css(tracking_id):
    """CSS背景画像追跡エンドポイント"""
    try:
        record_email_open_enhanced(tracking_id, request, 'css')

        # 1x1ピクセル画像を返す
        pixel_data = base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
        return Response(
            pixel_data,
            mimetype='image/gif',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
    except Exception as e:
        logger.error(f"CSS追跡エラー: {e}")
        pixel_data = base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
        return Response(pixel_data, mimetype='image/gif')

@app.route('/track-xhr/<tracking_id>', methods=['POST'])
def track_email_xhr(tracking_id):
    """XMLHttpRequest追跡エンドポイント"""
    try:
        record_email_open_enhanced(tracking_id, request, 'xhr')
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"XHR追跡エラー: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/track-unload/<tracking_id>', methods=['POST'])
def track_email_unload(tracking_id):
    """ページ離脱時追跡エンドポイント"""
    try:
        record_email_open_enhanced(tracking_id, request, 'unload')
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"離脱時追跡エラー: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/track-focus/<tracking_id>', methods=['POST'])
def track_email_focus(tracking_id):
    """フォーカス時追跡エンドポイント"""
    try:
        record_email_open_enhanced(tracking_id, request, 'focus')
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"フォーカス時追跡エラー: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/test-tracking/<tracking_id>')
def test_tracking(tracking_id):
    """開封追跡テスト用エンドポイント"""
    try:
        # テスト用の開封記録
        record_email_open_enhanced(tracking_id, request, 'test')

        return f"""
        <html>
        <head><title>開封追跡テスト</title></head>
        <body>
            <h1>開封追跡テスト完了</h1>
            <p>トラッキングID: {tracking_id}</p>
            <p>開封記録が正常に保存されました。</p>
            <a href="/open-rate-analytics">開封率分析ページで確認</a>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"テスト追跡エラー: {e}")
        return f"エラー: {e}", 500

def record_email_open_enhanced(tracking_id, request_obj, tracking_method='pixel'):
    """メール開封を記録する（改善版・多重追跡対応）"""
    try:
        # 既に同じ方法で開封記録があるかチェック
        if is_already_opened_by_method(tracking_id, tracking_method):
            logger.info(f"既に開封済み ({tracking_method}): {tracking_id}")
            return

        # デバイスタイプを判定（改善版）
        user_agent = request_obj.environ.get('HTTP_USER_AGENT', '') if hasattr(request_obj, 'environ') else request_obj.headers.get('User-Agent', '')
        device_type = detect_device_type_enhanced(user_agent)

        # IPアドレスを取得
        ip_address = request_obj.environ.get('REMOTE_ADDR', '') if hasattr(request_obj, 'environ') else request_obj.remote_addr or ''

        # リファラーを取得
        referer = request_obj.environ.get('HTTP_REFERER', '') if hasattr(request_obj, 'environ') else request_obj.headers.get('Referer', '')

        # 開封情報を準備（拡張フィールド付き）
        now = datetime.datetime.now()
        open_record = {
            'tracking_id': tracking_id,
            'opened_at': now.strftime('%Y-%m-%d %H:%M:%S'),
            'ip_address': ip_address,
            'device_type': device_type,
            'user_agent': user_agent[:200] if user_agent else '',
            'tracking_method': tracking_method,
            'referer': referer[:200] if referer else ''
        }

        # 開封追跡ファイルに記録（拡張版）
        save_email_open_record_enhanced(open_record)

        logger.info(f"メール開封を記録しました ({tracking_method}): {tracking_id} at {now} [{device_type}]")

        # 統計キャッシュをクリア
        clear_stats_cache()

    except Exception as e:
        logger.error(f"開封記録の保存エラー ({tracking_method}): {e}")

def is_already_opened_by_method(tracking_id, tracking_method):
    """指定されたトラッキングIDと方法で既に開封済みかチェック"""
    try:
        if not os.path.exists(NEW_EMAIL_OPEN_TRACKING):
            return False

        with open(NEW_EMAIL_OPEN_TRACKING, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (row.get('tracking_id', '') == tracking_id and
                    row.get('tracking_method', 'pixel') == tracking_method):
                    return True
        return False
    except Exception as e:
        logger.error(f"開封状況チェックエラー: {e}")
        return False

def detect_device_type_enhanced(user_agent):
    """User-Agentからデバイスタイプを判定（改善版）"""
    if not user_agent:
        return 'Unknown'

    user_agent_lower = user_agent.lower()

    # ボット検出
    if any(bot in user_agent_lower for bot in ['bot', 'crawler', 'spider', 'scraper']):
        return 'Bot'

    # モバイル検出
    if any(mobile in user_agent_lower for mobile in ['mobile', 'iphone', 'android', 'ipod', 'blackberry', 'windows phone']):
        return 'Mobile'

    # タブレット検出
    if any(tablet in user_agent_lower for tablet in ['tablet', 'ipad']):
        return 'Tablet'

    # デスクトップ検出
    if any(desktop in user_agent_lower for desktop in ['windows', 'macintosh', 'linux', 'chrome', 'firefox', 'safari', 'edge']):
        return 'Desktop'

    return 'Unknown'

def save_email_open_record_enhanced(open_record):
    """開封記録をファイルに保存（拡張版）"""
    try:
        # ファイルが存在しない場合はヘッダーを作成
        file_exists = os.path.exists(NEW_EMAIL_OPEN_TRACKING)

        with open(NEW_EMAIL_OPEN_TRACKING, 'a', newline='', encoding='utf-8-sig') as f:
            fieldnames = [
                'tracking_id', 'opened_at', 'ip_address', 'device_type', 'user_agent', 'tracking_method', 'referer'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            # ヘッダーを書き込み（新規ファイルの場合）
            if not file_exists:
                writer.writeheader()

            # 開封記録を書き込み（全フィールド）
            filtered_record = {
                'tracking_id': open_record.get('tracking_id', ''),
                'opened_at': open_record.get('opened_at', ''),
                'ip_address': open_record.get('ip_address', ''),
                'device_type': open_record.get('device_type', 'Unknown'),
                'user_agent': open_record.get('user_agent', ''),
                'tracking_method': open_record.get('tracking_method', 'pixel'),
                'referer': open_record.get('referer', '')
            }
            writer.writerow(filtered_record)

    except Exception as e:
        logger.error(f"開封記録ファイルの保存エラー: {e}")

def clear_stats_cache():
    """統計キャッシュをクリアする"""
    global stats_cache
    try:
        if 'stats_cache' in globals() and stats_cache is not None:
            stats_cache.clear()
        else:
            stats_cache = {}
    except Exception as e:
        logger.error(f"統計キャッシュクリアエラー: {e}")
        stats_cache = {}

@app.route('/open-rate-analytics')
def open_rate_analytics():
    """開封率分析ページ（キャッシュ対応）"""
    global open_rate_cache, open_rate_last_updated

    try:
        # キャッシュチェック
        current_time = time.time()
        if (open_rate_cache and
            open_rate_last_updated and
            current_time - open_rate_last_updated < OPEN_RATE_CACHE_TIMEOUT):

            logger.info("開封率分析データをキャッシュから取得")
            return render_template(
                'open_rate_analytics.html',
                open_rate_stats=open_rate_cache['open_rate_stats'],
                daily_open_rates=open_rate_cache['daily_open_rates'],
                company_open_status=open_rate_cache['company_open_status'],
                unopened_emails=open_rate_cache['unopened_emails']
            )

        # キャッシュがない場合は新規計算
        logger.info("開封率分析データを新規計算中...")

        # 開封率統計を取得
        open_rate_stats = get_comprehensive_open_rate_stats()

        # 日別開封率データを取得
        daily_open_rates = get_daily_open_rate_stats()

        # 企業別開封状況を取得
        company_open_status = get_company_open_status()

        # 未開封メールリストを取得
        unopened_emails = get_unopened_emails_list()

        # キャッシュに保存
        open_rate_cache = {
            'open_rate_stats': open_rate_stats,
            'daily_open_rates': daily_open_rates,
            'company_open_status': company_open_status,
            'unopened_emails': unopened_emails
        }
        open_rate_last_updated = current_time

        logger.info("開封率分析データをキャッシュに保存")

        return render_template(
            'open_rate_analytics.html',
            open_rate_stats=open_rate_stats,
            daily_open_rates=daily_open_rates,
            company_open_status=company_open_status,
            unopened_emails=unopened_emails,
            last_updated=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
    except Exception as e:
        logger.error(f"開封率分析ページエラー: {e}")
        return f"エラーが発生しました: {str(e)}", 500

def ensure_open_tracking_file_exists():
    """開封率追跡ファイルが存在しない場合は作成"""
    try:
        if not os.path.exists(NEW_EMAIL_OPEN_TRACKING):
            # dataディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(NEW_EMAIL_OPEN_TRACKING), exist_ok=True)

            # 空の開封率追跡ファイルを作成
            with open(NEW_EMAIL_OPEN_TRACKING, 'w', encoding='utf-8-sig', newline='') as f:
                fieldnames = [
                    'tracking_id', 'opened_at', 'ip_address', 'device_type', 'user_agent', 'tracking_method', 'referer'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

            logger.info(f"開封率追跡ファイルを作成しました: {NEW_EMAIL_OPEN_TRACKING}")
            return True
        return True
    except Exception as e:
        logger.error(f"開封率追跡ファイル作成エラー: {e}")
        return False

def get_comprehensive_open_rate_stats():
    """包括的な開封率統計を取得（バウンス企業を除外）"""
    try:
        # 開封率追跡ファイルが存在しない場合は作成
        ensure_open_tracking_file_exists()

        # 送信済みメール数を取得
        sent_emails = get_sent_emails_with_tracking()

        # デバッグ情報
        logger.info(f"取得した送信済みメール数: {len(sent_emails)}件")

        # CSVファイルから直接バウンス数を取得
        bounced_count = get_csv_bounce_count()
        logger.info(f"CSVファイルから取得したバウンス数: {bounced_count}件")

        # バウンス企業を除外した送信済みメールリストを作成
        valid_sent_emails = []
        csv_bounced_count = 0

        for email in sent_emails:
            bounce_status = check_bounce_status(email['company_id'])
            if bounce_status['is_bounced']:
                csv_bounced_count += 1
            else:
                valid_sent_emails.append(email)

        total_sent = len(sent_emails)
        temp_valid_sent_count = len(valid_sent_emails)

        # CSVから取得したバウンス数を優先使用
        final_bounced_count = max(bounced_count, csv_bounced_count)
        final_valid_sent_count = total_sent - final_bounced_count

        logger.info(f"総送信数: {total_sent}件, 有効送信数: {final_valid_sent_count}件, バウンス数: {final_bounced_count}件")

        # 開封記録を取得
        open_records = get_all_open_records()
        logger.info(f"取得した開封記録数: {len(open_records)}件")

        # バウンス企業の開封記録を除外
        valid_open_records = []
        for record in open_records:
            # トラッキングIDから企業IDを逆引き
            company_id = None
            for email in sent_emails:
                if email.get('tracking_id') == record.get('tracking_id'):
                    company_id = email.get('company_id')
                    break

            if company_id:
                bounce_status = check_bounce_status(company_id)
                if not bounce_status['is_bounced']:
                    valid_open_records.append(record)

        # ユニーク開封数を計算（バウンス除外後）
        unique_opens = len(set(record.get('tracking_id', '') for record in valid_open_records if record.get('tracking_id')))
        total_opens = len(valid_open_records)

        logger.info(f"有効開封記録数: {len(valid_open_records)}件, ユニーク開封数: {unique_opens}件")

        # 開封率データが存在しない場合のデフォルト値設定
        if total_sent == 0:
            logger.warning("送信済みメールが見つかりません。実際の送信数を取得します。")
            # 実際の送信数を取得
            total_sent = get_unified_sent_email_count()
            final_valid_sent_count = total_sent - final_bounced_count
            logger.info(f"実際の送信数を取得: {total_sent}件, 有効送信数: {final_valid_sent_count}件")

        # デバッグ情報を追加
        logger.info(f"開封率計算前の値: total_sent={total_sent}, valid_sent_count={final_valid_sent_count}, unique_opens={unique_opens}, bounced_count={final_bounced_count}")

        # デバイス別統計（バウンス除外）
        device_stats = calculate_device_based_stats(valid_open_records)

        # 開封率を計算（バウンス企業を除外）
        raw_open_rate = (unique_opens / final_valid_sent_count * 100) if final_valid_sent_count > 0 else 0.0

        # 統計的補正を適用した開封率を計算
        corrected_open_rate = calculate_corrected_open_rate(raw_open_rate, final_valid_sent_count, unique_opens)

        # 推定実際開封率を計算（企業メール環境を考慮）
        estimated_actual_rate = estimate_actual_open_rate(raw_open_rate, device_stats)

        # 開封率計算結果をログ出力
        logger.info(f"開封率計算結果: raw_open_rate={raw_open_rate}%, corrected_open_rate={corrected_open_rate}%, estimated_actual_rate={estimated_actual_rate}%")

        # ランク別開封率を計算（バウンス除外） - HUGANJOBシステムでは使用しない
        rank_stats = {}

        # 時間帯別統計（バウンス除外）
        hourly_stats = calculate_hourly_open_stats(valid_open_records)

        # 追跡方法別統計
        method_stats = calculate_method_based_stats(valid_open_records)

        return {
            'total_sent': total_sent,
            'valid_sent_count': final_valid_sent_count,  # バウンス除外後の送信数
            'bounced_count': final_bounced_count,  # バウンス数
            'unique_opens': unique_opens,
            'total_opens': total_opens,
            'raw_open_rate': round(raw_open_rate, 2),  # 生の開封率
            'corrected_open_rate': round(corrected_open_rate, 2),  # 統計的補正後
            'estimated_actual_rate': round(estimated_actual_rate, 2),  # 推定実際開封率
            'open_rate': round(raw_open_rate, 2),  # メイン表示用（生の開封率）
            'bounce_rate': round((final_bounced_count / total_sent * 100) if total_sent > 0 else 0.0, 2),
            'rank_stats': rank_stats,
            'device_stats': device_stats,
            'hourly_stats': hourly_stats,
            'method_stats': method_stats,
            'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        logger.error(f"包括的開封率統計取得エラー: {e}")
        logger.error(f"詳細エラー: {traceback.format_exc()}")
        # エラー時のデフォルト値でもCSVからバウンス数を取得
        csv_bounce_count = get_csv_bounce_count()
        return {
            'total_sent': 0,
            'valid_sent_count': 0,
            'bounced_count': csv_bounce_count,
            'unique_opens': 0,
            'total_opens': 0,
            'raw_open_rate': 0.0,
            'corrected_open_rate': 0.0,
            'estimated_actual_rate': 0.0,
            'open_rate': 0.0,
            'bounce_rate': 0.0,
            'rank_stats': {},
            'device_stats': {},
            'hourly_stats': {},
            'method_stats': {},
            'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

def calculate_corrected_open_rate(raw_rate, sent_count, open_count):
    """統計的補正を適用した開封率を計算"""
    try:
        # 企業メール環境での画像ブロック率を考慮（推定70-80%）
        image_block_rate = 0.75

        # 小サンプルサイズの補正
        if sent_count < 100:
            confidence_factor = 0.8
        elif sent_count < 500:
            confidence_factor = 0.9
        else:
            confidence_factor = 1.0

        # 補正計算
        if raw_rate > 0:
            # 実際の開封率は画像ブロックを考慮して推定
            corrected_rate = raw_rate / (1 - image_block_rate) * confidence_factor
            # 現実的な上限を設定（30%）
            corrected_rate = min(corrected_rate, 30.0)
        else:
            # 開封が0の場合は補正も0とする（推定値は別途計算）
            corrected_rate = 0.0

        return corrected_rate

    except Exception as e:
        logger.error(f"開封率補正計算エラー: {e}")
        return raw_rate

def estimate_actual_open_rate(raw_rate, device_stats):
    """推定実際開封率を計算（企業メール環境を考慮）"""
    try:
        # デバイス別の検出率を考慮
        mobile_rate = device_stats.get('Mobile', {}).get('count', 0)
        desktop_rate = device_stats.get('Desktop', {}).get('count', 0)
        total_detected = mobile_rate + desktop_rate

        if total_detected > 0:
            # モバイルは検出率が高い（60%）、デスクトップは低い（20%）
            mobile_detection_rate = 0.6
            desktop_detection_rate = 0.2

            # 加重平均で実際の検出率を計算
            weighted_detection_rate = (
                (mobile_rate * mobile_detection_rate + desktop_rate * desktop_detection_rate) / total_detected
            )

            # 実際の開封率を推定
            estimated_rate = raw_rate / weighted_detection_rate if weighted_detection_rate > 0 else raw_rate * 5
        else:
            # デバイス情報がない場合は保守的な推定
            estimated_rate = raw_rate * 4  # 25%の検出率を仮定

        # 現実的な範囲に制限
        estimated_rate = min(estimated_rate, 50.0)  # 最大50%
        estimated_rate = max(estimated_rate, raw_rate)  # 生の値より低くはならない

        return estimated_rate

    except Exception as e:
        logger.error(f"実際開封率推定エラー: {e}")
        return raw_rate * 3  # デフォルト推定

def calculate_method_based_stats(open_records):
    """追跡方法別統計を計算"""
    try:
        method_stats = {}

        for record in open_records:
            method = record.get('tracking_method', 'pixel')
            if method not in method_stats:
                method_stats[method] = {'count': 0, 'percentage': 0}
            method_stats[method]['count'] += 1

        total = len(open_records)
        for method in method_stats:
            method_stats[method]['percentage'] = round(
                (method_stats[method]['count'] / total * 100) if total > 0 else 0, 1
            )

        return method_stats

    except Exception as e:
        logger.error(f"追跡方法別統計計算エラー: {e}")
        return {}

def get_unified_sent_email_count():
    """統一された送信メール数を取得（全システム共通）"""
    try:
        total_sent = 0

        # メインの送信結果ファイルを確認
        if os.path.exists(NEW_EMAIL_SENDING_RESULTS):
            with open(NEW_EMAIL_SENDING_RESULTS, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    send_result = row.get('送信結果', '').strip()
                    if send_result == 'success':
                        total_sent += 1

        # HUGANJOBの送信結果ファイルも確認
        huganjob_files = [f for f in os.listdir('.') if f.startswith('huganjob_sending_results_') and f.endswith('.csv')]
        for huganjob_file in huganjob_files:
            try:
                with open(huganjob_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        success = row.get('success', '').strip()
                        if success == 'True':
                            total_sent += 1
            except Exception as e:
                logger.warning(f"HUGANJOBファイル {huganjob_file} 読み込みエラー: {e}")

        logger.info(f"統一送信数取得完了: {total_sent}件")
        return total_sent

    except Exception as e:
        logger.error(f"統一送信数取得エラー: {e}")
        return 0

def get_sent_emails_with_tracking():
    """トラッキングID付きの送信済みメールを取得（複数ファイル対応）"""
    try:
        sent_emails = []

        # メインの送信結果ファイルを確認
        if os.path.exists(NEW_EMAIL_SENDING_RESULTS):
            with open(NEW_EMAIL_SENDING_RESULTS, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # トラッキングIDがあり、送信成功したメールのみ
                    tracking_id = row.get('トラッキングID', '').strip()
                    send_result = row.get('送信結果', '').strip()
                    if tracking_id and send_result == 'success':
                        # ランク情報がない場合はデフォルト値を設定
                        rank = row.get('ランク', 'A')
                        if not rank or rank.strip() == '':
                            rank = 'A'

                        sent_emails.append({
                            'tracking_id': tracking_id,
                            'company_id': row.get('企業ID', ''),
                            'company_name': row.get('企業名', ''),
                            'email': row.get('メールアドレス', ''),
                            'rank': rank,
                            'sent_at': row.get('送信日時', '')
                        })

        # HUGANJOBの送信結果ファイルも確認
        huganjob_files = [f for f in os.listdir('.') if f.startswith('huganjob_sending_results_') and f.endswith('.csv')]
        for huganjob_file in huganjob_files:
            try:
                with open(huganjob_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        tracking_id = row.get('tracking_id', '').strip()
                        success = row.get('success', '').strip()
                        if tracking_id and success == 'True':
                            sent_emails.append({
                                'tracking_id': tracking_id,
                                'company_id': row.get('company_id', ''),
                                'company_name': row.get('company_name', ''),
                                'email': row.get('email_address', ''),
                                'rank': 'A',  # HUGANJOBファイルにはランク情報がないためデフォルト
                                'sent_at': row.get('send_datetime', '')
                            })
            except Exception as e:
                logger.warning(f"HUGANJOBファイル {huganjob_file} 読み込みエラー: {e}")

        logger.info(f"送信済みメール取得完了: {len(sent_emails)}件")
        return sent_emails

    except Exception as e:
        logger.error(f"送信済みメール取得エラー: {e}")
        logger.error(f"詳細エラー: {traceback.format_exc()}")
        return []

def get_all_open_records():
    """全ての開封記録を取得"""
    try:
        open_records = []

        if os.path.exists(NEW_EMAIL_OPEN_TRACKING):
            with open(NEW_EMAIL_OPEN_TRACKING, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 空行をスキップ
                    if row.get('tracking_id', '').strip():
                        open_records.append(row)

        logger.info(f"開封記録取得完了: {len(open_records)}件")
        return open_records

    except Exception as e:
        logger.error(f"開封記録取得エラー: {e}")
        logger.error(f"詳細エラー: {traceback.format_exc()}")
        return []

def calculate_rank_based_open_rates(sent_emails, open_records):
    """ランク別開封率を計算"""
    try:
        # トラッキングIDから企業ランクのマッピングを作成
        tracking_to_rank = {email['tracking_id']: email['rank'] for email in sent_emails}

        # ランク別統計を初期化
        rank_stats = {'A': {'sent': 0, 'opened': 0}, 'B': {'sent': 0, 'opened': 0}, 'C': {'sent': 0, 'opened': 0}}

        # 送信数をカウント
        for email in sent_emails:
            rank = email['rank']
            if rank in rank_stats:
                rank_stats[rank]['sent'] += 1

        # 開封数をカウント（ユニーク）
        opened_tracking_ids = set(record['tracking_id'] for record in open_records)
        for tracking_id in opened_tracking_ids:
            rank = tracking_to_rank.get(tracking_id)
            if rank and rank in rank_stats:
                rank_stats[rank]['opened'] += 1

        # 開封率を計算
        for rank in rank_stats:
            sent = rank_stats[rank]['sent']
            opened = rank_stats[rank]['opened']
            rank_stats[rank]['open_rate'] = round((opened / sent * 100) if sent > 0 else 0.0, 2)

        return rank_stats

    except Exception as e:
        logger.error(f"ランク別開封率計算エラー: {e}")
        return {}

def calculate_device_based_stats(open_records):
    """デバイス別統計を計算"""
    try:
        device_stats = {}

        for record in open_records:
            device = record.get('device_type', 'Unknown')
            if device not in device_stats:
                device_stats[device] = 0
            device_stats[device] += 1

        return device_stats

    except Exception as e:
        logger.error(f"デバイス別統計計算エラー: {e}")
        return {}

def calculate_hourly_open_stats(open_records):
    """時間帯別開封統計を計算（現実的な分布に修正）"""
    try:
        hourly_stats = {str(i): 0 for i in range(24)}
        valid_records = []

        for record in open_records:
            try:
                opened_at = record['opened_at']

                # 異常な時刻パターン（:10で終わる）は除外
                if opened_at.endswith(':10'):
                    continue

                open_time = datetime.datetime.strptime(opened_at, '%Y-%m-%d %H:%M:%S')
                hour = open_time.hour

                # 現実的でない時間帯（深夜0-5時）は除外
                if 0 <= hour <= 5:
                    continue

                valid_records.append(record)
                hourly_stats[str(hour)] += 1
            except:
                continue

        # 統計情報を追加
        total_valid = len(valid_records)
        for hour_str in hourly_stats:
            count = hourly_stats[hour_str]
            hourly_stats[hour_str] = {
                'count': count,
                'percentage': round((count / total_valid * 100) if total_valid > 0 else 0, 2),
                'is_realistic': int(hour_str) >= 6  # 6時以降を現実的とする
            }

        return hourly_stats

    except Exception as e:
        logger.error(f"時間帯別統計計算エラー: {e}")
        return {}

def get_daily_open_rate_stats(days=30):
    """日別開封率統計を取得（現実的な分布に修正）"""
    try:
        # 過去N日間の日付リストを生成
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)

        daily_stats = {}
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            daily_stats[date_str] = {
                'sent': 0,
                'opened': 0,
                'open_rate': 0.0,
                'valid_opens': 0  # 有効な開封数
            }
            current_date += datetime.timedelta(days=1)

        # 送信済みメールの日別集計（バウンス企業を除外）
        sent_emails = get_sent_emails_with_tracking()
        for email in sent_emails:
            try:
                # バウンス状況をチェック
                bounce_status = check_bounce_status(email['company_id'])
                if bounce_status['is_bounced']:
                    continue  # バウンス企業は除外

                sent_date = datetime.datetime.strptime(email['sent_at'], '%Y-%m-%d %H:%M:%S')
                date_str = sent_date.strftime('%Y-%m-%d')
                if date_str in daily_stats:
                    daily_stats[date_str]['sent'] += 1
            except:
                continue

        # 開封記録の日別集計（異常データを除外）
        open_records = get_all_open_records()
        opened_by_date = {}
        valid_opened_by_date = {}

        for record in open_records:
            try:
                opened_at = record['opened_at']

                # 異常な時刻パターン（:10で終わる）は除外
                if opened_at.endswith(':10'):
                    continue

                opened_date = datetime.datetime.strptime(opened_at, '%Y-%m-%d %H:%M:%S')

                # 現実的でない時間帯（深夜0-5時）は除外
                if 0 <= opened_date.hour <= 5:
                    continue

                date_str = opened_date.strftime('%Y-%m-%d')

                # 全開封記録
                if date_str not in opened_by_date:
                    opened_by_date[date_str] = set()
                opened_by_date[date_str].add(record['tracking_id'])

                # 有効な開封記録
                if date_str not in valid_opened_by_date:
                    valid_opened_by_date[date_str] = set()
                valid_opened_by_date[date_str].add(record['tracking_id'])

            except:
                continue

        # 開封率を計算
        for date_str in daily_stats:
            sent = daily_stats[date_str]['sent']
            opened = len(opened_by_date.get(date_str, set()))
            valid_opens = len(valid_opened_by_date.get(date_str, set()))

            daily_stats[date_str]['opened'] = opened
            daily_stats[date_str]['valid_opens'] = valid_opens
            daily_stats[date_str]['open_rate'] = round((valid_opens / sent * 100) if sent > 0 else 0.0, 2)

            # 現実的な開封率の上限を設定（50%を超える場合は異常とみなす）
            if daily_stats[date_str]['open_rate'] > 50.0:
                daily_stats[date_str]['is_suspicious'] = True
                daily_stats[date_str]['open_rate'] = min(daily_stats[date_str]['open_rate'], 30.0)  # 上限を30%に制限
            else:
                daily_stats[date_str]['is_suspicious'] = False

        return daily_stats

    except Exception as e:
        logger.error(f"日別開封率統計取得エラー: {e}")
        return {}

def get_csv_bounce_count():
    """CSVファイルから直接バウンス数を取得"""
    try:
        csv_file = 'data/new_input_test.csv'
        if not os.path.exists(csv_file):
            logger.warning(f"CSVファイルが見つかりません: {csv_file}")
            return 0

        bounce_count = 0
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                bounce_status = row.get('バウンス状態', '').strip()
                # バウンス状態が'permanent'、'temporary'、'unknown'のいずれかの場合はバウンスとしてカウント
                if bounce_status and bounce_status.lower() in ['permanent', 'temporary', 'unknown']:
                    bounce_count += 1

        logger.info(f"CSVファイルから取得したバウンス数: {bounce_count}件")
        return bounce_count

    except Exception as e:
        logger.error(f"CSVバウンス数取得エラー: {e}")
        return 0

def check_bounce_status(company_id):
    """企業のバウンス状況をチェック"""
    try:
        # まずCSVファイルから直接チェック
        csv_file = 'data/new_input_test.csv'
        if os.path.exists(csv_file):
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if str(row.get('ID', '')) == str(company_id):
                        bounce_status = row.get('バウンス状態', '').strip()
                        if bounce_status and bounce_status.lower() in ['permanent', 'temporary', 'unknown']:
                            return {
                                'is_bounced': True,
                                'reason': row.get('バウンス理由', ''),
                                'bounce_type': bounce_status,
                                'detected_at': row.get('バウンス日時', ''),
                                'status': bounce_status
                            }

        # 包括的バウンス検出結果ファイルを確認
        comprehensive_bounce_file = 'comprehensive_bounce_tracking_results.csv'
        if os.path.exists(comprehensive_bounce_file):
            with open(comprehensive_bounce_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if str(row.get('企業ID', '')) == str(company_id):
                        return {
                            'is_bounced': True,
                            'reason': row.get('バウンス理由', ''),
                            'bounce_type': row.get('バウンスタイプ', ''),
                            'detected_at': row.get('バウンス日時', ''),
                            'status': row.get('ステータス', '')
                        }

        # 標準バウンス追跡ファイルもチェック
        if os.path.exists(NEW_BOUNCE_TRACKING):
            with open(NEW_BOUNCE_TRACKING, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if str(row.get('企業ID', '')) == str(company_id):
                        return {
                            'is_bounced': True,
                            'reason': row.get('バウンス理由', ''),
                            'bounce_type': row.get('バウンスタイプ', ''),
                            'detected_at': row.get('バウンス日時', ''),
                            'status': 'bounced'
                        }

        return {'is_bounced': False}

    except Exception as e:
        logger.error(f"バウンス状況チェックエラー (企業ID: {company_id}): {e}")
        return {'is_bounced': False}

def get_company_open_status_detail(company_id):
    """指定企業の開封状況を取得（バウンス状況を最優先でチェック）"""
    try:
        # 1. バウンス状況を最優先でチェック
        bounce_status = check_bounce_status(company_id)
        if bounce_status['is_bounced']:
            return {
                'has_tracking': True,
                'is_opened': False,  # 強制的にFalse
                'bounce_reason': bounce_status['reason'],
                'bounce_type': bounce_status.get('bounce_type', ''),
                'bounce_detected_at': bounce_status.get('detected_at', ''),
                'message': f'メールがバウンスしたため開封不可 (理由: {bounce_status["reason"]})',
                'is_bounced': True
            }

        # 2. 送信済みメールからトラッキングIDを取得
        tracking_id = None
        sent_date = None
        email_address = None

        if os.path.exists(NEW_EMAIL_SENDING_RESULTS):
            with open(NEW_EMAIL_SENDING_RESULTS, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if str(row.get('企業ID', '')) == str(company_id):
                        tracking_id = row.get('トラッキングID', '').strip()
                        sent_date = row.get('送信日時', '')
                        email_address = row.get('メールアドレス', '')
                        break

        if not tracking_id:
            return {
                'has_tracking': False,
                'is_opened': False,
                'sent_date': sent_date,
                'email_address': email_address,
                'message': 'トラッキングIDが見つかりません',
                'is_bounced': False
            }

        # 3. 開封記録を取得
        open_records = []
        if os.path.exists(NEW_EMAIL_OPEN_TRACKING):
            with open(NEW_EMAIL_OPEN_TRACKING, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('tracking_id', '') == tracking_id:
                        open_records.append({
                            'opened_at': row.get('opened_at', ''),
                            'ip_address': row.get('ip_address', ''),
                            'device_type': row.get('device_type', 'Unknown'),
                            'user_agent': row.get('user_agent', '')
                        })

        # 4. 開封状況を分析
        is_opened = len(open_records) > 0

        if is_opened:
            # 開封時刻をソート
            sorted_opens = sorted(open_records, key=lambda x: x['opened_at'])
            first_open = sorted_opens[0]
            latest_open = sorted_opens[-1]

            # デバイス統計
            device_counts = {}
            for record in open_records:
                device = record['device_type']
                device_counts[device] = device_counts.get(device, 0) + 1

            # 送信からの経過日数計算
            days_since_sent = None
            if sent_date:
                try:
                    sent_dt = datetime.datetime.strptime(sent_date, '%Y-%m-%d %H:%M:%S')
                    first_open_dt = datetime.datetime.strptime(first_open['opened_at'], '%Y-%m-%d %H:%M:%S')
                    days_since_sent = (first_open_dt - sent_dt).days
                except:
                    days_since_sent = None

            return {
                'has_tracking': True,
                'is_opened': True,
                'tracking_id': tracking_id,
                'sent_date': sent_date,
                'email_address': email_address,
                'open_count': len(open_records),
                'first_opened_at': first_open['opened_at'],
                'latest_opened_at': latest_open['opened_at'],
                'days_since_sent': days_since_sent,
                'device_counts': device_counts,
                'open_records': open_records,
                'primary_device': max(device_counts.items(), key=lambda x: x[1])[0] if device_counts else 'Unknown',
                'is_bounced': False
            }
        else:
            # 未開封の場合の経過日数計算
            days_since_sent = None
            if sent_date:
                try:
                    sent_dt = datetime.datetime.strptime(sent_date, '%Y-%m-%d %H:%M:%S')
                    now_dt = datetime.datetime.now()
                    days_since_sent = (now_dt - sent_dt).days
                except:
                    days_since_sent = None

            return {
                'has_tracking': True,
                'is_opened': False,
                'tracking_id': tracking_id,
                'sent_date': sent_date,
                'email_address': email_address,
                'days_since_sent': days_since_sent,
                'message': 'メールは未開封です',
                'is_bounced': False
            }

    except Exception as e:
        logger.error(f"企業{company_id}の開封状況取得エラー: {e}")
        return {
            'has_tracking': False,
            'is_opened': False,
            'error': str(e),
            'message': 'データ取得中にエラーが発生しました',
            'is_bounced': False
        }

def get_company_open_status(limit=100):
    """企業別開封状況を取得（バウンス企業を考慮）"""
    try:
        sent_emails = get_sent_emails_with_tracking()
        open_records = get_all_open_records()

        # トラッキングIDから開封情報のマッピング
        opened_tracking_ids = set(record['tracking_id'] for record in open_records)

        # 企業別開封状況を作成
        company_status = []

        for email in sent_emails[:limit]:  # 最新のN件に制限
            company_id = email['company_id']

            # バウンス状況をチェック
            bounce_status = check_bounce_status(company_id)
            is_bounced = bounce_status['is_bounced']

            # バウンス企業は強制的に未開封扱い
            if is_bounced:
                is_opened = False
                open_time = None
                bounce_reason = bounce_status.get('reason', '')
            else:
                is_opened = email['tracking_id'] in opened_tracking_ids
                # 開封時刻を取得
                open_time = None
                if is_opened:
                    for record in open_records:
                        if record['tracking_id'] == email['tracking_id']:
                            open_time = record['opened_at']
                            break
                bounce_reason = None

            company_status.append({
                'company_id': company_id,
                'company_name': email['company_name'],
                'email': email['email'],
                'rank': email['rank'],
                'sent_at': email['sent_at'],
                'is_opened': is_opened,
                'opened_at': open_time,
                'tracking_id': email['tracking_id'],
                'is_bounced': is_bounced,
                'bounce_reason': bounce_reason
            })

        # 開封状況でソート（バウンス→未開封→開封の順）
        company_status.sort(key=lambda x: (x['is_opened'], not x['is_bounced'], x['sent_at']))

        return company_status

    except Exception as e:
        logger.error(f"企業別開封状況取得エラー: {e}")
        return []

def get_unopened_emails_list(days_threshold=7):
    """未開封メールリストを取得（指定日数経過後）"""
    try:
        sent_emails = get_sent_emails_with_tracking()
        open_records = get_all_open_records()

        # 開封済みトラッキングIDのセット
        opened_tracking_ids = set(record['tracking_id'] for record in open_records)

        # 指定日数前の日時
        threshold_date = datetime.datetime.now() - datetime.timedelta(days=days_threshold)

        unopened_emails = []

        for email in sent_emails:
            # 未開封かつ指定日数経過したメール
            if email['tracking_id'] not in opened_tracking_ids:
                try:
                    sent_date = datetime.datetime.strptime(email['sent_at'], '%Y-%m-%d %H:%M:%S')
                    if sent_date <= threshold_date:
                        days_since_sent = (datetime.datetime.now() - sent_date).days

                        unopened_emails.append({
                            'company_id': email['company_id'],
                            'company_name': email['company_name'],
                            'email': email['email'],
                            'rank': email['rank'],
                            'sent_at': email['sent_at'],
                            'days_since_sent': days_since_sent,
                            'tracking_id': email['tracking_id']
                        })
                except:
                    continue

        # 送信日時でソート（古い順）
        unopened_emails.sort(key=lambda x: x['sent_at'])

        return unopened_emails

    except Exception as e:
        logger.error(f"未開封メールリスト取得エラー: {e}")
        return []

def check_data_integrity():
    """データ整合性をチェック（バウンス企業の開封記録矛盾を検出）"""
    try:
        inconsistent_companies = []

        # 送信済みメールを取得
        sent_emails = get_sent_emails_with_tracking()

        # 開封記録を取得
        open_records = get_all_open_records()
        opened_tracking_ids = set(record['tracking_id'] for record in open_records)

        # 各企業について整合性をチェック
        for email in sent_emails:
            company_id = email['company_id']
            tracking_id = email['tracking_id']

            # バウンス状況をチェック
            bounce_status = check_bounce_status(company_id)
            is_bounced = bounce_status['is_bounced']

            # 開封状況をチェック
            is_opened = tracking_id in opened_tracking_ids

            # 矛盾を検出（バウンス済みなのに開封済み）
            if is_bounced and is_opened:
                inconsistent_companies.append({
                    'company_id': company_id,
                    'company_name': email['company_name'],
                    'email_address': email['email'],
                    'tracking_id': tracking_id,
                    'bounce_reason': bounce_status.get('reason', ''),
                    'bounce_detected_at': bounce_status.get('detected_at', ''),
                    'issue': 'バウンス済みなのに開封済み',
                    'detected_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

        return {
            'total_checked': len(sent_emails),
            'inconsistent_count': len(inconsistent_companies),
            'inconsistent_companies': inconsistent_companies,
            'integrity_rate': round(((len(sent_emails) - len(inconsistent_companies)) / len(sent_emails) * 100) if len(sent_emails) > 0 else 100.0, 2),
            'checked_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        logger.error(f"データ整合性チェックエラー: {e}")
        return {
            'total_checked': 0,
            'inconsistent_count': 0,
            'inconsistent_companies': [],
            'integrity_rate': 0.0,
            'error': str(e),
            'checked_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

def get_bounce_open_inconsistency_summary():
    """バウンス・開封の矛盾データサマリーを取得"""
    try:
        integrity_check = check_data_integrity()

        summary = {
            'has_issues': integrity_check['inconsistent_count'] > 0,
            'total_issues': integrity_check['inconsistent_count'],
            'integrity_rate': integrity_check['integrity_rate'],
            'sample_issues': integrity_check['inconsistent_companies'][:5],  # 最初の5件のサンプル
            'last_checked': integrity_check['checked_at']
        }

        return summary

    except Exception as e:
        logger.error(f"矛盾データサマリー取得エラー: {e}")
        return {
            'has_issues': False,
            'total_issues': 0,
            'integrity_rate': 100.0,
            'sample_issues': [],
            'error': str(e),
            'last_checked': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

def clean_open_tracking_data():
    """開封追跡データをクリーンアップ（重複除去、異常データ除去）"""
    try:
        if not os.path.exists(NEW_EMAIL_OPEN_TRACKING):
            return {
                'success': False,
                'message': '開封追跡ファイルが見つかりません',
                'original_count': 0,
                'cleaned_count': 0,
                'removed_count': 0
            }

        # 元のデータを読み込み
        original_records = []
        with open(NEW_EMAIL_OPEN_TRACKING, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                original_records.append(row)

        original_count = len(original_records)
        logger.info(f"開封追跡データクリーンアップ開始: {original_count}件")

        # 有効な送信済みトラッキングIDを取得
        valid_tracking_ids = set()
        if os.path.exists(NEW_EMAIL_SENDING_RESULTS):
            with open(NEW_EMAIL_SENDING_RESULTS, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    tracking_id = row.get('トラッキングID', '').strip()
                    if tracking_id:
                        valid_tracking_ids.add(tracking_id)

        # データをクリーンアップ
        cleaned_records = []
        seen_combinations = set()

        for record in original_records:
            tracking_id = record.get('tracking_id', '').strip()
            opened_at = record.get('opened_at', '').strip()

            # 基本的な検証
            if not tracking_id or not opened_at:
                continue

            # 有効なトラッキングIDかチェック
            if tracking_id not in valid_tracking_ids:
                continue

            # 異常な時刻パターンをチェック（全て:10で終わるのは不自然）
            if opened_at.endswith(':10'):
                continue

            # 深夜時間帯（0-5時）の開封は疑わしい
            try:
                open_time = datetime.datetime.strptime(opened_at, '%Y-%m-%d %H:%M:%S')
                if 0 <= open_time.hour <= 5:
                    continue
            except:
                continue

            # 重複チェック（同じtracking_idと時刻の組み合わせ）
            combination_key = f"{tracking_id}_{opened_at}"
            if combination_key in seen_combinations:
                continue

            seen_combinations.add(combination_key)
            cleaned_records.append(record)

        cleaned_count = len(cleaned_records)
        removed_count = original_count - cleaned_count

        # バックアップを作成
        backup_file = f"{NEW_EMAIL_OPEN_TRACKING}.backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        import shutil
        shutil.copy2(NEW_EMAIL_OPEN_TRACKING, backup_file)

        # クリーンアップされたデータを保存
        with open(NEW_EMAIL_OPEN_TRACKING, 'w', encoding='utf-8-sig', newline='') as f:
            if cleaned_records:
                fieldnames = cleaned_records[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(cleaned_records)
            else:
                # 空の場合はヘッダーのみ
                fieldnames = ['tracking_id', 'opened_at', 'ip_address', 'device_type', 'user_agent']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

        logger.info(f"開封追跡データクリーンアップ完了: {original_count}件 → {cleaned_count}件 (削除: {removed_count}件)")

        return {
            'success': True,
            'message': f'データクリーンアップ完了',
            'original_count': original_count,
            'cleaned_count': cleaned_count,
            'removed_count': removed_count,
            'backup_file': backup_file
        }

    except Exception as e:
        logger.error(f"開封追跡データクリーンアップエラー: {e}")
        return {
            'success': False,
            'message': f'クリーンアップエラー: {str(e)}',
            'original_count': 0,
            'cleaned_count': 0,
            'removed_count': 0
        }

def remove_duplicate_open_records():
    """重複開封記録を除去（同じtracking_idの最初の開封のみ保持）"""
    try:
        if not os.path.exists(NEW_EMAIL_OPEN_TRACKING):
            return {
                'success': False,
                'message': '開封追跡ファイルが見つかりません'
            }

        # データを読み込み
        records = []
        with open(NEW_EMAIL_OPEN_TRACKING, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)

        original_count = len(records)

        # 重複除去（tracking_idごとに最初の開封のみ保持）
        unique_records = []
        seen_tracking_ids = set()

        # 時刻順にソート
        records.sort(key=lambda x: x.get('opened_at', ''))

        for record in records:
            tracking_id = record.get('tracking_id', '').strip()
            if tracking_id and tracking_id not in seen_tracking_ids:
                seen_tracking_ids.add(tracking_id)
                unique_records.append(record)

        unique_count = len(unique_records)
        removed_count = original_count - unique_count

        # 結果を保存
        with open(NEW_EMAIL_OPEN_TRACKING, 'w', encoding='utf-8-sig', newline='') as f:
            if unique_records:
                fieldnames = unique_records[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(unique_records)

        logger.info(f"重複開封記録除去完了: {original_count}件 → {unique_count}件 (削除: {removed_count}件)")

        return {
            'success': True,
            'message': f'重複除去完了: {removed_count}件削除',
            'original_count': original_count,
            'unique_count': unique_count,
            'removed_count': removed_count
        }

    except Exception as e:
        logger.error(f"重複開封記録除去エラー: {e}")
        return {
            'success': False,
            'message': f'重複除去エラー: {str(e)}'
        }

# 開封率管理用のAPIエンドポイント

@app.route('/api/open-rate-stats')
def api_open_rate_stats():
    """開封率統計API"""
    try:
        stats = get_comprehensive_open_rate_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"開封率統計API エラー: {e}")
        return jsonify({'error': str(e)}), 500

# 企業管理機能のエンドポイント

@app.route('/company-management')
def company_management_page():
    """企業管理ページ（統合版）"""
    try:
        return render_template('company_management.html')
    except Exception as e:
        logger.error(f"企業管理ページ表示エラー: {e}")
        return f"エラーが発生しました: {e}", 500

# 旧エンドポイントのリダイレクト
@app.route('/add-company')
def add_company_redirect():
    """旧企業追加ページのリダイレクト"""
    return redirect('/company-management')

@app.route('/csv-import')
def csv_import_redirect():
    """旧CSVインポートページのリダイレクト"""
    return redirect('/company-management')

@app.route('/api/add-company', methods=['POST'])
def api_add_company():
    """企業追加API"""
    try:
        # リクエストデータの取得
        data = request.get_json()

        # 必須フィールドの検証
        required_fields = ['company_name', 'website', 'job_position']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field}は必須です'}), 400

        company_name = data['company_name'].strip()
        website = data['website'].strip()
        email_address = data.get('email_address', '').strip()
        job_position = data['job_position'].strip()

        # 🆕 不完全データのバリデーション（メールアドレスとウェブサイトの両方が空）
        email_empty = not email_address or email_address.strip() in ['', '未登録', '-', '‐']
        website_empty = not website or website.strip() in ['', '‐', '-']

        if email_empty and website_empty:
            return jsonify({
                'success': False,
                'error': '不完全なデータです。メールアドレスとウェブサイトの少なくとも一方は入力してください。'
            }), 400

        # データ検証
        validation_result = validate_company_data(company_name, website, email_address)
        if not validation_result['valid']:
            return jsonify({'success': False, 'error': validation_result['error']}), 400

        # 新しい企業IDを生成
        new_id = get_next_company_id()

        # CSVファイルに追加
        success = add_company_to_csv(new_id, company_name, website, email_address, job_position)

        if success:
            logger.info(f"新しい企業を追加しました: ID={new_id}, 企業名={company_name}")

            # 🆕 企業追加成功時にキャッシュをクリア（即時反映のため）
            logger.info("企業追加成功 - キャッシュをクリアします")
            clear_all_caches()
            logger.info("企業追加後のキャッシュクリア完了")

            return jsonify({
                'success': True,
                'message': f'企業「{company_name}」を追加しました（ID: {new_id}）',
                'company_id': new_id
            })
        else:
            return jsonify({'success': False, 'error': 'CSVファイルへの追加に失敗しました'}), 500

    except Exception as e:
        logger.error(f"企業追加API エラー: {e}")
        return jsonify({'success': False, 'error': f'サーバーエラー: {str(e)}'}), 500

# 旧CSVインポートページは /company-management に統合されました

@app.route('/api/csv-import', methods=['POST'])
def api_csv_import():
    """CSVファイルインポートAPI"""
    logger.info("CSVインポートAPI呼び出し開始")
    try:
        # ファイルの存在確認
        if 'csv_file' not in request.files:
            return jsonify({'success': False, 'error': 'CSVファイルが選択されていません'}), 400

        file = request.files['csv_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'ファイルが選択されていません'}), 400

        # ファイル形式チェック
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'success': False, 'error': 'CSVファイルのみアップロード可能です'}), 400

        # 一時ディレクトリの作成
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        # ファイル保存
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logger.info(f"ファイル保存先: {temp_path}")
        file.save(temp_path)
        logger.info(f"ファイル保存完了: {filename}")

        # CSVファイルの解析とプレビュー
        logger.info(f"CSVファイル解析開始: {temp_path}")
        preview_result = analyze_csv_file(temp_path)
        logger.info(f"CSVファイル解析結果: {preview_result.get('success', False)}")

        if not preview_result['success']:
            logger.error(f"CSVファイル解析失敗: {preview_result}")
            os.remove(temp_path)  # エラー時は一時ファイルを削除
            return jsonify(preview_result), 400

        # 一時ファイルパスを結果に含める
        preview_result['temp_file'] = temp_path
        logger.info(f"CSVファイル解析成功: プレビューデータ={len(preview_result.get('preview_data', []))}行")

        return jsonify(preview_result)

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"CSVインポートAPI エラー: {e}")
        logger.error(f"詳細エラー情報: {error_details}")
        return jsonify({'success': False, 'error': f'サーバーエラー: {str(e)}', 'details': error_details}), 500

@app.route('/api/csv-import-confirm', methods=['POST'])
def api_csv_import_confirm():
    """CSVインポート確定API"""
    try:
        data = request.get_json()
        temp_file = data.get('temp_file')
        skip_duplicates = data.get('skip_duplicates', True)

        if not temp_file or not os.path.exists(temp_file):
            return jsonify({'success': False, 'error': '一時ファイルが見つかりません'}), 400

        # CSVファイルから企業データをインポート
        import_result = import_companies_from_csv(temp_file, skip_duplicates)

        # 結果の構造を確認してログ出力
        logger.info(f"インポート結果: success={import_result.get('success')}, total_processed={import_result.get('total_processed')}, added={import_result.get('added')}")

        # 🆕 インポート成功時にキャッシュをクリア（即時反映のため）
        if import_result.get('success') and import_result.get('added', 0) > 0:
            logger.info(f"CSVインポート成功: {import_result.get('added')}社追加 - キャッシュをクリアします")
            clear_all_caches()
            logger.info("CSVインポート後のキャッシュクリア完了")

        # 一時ファイルを削除
        try:
            os.remove(temp_file)
        except:
            pass

        return jsonify(import_result)

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"CSVインポート確定API エラー: {e}")
        logger.error(f"詳細エラー情報: {error_details}")
        return jsonify({'success': False, 'error': f'サーバーエラー: {str(e)}', 'details': error_details}), 500

@app.route('/api/import-newdata', methods=['POST'])
def api_import_newdata():
    """data/newdata.csvを直接インポートするAPI"""
    try:
        newdata_path = 'data/newdata.csv'

        if not os.path.exists(newdata_path):
            return jsonify({'success': False, 'error': 'newdata.csvファイルが見つかりません'}), 404

        # CSVファイルから企業データをインポート
        import_result = import_companies_from_csv(newdata_path, skip_duplicates=True)

        # 🆕 インポート成功時にキャッシュをクリア（即時反映のため）
        if import_result.get('success') and import_result.get('added', 0) > 0:
            logger.info(f"newdata.csvインポート成功: {import_result.get('added')}社追加 - キャッシュをクリアします")
            clear_all_caches()
            logger.info("newdata.csvインポート後のキャッシュクリア完了")

        return jsonify(import_result)

    except Exception as e:
        logger.error(f"newdata.csvインポートAPI エラー: {e}")
        return jsonify({'success': False, 'error': f'サーバーエラー: {str(e)}'}), 500

def validate_company_data(company_name, website, email_address):
    """企業データの検証（重複チェック除外版）"""
    try:
        # 企業名の検証
        if not company_name or len(company_name.strip()) < 2:
            return {'valid': False, 'error': '企業名は2文字以上で入力してください'}

        # ウェブサイトURLの基本検証
        if website and website not in ['‐', '-', '']:
            # HTTPプロトコルの自動追加
            if not website.startswith(('http://', 'https://')):
                website = 'https://' + website

            # 基本的なURL形式チェック（正規表現を使わない）
            if '.' not in website or ' ' in website:
                return {'valid': False, 'error': 'ウェブサイトURLの形式が正しくありません'}

        # メールアドレスの基本検証
        if email_address and email_address.strip() and email_address.strip() not in ['‐', '-', '']:
            # 基本的なメールアドレス形式チェック（正規表現を使わない）
            if '@' not in email_address or '.' not in email_address.split('@')[-1]:
                return {'valid': False, 'error': 'メールアドレスの形式が正しくありません'}

        return {'valid': True, 'error': None}

    except Exception as e:
        logger.error(f"データ検証エラー: {e}")
        return {'valid': False, 'error': f'検証エラー: {str(e)}'}

def is_company_duplicate(company_name, website):
    """
    企業の重複チェック
    優先順位:
    1. ドメインの重複チェック（有効なURLがある場合）
    2. 企業名の重複チェック（URLがない場合のみ）
    """
    try:
        logger.debug(f"重複チェック開始: 企業名='{company_name}', ウェブサイト='{website}'")

        # 新規企業のURLが有効かどうかを判定
        new_has_valid_url = (website and
                           website not in ['‐', '-', ''] and
                           website.startswith(('http://', 'https://')))

        with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_name = row.get('企業名', '').strip()
                existing_website = row.get('企業ホームページ', '').strip()

                # 既存企業のURLが有効かどうかを判定
                existing_has_valid_url = (existing_website and
                                        existing_website not in ['‐', '-', ''] and
                                        existing_website.startswith(('http://', 'https://')))

                # ケース1: 両方とも有効なURLを持つ場合 → ドメインで比較
                if new_has_valid_url and existing_has_valid_url:
                    existing_domain = extract_domain(existing_website)
                    new_domain = extract_domain(website)
                    if existing_domain == new_domain and existing_domain != '':
                        logger.debug(f"ドメイン重複検出: '{existing_domain}' == '{new_domain}' (企業: {existing_name} vs {company_name})")
                        return True

                # ケース2: 新規企業にURLがない場合 → 企業名で比較
                elif not new_has_valid_url:
                    if existing_name and company_name and existing_name.lower().strip() == company_name.lower().strip():
                        logger.debug(f"企業名重複検出（新規企業URLなし）: '{existing_name}' == '{company_name}'")
                        return True

                # ケース3: 既存企業にURLがなく、新規企業にURLがある場合 → 企業名で比較
                elif new_has_valid_url and not existing_has_valid_url:
                    if existing_name and company_name and existing_name.lower().strip() == company_name.lower().strip():
                        logger.debug(f"企業名重複検出（既存企業URLなし）: '{existing_name}' == '{company_name}'")
                        return True

        logger.debug(f"重複なし: 企業名='{company_name}', URL有効={new_has_valid_url}")
        return False

    except Exception as e:
        logger.error(f"重複チェックエラー: {e}")
        return False

def extract_domain(url):
    """URLからドメイン部分を抽出"""
    try:
        # 正規表現を使わない方法でドメインを抽出
        domain = url

        # http://やhttps://を除去
        if domain.startswith('https://'):
            domain = domain[8:]
        elif domain.startswith('http://'):
            domain = domain[7:]

        # www.を除去
        if domain.startswith('www.'):
            domain = domain[4:]

        # パス部分を除去
        domain = domain.split('/')[0]

        return domain.lower()
    except Exception as e:
        logger.error(f"ドメイン抽出エラー: {e}")
        return url.lower()

def get_next_company_id():
    """次の企業IDを取得"""
    try:
        max_id = 0
        with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    company_id = int(row.get('ID', 0))
                    max_id = max(max_id, company_id)
                except ValueError:
                    continue

        return max_id + 1

    except Exception as e:
        logger.error(f"次のID取得エラー: {e}")
        return 1

def add_company_to_csv(company_id, company_name, website, email_address, job_position):
    """CSVファイルに新しい企業を追加"""
    try:
        # メールアドレスが空の場合は「‐」に設定
        if not email_address:
            email_address = '‐'

        # 新しい行のデータ
        new_row = [
            company_id,
            company_name,
            website,
            email_address,
            job_position,
            '',  # バウンス状態
            '',  # バウンス日時
            '',  # バウンス理由
            '',  # 配信停止状態
            '',  # 配信停止日時
            ''   # 配信停止理由
        ]

        # CSVファイルに追記
        with open(INPUT_FILE, 'a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(new_row)

        logger.info(f"企業をCSVに追加: ID={company_id}, 企業名={company_name}")
        return True

    except Exception as e:
        logger.error(f"CSV追加エラー: {e}")
        return False

def analyze_csv_file(file_path):
    """CSVファイルを解析してプレビューデータを生成"""
    try:
        # 複数のエンコーディングでCSVファイルの読み込みを試行
        encodings = ['utf-8-sig', 'utf-8', 'shift_jis', 'cp932', 'iso-2022-jp']
        sample_lines = []

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    # 最初の数行を読んで構造を確認
                    reader = csv.reader(f)
                    for i, row in enumerate(reader):
                        sample_lines.append(row)
                        if i >= 10:  # 最初の11行（ヘッダー + 10行）
                            break
                logger.info(f"CSVファイル読み込み成功: エンコーディング={encoding}")
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"エンコーディング {encoding} での読み込み失敗: {e}")
                continue
        else:
            return {'success': False, 'error': 'サポートされているエンコーディングでファイルを読み込めませんでした'}

        if not sample_lines:
            return {'success': False, 'error': 'CSVファイルが空です'}

        # ヘッダー行の確認
        header = sample_lines[0] if sample_lines else []
        data_rows = sample_lines[1:] if len(sample_lines) > 1 else []

        # 列数の確認
        if len(header) < 3:
            return {'success': False, 'error': 'CSVファイルには最低3列（企業名、ウェブサイト、募集職種）が必要です'}

        # 列マッピングの推定
        column_mapping = estimate_column_mapping(header)

        # データ品質チェック
        quality_check = check_data_quality(data_rows, column_mapping)

        # プレビューデータの生成
        preview_data = []
        for i, row in enumerate(data_rows[:5]):  # 最初の5行をプレビュー
            if len(row) >= len(header):
                preview_data.append({
                    'row_number': i + 2,  # ヘッダーを除いた行番号
                    'company_name': row[column_mapping['company_name']] if column_mapping['company_name'] is not None else '',
                    'website': row[column_mapping['website']] if column_mapping['website'] is not None else '',
                    'email': row[column_mapping['email']] if column_mapping['email'] is not None else '',
                    'job_position': row[column_mapping['job_position']] if column_mapping['job_position'] is not None else ''
                })

        return {
            'success': True,
            'header': header,
            'column_mapping': column_mapping,
            'preview_data': preview_data,
            'total_rows': len(data_rows),
            'quality_check': quality_check
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"CSV解析エラー: {e}")
        logger.error(f"詳細エラー情報: {error_details}")
        return {'success': False, 'error': f'CSVファイルの解析に失敗しました: {str(e)}', 'details': error_details}

def estimate_column_mapping(header):
    """ヘッダーから列マッピングを推定"""
    mapping = {
        'company_name': None,
        'website': None,
        'email': None,
        'job_position': None
    }

    logger.debug(f"ヘッダー解析開始: {header}")

    # 列名のパターンマッチング
    for i, col_name in enumerate(header):
        col_lower = col_name.lower()
        logger.debug(f"列 {i}: '{col_name}' -> '{col_lower}'")

        # 企業名の検出
        if any(keyword in col_lower for keyword in ['企業名', 'company', '会社名', '社名']):
            mapping['company_name'] = i
            logger.debug(f"企業名列検出: {i}")

        # ウェブサイトの検出
        elif any(keyword in col_lower for keyword in ['url', 'website', 'ウェブサイト', 'ホームページ', 'サイト']):
            mapping['website'] = i
            logger.debug(f"ウェブサイト列検出: {i}")

        # メールアドレスの検出
        elif any(keyword in col_lower for keyword in ['email', 'mail', 'メール', 'アドレス', '担当者']):
            mapping['email'] = i
            logger.debug(f"メールアドレス列検出: {i}")

        # 募集職種の検出
        elif any(keyword in col_lower for keyword in ['職種', 'job', 'position', '募集', '求人']):
            mapping['job_position'] = i
            logger.debug(f"募集職種列検出: {i}")

    # 必須項目が見つからない場合は位置で推定
    if mapping['company_name'] is None and len(header) > 0:
        mapping['company_name'] = 0
        logger.debug(f"企業名列を位置で推定: 0")
    if mapping['website'] is None and len(header) > 1:
        mapping['website'] = 1
        logger.debug(f"ウェブサイト列を位置で推定: 1")
    if mapping['email'] is None and len(header) > 2:
        mapping['email'] = 2
        logger.debug(f"メールアドレス列を位置で推定: 2")
    if mapping['job_position'] is None and len(header) > 3:
        mapping['job_position'] = 3
        logger.debug(f"募集職種列を位置で推定: 3")

    logger.debug(f"最終マッピング: {mapping}")
    return mapping

def check_data_quality(data_rows, column_mapping):
    """データ品質をチェック"""
    quality = {
        'total_rows': len(data_rows),
        'valid_companies': 0,
        'valid_websites': 0,
        'valid_emails': 0,
        'empty_rows': 0,
        'warnings': []
    }

    for row in data_rows:
        if not row or all(cell.strip() == '' for cell in row):
            quality['empty_rows'] += 1
            continue

        # 企業名チェック
        if column_mapping['company_name'] is not None and len(row) > column_mapping['company_name']:
            company_name = row[column_mapping['company_name']].strip()
            if company_name:
                quality['valid_companies'] += 1

        # ウェブサイトチェック
        if column_mapping['website'] is not None and len(row) > column_mapping['website']:
            website = row[column_mapping['website']].strip()
            if website and ('http' in website or '.' in website):
                quality['valid_websites'] += 1

        # メールアドレスチェック
        if column_mapping['email'] is not None and len(row) > column_mapping['email']:
            email = row[column_mapping['email']].strip()
            if email and '@' in email:
                quality['valid_emails'] += 1

    # 警告の生成
    if quality['valid_companies'] < quality['total_rows'] * 0.8:
        quality['warnings'].append('企業名が不完全な行が多く含まれています')

    if quality['valid_websites'] < quality['total_rows'] * 0.5:
        quality['warnings'].append('ウェブサイトURLが不完全な行が多く含まれています')

    if quality['empty_rows'] > 0:
        quality['warnings'].append(f'{quality["empty_rows"]}行の空行が含まれています')

    return quality

def import_companies_from_csv(file_path, skip_duplicates=True):
    """CSVファイルから企業データをインポート"""
    try:
        # CSVファイルの解析
        analysis_result = analyze_csv_file(file_path)
        if not analysis_result['success']:
            return analysis_result

        column_mapping = analysis_result['column_mapping']

        # 現在の最大IDを取得
        current_max_id = get_next_company_id() - 1

        # インポート結果の初期化
        import_stats = {
            'success': True,
            'total_processed': 0,
            'added': 0,
            'skipped': 0,
            'errors': 0,
            'details': [],
            'new_companies': []
        }

        # 複数のエンコーディングでCSVファイルの読み込みと処理
        encodings = ['utf-8-sig', 'utf-8', 'shift_jis', 'cp932', 'iso-2022-jp']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    reader = csv.reader(f)
                    header = next(reader, None)  # ヘッダーをスキップ

                    # エンコーディングが成功した場合、処理を続行
                    logger.info(f"CSVインポート: エンコーディング={encoding}で読み込み成功")
                    break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"エンコーディング {encoding} での読み込み失敗: {e}")
                continue
        else:
            return {'success': False, 'error': 'サポートされているエンコーディングでファイルを読み込めませんでした'}

        # 成功したエンコーディングで再度ファイルを開いて処理
        with open(file_path, 'r', encoding=encoding) as f:
            reader = csv.reader(f)
            header = next(reader, None)  # ヘッダーをスキップ

            for row_num, row in enumerate(reader, start=2):  # 行番号は2から開始（ヘッダー除く）
                import_stats['total_processed'] += 1

                try:
                    # データの抽出（安全な取得）
                    def safe_get_column(row, mapping_key, default=''):
                        """安全に列データを取得"""
                        try:
                            col_index = column_mapping.get(mapping_key)
                            if col_index is not None and len(row) > col_index:
                                return row[col_index].strip()
                            return default
                        except Exception as e:
                            logger.error(f"列データ取得エラー ({mapping_key}): {e}")
                            return default

                    company_name = safe_get_column(row, 'company_name')
                    website = safe_get_column(row, 'website')
                    email_address = safe_get_column(row, 'email')
                    job_position = safe_get_column(row, 'job_position')

                    logger.debug(f"行 {row_num} データ抽出: 企業名='{company_name}', URL='{website}', メール='{email_address}', 職種='{job_position}'")

                    # 必須項目のチェック
                    if not company_name or not job_position:
                        import_stats['errors'] += 1
                        import_stats['details'].append({
                            'row': row_num,
                            'status': 'error',
                            'message': '必須項目（企業名、募集職種）が不足しています'
                        })
                        continue

                    # 🆕 不完全データのバリデーション（メールアドレスとウェブサイトの両方が空）
                    email_empty = not email_address or email_address.strip() in ['', '未登録', '-', '‐']
                    website_empty = not website or website.strip() in ['', '‐', '-']

                    if email_empty and website_empty:
                        import_stats['errors'] += 1
                        import_stats['details'].append({
                            'row': row_num,
                            'status': 'excluded',
                            'company_name': company_name,
                            'message': '不完全データ: メールアドレスとウェブサイトの両方が空のため除外されました'
                        })
                        logger.info(f"不完全データを除外: {company_name} (行 {row_num})")
                        continue

                    # ウェブサイトが空または「‐」の場合はデフォルト値を設定
                    if not website or website in ['‐', '-', '']:
                        website = '‐'

                    # メールアドレスが「‐」の場合は空文字列として扱う（検証エラーを回避）
                    if email_address in ['‐', '-']:
                        email_address = ''

                    # 重複チェック
                    if skip_duplicates and is_company_duplicate(company_name, website):
                        import_stats['skipped'] += 1
                        import_stats['details'].append({
                            'row': row_num,
                            'status': 'skipped',
                            'company_name': company_name,
                            'message': '重複企業のためスキップしました'
                        })
                        continue

                    # データ検証
                    validation_result = validate_company_data(company_name, website, email_address)
                    if not validation_result['valid']:
                        import_stats['errors'] += 1
                        import_stats['details'].append({
                            'row': row_num,
                            'status': 'error',
                            'company_name': company_name,
                            'website': website,
                            'email': email_address,
                            'message': validation_result['error']
                        })
                        logger.warning(f"行 {row_num} 検証エラー: {validation_result['error']}, 企業名='{company_name}', URL='{website}', メール='{email_address}'")
                        continue

                    # 新しいIDを生成
                    current_max_id += 1
                    new_id = current_max_id

                    # CSVファイルに追加（メールアドレスが空の場合は「‐」に戻す）
                    csv_email_address = email_address if email_address else '‐'
                    success = add_company_to_csv(new_id, company_name, website, csv_email_address, job_position)

                    if success:
                        import_stats['added'] += 1
                        import_stats['new_companies'].append({
                            'id': new_id,
                            'name': company_name,
                            'website': website,
                            'job_position': job_position
                        })
                        import_stats['details'].append({
                            'row': row_num,
                            'status': 'added',
                            'company_name': company_name,
                            'company_id': new_id,
                            'message': f'企業を追加しました（ID: {new_id}）'
                        })
                    else:
                        import_stats['errors'] += 1
                        import_stats['details'].append({
                            'row': row_num,
                            'status': 'error',
                            'company_name': company_name,
                            'message': 'CSVファイルへの追加に失敗しました'
                        })

                except Exception as e:
                    import_stats['errors'] += 1
                    import_stats['details'].append({
                        'row': row_num,
                        'status': 'error',
                        'message': f'処理エラー: {str(e)}',
                        'raw_data': row[:4] if len(row) >= 4 else row,  # デバッグ用
                        'column_mapping': column_mapping,  # デバッグ用
                        'company_name': row[column_mapping['company_name']] if column_mapping['company_name'] is not None and len(row) > column_mapping['company_name'] else '不明'
                    })
                    logger.error(f"行 {row_num} 処理エラー: {e}, データ: {row[:4] if len(row) >= 4 else row}, 列マッピング: {column_mapping}")

        # 🆕 不完全データ除外数をカウント
        excluded_count = len([d for d in import_stats['details'] if d.get('status') == 'excluded'])
        import_stats['incomplete_excluded'] = excluded_count

        # 結果のサマリー
        if excluded_count > 0:
            import_stats['message'] = f'インポート完了: {import_stats["added"]}社追加, {import_stats["skipped"]}社スキップ, {excluded_count}社除外（不完全データ）, {import_stats["errors"]}件エラー'
        else:
            import_stats['message'] = f'インポート完了: {import_stats["added"]}社追加, {import_stats["skipped"]}社スキップ, {import_stats["errors"]}件エラー'

        logger.info(f"CSVインポート完了: {import_stats['message']}")
        return import_stats

    except Exception as e:
        logger.error(f"CSVインポートエラー: {e}")
        return {
            'success': False,
            'error': f'インポート処理中にエラーが発生しました: {str(e)}'
        }

@app.route('/api/daily-open-rates')
def api_daily_open_rates():
    """日別開封率API"""
    try:
        days = request.args.get('days', 30, type=int)
        stats = get_daily_open_rate_stats(days)
        return jsonify(stats)
    except Exception as e:
        logger.error(f"日別開封率API エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/unopened-emails')
def api_unopened_emails():
    """未開封メールAPI"""
    try:
        days_threshold = request.args.get('days', 7, type=int)
        limit = request.args.get('limit', 50, type=int)

        unopened = get_unopened_emails_list(days_threshold)
        return jsonify(unopened[:limit])
    except Exception as e:
        logger.error(f"未開封メールAPI エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-integrity-check')
def api_data_integrity_check():
    """データ整合性チェックAPI"""
    try:
        integrity_check = check_data_integrity()
        return jsonify(integrity_check)
    except Exception as e:
        logger.error(f"データ整合性チェックAPI エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bounce-open-inconsistency')
def api_bounce_open_inconsistency():
    """バウンス・開封矛盾データAPI"""
    try:
        summary = get_bounce_open_inconsistency_summary()
        return jsonify(summary)
    except Exception as e:
        logger.error(f"バウンス・開封矛盾データAPI エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/clean-open-tracking-data')
def api_clean_open_tracking_data():
    """開封追跡データクリーンアップAPI"""
    try:
        result = clean_open_tracking_data()
        return jsonify(result)
    except Exception as e:
        logger.error(f"開封追跡データクリーンアップAPI エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/remove-duplicate-opens')
def api_remove_duplicate_opens():
    """重複開封記録除去API"""
    try:
        result = remove_duplicate_open_records()
        return jsonify(result)
    except Exception as e:
        logger.error(f"重複開封記録除去API エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/daily-open-rate-stats')
def api_daily_open_rate_stats():
    """日別開封率統計API"""
    try:
        days = request.args.get('days', 30, type=int)
        daily_stats = get_daily_open_rate_stats(days)
        return jsonify(daily_stats)
    except Exception as e:
        logger.error(f"日別開封率統計API エラー: {e}")
        return jsonify({'error': str(e)}), 500

def start_high_quality_process(command, args, description):
    """高品質修復プロセスを開始する関数"""
    try:
        import subprocess
        import uuid

        # プロセスIDを生成
        process_id = str(uuid.uuid4())[:8]

        # コマンドを構築
        if command.endswith('.py'):
            full_command = f'python {command} {args}'
        else:
            full_command = f'{command} {args}'

        # プロセスを開始（出力バッファリング無効化）
        process = subprocess.Popen(
            full_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # 標準エラーを標準出力にリダイレクト
            text=True,
            bufsize=0,  # バッファリング無効化
            universal_newlines=True,
            cwd=os.getcwd()
        )

        # プロセス情報を保存
        process_info = {
            'id': process_id,
            'pid': process.pid,
            'command': command,
            'args': args,
            'description': description,
            'start_time': datetime.datetime.now(),
            'status': 'running',
            'process': process
        }

        # グローバルプロセスリストに追加
        running_processes[process_id] = process_info

        logger.info(f"高品質プロセス開始: {description} (ID: {process_id}, PID: {process.pid})")

        return process_id

    except Exception as e:
        logger.error(f"高品質プロセス開始エラー: {e}")
        raise

# 高品質修復処理API
@app.route('/api/high_quality_repair', methods=['POST'])
def high_quality_repair():
    """高品質修復処理を実行"""
    try:
        data = request.get_json()
        repair_type = data.get('repair_type')
        start_id = data.get('start_id', 2004)
        end_id = data.get('end_id', 2100)
        test_mode = data.get('test_mode', False)

        # 修復タイプに応じてコマンドを決定
        if repair_type == 'staged':
            # 段階的修復（10社ずつ）
            command = 'high_quality_integrated_workflow.py'
            args = f'--start-id {start_id} --end-id {end_id} --batch-size 10 --timeout 600'
            description = f'高品質段階的修復 (ID {start_id}-{end_id}, 10社ずつ)'
        elif repair_type == 'ultra_safe':
            # 超安全修復（3社ずつ）
            command = 'high_quality_integrated_workflow.py'
            args = f'--start-id {start_id} --end-id {end_id} --batch-size 3 --timeout 600'
            description = f'高品質超安全修復 (ID {start_id}-{end_id}, 3社ずつ)'
        elif repair_type == 'quality_test':
            # 品質テスト（ID 2001-2003）
            command = 'high_quality_integrated_workflow.py'
            args = '--start-id 2001 --end-id 2003 --batch-size 3 --timeout 600 --test-mode'
            description = '高品質テスト (ID 2001-2003)'
        elif repair_type == 'email_extraction':
            # メールアドレス抽出のみ
            command = 'high_quality_email_extractor.py'
            args = f'--start-id {start_id} --end-id {end_id} --input-file new_input_utf8.csv --timeout 45 --retries 5'
            description = f'高品質メールアドレス抽出 (ID {start_id}-{end_id})'
        elif repair_type == 'website_analysis':
            # ウェブサイト分析のみ
            command = 'high_quality_website_analyzer.py'
            args = f'--start-id {start_id} --end-id {end_id} --input-file new_input_utf8.csv --timeout 60 --retries 3'
            description = f'高品質ウェブサイト分析 (ID {start_id}-{end_id})'
        elif repair_type == 'consolidate':
            # 結果統合
            command = 'python'
            args = '-c "import consolidate_high_quality_results; consolidate_high_quality_results.main()"'
            description = '高品質処理結果統合'
        else:
            return jsonify({
                'success': False,
                'message': f'不明な修復タイプ: {repair_type}'
            }), 400

        # テストモードの場合は引数に追加
        if test_mode and repair_type in ['staged', 'ultra_safe']:
            args += ' --test-mode'

        # プロセスを開始
        process_id = start_high_quality_process(command, args, description)

        return jsonify({
            'success': True,
            'message': f'{description}を開始しました',
            'process_id': process_id
        })

    except Exception as e:
        logger.error(f"高品質修復処理エラー: {e}")
        return jsonify({
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500

@app.route('/api/high_quality_status')
def high_quality_status():
    """高品質修復処理の状況を取得"""
    try:
        import glob

        # 高品質処理結果ファイルを確認
        email_files = glob.glob('high_quality_email_extraction_results_id20*.csv')
        website_files = glob.glob('high_quality_website_analysis_results_id20*.csv')

        # 処理済み企業IDを取得
        processed_ids = set()

        for file in email_files + website_files:
            # ファイル名から企業ID範囲を抽出
            import re
            match = re.search(r'id(\d+)-(\d+)', file)
            if match:
                start_id = int(match.group(1))
                end_id = int(match.group(2))
                processed_ids.update(range(start_id, end_id + 1))

        # 企業ID 2001-2100の処理状況を確認
        total_companies = 100  # 2001-2100
        processed_companies = len([id for id in processed_ids if 2001 <= id <= 2100])
        remaining_companies = total_companies - processed_companies

        # 次に処理すべき範囲を計算
        next_start_id = 2001
        for id in range(2001, 2101):
            if id not in processed_ids:
                next_start_id = id
                break

        return jsonify({
            'success': True,
            'total_companies': total_companies,
            'processed_companies': processed_companies,
            'remaining_companies': remaining_companies,
            'progress_percent': round((processed_companies / total_companies) * 100, 1),
            'next_start_id': next_start_id,
            'processed_files': {
                'email_extraction': len(email_files),
                'website_analysis': len(website_files)
            }
        })

    except Exception as e:
        logger.error(f"高品質修復状況取得エラー: {e}")
        return jsonify({
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500

@app.route('/api/high_quality_logs')
def high_quality_logs():
    """高品質修復処理のログを取得"""
    try:
        # 高品質処理関連のログファイルを検索
        log_files = [
            'high_quality_integrated_workflow.log',
            'high_quality_email_extraction.log',
            'high_quality_website_analysis.log',
            'consolidate_high_quality_results.log'
        ]

        logs = []
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # 最新の50行を取得
                        recent_lines = lines[-50:] if len(lines) > 50 else lines
                        for line in recent_lines:
                            if line.strip():
                                logs.append({
                                    'timestamp': datetime.datetime.now().strftime('%H:%M:%S'),
                                    'source': log_file,
                                    'message': line.strip()
                                })
                except Exception as e:
                    logger.error(f"ログファイル読み込みエラー {log_file}: {e}")

        # 時系列でソート（簡易版）
        logs = logs[-100:]  # 最新100行に制限

        return jsonify({
            'success': True,
            'logs': logs
        })

    except Exception as e:
        logger.error(f"高品質ログ取得エラー: {e}")
        return jsonify({
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500

def check_port_availability(port=5001):
    """ポートの利用可能性をチェック"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', port))
            return True
    except OSError:
        return False

def find_available_port(start_port=5001, max_attempts=10):
    """利用可能なポートを見つける"""
    for port in range(start_port, start_port + max_attempts):
        if check_port_availability(port):
            return port
    return None

def cleanup_existing_processes():
    """既存のダッシュボードプロセスをクリーンアップ"""
    import psutil
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if 'new_dashboard.py' in cmdline:
                        logger.warning(f"既存のダッシュボードプロセスを終了します (PID: {proc.info['pid']})")
                        proc = psutil.Process(proc.info['pid'])
                        proc.terminate()
                        proc.wait(timeout=5)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                continue
    except Exception as e:
        logger.warning(f"プロセスクリーンアップ中にエラー: {e}")

def save_pid_file(port):
    """PIDファイルを保存"""
    try:
        import os
        pid_data = {
            'pid': os.getpid(),
            'port': port,
            'start_time': datetime.datetime.now().isoformat(),
            'url': f'http://127.0.0.1:{port}/'
        }
        with open('new_dashboard.pid', 'w', encoding='utf-8') as f:
            json.dump(pid_data, f, ensure_ascii=False, indent=2)
        logger.info(f"PIDファイルを保存しました: {pid_data}")
    except Exception as e:
        logger.warning(f"PIDファイル保存エラー: {e}")

# HUGANJOB専用APIエンドポイント
# テストメール送信API - 削除済み（本番送信のみ使用）

@app.route('/api/huganjob/send', methods=['POST'])
def api_huganjob_send():
    """HUGANJOB 統合メール送信API（huganjob_unified_sender.py専用）"""
    try:
        data = request.get_json()
        start_id = data.get('start_id', 1)
        end_id = data.get('end_id', 10)

        # huganjob_unified_sender.py専用コマンド
        command = 'huganjob_unified_sender.py'
        args = f'--start-id {start_id} --end-id {end_id} --email-format html_only'

        logger.info(f"HUGANJOB統合メール送信開始: ID {start_id}-{end_id}")

        process_id = run_process(command, args)
        if process_id:
            return jsonify({
                'success': True,
                'message': f'ID {start_id}-{end_id} のメール送信を開始しました',
                'process_id': process_id,
                'range': f'{start_id}-{end_id}',
                'command': f'python {command} {args}'
            })
        else:
            return jsonify({'success': False, 'message': 'メール送信の開始に失敗しました'})

    except Exception as e:
        logger.error(f"HUGANJOBメール送信API エラー: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/huganjob/progress')
def api_huganjob_progress():
    """HUGANJOB統合送信の進行状況を取得"""
    try:
        # 実行中のHUGANJOB統合送信プロセスを検索
        huganjob_processes = []
        for process_id, process_info in running_processes.items():
            command = process_info.get('command', '')
            if 'huganjob_unified_sender' in command:
                progress_info = analyze_huganjob_progress(process_info)
                huganjob_processes.append({
                    'process_id': process_id,
                    'status': process_info.get('status', 'unknown'),
                    'start_time': process_info.get('start_time', '').strftime('%Y-%m-%d %H:%M:%S') if process_info.get('start_time') else 'N/A',
                    'duration': str(datetime.datetime.now() - process_info['start_time']).split('.')[0] if process_info.get('start_time') else 'N/A',
                    'progress': progress_info
                })

        return jsonify({
            'success': True,
            'active_processes': len(huganjob_processes),
            'processes': huganjob_processes,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        logger.error(f"HUGANJOB進行状況取得エラー: {e}")
        return jsonify({
            'success': False,
            'message': f'エラー: {e}',
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

@app.route('/api/huganjob/active_processes')
def api_huganjob_active_processes():
    """アクティブなHUGANJOB送信プロセス一覧"""
    try:
        active_processes = []

        # 実行中プロセスから検索
        for process_id, process_info in running_processes.items():
            command = process_info.get('command', '')
            if 'huganjob_unified_sender' in command:
                progress_info = analyze_huganjob_progress(process_info)
                active_processes.append({
                    'process_id': process_id,
                    'command': command,
                    'status': process_info.get('status', 'unknown'),
                    'start_time': process_info.get('start_time', '').strftime('%Y-%m-%d %H:%M:%S') if process_info.get('start_time') else 'N/A',
                    'duration': str(datetime.datetime.now() - process_info['start_time']).split('.')[0] if process_info.get('start_time') else 'N/A',
                    'progress': progress_info
                })

        return jsonify({
            'success': True,
            'count': len(active_processes),
            'processes': active_processes
        })

    except Exception as e:
        logger.error(f"アクティブプロセス取得エラー: {e}")
        return jsonify({'success': False, 'message': f'エラー: {e}'})

@app.route('/api/get_active_processes')
def api_get_active_processes():
    """一般的なアクティブプロセス取得API（進行状況表示用）"""
    try:
        active_processes = []

        for process_id, process_info in running_processes.items():
            active_processes.append({
                'id': process_id,
                'command': process_info.get('command', ''),
                'status': process_info.get('status', 'unknown'),
                'start_time': process_info.get('start_time', '').strftime('%Y-%m-%d %H:%M:%S') if process_info.get('start_time') else 'N/A',
                'duration': str(datetime.datetime.now() - process_info['start_time']).split('.')[0] if process_info.get('start_time') else 'N/A',
                'description': process_info.get('description', process_info.get('command', ''))
            })

        return jsonify(active_processes)

    except Exception as e:
        logger.error(f"一般アクティブプロセス取得エラー: {e}")
        return jsonify([])









# 配信停止管理システム
@app.route('/unsubscribe-management')
def unsubscribe_management():
    """配信停止管理ページ"""
    try:
        # 配信停止ログを読み込み
        unsubscribe_log_path = 'data/huganjob_unsubscribe_log.csv'
        unsubscribed_companies = []

        if os.path.exists(unsubscribe_log_path):
            with open(unsubscribe_log_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                unsubscribed_companies = list(reader)

        # 統計情報を計算
        total_unsubscribed = len(unsubscribed_companies)

        # 申請元別統計
        source_stats = {}
        for entry in unsubscribed_companies:
            source = entry.get('申請元', 'unknown')
            source_stats[source] = source_stats.get(source, 0) + 1

        # 最近の配信停止（直近10件）
        recent_unsubscribes = sorted(
            unsubscribed_companies,
            key=lambda x: x.get('配信停止日時', ''),
            reverse=True
        )[:10]

        # 総企業数を取得
        total_companies = 0
        if os.path.exists('data/new_input_test.csv'):
            with open('data/new_input_test.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                total_companies = sum(1 for _ in reader) - 1

        # 配信停止率を計算
        unsubscribe_rate = (total_unsubscribed / total_companies * 100) if total_companies > 0 else 0

        return render_template(
            'unsubscribe_management.html',
            unsubscribed_companies=unsubscribed_companies,
            recent_unsubscribes=recent_unsubscribes,
            total_unsubscribed=total_unsubscribed,
            total_companies=total_companies,
            unsubscribe_rate=unsubscribe_rate,
            source_stats=source_stats,
            last_updated=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

    except Exception as e:
        logger.error(f"配信停止管理ページエラー: {e}")
        return f"エラーが発生しました: {str(e)}", 500

@app.route('/api/unsubscribe/process', methods=['POST'])
def api_process_unsubscribe():
    """配信停止処理API"""
    try:
        # huganjob_unsubscribe_manager.pyを実行
        import subprocess
        result = subprocess.run(
            ['python', 'huganjob_unsubscribe_manager.py', '--process'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': '配信停止処理が完了しました',
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'message': '配信停止処理でエラーが発生しました',
                'error': result.stderr
            })

    except Exception as e:
        logger.error(f"配信停止処理API エラー: {e}")
        return jsonify({
            'success': False,
            'message': f'処理エラー: {str(e)}'
        }), 500

@app.route('/api/unsubscribe/check', methods=['POST'])
def api_check_unsubscribe():
    """配信停止状況確認API"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()

        if not email:
            return jsonify({
                'success': False,
                'message': 'メールアドレスが指定されていません'
            }), 400

        # 配信停止ログを確認
        unsubscribe_log_path = 'data/huganjob_unsubscribe_log.csv'
        is_unsubscribed = False
        unsubscribe_info = None

        if os.path.exists(unsubscribe_log_path):
            with open(unsubscribe_log_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for entry in reader:
                    if entry.get('メールアドレス', '').lower().strip() == email.lower():
                        is_unsubscribed = True
                        unsubscribe_info = entry
                        break

        return jsonify({
            'success': True,
            'is_unsubscribed': is_unsubscribed,
            'unsubscribe_info': unsubscribe_info
        })

    except Exception as e:
        logger.error(f"配信停止確認API エラー: {e}")
        return jsonify({
            'success': False,
            'message': f'確認エラー: {str(e)}'
        }), 500

# Google Sheets監視システム制御
@app.route('/sheets-monitor')
def sheets_monitor_page():
    """Google Sheets監視システム制御ページ"""
    try:
        # 監視システムの状態確認
        monitor_status = {
            'is_running': False,
            'last_check': None,
            'processed_count': 0,
            'credentials_configured': False
        }

        # 認証情報ファイルの確認
        credentials_path = 'config/google_sheets_credentials.json'
        if os.path.exists(credentials_path):
            try:
                with open(credentials_path, 'r', encoding='utf-8') as f:
                    creds = json.load(f)
                if creds.get('type') == 'service_account' and 'your-project' not in creds.get('project_id', ''):
                    monitor_status['credentials_configured'] = True
            except:
                pass

        # 処理済みエントリ数の確認
        processed_file = 'data/huganjob_sheets_processed.json'
        if os.path.exists(processed_file):
            try:
                with open(processed_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    monitor_status['processed_count'] = len(data.get('processed_hashes', []))
                    monitor_status['last_check'] = data.get('last_updated')
            except:
                pass

        # 処理不可エントリの確認
        unprocessable_entries = []
        unprocessable_file = 'data/huganjob_unprocessable_entries.csv'
        if os.path.exists(unprocessable_file):
            try:
                with open(unprocessable_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    unprocessable_entries = list(reader)
            except:
                pass

        return render_template(
            'sheets_monitor.html',
            monitor_status=monitor_status,
            unprocessable_entries=unprocessable_entries,
            last_updated=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

    except Exception as e:
        logger.error(f"Google Sheets監視ページエラー: {e}")
        return f"エラーが発生しました: {str(e)}", 500

@app.route('/api/sheets-monitor/test', methods=['POST'])
def api_sheets_monitor_test():
    """Google Sheets監視システムテストAPI"""
    try:
        import subprocess
        result = subprocess.run(
            ['python', 'huganjob_google_sheets_monitor.py', '--test'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        return jsonify({
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr
        })

    except Exception as e:
        logger.error(f"Google Sheets監視テストAPI エラー: {e}")
        return jsonify({
            'success': False,
            'message': f'テストエラー: {str(e)}'
        }), 500

@app.route('/api/sheets-monitor/setup', methods=['POST'])
def api_sheets_monitor_setup():
    """Google Sheets監視システム設定API"""
    try:
        import subprocess
        result = subprocess.run(
            ['python', 'setup_google_sheets_api.py', '--all'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        return jsonify({
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr
        })

    except Exception as e:
        logger.error(f"Google Sheets監視設定API エラー: {e}")
        return jsonify({
            'success': False,
            'message': f'設定エラー: {str(e)}'
        }), 500

@app.route('/api/huganjob/stats')
def api_huganjob_stats():
    """HUGANJOB統計情報API"""
    try:
        # HUGANJOB専用統計を取得
        stats = {
            'total_companies': 0,
            'email_resolved': 0,
            'emails_sent': 0,
            'delivery_success': 0,
            'bounced': 0,
            'unsubscribed': 0,
            'success_rate': 0.0,
            'unsubscribe_rate': 0.0
        }

        # new_input_test.csvから企業数を取得
        if os.path.exists('data/new_input_test.csv'):
            try:
                with open('data/new_input_test.csv', 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    stats['total_companies'] = sum(1 for _ in reader) - 1  # ヘッダー除く
            except Exception as e:
                logger.error(f"企業数取得エラー: {e}")
                stats['total_companies'] = 0

        # 送信結果から詳細統計を取得
        if os.path.exists('new_email_sending_results.csv'):
            try:
                with open('new_email_sending_results.csv', 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    results = list(reader)

                # ユニークな企業IDを取得
                unique_companies = set()
                result_counts = {}

                for result in results:
                    try:
                        company_id = int(result['企業ID'])
                        unique_companies.add(company_id)

                        send_result = result.get('送信結果', 'unknown')
                        result_counts[send_result] = result_counts.get(send_result, 0) + 1
                    except:
                        continue

                stats['emails_sent'] = len(unique_companies)
                stats['delivery_success'] = result_counts.get('success', 0)
                stats['bounced'] = result_counts.get('bounced', 0)
                stats['unsubscribed'] = result_counts.get('unsubscribed', 0)

                # 成功率を計算
                if stats['emails_sent'] > 0:
                    stats['success_rate'] = (stats['delivery_success'] / stats['emails_sent']) * 100

            except Exception as e:
                logger.error(f"送信結果統計取得エラー: {e}")

        # 配信停止数を取得（ログファイルからも確認）
        unsubscribe_log_path = 'data/huganjob_unsubscribe_log.csv'
        if os.path.exists(unsubscribe_log_path):
            try:
                with open(unsubscribe_log_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    unsubscribe_count = sum(1 for _ in reader) - 1  # ヘッダー除く
                # 送信結果とログファイルの最大値を使用
                stats['unsubscribed'] = max(stats['unsubscribed'], unsubscribe_count)
            except Exception as e:
                logger.error(f"配信停止ログ取得エラー: {e}")

        # 配信停止率を計算
        if stats['total_companies'] > 0:
            stats['unsubscribe_rate'] = (stats['unsubscribed'] / stats['total_companies']) * 100

        # 送信履歴からも統計を補完
        try:
            with open('huganjob_sending_history.json', 'r', encoding='utf-8') as f:
                history = json.load(f)

            history_count = len(history.get('sending_records', []))
            # 送信結果ファイルと送信履歴の最大値を使用
            stats['emails_sent'] = max(stats['emails_sent'], history_count)

        except Exception as e:
            logger.error(f"送信履歴読み込みエラー: {e}")

        # 実質的な成功率を計算（配信停止とバウンスを除外）
        effective_sent = stats['emails_sent'] - stats['unsubscribed']
        effective_success = effective_sent - stats['bounced']

        if effective_sent > 0:
            stats['success_rate'] = (effective_success / effective_sent) * 100

        # 最終的な配信成功数を設定
        stats['delivery_success'] = effective_success

        # メールアドレス決定結果から統計を取得
        if os.path.exists('huganjob_email_resolution_results.csv'):
            try:
                import pandas as pd
                df = pd.read_csv('huganjob_email_resolution_results.csv', encoding='utf-8-sig')
                stats['email_resolved'] = len(df[df['決定メールアドレス'].notna()])
            except Exception as e:
                logger.warning(f"メール決定結果ファイル読み込みエラー: {e}")

        return jsonify({
            'success': True,
            'stats': stats,
            'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        logger.error(f"HUGANJOB統計情報API エラー: {e}")
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    import argparse

    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='HUGANJOB営業メール送信システム ダッシュボード')
    parser.add_argument('--port', type=int, default=5002, help='ポート番号 (デフォルト: 5002)')
    parser.add_argument('--host', default='127.0.0.1', help='ホストアドレス (デフォルト: 127.0.0.1)')
    parser.add_argument('--debug', action='store_true', help='デバッグモードで起動')
    parser.add_argument('--cleanup', action='store_true', help='既存プロセスをクリーンアップしてから起動')
    parser.add_argument('--auto-port', action='store_true', help='利用可能なポートを自動検索')
    args = parser.parse_args()

    try:
        # 初期化処理
        logger.info("=" * 60)
        logger.info("HUGANJOB営業メール送信システム ダッシュボード起動中...")
        logger.info("=" * 60)

        ensure_directories()
        initialize_config_files()

        # 入力ファイルの確認（軽量化）
        if not os.path.exists(INPUT_FILE):
            logger.error("❌ 入力ファイルが見つかりません。ダッシュボードを終了します。")
            sys.exit(1)

        logger.info("✅ 入力ファイルを確認しました")

        # プロセス履歴を読み込み（遅延読み込み対応）
        if not STARTUP_LAZY_LOADING:
            load_process_history()
        else:
            logger.info("⚡ 遅延読み込みモード: プロセス履歴は必要時に読み込みます")

        # 既存プロセスのクリーンアップ（オプション）
        if args.cleanup:
            logger.info("🧹 既存プロセスをクリーンアップしています...")
            cleanup_existing_processes()

        # ポートの確認と設定
        target_port = args.port
        if args.auto_port:
            available_port = find_available_port(target_port)
            if available_port:
                target_port = available_port
                logger.info(f"🔍 利用可能なポートを発見: {target_port}")
            else:
                logger.error(f"❌ 利用可能なポートが見つかりません (開始ポート: {args.port})")
                sys.exit(1)
        elif not check_port_availability(target_port):
            logger.error(f"❌ ポート {target_port} は既に使用されています")
            logger.info("💡 --auto-port オプションを使用するか、--cleanup オプションで既存プロセスを終了してください")
            sys.exit(1)

        # PIDファイルを保存
        save_pid_file(target_port)

        # HUGANJOB起動メッセージ
        logger.info("🚀 HUGANJOBダッシュボードを起動します...")
        logger.info(f"📊 アクセスURL: http://{args.host}:{target_port}/")
        logger.info(f"🔧 デバッグモード: {'有効' if args.debug else '無効'}")
        logger.info(f"⚡ 遅延読み込み: {'有効' if STARTUP_LAZY_LOADING else '無効'}")
        logger.info(f"💾 キャッシュタイムアウト: {CACHE_TIMEOUT_SECONDS}秒")
        logger.info(f"📧 HUGANJOB営業メール送信システム専用")
        logger.info("=" * 60)

        # 定期的なメモリクリーンアップを開始
        def periodic_memory_cleanup():
            """定期的なメモリクリーンアップ"""
            import time
            while True:
                time.sleep(300)  # 5分間隔
                try:
                    optimize_memory()
                except Exception as e:
                    logger.warning(f"定期メモリクリーンアップエラー: {e}")

        cleanup_thread = threading.Thread(target=periodic_memory_cleanup, daemon=True)
        cleanup_thread.start()
        logger.info("🧹 定期メモリクリーンアップを開始しました（5分間隔）")

        # Flaskアプリケーションを起動
        app.run(
            host=args.host,
            port=target_port,
            debug=args.debug,
            threaded=True,
            use_reloader=False  # リローダーを無効化してプロセス重複を防ぐ
        )

    except KeyboardInterrupt:
        logger.info("👋 HUGANJOBダッシュボードが手動で停止されました")
    except Exception as e:
        logger.error(f"💥 HUGANJOBダッシュボード起動エラー: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        # クリーンアップ
        try:
            if os.path.exists('huganjob_dashboard.pid'):
                os.remove('huganjob_dashboard.pid')
                logger.info("🧹 HUGANJOBPIDファイルを削除しました")
        except:
            pass
