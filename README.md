# HUGANJOB営業メール送信システム

## 📋 概要

HUGANJOB営業メール送信システムは、企業の採用担当者に対してHUGAN JOBの人材紹介サービスを紹介する営業メールを自動送信するシステムです。

## 🚀 主要機能

- **📊 企業データ管理**: 企業情報の登録・管理・編集
- **📧 メール送信**: HTML/テキスト形式での自動メール送信
- **📈 進行状況監視**: リアルタイム送信進捗表示
- **🚫 配信停止管理**: Googleフォーム連携による配信停止処理
- **📊 ダッシュボード**: Web管理画面による統合管理
- **🔄 バウンス処理**: 無効メールアドレスの自動検出・除外

## ディレクトリ構造

```
email_marketing_derivative_system/
├── core_scripts/           # コアスクリプトファイル
│   ├── derivative_integrated_workflow.py
│   ├── derivative_email_extractor.py
│   ├── derivative_website_analyzer.py
│   └── derivative_email_sender.py
├── dashboard/              # ダッシュボード関連
│   └── derivative_dashboard.py
├── templates/              # HTMLテンプレート
├── config/                 # 設定ファイル
│   └── derivative_email_config.ini
├── data/                   # データファイル
│   ├── derivative_input.csv
│   └── results/
├── logs/                   # ログファイル
└── README.md              # このファイル
```

## 主要機能

### 1. 統合ワークフロー
- **ファイル**: `core_scripts/derivative_integrated_workflow.py`
- **機能**: メール抽出、ウェブサイト分析、メール送信の統合処理

### 2. メールアドレス抽出
- **ファイル**: `core_scripts/derivative_email_extractor.py`
- **機能**: 企業ウェブサイトからのメールアドレス自動抽出

### 3. ウェブサイト分析
- **ファイル**: `core_scripts/derivative_website_analyzer.py`
- **機能**: 企業ウェブサイトの品質評価とランク付け

### 4. メール送信
- **ファイル**: `core_scripts/derivative_email_sender.py`
- **機能**: ランク別メールテンプレートによる自動送信

### 5. ダッシュボード
- **ファイル**: `dashboard/derivative_dashboard.py`
- **機能**: 統合管理画面、統計表示、リアルタイム監視
- **アクセス**: http://127.0.0.1:5002/ (元システムとは異なるポート)

## 元システムとの違い

### 独立性の確保
- **ポート番号**: 5002 (元システム: 5001)
- **データファイル**: 独立したCSVファイル
- **ログファイル**: 独立したログディレクトリ
- **設定ファイル**: 派生版専用の設定

### ファイル命名規則
- **接頭辞**: `derivative_` を追加
- **データファイル**: `derivative_` プレフィックス
- **ログファイル**: `derivative_logs/` ディレクトリ

## セットアップ手順

### 1. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 2. 設定ファイルの調整
```bash
# config/derivative_email_config.ini を編集
# 必要に応じてSMTP/IMAP設定を調整
```

### 3. 入力データの準備
```bash
# data/derivative_input.csv に企業データを配置
```

### 4. ダッシュボードの起動
```bash
cd dashboard
python derivative_dashboard.py
```

### 5. 統合ワークフローの実行
```bash
cd core_scripts
python derivative_integrated_workflow.py --start-id 1 --end-id 10
```

## 開発ガイドライン

### 新機能の追加
1. `core_scripts/` に新しいスクリプトを追加
2. `derivative_` プレフィックスを使用
3. 独立したデータファイルを使用
4. ダッシュボードに統合

### テスト
1. 小規模データでのテスト実行
2. 元システムとの干渉チェック
3. ログファイルでの動作確認

## 注意事項

- 元システムと同時実行する場合は、ポート番号の競合に注意
- データファイルの混在を避けるため、必ず派生版専用ファイルを使用
- 設定ファイルは派生版専用のものを使用し、元システムの設定を変更しない

## サポート

問題が発生した場合は、以下を確認してください：
1. ログファイル (`logs/` ディレクトリ)
2. 設定ファイル (`config/` ディレクトリ)
3. データファイルの整合性 (`data/` ディレクトリ)

---

**作成日**: 2025-06-18
**バージョン**: 1.0.0
**基盤システム**: メールマーケティングシステム v2.0
