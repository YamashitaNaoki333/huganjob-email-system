#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
派生版広告営業ワークフロー
ウェブサイト分析をスキップした広告運用代行営業専用ワークフロー
"""

import os
import sys
import logging
import subprocess
import argparse
import time
from datetime import datetime
import json

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdWorkflowManager:
    """広告営業ワークフロー管理クラス"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.progress_file = 'data/derivative_ad_workflow_progress.json'
        self.results = {
            'data_conversion': {'status': 'not_started', 'start_time': None, 'end_time': None},
            'email_extraction': {'status': 'not_started', 'start_time': None, 'end_time': None},
            'email_sending': {'status': 'not_started', 'start_time': None, 'end_time': None},
            'workflow_complete': {'status': 'not_started', 'start_time': None, 'end_time': None}
        }
    
    def update_progress(self, step, status, message=None):
        """進捗を更新"""
        try:
            self.results[step]['status'] = status
            if status == 'running':
                self.results[step]['start_time'] = datetime.now().isoformat()
            elif status in ['completed', 'failed']:
                self.results[step]['end_time'] = datetime.now().isoformat()
            
            if message:
                self.results[step]['message'] = message
            
            # 進捗ファイルに保存
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"進捗更新: {step} - {status}")
            
        except Exception as e:
            logger.error(f"進捗更新エラー: {e}")
    
    def run_command(self, command, step_name):
        """コマンドを実行"""
        try:
            logger.info(f"実行開始: {step_name}")
            logger.info(f"コマンド: {command}")
            
            self.update_progress(step_name, 'running')
            
            # コマンド実行
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                logger.info(f"実行成功: {step_name}")
                self.update_progress(step_name, 'completed', f"正常完了: {step_name}")
                return True
            else:
                logger.error(f"実行失敗: {step_name}")
                logger.error(f"エラー出力: {result.stderr}")
                self.update_progress(step_name, 'failed', f"エラー: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"コマンド実行エラー ({step_name}): {e}")
            self.update_progress(step_name, 'failed', f"例外エラー: {str(e)}")
            return False
    
    def step1_data_conversion(self):
        """ステップ1: データ変換"""
        print("\n" + "="*60)
        print("📊 ステップ1: test_input.csv → 派生版フォーマット変換")
        print("="*60)
        
        command = "python core_scripts/derivative_ad_data_converter.py"
        return self.run_command(command, 'data_conversion')
    
    def step2_email_extraction(self, start_id, end_id):
        """ステップ2: メールアドレス抽出"""
        print("\n" + "="*60)
        print("📧 ステップ2: メールアドレス抽出")
        print("="*60)
        
        # 広告営業用の入力ファイルを使用
        command = f"python core_scripts/derivative_email_extractor.py --input-file data/derivative_ad_input.csv --start-id {start_id} --end-id {end_id}"
        return self.run_command(command, 'email_extraction')
    
    def step3_email_sending(self, start_id, end_id, test_mode=False):
        """ステップ3: メール送信（ウェブサイト分析スキップ）"""
        print("\n" + "="*60)
        print("📤 ステップ3: 広告営業メール送信")
        print("="*60)
        print("ℹ️  ウェブサイト分析はスキップします（広告営業のため）")
        
        command = f"python core_scripts/derivative_ad_email_sender.py --input-file data/derivative_ad_input.csv --start-id {start_id} --end-id {end_id}"
        if test_mode:
            command += " --test-mode"
        
        return self.run_command(command, 'email_sending')
    
    def generate_summary_report(self):
        """サマリーレポートを生成"""
        try:
            end_time = datetime.now()
            duration = end_time - self.start_time
            
            report = {
                'workflow_type': 'ad_agency_campaign',
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'steps_completed': sum(1 for step in self.results.values() if step['status'] == 'completed'),
                'steps_failed': sum(1 for step in self.results.values() if step['status'] == 'failed'),
                'website_analysis_skipped': True,
                'campaign_type': 'ad_agency',
                'template_used': 'ad.html',
                'results': self.results
            }
            
            # レポートファイルに保存
            report_file = f"data/derivative_ad_workflow_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"サマリーレポートを生成しました: {report_file}")
            
            # コンソール出力
            print("\n" + "="*60)
            print("📋 広告営業ワークフロー完了レポート")
            print("="*60)
            print(f"開始時刻: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"終了時刻: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"実行時間: {duration}")
            print(f"完了ステップ: {report['steps_completed']}")
            print(f"失敗ステップ: {report['steps_failed']}")
            print(f"営業内容: 広告運用代行")
            print(f"テンプレート: ad.html")
            print(f"ウェブサイト分析: スキップ")
            print("="*60)
            
            return True
            
        except Exception as e:
            logger.error(f"サマリーレポート生成エラー: {e}")
            return False

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='派生版広告営業ワークフロー')
    parser.add_argument('--start-id', type=int, default=1, help='開始ID')
    parser.add_argument('--end-id', type=int, default=10, help='終了ID')
    parser.add_argument('--test-mode', action='store_true', help='テストモード')
    parser.add_argument('--skip-conversion', action='store_true', help='データ変換をスキップ')
    parser.add_argument('--skip-extraction', action='store_true', help='メール抽出をスキップ')
    
    args = parser.parse_args()
    
    print("🚀 派生版広告営業ワークフロー")
    print("=" * 60)
    print(f"営業内容: 広告運用代行")
    print(f"テンプレート: ad.html")
    print(f"処理範囲: ID {args.start_id} - {args.end_id}")
    print(f"テストモード: {'有効' if args.test_mode else '無効'}")
    print(f"ウェブサイト分析: スキップ")
    print("=" * 60)
    
    # ワークフローマネージャーを初期化
    workflow = AdWorkflowManager()
    
    try:
        success_count = 0
        total_steps = 3
        
        # ステップ1: データ変換
        if not args.skip_conversion:
            if workflow.step1_data_conversion():
                success_count += 1
            else:
                print("❌ データ変換に失敗しました")
        else:
            print("⏭️  データ変換をスキップしました")
            success_count += 1
        
        # ステップ2: メールアドレス抽出
        if not args.skip_extraction:
            if workflow.step2_email_extraction(args.start_id, args.end_id):
                success_count += 1
            else:
                print("❌ メールアドレス抽出に失敗しました")
        else:
            print("⏭️  メールアドレス抽出をスキップしました")
            success_count += 1
        
        # ステップ3: メール送信
        if workflow.step3_email_sending(args.start_id, args.end_id, args.test_mode):
            success_count += 1
        else:
            print("❌ メール送信に失敗しました")
        
        # 完了処理
        if success_count == total_steps:
            workflow.update_progress('workflow_complete', 'completed')
            print("\n✅ 広告営業ワークフローが正常に完了しました")
        else:
            workflow.update_progress('workflow_complete', 'failed')
            print(f"\n⚠️  ワークフローが部分的に完了しました ({success_count}/{total_steps})")
        
        # サマリーレポート生成
        workflow.generate_summary_report()
        
        return success_count == total_steps
        
    except Exception as e:
        logger.error(f"ワークフロー実行中にエラーが発生しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        workflow.update_progress('workflow_complete', 'failed')
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
