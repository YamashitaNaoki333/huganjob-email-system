# HUGAN JOB メール送信システム 使用ガイド

**作成日時**: 2025年06月20日 22:00:00  
**システム状況**: 🟢 実装完了・テスト準備完了  
**対応データ**: 1,885社（new_input_test.csv）

---

## 📋 目次

1. [システム概要](#システム概要)
2. [新機能の特徴](#新機能の特徴)
3. [使用方法](#使用方法)
4. [設定ファイル](#設定ファイル)
5. [トラブルシューティング](#トラブルシューティング)

---

## 🎯 システム概要

HUGAN JOBメール送信システムは、CSVデータを基にした企業向け採用メール一括送信システムです。

### 主要機能
- **📧 メールアドレス決定ロジック**: CSV直接 → ウェブ抽出の優先順位
- **🎨 動的テンプレート**: 企業名・募集職種の自動挿入
- **📊 送信状況追跡**: 成功・失敗・エラー内容の記録
- **⚡ 送信レート制限**: スパム対策のための送信間隔制御
- **🧪 テストモード**: 安全な動作確認機能

---

## ✨ 新機能の特徴

### 1. メールアドレス決定ロジック（優先順位順）

#### 第1優先：CSV直接メールアドレス
```
CSVの「担当者メールアドレス」列に有効なメールアドレスが存在
→ そのアドレスを使用
```

#### 第2優先：ウェブサイト抽出
```
担当者メールアドレスが空白（‐）または無効
→ 既存のメール抽出システムを使用
```

### 2. 動的メールカスタマイズ

**テンプレート変数**:
- `{{company_name}}`: 企業名の自動挿入
- `{{job_position}}`: 募集職種の自動挿入

**送信者情報**:
- 送信者名: `竹下隼平【株式会社HUGAN】`
- 送信者メール: `contact@huganjob.jp`
- SMTPサーバー: `smtp.huganjob.jp:587`

### 3. 送信制御機能

- **送信間隔**: 5秒（設定可能）
- **最大送信数制限**: 指定可能
- **ID範囲指定**: 開始ID〜終了IDでの送信
- **エラーハンドリング**: 詳細なエラー記録

---

## 🚀 使用方法

### 1. 簡単テスト送信

```bash
# テストモード（実際の送信なし）
python huganjob_test_sender.py
```

### 2. 少数企業への実際のテスト送信

```bash
# 1社のみテスト送信
python huganjob_bulk_email_sender.py --start-id 1 --end-id 1 --test-mode

# 実際の送信（1社のみ）
python huganjob_bulk_email_sender.py --start-id 1 --end-id 1
```

### 3. 一括送信

```bash
# 全企業への送信
python huganjob_bulk_email_sender.py

# ID範囲指定送信
python huganjob_bulk_email_sender.py --start-id 1 --end-id 100

# 最大送信数制限
python huganjob_bulk_email_sender.py --max-emails 50
```

### 4. コマンドラインオプション

| オプション | 説明 | 例 |
|-----------|------|-----|
| `--start-id` | 開始企業ID | `--start-id 1` |
| `--end-id` | 終了企業ID | `--end-id 100` |
| `--max-emails` | 最大送信数 | `--max-emails 50` |
| `--test-mode` | テストモード | `--test-mode` |
| `--config` | 設定ファイル | `--config config/huganjob_email_config.ini` |

---

## ⚙️ 設定ファイル

### config/huganjob_email_config.ini

```ini
[SMTP]
server = smtp.huganjob.jp
port = 587
user = contact@huganjob.jp
password = gD34bEmB
sender_name = 竹下隼平【株式会社HUGAN】
from_email = contact@huganjob.jp
reply_to = contact@huganjob.jp

[EMAIL_CONTENT]
subject = 【{job_position}の人材採用を強化しませんか？】株式会社HUGANからのご提案
template_file = corporate-email-newsletter.html
unsubscribe_url = https://forms.gle/49BTNfSgUeNkH7rz5

[SENDING]
interval = 5
max_per_hour = 50
method = send_message
```

---

## 📊 送信結果の確認

### 1. ログファイル
- `logs/huganjob_bulk_sender.log`: 送信処理ログ
- `logs/huganjob_email_resolver.log`: メールアドレス決定ログ

### 2. 結果CSVファイル
- `huganjob_sending_results_YYYYMMDD_HHMMSS.csv`: 送信結果詳細
- `huganjob_email_resolution_results.csv`: メールアドレス決定結果

### 3. ダッシュボード
```bash
python dashboard/derivative_dashboard.py --port 5002
# http://127.0.0.1:5002/ でアクセス
```

---

## 🔍 トラブルシューティング

### よくある問題

#### 1. SMTP接続エラー
```bash
# 設定確認
cat config/huganjob_email_config.ini

# 手動接続テスト
python send_huganjob_test_emails.py
```

#### 2. CSVデータ読み込みエラー
```bash
# ファイル存在確認
ls -la data/new_input_test.csv

# データ形式確認
head -5 data/new_input_test.csv
```

#### 3. メールアドレス決定エラー
```bash
# メールアドレス決定のみ実行
python huganjob_email_address_resolver.py
```

### エラーコード

| エラー | 原因 | 解決方法 |
|--------|------|----------|
| `設定ファイル読み込み失敗` | config/huganjob_email_config.ini不存在 | 設定ファイル確認 |
| `企業データ読み込み失敗` | data/new_input_test.csv不存在 | CSVファイル確認 |
| `SMTP接続失敗` | サーバー接続エラー | ネットワーク・認証情報確認 |
| `送信可能企業なし` | 有効メールアドレスなし | データ内容確認 |

---

## 📝 運用推奨手順

### 1. 初回実行時
```bash
# 1. テストモードで動作確認
python huganjob_test_sender.py

# 2. 1社のみ実際送信
python huganjob_bulk_email_sender.py --start-id 1 --end-id 1

# 3. 少数企業でテスト
python huganjob_bulk_email_sender.py --max-emails 10
```

### 2. 本格運用時
```bash
# 1. 段階的送信（100社ずつ）
python huganjob_bulk_email_sender.py --start-id 1 --end-id 100
python huganjob_bulk_email_sender.py --start-id 101 --end-id 200

# 2. 送信結果確認
# ダッシュボードまたはCSVファイルで確認

# 3. エラー企業への個別対応
# 必要に応じて個別送信
```

### 3. 定期メンテナンス
- 送信結果ログの確認
- バウンス率の監視
- 企業データの更新
- システムパフォーマンスの確認

---

## 🎯 重要な注意事項

1. **送信レート制限**: 1日あたりの送信数制限に注意
2. **スパム対策**: 送信内容・頻度の管理
3. **個人情報保護**: 企業データの適切な管理
4. **バックアップ**: 定期的なデータバックアップ
5. **テスト実行**: 本格送信前の必須テスト

---

**システム管理者**: AI Assistant  
**最終更新**: 2025年06月20日 22:00:00  
**バージョン**: 1.0.0
