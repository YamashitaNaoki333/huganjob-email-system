# Git管理対象ファイル一覧

## ✅ 安全にコミット可能なファイル

### 📋 基本ファイル
- `.gitignore` - Git除外設定
- `README.md` - プロジェクト説明
- `SAFE_FILES_FOR_GIT.md` - このファイル

### ⚙️ 設定ファイル（テンプレート）
- `config/huganjob_email_config.ini.template` - メール設定テンプレート
- `config/huganjob_dashboard_config.json` - ダッシュボード設定

### 📊 サンプルデータ
- `data/sample_companies.csv` - サンプル企業データ

### 🐍 Pythonスクリプト（機密情報除去後）
- `huganjob_unified_sender.py` - 統合メール送信システム
- `huganjob_lightweight_sender.py` - 軽量送信システム
- `huganjob_text_only_sender.py` - テキスト専用送信
- `huganjob_unsubscribe_manager.py` - 配信停止管理

### 🌐 ダッシュボード
- `dashboard/derivative_dashboard.py` - メインダッシュボード
- `dashboard/templates/` - HTMLテンプレート

### 📧 メールテンプレート
- `templates/corporate-email-newsletter.html` - HTMLメールテンプレート
- `templates/base.html` - ベーステンプレート

### 📚 ドキュメント
- `HUGANJOB_CORE_SYSTEM_SPECIFICATIONS.md` - システム仕様書
- `AI_ONBOARDING_CHECKLIST.md` - オンボーディングガイド

## ❌ 除外されるファイル（.gitignoreで設定済み）

### 🚨 機密情報
- `config/huganjob_email_config.ini` - SMTP認証情報
- `config/google_sheets_credentials.json` - Google API秘密鍵
- `config/rare-basis-454906-a9-bd7e05c67ab2.json` - Google認証ファイル

### 📊 企業データ
- `data/new_input_test.csv` - 実際の企業データ（4,831社）
- `huganjob_email_resolution_results.csv` - メールアドレス抽出結果
- `huganjob_sending_history.json` - 送信履歴
- `new_email_sending_results.csv` - 送信結果

### 📁 ログ・一時ファイル
- `logs/` - 全ログファイル
- `__pycache__/` - Pythonキャッシュ
- `temp_uploads/` - 一時アップロード
- `*.lock` - ロックファイル

## 🔧 次のステップ

1. 基本ファイルのコミット
2. Pythonスクリプトの機密情報除去
3. ダッシュボードファイルの追加
4. ドキュメントファイルの追加
5. 初回コミットの作成
