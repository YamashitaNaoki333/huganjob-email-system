#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Microsoft 365管理者向け設定ガイド
SMTP認証無効化問題の解決方法
"""

def show_admin_solutions():
    """管理者向け解決策の表示"""
    print("=" * 80)
    print("👨‍💼 Microsoft 365管理者向け解決策")
    print("=" * 80)
    
    print("\n🚨 現在の問題:")
    print("❌ テナントでSMTP基本認証が無効化されています")
    print("❌ アプリケーションからのメール送信ができません")
    print("❌ エラー: SmtpClientAuthentication is disabled for the Tenant")
    
    print("\n🎯 解決策（優先順位順）:")
    
    print("\n1️⃣ アプリパスワードの有効化（推奨）")
    print("   利点: セキュリティを保ちつつ送信可能")
    print("   手順: ユーザーレベルでアプリパスワード生成")
    print("   影響: 個別ユーザーのみ")
    
    print("\n2️⃣ OAuth2認証の実装（最高セキュリティ）")
    print("   利点: 最新のセキュリティ標準")
    print("   手順: Azure AD アプリケーション登録")
    print("   影響: 開発工数が必要")
    
    print("\n3️⃣ SMTP認証の部分的有効化（非推奨）")
    print("   利点: 既存システムの変更不要")
    print("   手順: 管理センターでの設定変更")
    print("   影響: セキュリティリスク増加")

def show_app_password_admin_guide():
    """アプリパスワード管理者ガイド"""
    print("\n" + "=" * 80)
    print("🔐 アプリパスワード設定ガイド（管理者向け）")
    print("=" * 80)
    
    print("\n📋 前提条件の確認:")
    print("1. ユーザーの多要素認証が有効であること")
    print("2. セキュリティデフォルトまたは条件付きアクセスが設定済み")
    print("3. アプリパスワードポリシーが許可されていること")
    
    print("\n🔧 管理者による設定確認手順:")
    print("1. Microsoft 365管理センターにログイン")
    print("2. 「ユーザー」→「アクティブなユーザー」")
    print("3. 対象ユーザー（client@hugan.co.jp）を選択")
    print("4. 「多要素認証」タブを確認")
    print("5. 状態が「有効」または「強制」であることを確認")
    
    print("\n👤 ユーザー向け手順:")
    print("1. https://portal.office.com にログイン")
    print("2. プロフィール → マイアカウント")
    print("3. セキュリティ → 追加のセキュリティ検証")
    print("4. アプリパスワード → 作成")
    print("5. 名前: 'HUGAN JOB Mail System'")
    print("6. 生成された16文字のパスワードを使用")

def show_oauth2_admin_guide():
    """OAuth2設定管理者ガイド"""
    print("\n" + "=" * 80)
    print("🔒 OAuth2認証設定ガイド（管理者向け）")
    print("=" * 80)
    
    print("\n🔧 Azure AD設定手順:")
    print("1. Azure Portal (https://portal.azure.com) にログイン")
    print("2. Azure Active Directory を選択")
    print("3. アプリの登録 → 新規登録")
    print("4. 名前: 'HUGAN JOB Mail System'")
    print("5. サポートされているアカウントの種類: 単一テナント")
    
    print("\n🔐 APIアクセス許可設定:")
    print("1. 作成したアプリを選択")
    print("2. APIのアクセス許可 → アクセス許可の追加")
    print("3. Microsoft Graph → アプリケーションのアクセス許可")
    print("4. 以下のアクセス許可を追加:")
    print("   - Mail.Send")
    print("   - User.Read")
    print("5. 管理者の同意を与える")
    
    print("\n🔑 クライアントシークレット作成:")
    print("1. 証明書とシークレット → 新しいクライアントシークレット")
    print("2. 説明: 'HUGAN JOB Mail Secret'")
    print("3. 有効期限: 24か月")
    print("4. 生成された値をコピー（一度しか表示されません）")
    
    print("\n📋 必要な情報:")
    print("- テナントID: 概要ページのディレクトリ(テナント)ID")
    print("- クライアントID: 概要ページのアプリケーション(クライアント)ID")
    print("- クライアントシークレット: 上記で作成した値")

def show_smtp_auth_enable_guide():
    """SMTP認証有効化ガイド（非推奨）"""
    print("\n" + "=" * 80)
    print("⚠️ SMTP認証有効化ガイド（非推奨・セキュリティリスクあり）")
    print("=" * 80)
    
    print("\n🚨 重要な警告:")
    print("❌ この方法はセキュリティリスクを伴います")
    print("❌ Microsoft は基本認証の廃止を推進しています")
    print("❌ 将来的に使用できなくなる可能性があります")
    print("✅ アプリパスワードまたはOAuth2を強く推奨します")
    
    print("\n🔧 設定手順（非推奨）:")
    print("1. Microsoft 365管理センターにログイン")
    print("2. Exchange管理センターに移動")
    print("3. メールフロー → 認証ポリシー")
    print("4. 「SMTP認証を有効にする」を選択")
    print("5. 対象ユーザーまたは全体に適用")
    
    print("\n📋 代替案（推奨）:")
    print("1. アプリパスワードの使用")
    print("2. OAuth2認証の実装")
    print("3. Microsoft Graph APIの使用")

def show_troubleshooting_guide():
    """トラブルシューティングガイド"""
    print("\n" + "=" * 80)
    print("🔧 トラブルシューティングガイド")
    print("=" * 80)
    
    print("\n❌ 問題: アプリパスワードが生成できない")
    print("原因と対策:")
    print("1. 多要素認証が無効")
    print("   → 管理者による多要素認証の有効化")
    print("2. セキュリティデフォルトが無効")
    print("   → セキュリティデフォルトまたは条件付きアクセスの設定")
    print("3. アプリパスワードポリシーが無効")
    print("   → 管理センターでアプリパスワードポリシーの確認")
    
    print("\n❌ 問題: OAuth2認証が失敗する")
    print("原因と対策:")
    print("1. APIアクセス許可が不足")
    print("   → Mail.Send, User.Read の追加")
    print("2. 管理者の同意が未実施")
    print("   → 管理者による同意の実行")
    print("3. クライアントシークレットの期限切れ")
    print("   → 新しいシークレットの生成")
    
    print("\n❌ 問題: 送信後に迷惑メール判定される")
    print("原因と対策:")
    print("1. SPF設定が不適切")
    print("   → hugan.co.jp の SPF レコード設定")
    print("2. DKIM設定が未実施")
    print("   → Microsoft 365 でのDKIM有効化")
    print("3. 送信頻度が高すぎる")
    print("   → 送信間隔の調整")

def show_security_recommendations():
    """セキュリティ推奨事項"""
    print("\n" + "=" * 80)
    print("🛡️ セキュリティ推奨事項")
    print("=" * 80)
    
    print("\n🔒 推奨セキュリティ設定:")
    print("1. 多要素認証の強制")
    print("2. 条件付きアクセスポリシーの設定")
    print("3. アプリパスワードの定期更新")
    print("4. OAuth2認証への移行")
    print("5. 送信ログの監視")
    
    print("\n📊 監視項目:")
    print("1. 異常な送信パターンの検出")
    print("2. 認証失敗の監視")
    print("3. アプリパスワードの使用状況")
    print("4. 迷惑メール判定率の追跡")
    
    print("\n🔄 定期メンテナンス:")
    print("1. アプリパスワードの更新（6ヶ月毎）")
    print("2. OAuth2クライアントシークレットの更新（24ヶ月毎）")
    print("3. セキュリティログの確認（月次）")
    print("4. 送信レピュテーションの監視（週次）")

def main():
    """メイン処理"""
    print("🏢 Microsoft 365 SMTP認証問題 - 管理者向け包括ガイド")
    
    # 解決策の概要
    show_admin_solutions()
    
    # アプリパスワードガイド
    show_app_password_admin_guide()
    
    # OAuth2ガイド
    show_oauth2_admin_guide()
    
    # SMTP認証有効化（非推奨）
    show_smtp_auth_enable_guide()
    
    # トラブルシューティング
    show_troubleshooting_guide()
    
    # セキュリティ推奨事項
    show_security_recommendations()
    
    print("\n" + "=" * 80)
    print("📋 推奨アクション:")
    print("1. アプリパスワード生成の実行")
    print("2. python microsoft365_app_password_guide.py の実行")
    print("3. 送信テストの実施")
    print("4. 本格運用への移行")
    print("=" * 80)

if __name__ == "__main__":
    main()
