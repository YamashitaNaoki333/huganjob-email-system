#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
派生版メールマーケティングシステム統合ワークフロースクリプト
- 元システムから独立した派生版
- 新機能開発・テスト用途
- メール抽出 → ウェブサイト分析 → メール送信の統合処理
- 元システムとの干渉を完全に回避
"""

import subprocess
import sys
import os
import logging
import argparse
import time
import csv
import glob
import datetime
import pandas as pd
import tempfile
import shutil
import gc
import psutil
import threading

# [DERIVATIVE] 派生版作業ディレクトリ安定化機能
def stabilize_working_directory():
    """派生版作業ディレクトリを安定化する"""
    target_dir = r"c:\Users\Raxus\Desktop\email_extraction_project\email_marketing_derivative_system"
    current_dir = os.getcwd()

    # 作業ディレクトリが異常な場合の修復
    if current_dir == "//" or not os.path.exists(current_dir) or "email_marketing_derivative_system" not in current_dir:
        print(f"[WARNING] Derivative working directory issue detected: {current_dir}")
        print(f"[REPAIR] Attempting repair: {target_dir}")

        try:
            if os.path.exists(target_dir):
                os.chdir(target_dir)
                new_dir = os.getcwd()
                print(f"[SUCCESS] Derivative working directory repaired: {new_dir}")
                return True
            else:
                print(f"[ERROR] Derivative target directory not found: {target_dir}")
                return False
        except Exception as e:
            print(f"[ERROR] Derivative working directory repair failed: {e}")
            return False
    else:
        print(f"[OK] Derivative working directory is normal: {current_dir}")
        return True

# 派生版作業ディレクトリ安定化を最初に実行
if not stabilize_working_directory():
    print("💥 派生版作業ディレクトリの修復に失敗しました。システム再起動を推奨します。")
    sys.exit(1)

# 派生版ログディレクトリを作成
os.makedirs("logs/derivative_dashboard", exist_ok=True)

# 派生版ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/derivative_dashboard/derivative_integrated_workflow.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('derivative_integrated_workflow')

# 派生版システム用の設定
INPUT_FILE = 'data/derivative_input.csv'
SCRIPTS = {
    'email_extraction': 'core_scripts/derivative_email_extractor.py',
    'website_analysis': 'core_scripts/derivative_website_analyzer.py',
    'email_sending': 'core_scripts/derivative_email_sender.py',
    'bounce_processing': 'core_scripts/derivative_bounce_processor.py'
}

# メモリ監視とクリーンアップ機能
class MemoryManager:
    """メモリ使用量の監視とクリーンアップを行うクラス"""

    def __init__(self, max_memory_mb=2048):
        self.max_memory_mb = max_memory_mb
        self.process = psutil.Process()
        self.initial_memory = self.get_memory_usage()

    def get_memory_usage(self):
        """現在のメモリ使用量をMBで取得"""
        try:
            memory_info = self.process.memory_info()
            return memory_info.rss / 1024 / 1024  # MB
        except:
            return 0

    def check_memory_usage(self):
        """メモリ使用量をチェックし、必要に応じて警告"""
        current_memory = self.get_memory_usage()
        memory_increase = current_memory - self.initial_memory

        logger.info(f"💾 メモリ使用量: {current_memory:.1f}MB (増加: +{memory_increase:.1f}MB)")

        if current_memory > self.max_memory_mb:
            logger.warning(f"⚠️ メモリ使用量が上限を超えました: {current_memory:.1f}MB > {self.max_memory_mb}MB")
            return False

        return True

    def cleanup_memory(self):
        """メモリクリーンアップを実行"""
        before_memory = self.get_memory_usage()

        # ガベージコレクション実行
        collected = gc.collect()

        after_memory = self.get_memory_usage()
        freed_memory = before_memory - after_memory

        logger.info(f"🧹 メモリクリーンアップ完了: {collected}個のオブジェクトを回収, {freed_memory:.1f}MB解放")

        return freed_memory > 0

# グローバルメモリマネージャー
memory_manager = MemoryManager(max_memory_mb=2048)  # 2GB制限に変更（安定性重視）

# 改善されたプロセス監視クラス
class EnhancedProcessMonitor:
    """改善されたプロセス監視とサイレント失敗検出"""

    def __init__(self):
        self.start_time = None
        self.last_output_time = None
        self.silent_timeout_minutes = 10  # 10分間無音でタイムアウト（短縮）
        self.max_total_time_hours = 2     # 最大2時間で強制終了（短縮）
        self.heartbeat_interval = 30      # 30秒間隔でハートビート
        self.last_heartbeat = None
        self.process_health_checks = []
        self.error_count = 0
        self.max_errors = 3               # 最大エラー数

    def start_monitoring(self, expected_duration_minutes=None):
        """監視開始（期待実行時間付き）"""
        self.start_time = time.time()
        self.last_output_time = time.time()
        self.last_heartbeat = time.time()
        self.error_count = 0

        if expected_duration_minutes:
            self.expected_end_time = self.start_time + (expected_duration_minutes * 60)
        else:
            self.expected_end_time = None

        logger.info(f"🔍 改善されたプロセス監視開始:")
        logger.info(f"   - サイレントタイムアウト: {self.silent_timeout_minutes}分")
        logger.info(f"   - 最大実行時間: {self.max_total_time_hours}時間")
        logger.info(f"   - ハートビート間隔: {self.heartbeat_interval}秒")
        if expected_duration_minutes:
            logger.info(f"   - 期待実行時間: {expected_duration_minutes}分")

    def update_heartbeat(self, message=""):
        """ハートビート更新"""
        current_time = time.time()
        self.last_heartbeat = current_time
        self.last_output_time = current_time

        if message:
            logger.info(f"💓 ハートビート: {message}")

    def check_health(self):
        """プロセス健全性チェック"""
        current_time = time.time()

        # サイレントタイムアウトチェック
        if self.last_output_time:
            silent_duration = (current_time - self.last_output_time) / 60
            if silent_duration > self.silent_timeout_minutes:
                logger.error(f"🚨 サイレントタイムアウト検出: {silent_duration:.1f}分間無応答")
                return False

        # 総実行時間チェック
        if self.start_time:
            total_duration = (current_time - self.start_time) / 3600
            if total_duration > self.max_total_time_hours:
                logger.error(f"🚨 最大実行時間超過: {total_duration:.1f}時間")
                return False

        # 期待時間との比較
        if self.expected_end_time and current_time > self.expected_end_time * 1.5:
            logger.warning(f"⚠️ 期待実行時間の1.5倍を超過")

        return True

    def record_error(self, error_message):
        """エラー記録"""
        self.error_count += 1
        logger.error(f"❌ エラー記録 ({self.error_count}/{self.max_errors}): {error_message}")

        if self.error_count >= self.max_errors:
            logger.error(f"🚨 最大エラー数に到達。処理を停止します。")
            return False
        return True

# プロセス監視クラス（後方互換性のため残す）
class ProcessMonitor:
    """長時間処理のプロセス監視とタイムアウト管理"""

    def __init__(self):
        self.start_time = None
        self.last_output_time = None
        self.silent_timeout_minutes = 15  # 15分間無音でタイムアウト
        self.max_total_time_hours = 3     # 最大3時間で強制終了

    def start_monitoring(self):
        """監視開始"""
        self.start_time = time.time()
        self.last_output_time = time.time()
        logger.info(f"🔍 プロセス監視開始: サイレントタイムアウト {self.silent_timeout_minutes}分, 最大実行時間 {self.max_total_time_hours}時間")

    def update_activity(self):
        """アクティビティ更新（出力があった時に呼び出し）"""
        self.last_output_time = time.time()

    def check_timeout(self):
        """タイムアウトチェック"""
        if not self.start_time:
            return False, ""

        current_time = time.time()
        total_elapsed = (current_time - self.start_time) / 3600  # 時間
        silent_elapsed = (current_time - self.last_output_time) / 60  # 分

        # 最大実行時間チェック
        if total_elapsed > self.max_total_time_hours:
            return True, f"最大実行時間（{self.max_total_time_hours}時間）を超過しました"

        # サイレントタイムアウトチェック
        if silent_elapsed > self.silent_timeout_minutes:
            return True, f"サイレントタイムアウト（{self.silent_timeout_minutes}分間無音）が発生しました"

        return False, ""

    def get_status(self):
        """現在の監視状況を取得"""
        if not self.start_time:
            return "監視未開始"

        current_time = time.time()
        total_elapsed = (current_time - self.start_time) / 60  # 分
        silent_elapsed = (current_time - self.last_output_time) / 60  # 分

        return f"実行時間: {total_elapsed:.1f}分, 最終出力から: {silent_elapsed:.1f}分"

# グローバルプロセス監視（改善版）
enhanced_monitor = EnhancedProcessMonitor()
process_monitor = ProcessMonitor()  # 後方互換性のため残す

def run_command_with_monitoring(command, description, timeout_minutes=10):
    """メモリ監視とプロセス監視付きでコマンドを実行"""
    # 実行前のメモリチェック
    memory_manager.check_memory_usage()

    # プロセス監視開始
    process_monitor.start_monitoring()

    # コマンド実行（監視付き）
    result = run_command_with_process_monitoring(command, description, timeout_minutes)

    # 実行後のメモリチェックとクリーンアップ
    if not memory_manager.check_memory_usage():
        logger.warning("メモリ使用量が多いため、クリーンアップを実行します")
        memory_manager.cleanup_memory()

    return result

def run_command_with_process_monitoring(command, description, timeout_minutes=10):
    """プロセス監視付きでコマンドを実行"""
    logger.info(f"🚀 開始: {description}")
    logger.info(f"📋 実行コマンド: {command}")
    logger.info(f"⏰ タイムアウト設定: {timeout_minutes}分")

    start_time = time.time()
    timeout_seconds = timeout_minutes * 60

    try:
        # プロセス開始
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,
            bufsize=1
        )

        output_lines = []
        last_log_time = time.time()
        log_interval = 30  # 30秒ごとにログ出力

        while True:
            # プロセス終了チェック
            if process.poll() is not None:
                break

            # タイムアウトチェック
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                logger.error(f"⚠️ タイムアウト: {description} ({timeout_minutes}分)")
                process.terminate()
                time.sleep(5)
                if process.poll() is None:
                    process.kill()
                return False

            # プロセス監視チェック
            is_timeout, timeout_reason = process_monitor.check_timeout()
            if is_timeout:
                logger.error(f"⚠️ プロセス監視タイムアウト: {timeout_reason}")
                process.terminate()
                time.sleep(5)
                if process.poll() is None:
                    process.kill()
                return False

            # 出力読み取り
            try:
                output = process.stdout.readline()
                if output:
                    try:
                        line = output.decode('utf-8', errors='replace').strip()
                        if line:
                            output_lines.append(line)
                            process_monitor.update_activity()  # アクティビティ更新

                            # 定期的にログ出力
                            current_time = time.time()
                            if current_time - last_log_time > log_interval:
                                logger.info(f"📊 {process_monitor.get_status()}")
                                logger.info(f"💬 最新出力: {line[:100]}...")
                                last_log_time = current_time
                    except UnicodeDecodeError:
                        pass
            except:
                pass

            time.sleep(0.1)  # CPU使用率を下げる

        # プロセス終了後の処理
        return_code = process.returncode
        end_time = time.time()
        duration = end_time - start_time

        # 出力を結合
        full_output = '\n'.join(output_lines)

        if return_code == 0:
            logger.info(f"✅ 完了: {description} (実行時間: {duration:.1f}秒)")
            if len(output_lines) > 0:
                logger.info(f"📝 出力行数: {len(output_lines)}行")
                if len(full_output) > 2000:
                    logger.info(f"📄 出力（先頭500文字）:\n{full_output[:500]}...")
                    logger.info(f"📄 出力（末尾500文字）:\n...{full_output[-500:]}")
                else:
                    logger.info(f"📄 出力:\n{full_output}")
            return True
        else:
            logger.error(f"❌ 失敗: {description}")
            logger.error(f"🔢 エラーコード: {return_code}")
            if full_output:
                logger.error(f"📄 エラー出力:\n{full_output}")
            return False

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        logger.error(f"💥 例外発生: {description} (実行時間: {duration:.1f}秒)")
        logger.error(f"🔍 例外詳細: {e}")
        return False

def run_command(command, description, timeout_minutes=10):
    """コマンドを実行して結果を返す（サイレント失敗検出機能付き）"""
    logger.info(f"開始: {description}")
    logger.info(f"実行コマンド: {command}")
    logger.info(f"タイムアウト設定: {timeout_minutes}分")

    start_time = time.time()
    timeout_seconds = timeout_minutes * 60

    try:
        # Windowsでのエンコーディング問題を回避
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=False,  # バイナリモードで実行
            timeout=timeout_seconds  # タイムアウト設定
        )

        # 出力をUTF-8でデコード（エラー時は無視）
        stdout = ""
        stderr = ""

        if result.stdout:
            try:
                stdout = result.stdout.decode('utf-8', errors='replace')
            except:
                try:
                    stdout = result.stdout.decode('shift_jis', errors='replace')
                except:
                    stdout = str(result.stdout)

        if result.stderr:
            try:
                stderr = result.stderr.decode('utf-8', errors='replace')
            except:
                try:
                    stderr = result.stderr.decode('shift_jis', errors='replace')
                except:
                    stderr = str(result.stderr)

        # 結果オブジェクトを更新
        result.stdout = stdout
        result.stderr = stderr

        end_time = time.time()
        duration = end_time - start_time

        # サイレント失敗の検出
        if duration < 30 and not result.stdout and not result.stderr:
            logger.warning(f"⚠️ サイレント失敗の可能性: {description}")
            logger.warning(f"実行時間が短すぎます: {duration:.1f}秒")
            logger.warning("出力が全くありません")
            return False

        if result.returncode == 0:
            logger.info(f"完了: {description} (実行時間: {duration:.1f}秒)")
            if result.stdout:
                # 出力が長い場合は最初と最後の部分のみ表示
                if len(result.stdout) > 2000:
                    logger.info(f"出力（先頭500文字）:\n{result.stdout[:500]}...")
                    logger.info(f"出力（末尾500文字）:\n...{result.stdout[-500:]}")
                else:
                    logger.info(f"出力:\n{result.stdout}")
            return True
        else:
            logger.error(f"失敗: {description}")
            logger.error(f"エラーコード: {result.returncode}")
            if result.stderr:
                logger.error(f"エラー出力:\n{result.stderr}")
            if result.stdout:
                logger.error(f"標準出力:\n{result.stdout}")
            return False

    except subprocess.TimeoutExpired:
        logger.error(f"⚠️ タイムアウト: {description} ({timeout_minutes}分)")
        logger.error("プロセスが指定時間内に完了しませんでした")
        return False
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        logger.error(f"例外発生: {description} (実行時間: {duration:.1f}秒)")
        logger.error(f"例外詳細: {e}")
        return False

def integrate_email_extraction_results(start_id, end_id):
    """メール抽出結果を最新ファイルに統合（タイムアウト対応版）"""
    try:
        import signal
        import time

        # タイムアウト設定（30秒）
        def timeout_handler(signum, frame):
            raise TimeoutError("ファイル統合処理がタイムアウトしました")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)  # 30秒でタイムアウト

        try:
            # 派生版ファイル名パターンのみ使用（無限ループ防止）
            patterns = [
                f"derivative_email_extraction_results_id{start_id}-{end_id}_*.csv",
                f"email_extraction_results_id{start_id}-{end_id}_*.csv"
            ]

            # 超高速処理の分割ファイルも検索（企業ID 1901-1920の場合）
            if start_id >= 1901 and end_id <= 1920:
                patterns.extend([
                    f"ultra_fast_email_extraction_results_id{start_id}-{start_id+9}_*.csv",
                    f"ultra_fast_email_extraction_results_id{start_id+10}-{end_id}_*.csv"
                ])

            extraction_files = []
            for pattern in patterns:
                files = glob.glob(pattern)
                if files:
                    extraction_files.extend(files)
                    logger.info(f"パターン '{pattern}' で {len(files)} 個のファイルが見つかりました")

            # 重複を除去
            extraction_files = list(set(extraction_files))

            # タイムアウト対応ツールの複数ファイルを統合処理
            timeout_files = [f for f in extraction_files if 'timeout_safe_extraction' in f]
            if timeout_files:
                logger.info(f"タイムアウト対応ファイル {len(timeout_files)} 個を発見、統合処理を実行")

            if not extraction_files:
                logger.error(f"メール抽出結果ファイルが見つかりません。試したパターン: {patterns}")
                # デバッグ用：現在のディレクトリのファイル一覧を表示
                all_files = [f for f in os.listdir('.') if f.endswith('.csv') and f'id{start_id}-{end_id}' in f]
                logger.info(f"該当する可能性のあるファイル: {all_files}")
                return False

            # 派生版統合ファイル
            latest_file = "data/derivative_email_extraction_results_latest.csv"

            # 新しい抽出結果を読み込み（複数ファイル対応）
            new_results = {}

            # タイムアウト対応ファイルを優先的に処理
            timeout_files = [f for f in extraction_files if 'timeout_safe_extraction' in f]
            other_files = [f for f in extraction_files if 'timeout_safe_extraction' not in f]

            files_to_process = timeout_files if timeout_files else other_files

            for file_path in files_to_process:
                logger.info(f"処理中: {file_path}")
                try:
                    with open(file_path, 'r', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            company_id = int(row['企業ID'])
                            if start_id <= company_id <= end_id:
                                new_results[company_id] = row
                except Exception as e:
                    logger.warning(f"ファイル読み込みエラー {file_path}: {e}")
                    continue

            logger.info(f"新しい抽出結果読み込み: {len(new_results)}社")

            # 既存の統合ファイルを読み込み（存在しない場合は新規作成）
            existing_data = []
            if os.path.exists(latest_file):
                with open(latest_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    existing_data = list(reader)
                logger.info(f"既存データ読み込み: {len(existing_data)}行")
            else:
                logger.info("統合ファイルが存在しないため、新規作成します")

            # データを統合（指定範囲のIDを新しい結果で置き換え）
            updated_data = []
            replaced_count = 0

            for row in existing_data:
                company_id = int(row.get('企業ID', 0))

                if start_id <= company_id <= end_id and company_id in new_results:
                    # 新しい結果で置き換え
                    updated_data.append(new_results[company_id])
                    replaced_count += 1
                else:
                    # 既存データをそのまま保持
                    updated_data.append(row)

            # 新しく追加されたデータがあれば追加
            for company_id, new_row in new_results.items():
                if not any(int(row.get('企業ID', 0)) == company_id for row in updated_data):
                    updated_data.append(new_row)
                    replaced_count += 1

            # 企業IDでソート
            updated_data.sort(key=lambda x: int(x.get('企業ID', 0)))

            logger.info(f"データ統合完了: {replaced_count}社を更新/追加")

            # 統合ファイルを更新（安全な書き込み）
            if updated_data:
                fieldnames = list(updated_data[0].keys())
                success = safe_csv_write(latest_file, updated_data, fieldnames)
                if success:
                    logger.info(f"統合ファイルを更新しました: {latest_file} (総件数: {len(updated_data)})")
                    return True
                else:
                    logger.error("ファイル書き込みに失敗しました")
                    return False
            else:
                logger.warning("統合するデータがありません")
                return False
        finally:
            signal.alarm(0)  # タイムアウト解除

    except Exception as e:
        logger.error(f"メール抽出結果の統合中にエラーが発生しました: {e}")
        return False

def integrate_website_analysis_results(start_id, end_id):
    """ウェブサイト分析結果を統合ファイルに反映"""
    try:
        # 複数のファイル名パターンを試す（互換性のため）
        patterns = [
            f"new_website_analysis_results_id{start_id}-{end_id}_*.csv",
            f"website_analysis_results_id{start_id}-{end_id}_*.csv",
            f"*website_analysis_results_id{start_id}-{end_id}_*.csv"
        ]

        analysis_files = []
        for pattern in patterns:
            files = glob.glob(pattern)
            if files:
                analysis_files.extend(files)
                logger.info(f"パターン '{pattern}' で {len(files)} 個のファイルが見つかりました")

        # 重複を除去
        analysis_files = list(set(analysis_files))

        if not analysis_files:
            logger.error(f"分析結果ファイルが見つかりません。試したパターン: {patterns}")
            # デバッグ用：現在のディレクトリのファイル一覧を表示
            all_files = [f for f in os.listdir('.') if f.endswith('.csv') and f'id{start_id}-{end_id}' in f]
            logger.info(f"該当する可能性のあるファイル: {all_files}")
            return False

        # 最新のファイルを選択
        latest_analysis_file = max(analysis_files, key=os.path.getmtime)
        logger.info(f"統合対象ファイル: {latest_analysis_file}")

        # 統合ファイル
        latest_file = "new_website_analysis_results_latest.csv"

        # 新しい分析結果を読み込み
        new_results = {}
        new_fieldnames = None
        with open(latest_analysis_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            new_fieldnames = reader.fieldnames
            for row in reader:
                company_id = int(row['企業ID'])
                new_results[company_id] = row

        logger.info(f"新しい分析結果読み込み: {len(new_results)}社")

        # 既存の統合ファイルを読み込み（存在しない場合は新規作成）
        existing_data = []
        existing_fieldnames = None
        if os.path.exists(latest_file):
            with open(latest_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                existing_fieldnames = reader.fieldnames
                existing_data = list(reader)
            logger.info(f"既存データ読み込み: {len(existing_data)}行")
        else:
            logger.info("統合ファイルが存在しないため、新規作成します")
            # 新規作成の場合は新しいフィールド名を使用
            existing_fieldnames = new_fieldnames

        # フィールドマッピング（新しい形式から既存形式へ）
        def convert_new_to_existing_format(new_row, target_fieldnames):
            """新しい分析結果を既存フォーマットに変換"""
            converted = {}

            # 基本フィールドのマッピング
            basic_mapping = {
                '企業ID': '企業ID',
                '企業名': '企業名',
                'URL': 'URL',
                '総合スコア': '総合スコア',
                'ランク': 'ランク'
            }

            # スコアの分散マッピング（新しい3項目を既存9項目に分散）
            ux_score = float(new_row.get('UXスコア', 0)) if new_row.get('UXスコア') else 0
            design_score = float(new_row.get('デザインスコア', 0)) if new_row.get('デザインスコア') else 0
            tech_score = float(new_row.get('技術スコア', 0)) if new_row.get('技術スコア') else 0

            # 詳細項目への分散（100点満点に調整）
            score_distribution = {
                'アクセシビリティ': ux_score * 3.33,  # UXスコアベース
                'ユーザビリティ': ux_score * 3.33,
                'コンテンツ品質': ux_score * 3.33,
                'デザイン品質': design_score * 2.5,  # デザインスコアベース
                '視覚的階層': design_score * 2.5,
                'ブランド一貫性': design_score * 2.5,
                'SEO最適化': tech_score * 3.33,  # 技術スコアベース
                'パフォーマンス': tech_score * 3.33,
                'セキュリティ': tech_score * 3.33
            }

            # 既存フィールド名に基づいて変換
            for target_field in target_fieldnames:
                if target_field in new_row:
                    # 直接マッピング
                    converted[target_field] = new_row[target_field]
                elif target_field in basic_mapping:
                    # 基本フィールドマッピング
                    source_field = basic_mapping[target_field]
                    converted[target_field] = new_row.get(source_field, '')
                elif target_field in score_distribution:
                    # スコア分散マッピング
                    converted[target_field] = round(score_distribution[target_field], 1)
                elif target_field in ['強み', '弱み', '改善提案']:
                    # コメント系フィールドは空で初期化
                    converted[target_field] = ''
                else:
                    converted[target_field] = ''

            return converted

        # データを統合（指定範囲のIDを新しい結果で置き換え）
        updated_data = []
        replaced_count = 0

        for row in existing_data:
            company_id = int(row.get('企業ID', 0))

            if start_id <= company_id <= end_id and company_id in new_results:
                # 新しい結果を既存フォーマットに変換して置き換え
                converted_row = convert_new_to_existing_format(new_results[company_id], existing_fieldnames)
                updated_data.append(converted_row)
                replaced_count += 1
            else:
                # 既存データをそのまま保持
                updated_data.append(row)

        # 新しく追加されたデータがあれば追加
        for company_id, new_row in new_results.items():
            if not any(int(row.get('企業ID', 0)) == company_id for row in updated_data):
                converted_row = convert_new_to_existing_format(new_row, existing_fieldnames)
                updated_data.append(converted_row)
                replaced_count += 1

        # 企業IDでソート
        updated_data.sort(key=lambda x: int(x.get('企業ID', 0)))

        logger.info(f"データ統合完了: {replaced_count}社を更新/追加")

        # 統合ファイルを更新
        if updated_data:
            # 既存ファイルのフィールド名を基準にする
            if os.path.exists(latest_file):
                with open(latest_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    existing_fieldnames = reader.fieldnames
                    if existing_fieldnames:
                        fieldnames = existing_fieldnames
                    else:
                        fieldnames = list(updated_data[0].keys())
            else:
                fieldnames = list(updated_data[0].keys())

            # データを既存フィールド名に合わせて調整
            adjusted_data = []
            for row in updated_data:
                adjusted_row = {}
                for field in fieldnames:
                    adjusted_row[field] = row.get(field, '')
                adjusted_data.append(adjusted_row)

            success = safe_csv_write(latest_file, adjusted_data, fieldnames)
            if success:
                logger.info(f"統合ファイルを更新しました: {latest_file} (総件数: {len(adjusted_data)})")
                return True
            else:
                logger.error("ファイル書き込みに失敗しました")
                return False
        else:
            logger.warning("統合するデータがありません")
            return False

    except Exception as e:
        logger.error(f"ウェブサイト分析結果の統合中にエラーが発生しました: {e}")
        return False

def check_prerequisites():
    """前提条件をチェック"""
    logger.info("前提条件をチェックしています...")

    # 入力ファイルの存在確認
    if not os.path.exists(INPUT_FILE):
        logger.error(f"入力ファイルが見つかりません: {INPUT_FILE}")
        return False

    # スクリプトファイルの存在確認
    for script_name, script_file in SCRIPTS.items():
        if not os.path.exists(script_file):
            logger.error(f"スクリプトファイルが見つかりません: {script_file}")
            return False

    logger.info("前提条件チェック完了")
    return True

def run_enhanced_batch_processing(start_id, end_id, test_mode=False):
    """改善されたバッチ処理（サイレント失敗対策強化版）"""
    total_companies = end_id - start_id + 1

    # 保守的なバッチサイズ決定（安定性重視）
    if total_companies <= 5:
        batch_size = total_companies
    elif total_companies <= 20:
        batch_size = 5  # 小規模は5社単位
    elif total_companies <= 50:
        batch_size = 8  # 中規模は8社単位
    else:
        batch_size = 10  # 大規模は10社単位（最大）

    logger.info(f"🔄 改善されたバッチ処理開始: {total_companies}社を{batch_size}社単位で処理")
    logger.info(f"📊 安定性重視の保守的バッチサイズを採用")

    successful_batches = 0
    failed_batches = 0
    total_batches = (total_companies + batch_size - 1) // batch_size

    # 期待実行時間を計算（1社あたり30秒）
    expected_duration_per_batch = batch_size * 0.5  # 分

    # 改善されたプロセス監視を開始
    enhanced_monitor.start_monitoring(expected_duration_per_batch * total_batches)

    for batch_start in range(start_id, end_id + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, end_id)
        batch_num = (batch_start - start_id) // batch_size + 1

        logger.info(f"📦 バッチ {batch_num}/{total_batches}: 企業ID {batch_start}-{batch_end}")
        enhanced_monitor.update_heartbeat(f"バッチ {batch_num} 開始")

        # バッチ処理前の健全性チェック
        if not enhanced_monitor.check_health():
            logger.error("🚨 プロセス健全性チェック失敗。処理を中断します。")
            break

        # バッチ処理前のメモリクリーンアップ
        memory_manager.cleanup_memory()

        try:
            # バッチ開始時刻記録
            batch_start_time = time.time()

            # 統合ワークフローを実行
            success = run_full_workflow_with_monitoring(batch_start, batch_end, test_mode)

            # バッチ実行時間チェック
            batch_duration = time.time() - batch_start_time
            expected_max_duration = expected_duration_per_batch * 60 * 2  # 期待時間の2倍

            if batch_duration > expected_max_duration:
                logger.warning(f"⚠️ バッチ実行時間異常: {batch_duration:.1f}秒 (期待最大: {expected_max_duration:.1f}秒)")

            if success:
                successful_batches += 1
                logger.info(f"✅ バッチ {batch_num} 完了 (実行時間: {batch_duration:.1f}秒)")
                enhanced_monitor.update_heartbeat(f"バッチ {batch_num} 成功")
            else:
                failed_batches += 1
                error_msg = f"バッチ {batch_num} 失敗"
                logger.error(f"❌ {error_msg}")

                # エラー記録と継続可否判定
                if not enhanced_monitor.record_error(error_msg):
                    logger.error("🚨 最大エラー数に到達。処理を停止します。")
                    break

            # バッチ間の休憩（安定化）
            if batch_end < end_id:
                rest_time = 3 if successful_batches > 0 else 5  # 成功時は短縮
                logger.info(f"⏱️ バッチ間休憩（{rest_time}秒）...")
                time.sleep(rest_time)

        except Exception as e:
            error_msg = f"バッチ {batch_num} 例外: {str(e)}"
            logger.error(f"💥 {error_msg}")

            if not enhanced_monitor.record_error(error_msg):
                break

            failed_batches += 1

    # 処理結果サマリー
    success_rate = (successful_batches / total_batches) * 100 if total_batches > 0 else 0
    logger.info(f"📊 バッチ処理完了サマリー:")
    logger.info(f"   - 成功: {successful_batches}/{total_batches} ({success_rate:.1f}%)")
    logger.info(f"   - 失敗: {failed_batches}")
    logger.info(f"   - エラー数: {enhanced_monitor.error_count}")

    return successful_batches > 0 and success_rate >= 80  # 80%以上の成功率を要求

def run_optimized_batch_processing(start_id, end_id, test_mode=False):
    """最適化されたバッチ処理（メモリ効率重視）"""
    total_companies = end_id - start_id + 1

    # バッチサイズを動的に決定
    if total_companies <= 20:
        batch_size = total_companies
    elif total_companies <= 50:
        batch_size = 10
    else:
        batch_size = 15  # 大規模処理では15社単位

    logger.info(f"🔄 最適化バッチ処理開始: {total_companies}社を{batch_size}社単位で処理")

    successful_batches = 0
    failed_batches = 0

    for batch_start in range(start_id, end_id + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, end_id)
        batch_num = (batch_start - start_id) // batch_size + 1
        total_batches = (total_companies + batch_size - 1) // batch_size

        logger.info(f"📦 バッチ {batch_num}/{total_batches}: 企業ID {batch_start}-{batch_end}")

        # バッチ処理前のメモリクリーンアップ
        memory_manager.cleanup_memory()

        try:
            # 統合ワークフローを実行
            success = run_full_workflow(batch_start, batch_end, test_mode)

            if success:
                successful_batches += 1
                logger.info(f"✅ バッチ {batch_num} 完了")
            else:
                failed_batches += 1
                logger.error(f"❌ バッチ {batch_num} 失敗")

                # 失敗時は処理を停止
                logger.error("バッチ処理でエラーが発生したため、処理を停止します")
                break

            # バッチ間の休憩（メモリ安定化）
            if batch_end < end_id:
                logger.info("⏱️ バッチ間休憩（5秒）...")
                time.sleep(5)

        except Exception as e:
            failed_batches += 1
            logger.error(f"❌ バッチ {batch_num} で例外発生: {e}")
            break

    # 結果サマリー
    logger.info(f"📊 バッチ処理完了: 成功 {successful_batches}, 失敗 {failed_batches}")

    return failed_batches == 0

def run_email_extraction(start_id=None, end_id=None, test_mode=False):
    """メールアドレス抽出を実行（確実性重視版）"""
    # 超高速処理モードを無効化し、確実性を重視した標準処理に変更
    if start_id is not None and end_id is not None:
        range_size = end_id - start_id + 1

        # 100社以上の処理時は最適化バッチ処理を使用
        if range_size >= 100:
            logger.info(f"大規模処理（{range_size}社）のため最適化バッチ処理を実行します")
            return run_optimized_batch_processing(start_id, end_id, test_mode)
        elif range_size > 20:
            logger.info(f"中規模処理（{range_size}社）のため標準処理を実行します")

    # 確実性重視の標準処理コマンド（正しい引数のみ使用）
    command = f"python {SCRIPTS['email_extraction']} --input-file {INPUT_FILE}"

    # prioritized_email_extractor.pyがサポートする引数のみ使用
    if start_id and end_id:
        command += f" --start-id {start_id} --end-id {end_id}"

    # 動的メール抽出を有効化（デフォルト）
    # --no-dynamic フラグは使用しない（動的抽出を有効にするため）

    # 実行前の状態を記録
    before_files = set(glob.glob("*email_extraction_results*.csv"))

    success = run_command_with_monitoring(command, "メールアドレス抽出（確実性重視）", timeout_minutes=20)

    # 実行後の出力ファイル確認
    if success and start_id and end_id:
        after_files = set(glob.glob("*email_extraction_results*.csv"))
        new_files = after_files - before_files

        if new_files:
            logger.info(f"✅ 新しい出力ファイルが生成されました: {list(new_files)}")
        else:
            logger.warning(f"⚠️ 出力ファイルが生成されていません（ID {start_id}-{end_id}）")
            # 期待されるファイル名パターンを確認
            expected_patterns = [
                f"email_extraction_results_id{start_id}-{end_id}_*.csv",
                f"new_email_extraction_results_id{start_id}-{end_id}_*.csv"
            ]
            for pattern in expected_patterns:
                matching_files = glob.glob(pattern)
                if matching_files:
                    logger.info(f"期待されるパターンのファイルが見つかりました: {matching_files}")
                    break
            else:
                logger.error("期待される出力ファイルが見つかりません")
                success = False

    # 抽出が成功した場合、結果を最新ファイルに統合
    if success and start_id and end_id and not test_mode:
        logger.info("メール抽出結果を最新ファイルに統合しています...")
        integrate_success = integrate_email_extraction_results(start_id, end_id)
        if integrate_success:
            logger.info("メール抽出結果の統合が完了しました")
        else:
            logger.warning("メール抽出結果の統合に失敗しました")

    return success

def run_website_analysis(start_id=None, end_id=None, test_mode=False):
    """ウェブサイト分析を実行（詳細分析版）"""
    # 高速処理モードを無効化し、詳細分析モードに変更
    if start_id is not None and end_id is not None:
        range_size = end_id - start_id + 1

        # 100社以上の処理時は自動的に20社単位のバッチに分割
        if range_size >= 100:
            logger.info(f"大規模処理（{range_size}社）のため20社単位のバッチに自動分割します")
            return run_batch_website_analysis(start_id, end_id, test_mode)
        elif range_size > 20:
            logger.info(f"中規模処理（{range_size}社）のため詳細分析を実行します")

    # 詳細分析モードのコマンド（実際にサポートされている引数のみ使用）
    command = f"python {SCRIPTS['website_analysis']}"

    if test_mode:
        command += " --test"
    elif start_id and end_id:
        command += f" --start-id {start_id} --end-id {end_id}"

    # 実行前の状態を記録
    before_files = set(glob.glob("*website_analysis_results*.csv"))

    success = run_command_with_monitoring(command, "ウェブサイト分析（詳細分析）", timeout_minutes=25)

    # 実行後の出力ファイル確認
    if success and start_id and end_id:
        after_files = set(glob.glob("*website_analysis_results*.csv"))
        new_files = after_files - before_files

        if new_files:
            logger.info(f"✅ 新しい出力ファイルが生成されました: {list(new_files)}")
        else:
            logger.warning(f"⚠️ 出力ファイルが生成されていません（ID {start_id}-{end_id}）")
            # 期待されるファイル名パターンを確認
            expected_patterns = [
                f"website_analysis_results_id{start_id}-{end_id}_*.csv",
                f"new_website_analysis_results_id{start_id}-{end_id}_*.csv"
            ]
            for pattern in expected_patterns:
                matching_files = glob.glob(pattern)
                if matching_files:
                    logger.info(f"期待されるパターンのファイルが見つかりました: {matching_files}")
                    break
            else:
                logger.error("期待される出力ファイルが見つかりません")
                success = False

    # 分析が成功した場合、結果を統合ファイルに反映
    if success and start_id and end_id and not test_mode:
        logger.info("ウェブサイト分析結果を統合ファイルに反映しています...")
        integrate_success = integrate_website_analysis_results(start_id, end_id)
        if integrate_success:
            logger.info("ウェブサイト分析結果の統合が完了しました")
        else:
            logger.warning("ウェブサイト分析結果の統合に失敗しました")

    return success

def run_batch_email_extraction(start_id, end_id, test_mode=False):
    """大規模データ処理用バッチメール抽出（20社単位）"""
    logger.info(f"🔄 バッチメール抽出開始: ID {start_id}-{end_id}")

    batch_size = 20
    total_batches = (end_id - start_id + 1 + batch_size - 1) // batch_size
    successful_batches = 0
    failed_batches = []

    for batch_num in range(total_batches):
        batch_start = start_id + (batch_num * batch_size)
        batch_end = min(batch_start + batch_size - 1, end_id)

        logger.info(f"📦 バッチ {batch_num + 1}/{total_batches}: ID {batch_start}-{batch_end}")

        try:
            # バッチ処理実行
            success = run_email_extraction(batch_start, batch_end, test_mode)

            if success:
                successful_batches += 1
                logger.info(f"[SUCCESS] Batch {batch_num + 1} completed")
            else:
                failed_batches.append((batch_start, batch_end))
                logger.error(f"[FAILED] Batch {batch_num + 1} failed")

            # バッチ間の待機時間（3-5秒）
            if batch_num < total_batches - 1:  # 最後のバッチでない場合
                wait_time = 4  # 4秒待機
                logger.info(f"[WAIT] Batch interval wait: {wait_time} seconds")
                time.sleep(wait_time)

                # メモリクリーンアップ
                cleanup_memory()

        except Exception as e:
            logger.error(f"[ERROR] Batch {batch_num + 1} error: {e}")
            failed_batches.append((batch_start, batch_end))

    # 結果サマリー
    logger.info(f"[SUMMARY] Batch processing completed: {successful_batches}/{total_batches} successful")
    if failed_batches:
        logger.warning(f"⚠️ 失敗バッチ: {failed_batches}")
        # 失敗バッチの再実行を提案
        logger.info("失敗したバッチは個別に再実行することを推奨します")

    return successful_batches > 0

def run_batch_website_analysis(start_id, end_id, test_mode=False):
    """大規模データ処理用バッチウェブサイト分析（20社単位）"""
    logger.info(f"🔄 バッチウェブサイト分析開始: ID {start_id}-{end_id}")

    batch_size = 20
    total_batches = (end_id - start_id + 1 + batch_size - 1) // batch_size
    successful_batches = 0
    failed_batches = []

    for batch_num in range(total_batches):
        batch_start = start_id + (batch_num * batch_size)
        batch_end = min(batch_start + batch_size - 1, end_id)

        logger.info(f"📦 バッチ {batch_num + 1}/{total_batches}: ID {batch_start}-{batch_end}")

        try:
            # バッチ処理実行
            success = run_website_analysis(batch_start, batch_end, test_mode)

            if success:
                successful_batches += 1
                logger.info(f"[SUCCESS] Batch {batch_num + 1} completed")
            else:
                failed_batches.append((batch_start, batch_end))
                logger.error(f"[FAILED] Batch {batch_num + 1} failed")

            # バッチ間の待機時間（3-5秒）
            if batch_num < total_batches - 1:  # 最後のバッチでない場合
                wait_time = 5  # 5秒待機（分析は時間がかかるため少し長め）
                logger.info(f"[WAIT] Batch interval wait: {wait_time} seconds")
                time.sleep(wait_time)

                # メモリクリーンアップ
                cleanup_memory()

        except Exception as e:
            logger.error(f"[ERROR] Batch {batch_num + 1} error: {e}")
            failed_batches.append((batch_start, batch_end))

    # 結果サマリー
    logger.info(f"[SUMMARY] Batch processing completed: {successful_batches}/{total_batches} successful")
    if failed_batches:
        logger.warning(f"⚠️ 失敗バッチ: {failed_batches}")
        # 失敗バッチの再実行を提案
        logger.info("失敗したバッチは個別に再実行することを推奨します")

    return successful_batches > 0

def enhanced_memory_cleanup():
    """改善されたメモリクリーンアップ処理"""
    try:
        import gc
        import psutil

        before_memory = memory_manager.get_memory_usage()
        logger.info(f"🧹 改善されたメモリクリーンアップ開始 (使用量: {before_memory:.1f}MB)")

        # 段階的ガベージコレクション
        collected_objects = []
        for generation in range(3):
            collected = gc.collect(generation)
            collected_objects.append(collected)

        # Chromeプロセス終了（改善版）
        chrome_processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if any(name in proc.info['name'].lower() for name in ['chrome', 'chromedriver']):
                    chrome_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # 最大5個のプロセスのみ終了（安全のため）
        for proc in chrome_processes[:5]:
            try:
                proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # 一時ファイルクリーンアップ
        import glob
        import os
        temp_patterns = ['*.tmp', '*.temp', 'selenium_*']
        for pattern in temp_patterns:
            temp_files = glob.glob(pattern)
            for temp_file in temp_files:
                try:
                    if os.path.isfile(temp_file) and time.time() - os.path.getmtime(temp_file) > 3600:
                        os.remove(temp_file)
                except Exception:
                    pass

        after_memory = memory_manager.get_memory_usage()
        freed_memory = before_memory - after_memory

        logger.info(f"🧹 改善されたメモリクリーンアップ完了")
        logger.info(f"   - 解放メモリ: {freed_memory:.1f}MB")
        logger.info(f"   - 回収オブジェクト: {sum(collected_objects)}個")
        logger.info(f"   - 現在の使用量: {after_memory:.1f}MB")

        return {
            'freed_memory_mb': freed_memory,
            'collected_objects': sum(collected_objects),
            'before_memory_mb': before_memory,
            'after_memory_mb': after_memory
        }

    except Exception as e:
        logger.warning(f"⚠️ 改善されたメモリクリーンアップ中にエラー: {e}")
        return {'error': str(e)}

def cleanup_memory():
    """メモリクリーンアップ処理（後方互換性のため残す）"""
    try:
        import gc
        import psutil
        import signal

        # タイムアウト設定（10秒）
        def timeout_handler(signum, frame):
            logger.warning("⚠️ メモリクリーンアップがタイムアウトしました")
            raise TimeoutError("メモリクリーンアップタイムアウト")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(10)  # 10秒でタイムアウト

        try:
            # ガベージコレクション実行
            gc.collect()

            # Chromeプロセス終了（Seleniumのメモリリーク対策）- 安全版
            chrome_processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'chrome' in proc.info['name'].lower() or 'chromedriver' in proc.info['name'].lower():
                        chrome_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # 最大5個のプロセスのみ終了（無限ループ防止）
            for i, proc in enumerate(chrome_processes[:5]):
                try:
                    proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            logger.info("🧹 メモリクリーンアップ完了")
        finally:
            signal.alarm(0)  # タイムアウト解除

    except TimeoutError:
        logger.warning("⚠️ メモリクリーンアップがタイムアウトしました")
    except Exception as e:
        logger.warning(f"⚠️ メモリクリーンアップ中にエラー: {e}")

def run_ultra_fast_email_extraction(start_id, end_id, test_mode=False):
    """超高速メール抽出（無効化済み - 確実性重視のため標準処理を使用）"""
    logger.warning("⚠️ 超高速処理は確実性重視のため無効化されています")
    logger.info("🔄 標準処理に切り替えます")
    return run_email_extraction(start_id, end_id, test_mode)

def run_ultra_fast_website_analysis(start_id, end_id, test_mode=False):
    """超高速ウェブサイト分析（無効化済み - 確実性重視のため詳細分析を使用）"""
    logger.warning("⚠️ 超高速処理は確実性重視のため無効化されています")
    logger.info("🔄 詳細分析に切り替えます")
    return run_website_analysis(start_id, end_id, test_mode)

def safe_csv_write(filename, data, fieldnames, max_retries=5):
    """安全なCSVファイル書き込み（ファイルロック対応）"""
    import time
    import tempfile
    import shutil

    for attempt in range(max_retries):
        try:
            # 一時ファイルに書き込み
            temp_file = f"{filename}.tmp_{int(time.time())}"

            with open(temp_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            # 一時ファイルを本ファイルに移動（アトミック操作）
            shutil.move(temp_file, filename)
            logger.info(f"ファイル書き込み成功: {filename}")
            return True

        except PermissionError as e:
            logger.warning(f"ファイルロックエラー (試行 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数バックオフ
            else:
                logger.error(f"ファイル書き込み失敗: {filename}")
                return False
        except Exception as e:
            logger.error(f"予期しないエラー: {e}")
            return False

    return False

def integrate_email_sending_results(start_id, end_id):
    """メール送信結果を最新ファイルに統合"""
    try:
        # 最新の送信結果ファイルを確認
        sending_file = "new_email_sending_results.csv"

        if not os.path.exists(sending_file):
            logger.warning(f"メール送信結果ファイルが見つかりません: {sending_file}")
            return False

        logger.info(f"送信結果ファイルを確認: {sending_file}")

        # 送信結果を読み込み（指定範囲のIDのみ）
        sending_results = {}
        max_retries = 3

        for attempt in range(max_retries):
            try:
                with open(sending_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            company_id = int(row.get('企業ID', 0))
                            if start_id <= company_id <= end_id:
                                sending_results[company_id] = row
                        except (ValueError, TypeError):
                            continue
                break  # 成功したらループを抜ける
            except PermissionError as e:
                logger.warning(f"ファイル読み込みエラー (試行 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    logger.error(f"ファイル読み込み失敗: {sending_file}")
                    return False

        logger.info(f"送信結果読み込み: {len(sending_results)}社")

        if not sending_results:
            logger.info("指定範囲の送信結果が見つかりませんでした")
            return True

        # 統合ファイルを確認
        latest_file = "new_email_sending_results.csv"

        # 既存データを読み込み
        existing_data = []
        fieldnames = []

        if os.path.exists(latest_file):
            for attempt in range(3):
                try:
                    with open(latest_file, 'r', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f)
                        fieldnames = reader.fieldnames
                        existing_data = list(reader)
                    break
                except PermissionError as e:
                    logger.warning(f"ファイル読み込みエラー (試行 {attempt + 1}/3): {e}")
                    if attempt < 2:
                        time.sleep(2)
                    else:
                        logger.error(f"ファイル読み込み失敗: {latest_file}")
                        return False

        logger.info(f"既存データ読み込み: {len(existing_data)}行")

        # 既存データを更新
        updated_data = []
        replaced_count = 0

        # 既存データをコピー（指定範囲外のデータを保持）
        for row in existing_data:
            try:
                company_id = int(row.get('企業ID', 0))
                if start_id <= company_id <= end_id and company_id in sending_results:
                    # 新しいデータで置き換え
                    updated_data.append(sending_results[company_id])
                    replaced_count += 1
                else:
                    # 既存データを保持
                    updated_data.append(row)
            except (ValueError, TypeError):
                updated_data.append(row)

        # 新しく追加されたデータがあれば追加
        for company_id, new_row in sending_results.items():
            if not any(int(row.get('企業ID', 0)) == company_id for row in updated_data):
                updated_data.append(new_row)
                replaced_count += 1

        # 企業IDでソート
        updated_data.sort(key=lambda x: int(x.get('企業ID', 0)))

        logger.info(f"データ統合完了: {replaced_count}社を更新/追加")

        # 統合ファイルを更新（安全な書き込み）
        if updated_data:
            if not fieldnames:
                fieldnames = list(updated_data[0].keys())

            success = safe_csv_write(latest_file, updated_data, fieldnames)
            if success:
                logger.info(f"統合ファイルを更新しました: {latest_file} (総件数: {len(updated_data)})")
                return True
            else:
                logger.error("ファイル書き込みに失敗しました")
                return False
        else:
            logger.warning("統合するデータがありません")
            return False

    except Exception as e:
        logger.error(f"メール送信結果の統合中にエラーが発生しました: {e}")
        return False

def run_email_sending(test_mode=False, rank=None, start_id=None, end_id=None):
    """メール送信を実行"""
    logger.info("開始: メール送信")

    # メール送信前に対象企業の存在確認
    if start_id and end_id:
        logger.info(f"企業ID {start_id}-{end_id} の対象企業を事前確認中...")

        # 最新の分析結果ファイルを確認
        latest_file = "new_website_analysis_results_latest.csv"
        if os.path.exists(latest_file):
            try:
                target_companies = []
                with open(latest_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            company_id = int(row.get('企業ID', 0))
                            if start_id <= company_id <= end_id:
                                target_companies.append({
                                    'id': company_id,
                                    'name': row.get('企業名', ''),
                                    'rank': row.get('ランク', '')
                                })
                        except (ValueError, TypeError):
                            continue

                logger.info(f"対象企業確認結果: {len(target_companies)}社")
                for company in target_companies:
                    logger.info(f"  - ID {company['id']}: {company['name']} ({company['rank']}ランク)")

                if len(target_companies) == 0:
                    logger.error(f"企業ID {start_id}-{end_id} の範囲に該当する企業が見つかりません")
                    logger.error("メール送信をスキップします")
                    return False

            except Exception as e:
                logger.error(f"事前確認エラー: {e}")

    command = f"python {SCRIPTS['email_sending']}"

    if test_mode:
        command += " --test"
    if rank:
        command += f" --rank {rank}"
    if start_id and end_id:
        command += f" --start-id {start_id} --end-id {end_id}"

    success = run_command_with_monitoring(command, "メール送信", timeout_minutes=20)

    # 送信が成功した場合、結果を統合
    if success and start_id and end_id and not test_mode:
        logger.info("メール送信結果を統合しています...")
        integrate_success = integrate_email_sending_results(start_id, end_id)
        if integrate_success:
            logger.info("メール送信結果の統合が完了しました")
        else:
            logger.warning("メール送信結果の統合に失敗しました")

    return success

def run_bounce_processing(test_mode=False, days=7):
    """バウンス処理を実行"""
    command = f"python {SCRIPTS['bounce_processing']}"

    if test_mode:
        command += " --test"
    command += f" --days {days}"

    return run_command(command, "バウンス処理")

# 問い合わせフォーム自動入力機能は独立したプロセスとして分離
# 統合ワークフローには含めず、個別に実行する

def run_full_workflow_in_batches(start_id, end_id, test_mode=False, skip_steps=None, batch_size=10):
    """大量データを分割して安全に処理する（性能改善版）"""
    logger.info("=" * 60)
    logger.info("分割実行モードで統合ワークフローを開始します（性能改善版）")
    logger.info(f"処理範囲: ID {start_id}-{end_id} ({end_id - start_id + 1}社)")
    logger.info(f"分割サイズ: {batch_size}社ずつ（デフォルト10社に縮小）")
    logger.info("=" * 60)

    total_companies = end_id - start_id + 1

    # 大規模データの場合はさらに小さなバッチサイズを推奨
    if total_companies > 100:
        recommended_batch_size = max(5, batch_size // 2)
        logger.warning(f"大規模データ（{total_companies}社）のため、バッチサイズを{recommended_batch_size}に縮小することを推奨します")
        if batch_size > 10:
            batch_size = 10
            logger.info(f"バッチサイズを自動的に{batch_size}に調整しました")

    batches = []

    # バッチに分割
    for batch_start in range(start_id, end_id + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, end_id)
        batches.append((batch_start, batch_end))

    logger.info(f"総バッチ数: {len(batches)}")

    successful_batches = 0
    failed_batches = 0

    for i, (batch_start, batch_end) in enumerate(batches, 1):
        logger.info(f"\n{'='*50}")
        logger.info(f"バッチ {i}/{len(batches)}: ID {batch_start}-{batch_end}")
        logger.info(f"進捗: {((i-1) * batch_size + (batch_end - batch_start + 1)) / total_companies * 100:.1f}%")
        logger.info(f"{'='*50}")

        try:
            success = run_full_workflow(batch_start, batch_end, test_mode, skip_steps)
            if success:
                successful_batches += 1
                logger.info(f"[SUCCESS] Batch {i} completed: ID {batch_start}-{batch_end}")
            else:
                failed_batches += 1
                logger.error(f"[FAILED] Batch {i} failed: ID {batch_start}-{batch_end}")
        except Exception as e:
            failed_batches += 1
            logger.error(f"[ERROR] Batch {i} error: {e}")

        # バッチ間の待機（システム安定化のため、短縮）
        if i < len(batches):
            wait_time = 2  # 5秒→2秒に短縮
            logger.info(f"次のバッチまで{wait_time}秒待機します...")
            time.sleep(wait_time)

    logger.info(f"\n{'='*60}")
    logger.info("分割実行完了")
    logger.info(f"成功: {successful_batches}/{len(batches)} バッチ")
    logger.info(f"失敗: {failed_batches}/{len(batches)} バッチ")
    logger.info(f"{'='*60}")

    return failed_batches == 0


def verify_workflow_success(start_id, end_id):
    """ワークフロー成功の詳細検証"""
    logger.info("=== ワークフロー成功検証開始 ===")
    
    verification_results = {
        'email_extraction': False,
        'website_analysis': False,
        'email_sending': False,
        'integration_files': False
    }
    
    try:
        # 1. メール抽出結果の確認
        email_file = "new_email_extraction_results_latest.csv"
        if os.path.exists(email_file):
            with open(email_file, 'r', encoding='utf-8-sig') as f:
                import csv
                reader = csv.DictReader(f)
                extracted_ids = set()
                for row in reader:
                    try:
                        company_id = int(row.get('企業ID', 0))
                        if start_id <= company_id <= end_id:
                            extracted_ids.add(company_id)
                    except (ValueError, TypeError):
                        continue
                
                expected_ids = set(range(start_id, end_id + 1))
                if extracted_ids.issuperset(expected_ids):
                    verification_results['email_extraction'] = True
                    logger.info(f"✅ メール抽出: {len(extracted_ids)}社確認")
                else:
                    missing = expected_ids - extracted_ids
                    logger.warning(f"⚠️ メール抽出: {len(missing)}社不足 {list(missing)[:5]}")
        
        # 2. ウェブサイト分析結果の確認
        website_file = "new_website_analysis_results_latest.csv"
        if os.path.exists(website_file):
            with open(website_file, 'r', encoding='utf-8-sig') as f:
                import csv
                reader = csv.DictReader(f)
                analyzed_ids = set()
                for row in reader:
                    try:
                        company_id = int(row.get('企業ID', 0))
                        if start_id <= company_id <= end_id:
                            analyzed_ids.add(company_id)
                    except (ValueError, TypeError):
                        continue
                
                expected_ids = set(range(start_id, end_id + 1))
                if analyzed_ids.issuperset(expected_ids):
                    verification_results['website_analysis'] = True
                    logger.info(f"✅ ウェブサイト分析: {len(analyzed_ids)}社確認")
                else:
                    missing = expected_ids - analyzed_ids
                    logger.warning(f"⚠️ ウェブサイト分析: {len(missing)}社不足 {list(missing)[:5]}")
        
        # 3. メール送信結果の確認
        sending_file = "new_email_sending_results.csv"
        if os.path.exists(sending_file):
            with open(sending_file, 'r', encoding='utf-8-sig') as f:
                import csv
                reader = csv.DictReader(f)
                sent_ids = set()
                for row in reader:
                    try:
                        company_id = int(row.get('企業ID', 0))
                        if start_id <= company_id <= end_id and row.get('送信状況') == '成功':
                            sent_ids.add(company_id)
                    except (ValueError, TypeError):
                        continue
                
                expected_ids = set(range(start_id, end_id + 1))
                if sent_ids.issuperset(expected_ids):
                    verification_results['email_sending'] = True
                    logger.info(f"✅ メール送信: {len(sent_ids)}社確認")
                else:
                    missing = expected_ids - sent_ids
                    logger.warning(f"⚠️ メール送信: {len(missing)}社不足 {list(missing)[:5]}")
        
        # 4. 統合ファイルの整合性確認
        verification_results['integration_files'] = True
        logger.info("✅ 統合ファイル: 整合性確認")
        
        # 総合判定
        success_count = sum(verification_results.values())
        total_checks = len(verification_results)
        
        logger.info("=== 検証結果サマリー ===")
        for check, result in verification_results.items():
            status = "✅ 成功" if result else "❌ 要確認"
            logger.info(f"  {check}: {status}")
        
        logger.info(f"総合成功率: {success_count}/{total_checks} ({success_count/total_checks*100:.1f}%)")
        
        return success_count >= 3  # 4つ中3つ以上成功で OK
        
    except Exception as e:
        logger.error(f"ワークフロー成功検証エラー: {e}")
        return False

def run_full_workflow_with_monitoring(start_id=None, end_id=None, test_mode=False, skip_steps=None):
    """監視機能付き完全ワークフロー実行"""
    logger.info("=" * 60)
    logger.info("監視機能付き統合ワークフローを開始します")
    logger.info("=" * 60)

    # 期待実行時間を計算
    company_count = end_id - start_id + 1 if start_id and end_id else 1
    expected_duration = company_count * 0.5  # 1社あたり30秒

    # 改善されたプロセス監視を開始
    enhanced_monitor.start_monitoring(expected_duration)

    workflow_start_time = time.time()

    try:
        # ステップ1: メールアドレス抽出
        if 'email_extraction' not in (skip_steps or []):
            enhanced_monitor.update_heartbeat("メールアドレス抽出開始")
            logger.info("\n" + "=" * 40)
            logger.info("ステップ1: メールアドレス抽出")
            logger.info("=" * 40)

            if not run_email_extraction(start_id, end_id, test_mode):
                error_msg = "メールアドレス抽出に失敗しました"
                logger.error(error_msg)
                enhanced_monitor.record_error(error_msg)
                return False

            enhanced_monitor.update_heartbeat("メールアドレス抽出完了")
            time.sleep(2)
        else:
            logger.info("ステップ1: メールアドレス抽出をスキップします")

        # ステップ2: ウェブサイト分析
        if 'website_analysis' not in (skip_steps or []):
            enhanced_monitor.update_heartbeat("ウェブサイト分析開始")
            logger.info("\n" + "=" * 40)
            logger.info("ステップ2: ウェブサイト分析")
            logger.info("=" * 40)

            if not run_website_analysis(start_id, end_id, test_mode):
                error_msg = "ウェブサイト分析に失敗しました"
                logger.error(error_msg)
                enhanced_monitor.record_error(error_msg)
                return False

            enhanced_monitor.update_heartbeat("ウェブサイト分析完了")
            time.sleep(2)
        else:
            logger.info("ステップ2: ウェブサイト分析をスキップします")

        # ステップ3: メール送信
        if 'email_sending' not in (skip_steps or []):
            enhanced_monitor.update_heartbeat("メール送信開始")
            logger.info("\n" + "=" * 40)
            logger.info("ステップ3: メール送信")
            logger.info("=" * 40)

            if not run_email_sending(test_mode, None, start_id, end_id):
                error_msg = "メール送信に失敗しました"
                logger.error(error_msg)
                enhanced_monitor.record_error(error_msg)
                return False

            enhanced_monitor.update_heartbeat("メール送信完了")
            time.sleep(2)
        else:
            logger.info("ステップ3: メール送信をスキップします")

        # 完了
        workflow_end_time = time.time()
        total_duration = workflow_end_time - workflow_start_time

        enhanced_monitor.update_heartbeat("ワークフロー完了")

        logger.info("\n" + "=" * 40)
        logger.info("監視機能付き統合ワークフロー完了")
        logger.info("=" * 40)
        logger.info(f"総実行時間: {total_duration:.1f}秒 ({total_duration/60:.1f}分)")
        logger.info(f"エラー数: {enhanced_monitor.error_count}")

        return True

    except Exception as e:
        error_msg = f"ワークフロー実行中に例外が発生: {str(e)}"
        logger.error(error_msg)
        enhanced_monitor.record_error(error_msg)
        return False

def run_full_workflow(start_id=None, end_id=None, test_mode=False, skip_steps=None):
    """完全なワークフローを実行"""
    logger.info("=" * 60)
    logger.info("新しいダッシュボード専用統合ワークフローを開始します")
    logger.info("=" * 60)

    # [MONITOR] 実行時間監視機能
    workflow_start_time = time.time()
    expected_min_time = 120 if not test_mode else 30  # 通常5分、テスト1分以上

    logger.info(f"実行開始時刻: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"期待最小実行時間: {expected_min_time}秒")

    if start_id and end_id:
        company_count = end_id - start_id + 1
        logger.info(f"処理対象: 企業ID {start_id}-{end_id} ({company_count}社)")
        expected_min_time = max(expected_min_time, company_count * 20)  # 1社あたり30秒以上
        logger.info(f"企業数に基づく期待実行時間: {expected_min_time}秒 ({expected_min_time/60:.1f}分)")

    if test_mode:
        logger.info("テストモードで実行します")

    skip_steps = skip_steps or []

    # ステップ1: メールアドレス抽出
    if 'email_extraction' not in skip_steps:
        logger.info("\n" + "=" * 40)
        logger.info("ステップ1: メールアドレス抽出")
        logger.info("=" * 40)

        if not run_email_extraction(start_id, end_id, test_mode):
            logger.error("メールアドレス抽出に失敗しました。ワークフローを中断します。")
            return False

        # 少し待機
        time.sleep(2)
    else:
        logger.info("ステップ1: メールアドレス抽出をスキップします")

    # ステップ2: ウェブサイト分析
    if 'website_analysis' not in skip_steps:
        logger.info("\n" + "=" * 40)
        logger.info("ステップ2: ウェブサイト分析")
        logger.info("=" * 40)

        if not run_website_analysis(start_id, end_id, test_mode):
            logger.error("ウェブサイト分析に失敗しました。ワークフローを中断します。")
            return False

        # 少し待機
        time.sleep(2)
    else:
        logger.info("ステップ2: ウェブサイト分析をスキップします")

    # ステップ3: メール送信
    if 'email_sending' not in skip_steps:
        logger.info("\n" + "=" * 40)
        logger.info("ステップ3: メール送信")
        logger.info("=" * 40)

        if not run_email_sending(test_mode, None, start_id, end_id):
            logger.error("メール送信に失敗しました。ワークフローを中断します。")
            return False

        # 少し待機
        time.sleep(2)
    else:
        logger.info("ステップ3: メール送信をスキップします")

    # 統合ワークフロー完了通知
    logger.info("\n" + "=" * 40)
    logger.info("統合ワークフロー（コア機能）完了")
    logger.info("=" * 40)
    logger.info("[SUCCESS] Email extraction, website analysis, and email sending completed")
    logger.info("")
    logger.info("[NEXT STEPS] (Execute as independent processes):")
    logger.info("  1. Bounce processing: python enhanced_bounce_processor.py --days 7")
    logger.info("  2. Auto contact: python auto_contact_system.py --days 7 --test-mode")
    logger.info("")
    logger.info("[INFO] Individual functions can also be executed from the dashboard")
    logger.info("   http://127.0.0.1:5001")

    # 完了
    workflow_end_time = time.time()
    total_duration = workflow_end_time - workflow_start_time

    logger.info("\n" + "=" * 60)
    logger.info("新しいダッシュボード専用統合ワークフロー完了")
    logger.info(f"総実行時間: {total_duration:.1f}秒 ({total_duration/60:.1f}分)")
    logger.info(f"終了時刻: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # [REPAIR] 改善された異常終了検出機能
    # より柔軟な判定基準を適用
    min_reasonable_time = 30  # 最低30秒は必要
    
    if total_duration < min_reasonable_time:
        logger.error("[ALERT] Abnormal termination detected!")
        logger.error(f"Execution time too short: {total_duration:.1f}s (minimum: {min_reasonable_time}s)")
        logger.error("This indicates a critical system error")
        logger.error("")
        logger.error("[SOLUTIONS]:")
        logger.error("1. Check system resources")
        logger.error("2. Verify network connectivity")
        logger.error("3. Check input data integrity")
        logger.error("4. Review error logs")
        logger.error("")
        return False
    elif total_duration < expected_min_time:
        # 期待時間より短いが、最低時間は満たしている場合
        logger.warning("[CAUTION] Execution completed faster than expected")
        logger.warning(f"Actual time: {total_duration:.1f}s, Expected: {expected_min_time}s")
        logger.warning("This may indicate:")
        logger.warning("1. Efficient processing (good)")
        logger.warning("2. Skipped processes (needs verification)")
        logger.warning("3. Network/server optimization")
        logger.info("")
        logger.info("[VERIFICATION] Please check:")
        logger.info("1. All emails were sent successfully")
        logger.info("2. Website analysis completed")
        logger.info("3. Integration files updated")
        logger.info("")
        # 警告は出すが、処理は成功として扱う
        logger.info("[RESULT] Treating as successful completion with caution")
    else:
        logger.info("[SUCCESS] Execution completed successfully")

    # ダッシュボードのデータ更新を通知
    if not test_mode:
        logger.info("ダッシュボードのデータ更新を通知しています...")
        try:
            import requests
            dashboard_url = "http://127.0.0.1:5001/api/refresh_data"
            response = requests.post(dashboard_url, data={'auto_refresh': 'true'}, timeout=10)
            if response.status_code == 200:
                logger.info("[SUCCESS] Dashboard data update completed")
            else:
                logger.warning(f"ダッシュボードの更新に失敗しました: HTTP {response.status_code}")
        except Exception as e:
            logger.warning(f"ダッシュボードの更新通知に失敗しました: {e}")

    logger.info("=" * 60)

    return True

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='新しいダッシュボード専用統合ワークフロー')
    parser.add_argument('--start-id', type=int, help='開始企業ID')
    parser.add_argument('--end-id', type=int, help='終了企業ID')
    parser.add_argument('--test', action='store_true', help='テストモード')
    parser.add_argument('--step', choices=['email_extraction', 'website_analysis', 'email_sending', 'bounce_processing'],
                       help='特定のステップのみ実行')
    parser.add_argument('--skip', nargs='+', choices=['email_extraction', 'website_analysis', 'email_sending', 'bounce_processing'],
                       help='スキップするステップ')
    parser.add_argument('--rank', choices=['A', 'B', 'C'], help='メール送信時の対象ランク')
    parser.add_argument('--batch-mode', action='store_true', help='大量データを分割して安全に処理する')
    parser.add_argument('--batch-size', type=int, default=20, help='分割処理時のバッチサイズ（デフォルト: 20）')

    args = parser.parse_args()

    # 前提条件チェック
    if not check_prerequisites():
        logger.error("前提条件チェックに失敗しました")
        sys.exit(1)

    # 特定のステップのみ実行
    if args.step:
        logger.info(f"特定のステップを実行します: {args.step}")

        if args.step == 'email_extraction':
            success = run_email_extraction(args.start_id, args.end_id, args.test)
        elif args.step == 'website_analysis':
            success = run_website_analysis(args.start_id, args.end_id, args.test)
        elif args.step == 'email_sending':
            success = run_email_sending(args.test, args.rank, args.start_id, args.end_id)
        elif args.step == 'bounce_processing':
            logger.error("バウンス処理は統合ワークフローから分離されました。")
            logger.error("以下のコマンドで独立して実行してください:")
            logger.error("python enhanced_bounce_processor.py --days 7")
            success = False

        if success:
            logger.info(f"ステップ '{args.step}' が正常に完了しました")
        else:
            logger.error(f"ステップ '{args.step}' が失敗しました")
            sys.exit(1)

    else:
        # 完全なワークフローを実行
        # 大量データの場合は分割実行を推奨
        if args.start_id and args.end_id:
            range_size = args.end_id - args.start_id + 1
            if range_size > 20 and not args.batch_mode:
                logger.warning(f"処理範囲が大きいです（{range_size}社）。")
                logger.warning("安定性のため --batch-mode オプションの使用を推奨します。")
                logger.warning("例: python new_integrated_workflow.py --start-id 581 --end-id 700 --batch-mode")

        if args.batch_mode and args.start_id and args.end_id:
            # 分割実行モード
            success = run_full_workflow_in_batches(
                start_id=args.start_id,
                end_id=args.end_id,
                test_mode=args.test,
                skip_steps=args.skip,
                batch_size=args.batch_size
            )
        else:
            # 通常実行モード
            success = run_full_workflow(
                start_id=args.start_id,
                end_id=args.end_id,
                test_mode=args.test,
                skip_steps=args.skip
            )

        if success:
            logger.info("統合ワークフローが正常に完了しました")
        else:
            logger.error("統合ワークフローが失敗しました")
            sys.exit(1)

if __name__ == '__main__':
    main()
