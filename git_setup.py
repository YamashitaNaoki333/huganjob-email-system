#!/usr/bin/env python3
"""
HUGANJOB Git セットアップスクリプト
ターミナル問題を回避してGit操作を実行
"""

import subprocess
import os
import sys
from pathlib import Path

def run_git_command(command, description):
    """Git コマンドを実行"""
    print(f"\n🔧 {description}")
    print(f"実行: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            print(f"✅ 成功: {description}")
            if result.stdout.strip():
                print(f"出力: {result.stdout.strip()}")
        else:
            print(f"❌ エラー: {description}")
            print(f"エラー内容: {result.stderr.strip()}")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 例外エラー: {e}")
        return False

def check_git_status():
    """Git状況の確認"""
    print("\n📋 Git状況確認")
    
    # .gitディレクトリの存在確認
    if Path('.git').exists():
        print("✅ Gitリポジトリが初期化済み")
    else:
        print("❌ Gitリポジトリが未初期化")
        return False
    
    # Git設定確認
    run_git_command("git config --list", "Git設定確認")
    
    return True

def add_safe_files():
    """安全なファイルをGitに追加"""
    print("\n📁 安全なファイルをGitに追加")
    
    safe_files = [
        ".gitignore",
        "README.md", 
        "SAFE_FILES_FOR_GIT.md",
        "config/huganjob_email_config.ini.template",
        "config/huganjob_dashboard_config.json",
        "data/sample_companies.csv"
    ]
    
    for file_path in safe_files:
        if Path(file_path).exists():
            success = run_git_command(f"git add {file_path}", f"追加: {file_path}")
            if not success:
                print(f"⚠️ ファイル追加失敗: {file_path}")
        else:
            print(f"⚠️ ファイルが存在しません: {file_path}")

def check_staged_files():
    """ステージングされたファイルの確認"""
    print("\n📋 ステージングされたファイルの確認")
    run_git_command("git status --porcelain", "Git状況（簡潔版）")
    run_git_command("git status", "Git状況（詳細版）")

def create_initial_commit():
    """初回コミットの作成"""
    print("\n💾 初回コミットの作成")
    
    commit_message = """Initial commit: HUGANJOB system core files

- Add .gitignore for security (exclude credentials and data)
- Add README.md with project overview  
- Add configuration templates
- Add sample data files
- Add Git setup documentation

Note: All sensitive data and credentials are excluded from version control"""
    
    success = run_git_command(f'git commit -m "{commit_message}"', "初回コミット作成")
    
    if success:
        print("🎉 初回コミットが正常に作成されました！")
        run_git_command("git log --oneline", "コミット履歴確認")
    else:
        print("❌ コミット作成に失敗しました")

def main():
    """メイン処理"""
    print("🚀 HUGANJOB Git セットアップ開始")
    print("=" * 50)
    
    # 現在のディレクトリ確認
    print(f"📁 現在のディレクトリ: {os.getcwd()}")
    
    # Git状況確認
    if not check_git_status():
        print("❌ Git初期化が必要です")
        return
    
    # 安全なファイルを追加
    add_safe_files()
    
    # ステージング状況確認
    check_staged_files()
    
    # ユーザー確認
    print("\n❓ 初回コミットを作成しますか？ (y/n): ", end="")
    response = input().lower().strip()
    
    if response in ['y', 'yes', 'はい']:
        create_initial_commit()
    else:
        print("⏸️ コミット作成をスキップしました")
    
    print("\n🎯 Git セットアップ完了")
    print("=" * 50)

if __name__ == "__main__":
    main()
