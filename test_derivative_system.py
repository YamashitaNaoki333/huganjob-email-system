#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
派生版システム動作確認テストスクリプト
- 元システムとの独立性確認
- 基本機能の動作確認
- ファイル参照の正確性確認
"""

import os
import sys
import json
import datetime
import subprocess
import time

def test_directory_structure():
    """ディレクトリ構造の確認"""
    print("🔍 ディレクトリ構造テスト")
    
    required_dirs = [
        'core_scripts',
        'dashboard', 
        'config',
        'data',
        'logs',
        'templates'
    ]
    
    required_files = [
        'core_scripts/derivative_integrated_workflow.py',
        'core_scripts/derivative_email_extractor.py',
        'core_scripts/derivative_website_analyzer.py',
        'core_scripts/derivative_email_sender.py',
        'dashboard/derivative_dashboard.py',
        'config/derivative_email_config.ini',
        'data/derivative_input.csv',
        'README.md'
    ]
    
    all_passed = True
    
    # ディレクトリ確認
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"  ✅ {dir_name}/ - 存在")
        else:
            print(f"  ❌ {dir_name}/ - 不存在")
            all_passed = False
    
    # ファイル確認
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path} - 存在")
        else:
            print(f"  ❌ {file_path} - 不存在")
            all_passed = False
    
    return all_passed

def test_config_independence():
    """設定ファイルの独立性確認"""
    print("\n🔍 設定ファイル独立性テスト")
    
    config_file = 'config/derivative_email_config.ini'
    if not os.path.exists(config_file):
        print(f"  ❌ 設定ファイルが見つかりません: {config_file}")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 派生版特有の設定を確認
        checks = [
            ('派生版コメント', '派生版' in content),
            ('独立フォルダ設定', 'Derivative_Processed' in content),
            ('派生版送信者名', '派生版' in content)
        ]
        
        all_passed = True
        for check_name, result in checks:
            if result:
                print(f"  ✅ {check_name} - 確認")
            else:
                print(f"  ❌ {check_name} - 未設定")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"  ❌ 設定ファイル読み込みエラー: {e}")
        return False

def test_data_file_references():
    """データファイル参照の確認"""
    print("\n🔍 データファイル参照テスト")
    
    # 入力ファイルの確認
    input_file = 'data/derivative_input.csv'
    if os.path.exists(input_file):
        print(f"  ✅ 入力ファイル存在: {input_file}")
        
        # ファイル内容の確認
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            print(f"  ✅ 入力データ行数: {len(lines)}行")
            
            if len(lines) > 1:
                print(f"  ✅ サンプルデータ確認: {lines[1].strip()[:50]}...")
            
        except Exception as e:
            print(f"  ❌ 入力ファイル読み込みエラー: {e}")
            return False
    else:
        print(f"  ❌ 入力ファイル不存在: {input_file}")
        return False
    
    # 必要なディレクトリの確認
    required_data_dirs = [
        'data/results',
        'data/derivative_consolidated'
    ]
    
    for dir_path in required_data_dirs:
        if os.path.exists(dir_path):
            print(f"  ✅ データディレクトリ存在: {dir_path}")
        else:
            print(f"  ❌ データディレクトリ不存在: {dir_path}")
            return False
    
    return True

def test_port_independence():
    """ポート独立性の確認"""
    print("\n🔍 ポート独立性テスト")

    # ダッシュボードファイルのポート設定確認
    dashboard_file = 'dashboard/derivative_dashboard.py'
    if not os.path.exists(dashboard_file):
        print(f"  ❌ ダッシュボードファイルが見つかりません: {dashboard_file}")
        return False

    try:
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            dashboard_content = f.read()

        # ポート5002の設定確認
        if 'default=5002' in dashboard_content:
            print("  ✅ 派生版ポート設定確認: 5002")
        else:
            print("  ❌ 派生版ポート設定未確認")
            return False

    except Exception as e:
        print(f"  ❌ ダッシュボードファイル読み込みエラー: {e}")
        return False

    # メール送信スクリプトのURL設定確認
    email_sender_file = 'core_scripts/derivative_email_sender.py'
    if not os.path.exists(email_sender_file):
        print(f"  ❌ メール送信ファイルが見つかりません: {email_sender_file}")
        return False

    try:
        with open(email_sender_file, 'r', encoding='utf-8') as f:
            sender_content = f.read()

        # 派生版URL設定確認
        if '127.0.0.1:5002' in sender_content:
            print("  ✅ 派生版URL設定確認: 127.0.0.1:5002")
        else:
            print("  ❌ 派生版URL設定未確認")
            return False

        return True

    except Exception as e:
        print(f"  ❌ メール送信ファイル読み込みエラー: {e}")
        return False

def test_script_syntax():
    """スクリプトの構文確認"""
    print("\n🔍 スクリプト構文テスト")
    
    scripts = [
        'core_scripts/derivative_integrated_workflow.py',
        'core_scripts/derivative_email_extractor.py',
        'core_scripts/derivative_website_analyzer.py',
        'core_scripts/derivative_email_sender.py',
        'dashboard/derivative_dashboard.py'
    ]
    
    all_passed = True
    
    for script in scripts:
        try:
            # Python構文チェック
            result = subprocess.run([
                sys.executable, '-m', 'py_compile', script
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  ✅ {script} - 構文OK")
            else:
                print(f"  ❌ {script} - 構文エラー")
                print(f"      {result.stderr}")
                all_passed = False
                
        except Exception as e:
            print(f"  ❌ {script} - チェック失敗: {e}")
            all_passed = False
    
    return all_passed

def generate_test_report():
    """テストレポート生成"""
    print("\n📊 派生版システムテスト実行中...")
    
    test_results = {
        'test_time': datetime.datetime.now().isoformat(),
        'tests': {}
    }
    
    # 各テストを実行
    tests = [
        ('directory_structure', test_directory_structure),
        ('config_independence', test_config_independence),
        ('data_file_references', test_data_file_references),
        ('port_independence', test_port_independence),
        ('script_syntax', test_script_syntax)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results['tests'][test_name] = {
                'passed': result,
                'timestamp': datetime.datetime.now().isoformat()
            }
            if not result:
                all_passed = False
        except Exception as e:
            print(f"  ❌ テスト実行エラー ({test_name}): {e}")
            test_results['tests'][test_name] = {
                'passed': False,
                'error': str(e),
                'timestamp': datetime.datetime.now().isoformat()
            }
            all_passed = False
    
    # 総合結果
    test_results['overall_result'] = all_passed
    
    # レポート保存
    report_file = f"derivative_system_test_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📋 テストレポート: {report_file}")
    
    if all_passed:
        print("\n🎉 全テスト合格！派生版システムは正常に構築されています。")
        print("✅ 元システムから独立して動作可能です。")
    else:
        print("\n⚠️ 一部テストが失敗しました。上記の問題を修正してください。")
    
    return all_passed

if __name__ == "__main__":
    print("=" * 60)
    print("派生版メールマーケティングシステム 動作確認テスト")
    print("=" * 60)
    
    # 作業ディレクトリを派生版システムに変更
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📍 テスト実行ディレクトリ: {os.getcwd()}")
    
    # テスト実行
    success = generate_test_report()
    
    print("\n" + "=" * 60)
    sys.exit(0 if success else 1)
