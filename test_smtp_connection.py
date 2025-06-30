#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMTP接続テストスクリプト
smtp.huganjob.jpへの接続状況を確認
"""

import smtplib
import socket
from datetime import datetime

def test_smtp_connection():
    """SMTP接続テスト"""
    print("="*60)
    print("📡 SMTP接続テスト開始")
    print("="*60)
    
    smtp_server = "smtp.huganjob.jp"
    smtp_port = 587
    smtp_user = "contact@huganjob.jp"
    smtp_password = "gD34bEmB"
    
    print(f"🌐 サーバー: {smtp_server}:{smtp_port}")
    print(f"👤 ユーザー: {smtp_user}")
    print(f"🕐 テスト時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. 基本的なソケット接続テスト
        print("🔌 ソケット接続テスト...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((smtp_server, smtp_port))
        sock.close()
        
        if result == 0:
            print("✅ ソケット接続成功")
        else:
            print(f"❌ ソケット接続失敗: エラーコード {result}")
            return False
        
        # 2. SMTP接続テスト
        print("📧 SMTP接続テスト...")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        print("✅ SMTP接続成功")
        
        # 3. STARTTLS テスト
        print("🔒 STARTTLS テスト...")
        server.starttls()
        print("✅ STARTTLS成功")
        
        # 4. 認証テスト
        print("🔑 認証テスト...")
        server.login(smtp_user, smtp_password)
        print("✅ 認証成功")
        
        # 5. 接続終了
        server.quit()
        print("✅ 接続終了")
        
        print()
        print("🎉 全てのテストが成功しました！")
        return True
        
    except socket.timeout:
        print("❌ 接続タイムアウト")
        return False
    except socket.gaierror as e:
        print(f"❌ DNS解決エラー: {e}")
        return False
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ 認証エラー: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTPエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

if __name__ == "__main__":
    test_smtp_connection()
