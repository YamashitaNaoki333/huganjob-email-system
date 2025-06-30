#!/usr/bin/env python3
"""
HUGANJOB Git 継続セットアップスクリプト
現在の進捗を確認し、次のステップを実行
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
            
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        
    except Exception as e:
        print(f"❌ 例外エラー: {e}")
        return False, "", str(e)

def check_current_status():
    """現在のGit状況確認"""
    print("\n📋 現在のGit状況確認")
    
    # Git状況確認
    success, stdout, stderr = run_git_command("git status --porcelain", "Git状況確認")
    
    if success:
        if stdout:
            print("📁 変更されたファイル:")
            for line in stdout.split('\n'):
                if line.strip():
                    print(f"  {line}")
        else:
            print("✅ 作業ディレクトリはクリーンです")
    
    # ブランチ確認
    run_git_command("git branch", "ブランチ確認")
    
    # リモート確認
    run_git_command("git remote -v", "リモートリポジトリ確認")
    
    return success

def add_remaining_files():
    """残りの安全なファイルを追加"""
    print("\n📁 残りの安全なファイルを追加")
    
    # 追加すべきファイルリスト
    additional_files = [
        "git_setup.py",
        "git_continue_setup.py", 
        "check_git_status.py",
        "SAFE_FILES_FOR_GIT.md",
        "huganjob_unified_sender.py",
        "huganjob_lightweight_sender.py",
        "huganjob_text_only_sender.py",
        "dashboard/derivative_dashboard.py",
        "templates/corporate-email-newsletter.html",
        "templates/base.html",
        "HUGANJOB_CORE_SYSTEM_SPECIFICATIONS.md",
        "AI_ONBOARDING_CHECKLIST.md"
    ]
    
    added_files = []
    
    for file_path in additional_files:
        if Path(file_path).exists():
            success, _, _ = run_git_command(f"git add {file_path}", f"追加: {file_path}")
            if success:
                added_files.append(file_path)
        else:
            print(f"⚠️ ファイルが存在しません: {file_path}")
    
    print(f"\n✅ 追加されたファイル数: {len(added_files)}")
    return added_files

def create_commit():
    """コミットの作成"""
    print("\n💾 コミットの作成")
    
    # ステージング状況確認
    success, stdout, stderr = run_git_command("git status --porcelain --cached", "ステージング確認")
    
    if not stdout:
        print("⚠️ ステージングされたファイルがありません")
        return False
    
    print("📁 ステージングされたファイル:")
    for line in stdout.split('\n'):
        if line.strip():
            print(f"  {line}")
    
    # コミットメッセージ
    commit_message = """Add HUGANJOB system core files and Git setup

- Add Git setup and management scripts
- Add core email sending systems (unified, lightweight, text-only)
- Add dashboard application and templates
- Add system documentation and specifications
- Add safety documentation for Git management

All sensitive data and credentials are properly excluded via .gitignore"""
    
    success, _, _ = run_git_command(f'git commit -m "{commit_message}"', "コミット作成")
    
    if success:
        print("🎉 コミットが正常に作成されました！")
        run_git_command("git log --oneline -5", "最新コミット履歴")
    
    return success

def check_remote_status():
    """リモートリポジトリの状況確認"""
    print("\n🌐 リモートリポジトリ状況確認")
    
    # リモートブランチ確認
    run_git_command("git ls-remote origin", "リモートブランチ確認")
    
    # ローカルとリモートの差分確認
    run_git_command("git status -uno", "ローカル/リモート状況")

def main():
    """メイン処理"""
    print("🚀 HUGANJOB Git 継続セットアップ")
    print("=" * 50)
    
    # 現在のディレクトリ確認
    print(f"📁 現在のディレクトリ: {os.getcwd()}")
    
    # 現在の状況確認
    if not check_current_status():
        print("❌ Git状況確認に失敗しました")
        return
    
    # 残りのファイルを追加
    added_files = add_remaining_files()
    
    if added_files:
        # コミット作成
        if create_commit():
            print("\n✅ ローカルでのGit設定が完了しました")
        else:
            print("\n❌ コミット作成に失敗しました")
    else:
        print("\n⚠️ 新しく追加するファイルがありません")
    
    # リモート状況確認
    check_remote_status()
    
    print("\n🎯 次のステップ:")
    print("1. リモートリポジトリとの同期:")
    print("   git pull origin main --allow-unrelated-histories")
    print("2. プッシュ:")
    print("   git push -u origin main")
    
    print("\n🎯 Git 継続セットアップ完了")
    print("=" * 50)

if __name__ == "__main__":
    main()
