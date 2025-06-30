# 派生版メールマーケティングシステム デプロイメントガイド

## 🎯 概要

この派生版システムは、元のメールマーケティングシステムから完全に独立した環境で動作します。
新機能の開発、テスト、実験を安全に行うことができます。

## ✅ 構築完了確認

### テスト結果
- **全テスト合格**: ✅ 
- **独立性確認**: ✅ 元システムとの干渉なし
- **構文チェック**: ✅ 全スクリプト正常
- **設定分離**: ✅ 独立した設定ファイル
- **ポート分離**: ✅ 5002番ポート使用

## 🚀 クイックスタート

### 1. ダッシュボード起動
```bash
# 派生版システムディレクトリに移動
cd email_marketing_derivative_system

# ダッシュボード起動
start_derivative_dashboard.bat
```
**アクセスURL**: http://127.0.0.1:5002/

### 2. 統合ワークフロー実行
```bash
# 派生版システムディレクトリに移動
cd email_marketing_derivative_system

# 統合ワークフロー実行
run_derivative_workflow.bat
```

### 3. 個別スクリプト実行
```bash
# メールアドレス抽出
python core_scripts/derivative_email_extractor.py --start-id 1 --end-id 3

# ウェブサイト分析
python core_scripts/derivative_website_analyzer.py --start-id 1 --end-id 3

# メール送信
python core_scripts/derivative_email_sender.py --start-id 1 --end-id 3
```

## 📁 システム構造

```
email_marketing_derivative_system/
├── 📂 core_scripts/           # コアスクリプト
│   ├── derivative_integrated_workflow.py
│   ├── derivative_email_extractor.py
│   ├── derivative_website_analyzer.py
│   └── derivative_email_sender.py
├── 📂 dashboard/              # ダッシュボード
│   └── derivative_dashboard.py
├── 📂 config/                 # 設定ファイル
│   └── derivative_email_config.ini
├── 📂 data/                   # データファイル
│   ├── derivative_input.csv
│   ├── results/
│   └── derivative_consolidated/
├── 📂 templates/              # HTMLテンプレート
├── 📂 logs/                   # ログファイル
├── 🚀 start_derivative_dashboard.bat
├── 🔄 run_derivative_workflow.bat
├── 🧪 test_derivative_system.py
└── 📖 README.md
```

## 🔧 設定詳細

### ポート設定
- **派生版ダッシュボード**: 5002番ポート
- **元システム**: 5001番ポート（干渉なし）

### データファイル
- **入力**: `data/derivative_input.csv`
- **出力**: `data/results/` ディレクトリ
- **統合**: `data/derivative_consolidated/` ディレクトリ

### ログファイル
- **ダッシュボード**: `logs/derivative_dashboard/`
- **統合ワークフロー**: `logs/derivative_dashboard/derivative_integrated_workflow.log`

## 🛠️ 開発ガイド

### 新機能追加手順
1. `core_scripts/` に新しいスクリプトを追加
2. `derivative_` プレフィックスを使用
3. 設定ファイルは `config/derivative_email_config.ini` を参照
4. データファイルは `data/` ディレクトリを使用
5. ダッシュボードに統合

### テスト実行
```bash
python test_derivative_system.py
```

### デバッグモード
```bash
python dashboard/derivative_dashboard.py --debug --port 5002
```

## 🔒 セキュリティ

### 独立性の確保
- ✅ 独立したポート番号（5002）
- ✅ 独立したデータディレクトリ
- ✅ 独立した設定ファイル
- ✅ 独立したログディレクトリ
- ✅ 派生版専用のファイル命名規則

### 元システムとの分離
- ❌ 元システムのファイルを変更しない
- ❌ 元システムのポートを使用しない
- ❌ 元システムのデータを変更しない

## 📊 監視とメンテナンス

### ログ監視
```bash
# ダッシュボードログ
tail -f logs/derivative_dashboard/derivative_dashboard.log

# 統合ワークフローログ
tail -f logs/derivative_dashboard/derivative_integrated_workflow.log
```

### パフォーマンス監視
- メモリ使用量: ダッシュボードで確認
- 処理時間: ログファイルで確認
- エラー率: ダッシュボードで確認

## 🚨 トラブルシューティング

### よくある問題

#### 1. ポート競合
```bash
# ポート使用状況確認
netstat -an | findstr :5002

# 別ポートで起動
python dashboard/derivative_dashboard.py --port 5003
```

#### 2. ファイル権限エラー
```bash
# ディレクトリ権限確認
dir data /Q

# 権限修正（管理者権限で実行）
icacls data /grant Users:F /T
```

#### 3. 依存関係エラー
```bash
# 必要なパッケージインストール
pip install -r requirements.txt
```

### エラーログ確認
1. `logs/derivative_dashboard/` ディレクトリを確認
2. 最新のログファイルを開く
3. ERROR または CRITICAL レベルのメッセージを検索

## 📈 パフォーマンス最適化

### 推奨設定
- **バッチサイズ**: 3-5社（小規模テスト用）
- **タイムアウト**: 10分（安全性重視）
- **メモリ制限**: 2GB
- **同時実行**: 1プロセス

### スケーリング
- 大量データ処理時は元システムを使用
- 派生版は開発・テスト用途に限定
- 本番環境への適用前に十分なテストを実施

## 🔄 バックアップとリストア

### バックアップ
```bash
# データディレクトリのバックアップ
xcopy data backup_data /E /I /Y

# 設定ファイルのバックアップ
copy config\derivative_email_config.ini backup_config.ini
```

### リストア
```bash
# データディレクトリのリストア
xcopy backup_data data /E /I /Y

# 設定ファイルのリストア
copy backup_config.ini config\derivative_email_config.ini
```

## 📞 サポート

### 問題報告
1. `test_derivative_system.py` を実行
2. 生成されたレポートファイルを確認
3. ログファイルを添付して報告

### 開発者向け情報
- **基盤システム**: メールマーケティングシステム v2.0
- **Python バージョン**: 3.8+
- **主要依存関係**: Flask, pandas, selenium, requests

---

**作成日**: 2025-06-18  
**バージョン**: 1.0.0  
**ステータス**: 本番準備完了 ✅
