#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
古いメール送信スクリプトの無効化
重複送信防止のため、古いスクリプトを安全に無効化

作成日時: 2025年06月23日 12:30:00
"""

import os
import shutil
from datetime import datetime

def disable_old_senders():
    """古いメール送信スクリプトを無効化"""
    
    # 無効化対象スクリプト
    old_senders = [
        'huganjob_direct_sender.py',
        'huganjob_fixed_sender.py',
        'huganjob_fresh_sender.py',
        'huganjob_id1to5_sender.py',
        'huganjob_final_sender.py'
    ]
    
    # バックアップディレクトリ作成
    backup_dir = f"old_senders_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    print("🔧 古いメール送信スクリプトの無効化開始")
    print("=" * 50)
    
    for script in old_senders:
        if os.path.exists(script):
            # バックアップ作成
            backup_path = os.path.join(backup_dir, script)
            shutil.copy2(script, backup_path)
            
            # 無効化（.disabled拡張子を追加）
            disabled_path = f"{script}.disabled"
            os.rename(script, disabled_path)
            
            print(f"✅ 無効化: {script} -> {disabled_path}")
            print(f"   バックアップ: {backup_path}")
        else:
            print(f"⚠️ ファイルなし: {script}")
    
    print(f"\n📁 バックアップディレクトリ: {backup_dir}")
    print("✅ 古いスクリプトの無効化完了")
    print("\n💡 今後は huganjob_unified_sender.py を使用してください")

if __name__ == "__main__":
    disable_old_senders()
