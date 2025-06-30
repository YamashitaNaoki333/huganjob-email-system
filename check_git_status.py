#!/usr/bin/env python3
"""
Git状況確認スクリプト
現在のGit状況を詳細に確認
"""

import subprocess
import os
from pathlib import Path

def run_command(command):
    """コマンドを実行して結果を返す"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=os.getcwd()
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def main():
    """Git状況の詳細確認"""
    print("🔍 Git状況詳細確認")
    print("=" * 50)
    
    # 基本情報
    print(f"📁 現在のディレクトリ: {os.getcwd()}")
    print(f"📂 .gitディレクトリ存在: {Path('.git').exists()}")
    
    # Git コマンドの実行
    commands = [
        ("git --version", "Gitバージョン"),
        ("git status", "Git状況"),
        ("git log --oneline", "コミット履歴"),
        ("git branch", "ブランチ一覧"),
        ("git config --list", "Git設定"),
        ("git ls-files", "追跡中ファイル"),
        ("git ls-files --others --ignored --exclude-standard", "除外ファイル")
    ]
    
    for command, description in commands:
        print(f"\n🔧 {description}")
        print(f"実行: {command}")
        
        returncode, stdout, stderr = run_command(command)
        
        if returncode == 0:
            if stdout:
                print(f"✅ 結果:\n{stdout}")
            else:
                print("✅ 結果: (出力なし)")
        else:
            print(f"❌ エラー (code: {returncode})")
            if stderr:
                print(f"エラー内容: {stderr}")
    
    print("\n" + "=" * 50)
    print("🎯 Git状況確認完了")

if __name__ == "__main__":
    main()
