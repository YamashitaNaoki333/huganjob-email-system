#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HUGAN JOB 重複送信防止システム
複数のスクリプトが同時実行されることを防ぐ

作成日時: 2025年06月23日 12:20:00
目的: バウンスメール複数受信問題の解決
"""

import os
import time
import json
import platform
from datetime import datetime, timedelta
from pathlib import Path

# Windows対応のファイルロック
try:
    if platform.system() == 'Windows':
        import msvcrt
        WINDOWS_LOCK = True
    else:
        import fcntl
        WINDOWS_LOCK = False
except ImportError:
    # フォールバック: ファイルベースロック
    WINDOWS_LOCK = None

class DuplicatePreventionManager:
    """重複送信防止管理クラス"""
    
    def __init__(self, lock_file='huganjob_sending.lock', history_file='huganjob_sending_history.json'):
        self.lock_file = lock_file
        self.history_file = history_file
        self.lock_handle = None
        
    def acquire_lock(self, timeout=30):
        """送信ロックを取得（Windows対応）"""
        try:
            # Windows対応のファイルロック
            if WINDOWS_LOCK is True:
                return self._acquire_lock_windows(timeout)
            elif WINDOWS_LOCK is False:
                return self._acquire_lock_unix(timeout)
            else:
                # フォールバック: ファイルベースロック
                return self._acquire_lock_fallback(timeout)

        except Exception as e:
            print(f"❌ ロック取得エラー: {e}")
            return False

    def _acquire_lock_windows(self, timeout):
        """Windowsファイルロック"""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    # Windowsでは排他モードでファイルを開く
                    self.lock_handle = open(self.lock_file, 'w')
                    msvcrt.locking(self.lock_handle.fileno(), msvcrt.LK_NBLCK, 1)

                    # ロック取得成功
                    lock_info = {
                        'pid': os.getpid(),
                        'start_time': datetime.now().isoformat(),
                        'script_name': 'huganjob_unified_sender.py',
                        'platform': 'Windows'
                    }
                    self.lock_handle.write(json.dumps(lock_info, indent=2))
                    self.lock_handle.flush()

                    print("✅ 送信ロック取得成功 (Windows)")
                    return True

                except (IOError, OSError):
                    # ロック取得失敗、少し待機
                    if self.lock_handle:
                        self.lock_handle.close()
                        self.lock_handle = None
                    time.sleep(1)
                    continue

            print("❌ 送信ロック取得タイムアウト (Windows)")
            return False

        except Exception as e:
            print(f"❌ Windowsロック取得エラー: {e}")
            return False

    def _acquire_lock_unix(self, timeout):
        """Unix/Linuxファイルロック"""
        try:
            self.lock_handle = open(self.lock_file, 'w')

            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    fcntl.flock(self.lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

                    # ロック取得成功
                    lock_info = {
                        'pid': os.getpid(),
                        'start_time': datetime.now().isoformat(),
                        'script_name': 'huganjob_unified_sender.py',
                        'platform': 'Unix/Linux'
                    }
                    self.lock_handle.write(json.dumps(lock_info, indent=2))
                    self.lock_handle.flush()

                    print("✅ 送信ロック取得成功 (Unix/Linux)")
                    return True

                except IOError:
                    time.sleep(1)
                    continue

            print("❌ 送信ロック取得タイムアウト (Unix/Linux)")
            return False

        except Exception as e:
            print(f"❌ Unix/Linuxロック取得エラー: {e}")
            return False

    def _acquire_lock_fallback(self, timeout):
        """フォールバック: ファイルベースロック"""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                if not os.path.exists(self.lock_file):
                    # ロックファイル作成
                    lock_info = {
                        'pid': os.getpid(),
                        'start_time': datetime.now().isoformat(),
                        'script_name': 'huganjob_unified_sender.py',
                        'platform': 'Fallback'
                    }

                    with open(self.lock_file, 'w') as f:
                        json.dump(lock_info, f, indent=2)

                    print("✅ 送信ロック取得成功 (Fallback)")
                    return True
                else:
                    # ロックファイルが存在、少し待機
                    time.sleep(1)
                    continue

            print("❌ 送信ロック取得タイムアウト (Fallback)")
            return False

        except Exception as e:
            print(f"❌ フォールバックロック取得エラー: {e}")
            return False
    
    def release_lock(self):
        """送信ロックを解放（Windows対応）"""
        try:
            if WINDOWS_LOCK is True:
                return self._release_lock_windows()
            elif WINDOWS_LOCK is False:
                return self._release_lock_unix()
            else:
                return self._release_lock_fallback()

        except Exception as e:
            print(f"❌ ロック解放エラー: {e}")
            return False

    def _release_lock_windows(self):
        """Windowsファイルロック解放"""
        try:
            if self.lock_handle:
                msvcrt.locking(self.lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
                self.lock_handle.close()
                self.lock_handle = None

            # ロックファイル削除
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)

            print("✅ 送信ロック解放完了 (Windows)")
            return True

        except Exception as e:
            print(f"❌ Windowsロック解放エラー: {e}")
            return False

    def _release_lock_unix(self):
        """Unix/Linuxファイルロック解放"""
        try:
            if self.lock_handle:
                fcntl.flock(self.lock_handle.fileno(), fcntl.LOCK_UN)
                self.lock_handle.close()
                self.lock_handle = None

            # ロックファイル削除
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)

            print("✅ 送信ロック解放完了 (Unix/Linux)")
            return True

        except Exception as e:
            print(f"❌ Unix/Linuxロック解放エラー: {e}")
            return False

    def _release_lock_fallback(self):
        """フォールバックファイルロック解放"""
        try:
            # ロックファイル削除
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)

            print("✅ 送信ロック解放完了 (Fallback)")
            return True

        except Exception as e:
            print(f"❌ フォールバックロック解放エラー: {e}")
            return False
    
    def check_recent_sending(self, company_id, hours=24):
        """最近の送信履歴をチェック（配信停止以外は複数回送信可能に変更）"""
        try:
            # 配信停止以外は複数回送信を許可するため、常にFalseを返す
            # 配信停止チェックは各送信システムで個別に実装済み
            print(f"✅ 企業ID {company_id} - 重複送信チェック無効化（複数回送信許可）")
            return False

        except Exception as e:
            print(f"❌ 送信履歴チェックエラー: {e}")
            return False
    
    def record_sending(self, company_id, company_name, email_address, script_name=None):
        """送信履歴を記録"""
        try:
            # 既存履歴読み込み
            history = {'sending_records': []}
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)

            # 新しい送信記録を追加
            record = {
                'company_id': company_id,
                'company_name': company_name,
                'email_address': email_address,
                'send_time': datetime.now().isoformat(),
                'script_name': script_name or 'huganjob_duplicate_prevention.py',
                'pid': os.getpid()
            }
            
            history['sending_records'].append(record)
            
            # 古い記録を削除（7日以上前）
            cutoff_time = datetime.now() - timedelta(days=7)
            history['sending_records'] = [
                r for r in history['sending_records']
                if datetime.fromisoformat(r['send_time']) > cutoff_time
            ]
            
            # ファイルに保存
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 送信履歴記録: {company_name} ({company_id})")
            return True
            
        except Exception as e:
            print(f"❌ 送信履歴記録エラー: {e}")
            return False
    
    def get_sending_statistics(self):
        """送信統計を取得"""
        try:
            if not os.path.exists(self.history_file):
                return {'total_sends': 0, 'unique_companies': 0, 'recent_sends': 0}
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            records = history.get('sending_records', [])
            
            # 統計計算
            total_sends = len(records)
            unique_companies = len(set(r['company_id'] for r in records))
            
            # 過去24時間の送信数
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_sends = len([
                r for r in records
                if datetime.fromisoformat(r['send_time']) > cutoff_time
            ])
            
            return {
                'total_sends': total_sends,
                'unique_companies': unique_companies,
                'recent_sends': recent_sends
            }
            
        except Exception as e:
            print(f"❌ 統計取得エラー: {e}")
            return {'total_sends': 0, 'unique_companies': 0, 'recent_sends': 0}

def check_duplicate_prevention():
    """重複送信防止チェック（スタンドアロン関数）"""
    manager = DuplicatePreventionManager()
    
    print("🔍 重複送信防止チェック開始")
    print("=" * 50)
    
    # 統計表示
    stats = manager.get_sending_statistics()
    print(f"📊 送信統計:")
    print(f"  総送信数: {stats['total_sends']}")
    print(f"  送信企業数: {stats['unique_companies']}")
    print(f"  過去24時間: {stats['recent_sends']}")
    
    # ロック状況確認
    if os.path.exists(manager.lock_file):
        print(f"⚠️ 送信ロックファイルが存在: {manager.lock_file}")
        try:
            with open(manager.lock_file, 'r') as f:
                lock_info = json.load(f)
            print(f"  PID: {lock_info.get('pid')}")
            print(f"  開始時刻: {lock_info.get('start_time')}")
            print(f"  スクリプト: {lock_info.get('script_name')}")
        except:
            print("  ロックファイル情報読み込み失敗")
    else:
        print("✅ 送信ロックファイルなし（送信可能）")
    
    print("=" * 50)

if __name__ == "__main__":
    check_duplicate_prevention()
