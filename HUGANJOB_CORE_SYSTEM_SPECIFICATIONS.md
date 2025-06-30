# HUGAN JOB営業メール送信システム - 基幹システム仕様書

## 📋 システム概要

HUGAN JOB営業メール送信システムは、大阪府内の企業に対してHUGAN JOBの採用支援サービスを紹介する営業メールを自動送信するシステムです。

### 主要機能
- 企業データの管理（4,838社）
- **🆕 企業追加機能**（手動・CSV一括インポート）
- **🆕 重複チェック機能**（ドメイン優先・企業名フォールバック）
- **🆕 不完全データバリデーション**（メールアドレス・ウェブサイト両方空の自動除外）
- **🆕 CSVインポート即時反映**（自動キャッシュクリア・ページリロード）
- メールアドレスの自動抽出・検証
- 営業メールの自動生成・送信
- 送信結果の追跡・管理
- ダッシュボードによる進捗管理
- **🆕 配信停止管理システム**（Googleフォーム連携）
- **🆕 Google Sheets監視システム**（リアルタイム配信停止処理）

## 🏗️ システムアーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                    HUGAN JOB営業メールシステム                    │
├─────────────────────────────────────────────────────────────┤
│  📊 ダッシュボード (Flask) - 🔧huganjob_unified_sender.py専用化    │
│  ├─ derivative_dashboard.py (🔧簡素化・統一送信専用)         │
│  ├─ templates/index.html (🔧統一送信フォームのみ)            │
│  ├─ templates/huganjob_companies.html                      │
│  ├─ templates/add_company.html (🆕企業追加フォーム)           │
│  ├─ templates/csv_import.html (🆕CSVインポート)              │
│  ├─ templates/unsubscribe_management.html                  │
│  ├─ templates/sheets_monitor.html                          │
│  └─ [削除] 複数送信システム対応機能                           │
├─────────────────────────────────────────────────────────────┤
│  🚫 配信停止管理システム                                         │
│  ├─ huganjob_unsubscribe_manager.py                        │
│  ├─ huganjob_google_sheets_monitor.py                      │
│  ├─ setup_google_sheets_api.py                             │
│  └─ data/huganjob_unsubscribe_log.csv                      │
├─────────────────────────────────────────────────────────────┤
│  📧 メールアドレス抽出・決定システム                                │
│  ├─ huganjob_email_address_resolver.py                     │
│  ├─ core_scripts/derivative_email_extractor.py             │
│  └─ huganjob_email_resolution_results.csv                  │
├─────────────────────────────────────────────────────────────┤
│  📨 メール送信システム（🔧統一化・簡素化）                          │
│  ├─ huganjob_unified_sender.py (🎯専用送信システム・MIMEText構造) │
│  ├─ [削除] huganjob_lightweight_sender.py                  │
│  ├─ [削除] huganjob_anti_spam_sender.py                    │
│  ├─ [削除] huganjob_thunderbird_style_sender.py            │
│  ├─ huganjob_unsubscribe_sender.py (🆕配信停止リンク付き)    │
│  ├─ huganjob_clean_sender.py (🆕URL削除版)                 │
│  ├─ huganjob_text_only_sender.py (非推奨)                  │
│  ├─ templates/corporate-email-newsletter.html (追跡削除済み)│
│  ├─ templates/corporate-email-newsletter-clean.html (🆕URL削除版)│
│  ├─ templates/corporate-email-newsletter-text.txt (非推奨) │
│  └─ SMTP: smtp.huganjob.jp:587                             │
├─────────────────────────────────────────────────────────────┤
│  📂 データ管理                                                │
│  ├─ data/new_input_test.csv (1,859社の企業データ)             │
│  ├─ new_email_sending_results.csv                          │
│  ├─ huganjob_sending_history.json                          │
│  └─ logs/huganjob_*.log                                    │
└─────────────────────────────────────────────────────────────┘
```

## 📁 重要な基幹ファイル一覧

### 1. メールアドレス抽出・決定システム
- **`huganjob_email_address_resolver.py`** (基幹)
  - 企業のメールアドレス決定処理
  - CSV直接取得 → ウェブサイト抽出の優先順位
  - 高度な抽出システムとの連携
  - 結果のCSV保存（追記機能付き）

### 2. ダッシュボードシステム（🔧2025年6月27日 統一化・簡素化）
- **`dashboard/derivative_dashboard.py`** (基幹)
  - Flask Webアプリケーション
  - 🔧 huganjob_unified_sender.py専用化
  - 🗑️ 複数送信システム削除（production_send, text_only_send, flexible_send, anti_spam_send）
  - 🎯 単一API: `/api/huganjob/send`のみ
  - 企業一覧表示・管理機能は維持

- **`dashboard/templates/index.html`** (🔧簡素化)
  - huganjob_unified_sender.py専用送信フォーム
  - 固定パラメータ: `--email-format html_only`
  - リアルタイムコマンド表示
  - 🗑️ 複数送信オプション削除

- **`dashboard/templates/huganjob_companies.html`**
  - 企業一覧表示テンプレート（変更なし）
  - メールアドレス抽出状況表示
  - 送信ステータス管理

### 3. メール送信システム（🔧2025年6月27日 統一化完了）
- **`huganjob_unified_sender.py`** (🎯唯一の送信システム)
  - 🔧 MIMEText単体構造（迷惑メール対策）
  - 🎯 HTMLメール専用（`--email-format html_only`固定）
  - ✅ 重複送信防止・バウンス除外・配信停止チェック
  - ✅ 5秒送信間隔・SMTP認証・追跡ID生成
  - 🗑️ 他の送信システムは全て削除済み

- **`templates/corporate-email-newsletter.html`**
  - HTMLメールテンプレート（唯一のテンプレート）
  - 動的フィールド挿入対応（{{company_name}}, {{job_position}}）
  - UTMパラメータ・マーケティング要素含む

- **🗑️ 削除済みシステム**
  - huganjob_text_only_sender.py
  - huganjob_lightweight_sender.py
  - huganjob_anti_spam_sender.py
  - huganjob_thunderbird_style_sender.py
  - 対応するテンプレートファイル

### 4. データファイル
- **`data/new_input_test.csv`** (1885社)
  - 企業マスターデータ
  - 列: ID, 企業名, 企業ホームページ, 採用担当メールアドレス, 募集職種

- **`huganjob_email_resolution_results.csv`**
  - メールアドレス抽出結果
  - 追記式保存（重複ID自動更新）

## 🏢 企業追加・管理システム

### 🆕 企業追加機能

#### 手動企業追加（/add-company）
**用途**: 単一企業の手動追加

**機能**:
- 企業名、ウェブサイト、メールアドレス、募集職種の入力
- リアルタイムデータ検証
- 重複チェック（ドメイン優先・企業名フォールバック）
- 自動ID採番（最大ID + 1）

**APIエンドポイント**:
- `GET /add-company` - 企業追加フォーム表示
- `POST /api/add-company` - 企業追加処理

#### CSVインポート機能（/csv-import）
**用途**: 複数企業の一括追加

**機能**:
- CSVファイルアップロード（ドラッグ&ドロップ対応）
- 自動列マッピング（ヘッダー解析）
- データプレビュー・品質チェック
- 一括重複チェック・スキップ機能
- 詳細インポート結果レポート

**APIエンドポイント**:
- `GET /csv-import` - CSVインポートページ表示
- `POST /api/csv-import` - CSVファイル解析・プレビュー
- `POST /api/csv-import-confirm` - インポート実行
- `POST /api/import-newdata` - newdata.csv直接インポート

### 🔍 重複チェックアルゴリズム

#### 優先順位ベース判定
1. **ドメイン優先判定**
   - 両企業が有効なURLを持つ場合 → ドメインで比較
   - 同じドメインなら重複と判定

2. **企業名フォールバック判定**
   - 新規企業にURLがない場合 → 企業名で比較
   - 既存企業にURLがなく新規企業にURLがある場合 → 企業名で比較

#### 有効なURLの定義
- `http://`または`https://`で始まる
- `‐`、`-`、空文字列は無効

#### 判定ケース
| 既存企業 | 新規企業 | 判定方法 | 例 |
|----------|----------|----------|-----|
| URL有り | URL有り | ドメイン比較 | `example.com` vs `example.com` |
| URL無し | URL無し | 企業名比較 | `株式会社A` vs `株式会社A` |
| URL有り | URL無し | 企業名比較 | `株式会社A` vs `株式会社A` |
| URL無し | URL有り | 企業名比較 | `株式会社A` vs `株式会社A` |

### 📊 データ検証機能

#### 企業名検証
- 2文字以上の長さチェック
- 空文字列・None値のチェック

#### ウェブサイト検証
- 基本的なURL形式チェック（ドット含有、スペース除外）
- `http://`または`https://`の自動補完
- 「‐」、「-」、空文字列は有効なURLとして扱わない

#### メールアドレス検証
- `@`マークの存在確認
- ドメイン部分にドットが含まれているかチェック

## 📧 メール送信システム

### 🔄 統合送信システム（huganjob_unified_sender.py）
**用途**: 🆕 HTMLメール専用送信（2025年6月25日より変更）

#### 送信フロー
1. **企業データ読み込み** (`data/new_input_test.csv`)
2. **メールアドレス決定** (抽出結果 → CSV直接 → ドメイン生成)
3. **抽出結果自動更新** (新規メールアドレスの自動記録)
4. **重複送信チェック** (24時間以内の送信履歴確認)
5. **バウンス履歴チェック** (無効アドレス除外)
6. **🆕 HTMLメール作成** (テキスト版は無効化)
7. **メール送信実行** (SMTP経由)
8. **結果記録** (JSON + CSV形式)
9. **データ整合性確保** (抽出結果ファイルとの同期)

### 📝 テキスト専用送信システム（huganjob_text_only_sender.py）
**用途**: HTMLメール表示問題対応、軽量・高速送信

#### 送信フロー
1. **企業データ読み込み** (`data/new_input_test.csv`)
2. **メールアドレス決定** (抽出結果 → CSV直接)
3. **配信停止チェック** (配信停止企業の除外)
4. **バウンス履歴チェック** (無効アドレス除外)
5. **テキストメール作成** (プレーンテキストのみ)
6. **メール送信実行** (SMTP経由)
7. **結果記録** (CSV形式: huganjob_text_email_results.csv)

#### 特徴
- **軽量処理**: HTMLレンダリング不要
- **高互換性**: 全てのメールクライアントで表示可能
- **重複送信許可**: 配信停止以外は複数回送信可能
- **専用テンプレート**: 自然で読みやすいテキスト構成

### メールアドレス決定ロジック（優先順位）
1. **第1優先**: CSVの担当者メールアドレス（`担当者メールアドレス`列）
2. **第2優先**: メールアドレス抽出結果 (`huganjob_email_resolution_results.csv`)
3. **第3優先**: ドメインベース生成 (`info@domain.com`、www.除去機能付き)

### 🆕 自動データ管理機能
- **抽出結果自動更新**: 送信時に`huganjob_email_resolution_results.csv`を自動更新
- **www.ドメイン処理**: `www.domain.com` → `domain.com`の自動変換
- **データ整合性チェック**: 送信記録と抽出結果の自動同期
- **重複データ防止**: 同一企業IDの重複エントリ自動削除

### 🛡️ 共通安全機能
- **送信間隔**: 5-10秒（スパム対策）
- **配信停止チェック**: 配信停止企業の自動除外
- **バウンス管理**: 無効アドレスの自動除外
- **SMTP認証**: contact@huganjob.jp経由の認証済み送信
- **DNS検証スキップ**: デフォルトでDNS解決チェックを無効化（機械的送信）
- **🆕 迷惑メール対策**: 偽装ヘッダー削除、追跡機能削除、配信停止リンク挿入

### 🔍 データ品質管理システム（2025年6月26日実装）

#### 不完全データバリデーション
- **自動除外条件**: メールアドレスとウェブサイトの両方が空または無効値
- **無効値判定**: `''`, `'未登録'`, `'-'`, `'‐'`, `null`, `NaN`
- **適用範囲**: CSVインポート時・手動企業追加時
- **レポート機能**: 除外された企業の詳細情報を表示

#### 即時反映システム
- **自動キャッシュクリア**: CSVインポート・企業追加成功時
- **フロントエンド自動更新**: 2秒後の自動ページリロード
- **データ整合性保証**: 操作後の即座なデータ反映

### 🔄 重複送信制御
#### 統合送信システム（huganjob_unified_sender.py）
- **重複防止**: 24時間以内の重複送信を防止
- **多重化開封追跡**: 9種類の並行追跡システム

#### テキスト専用システム（huganjob_text_only_sender.py）
- **重複送信許可**: 配信停止以外は複数回送信可能
- **開封追跡なし**: プレーンテキストのため追跡機能なし

#### 🆕 軽量送信システム（huganjob_lightweight_sender.py）
- **高速処理**: 重いファイル処理を完全排除
- **確実な終了**: プロセスハング問題の回避
- **最小限機能**: 送信とメモリ内結果管理のみ
- **緊急対応用**: ダッシュボード問題時の代替手段

## 📊 多重化開封追跡システム（2025年6月24日実装）

### 追跡システムアーキテクチャ
```
┌─────────────────────────────────────────────────────────────┐
│                    多重化開封追跡システム                        │
├─────────────────────────────────────────────────────────────┤
│  🎯 HTMLメールテンプレート追跡要素                               │
│  ├─ メインピクセル追跡 (track-open)                           │
│  ├─ フォールバックピクセル (track)                            │
│  ├─ CSS背景画像追跡 (track-css)                              │
│  └─ JavaScript多重ビーコン (6種類)                           │
├─────────────────────────────────────────────────────────────┤
│  🌐 ダッシュボード追跡エンドポイント                             │
│  ├─ /track-open/{tracking_id} - メイン追跡                   │
│  ├─ /track/{tracking_id} - フォールバック追跡                │
│  ├─ /track-css/{tracking_id} - CSS追跡                      │
│  ├─ /track-beacon/{tracking_id} - ビーコン追跡               │
│  ├─ /track-xhr/{tracking_id} - XHR追跡                      │
│  ├─ /track-focus/{tracking_id} - フォーカス追跡              │
│  └─ /track-unload/{tracking_id} - 離脱時追跡                │
├─────────────────────────────────────────────────────────────┤
│  📁 追跡データ保存                                            │
│  ├─ data/derivative_email_open_tracking.csv                │
│  └─ 追跡方法別統計・分析機能                                  │
└─────────────────────────────────────────────────────────────┘
```

### 9種類の並行追跡方法
1. **メインピクセル追跡**: `/track-open/{tracking_id}` - 基本的な1x1ピクセル画像
2. **フォールバックピクセル**: `/track/{tracking_id}` - 代替追跡ピクセル
3. **CSS背景画像追跡**: `/track-css/{tracking_id}` - 画像ブロック回避
4. **JavaScript ビーコン追跡**: `/track-beacon/{tracking_id}` - navigator.sendBeacon API
5. **XMLHttpRequest追跡**: `/track-xhr/{tracking_id}` - XHR通信
6. **Fetch API追跡**: JavaScript fetch() による追跡
7. **フォーカス時追跡**: `/track-focus/{tracking_id}` - ページフォーカス検知
8. **離脱時追跡**: `/track-unload/{tracking_id}` - ページ離脱時検知
9. **画像リクエスト追跡**: JavaScript Image() オブジェクト

### 追跡実行フロー
```
メール開封時の追跡シーケンス:
1. 即座実行: ビーコンAPI追跡
2. 1秒後: Fetch API追跡
3. 3秒後: 画像リクエスト追跡
4. フォーカス時: フォーカス追跡
5. 離脱時: 離脱時追跡

エラー時自動リトライ:
ビーコン失敗 → Fetch API → XMLHttpRequest → 画像リクエスト
最大3回まで自動リトライ
```

### 企業環境対応機能
- **画像ブロック環境**: CSS追跡、JavaScript追跡で対応
- **JavaScript無効環境**: 複数ピクセル追跡で対応
- **厳格セキュリティ環境**: フォールバック機能で対応
- **プロキシ環境**: 複数経路での追跡試行

### 🔧 システムエラー修正（2025年6月24日）
**修正されたエラー**: `'NoneType' object has no attribute 'clear'`
```python
def clear_stats_cache():
    """統計キャッシュをクリアする（エラー修正版）"""
    global stats_cache
    try:
        if 'stats_cache' in globals() and stats_cache is not None:
            stats_cache.clear()
        else:
            stats_cache = {}
    except Exception as e:
        logger.error(f"統計キャッシュクリアエラー: {e}")
        stats_cache = {}
```

## 📧 バウンス処理システム（統合管理）

### バウンス検出・処理（2025年6月24日更新）
- **huganjob_bounce_processor.py**: バウンスメール自動検出・統合処理
- **処理方式**: 受信ボックスからバウンスメールを検出し、bounceフォルダに移動
- **🆕 統合更新**: バウンス検出と企業データベース更新を同時実行（重要な改善）
- **重複防止**: 処理済みメールIDの追跡による重複処理防止
- **バウンス分類**: permanent（永続的）、temporary（一時的）、unknown（不明）
- **自動除外**: バウンス企業を今後の送信から自動除外
- **履歴管理**: 完全な処理履歴とレポート保存による監査証跡確保

### 🆕 統合処理の改善（2025年6月24日実装）
**重要な変更**: バウンスメール処理時に企業データベースを自動更新する機能を追加

#### 改善前の問題
- バウンスメールをbounceフォルダに移動するだけで企業データベースが更新されない
- ID 101以降の企業でバウンス判定が機能しない
- 手動でのデータ復元作業が必要

#### 改善後の機能
```python
def update_company_database(self):
    """企業データベースのバウンス状態を自動更新"""
    # 送信結果ファイルとバウンスメールを関連付け
    for bounce_info in self.bounce_emails:
        for bounced_email in bounce_info['bounced_addresses']:
            # 送信結果から企業を特定
            matches = df_results[df_results['メールアドレス'].str.lower() == bounced_email.lower()]
            # 企業データベースのバウンス状態を更新
            df_companies.loc[mask, 'バウンス状態'] = bounce_info['bounce_type']
            df_companies.loc[mask, 'バウンス日時'] = bounce_info['received_date']
            df_companies.loc[mask, 'バウンス理由'] = bounce_info['bounce_reason']
```

### フォルダ管理
- **INBOX**: 新着バウンスメール受信
- **INBOX.bounce**: 処理済みバウンスメール保存（検索性向上のため）
- **追跡ファイル**: `huganjob_processed_bounces.json`で処理済みメールID管理
- **レポートファイル**: `huganjob_bounce_report_YYYYMMDD_HHMMSS.json`で詳細記録

### 🔄 改善された処理フロー（2025年6月24日更新）
1. **バウンスメール検出**: IMAP接続でバウンスメール特定
2. **重複チェック**: 処理済みメールIDとの照合
3. **メール移動**: INBOXからbounceフォルダに移動
4. **🆕 企業データベース統合更新**: バウンス状態の自動更新（新機能）
5. **追跡更新**: 処理済みメールIDリストの更新
6. **レポート生成**: 処理結果の詳細レポート作成
7. **🆕 データ整合性確認**: 送信結果とバウンス状態の同期確認

### バウンス復元システム（拡張）
- **huganjob_bounce_folder_analyzer.py**: bounceフォルダ分析
- **huganjob_bounce_report_restorer.py**: レポートからの復元
- **🆕 huganjob_mailbox_investigator.py**: メールボックス調査システム
- **データ整合性**: 送信結果とバウンス状態の自動同期
- **バックアップ**: 復元前の自動バックアップ作成
- **🆕 統合復元**: バウンスレポートから企業データベースの完全復元機能

### ダッシュボードバウンス判定ロジック（2025年6月24日更新）
```python
def is_company_bounced(company):
    """多重条件によるバウンス状態判定"""
    return (
        company.get('bounced') == True or
        company.get('bounce_status') == 'permanent' or
        str(company.get('bounce_status', '')).strip().lower() == 'permanent'
    )
```

### 🆕 送信結果統合処理の改善（2025年6月24日）
**問題**: 送信結果ファイルとダッシュボード表示の不整合
**解決**: CSV読み込み処理とデータ統合ロジックの改善

#### 改善されたCSV読み込み処理
```python
# 実際のCSVファイル構造に対応
# 列順序: 企業ID, 企業名, メールアドレス, 募集職種, 送信日時, 送信結果, トラッキングID, エラーメッセージ, 件名
with open(csv_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    next(reader, None)  # ヘッダー行をスキップ
    for row_data in reader:
        company_id = row_data[0].strip()
        sent_result = row_data[5].strip()
        tracking_id = row_data[6].strip()
```

#### 統合処理の優先順位
1. **HUGANJOB送信履歴**: 最新の送信記録として最優先
2. **CSV送信結果**: 補完データとして第2優先
3. **既存バウンス状態**: 保護対象として最優先保持

**企業データベース構造（data/new_input_test.csv）:**
- 列1: 企業ID
- 列2: 企業名
- 列3: 企業ホームページ
- 列4: 担当者メールアドレス
- 列5: 募集職種
- 列6: バウンス状態（permanent/temporary/空白）
- 列7: バウンス日時
- 列8: バウンス理由

## 🔄 データフロー

```
1. 企業データ読み込み
   data/new_input_test.csv → huganjob_unified_sender.py

2. メールアドレス決定（優先順位）
   抽出結果 → CSV直接 → ドメイン生成（www.除去）

3. 自動データ更新
   huganjob_email_resolution_results.csv (自動更新・同期)

4. ダッシュボード表示
   derivative_dashboard.py → 企業一覧表示

5. メール送信
   huganjob_unified_sender.py → SMTP送信 → 結果記録
```

## ⚙️ 設定ファイルと環境変数

### SMTP設定
```python
SMTP_SERVER = "smtp.huganjob.jp"
SMTP_PORT = 587
SMTP_USERNAME = "contact@huganjob.jp"
SMTP_PASSWORD = "[設定済み]"
SMTP_USE_TLS = True
```

### 送信者情報
```python
SENDER_NAME = "竹下隼平【株式会社HUGAN】"
SENDER_EMAIL = "contact@huganjob.jp"
REPLY_TO = "contact@huganjob.jp"
```

### ダッシュボード設定
```python
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5002
DEBUG_MODE = False

# パフォーマンス最適化設定（2025年6月25日追加）
CACHE_TIMEOUT_SECONDS = 600  # 企業データキャッシュ（10分）
STATS_CACHE_TIMEOUT_SECONDS = 300  # 統計キャッシュ（5分）
DAILY_STATS_CACHE_TIMEOUT = 900  # 日別統計キャッシュ（15分）
OPEN_RATE_CACHE_TIMEOUT = 1200  # 開封率分析キャッシュ（20分）
PERFORMANCE_MODE = False  # パフォーマンス重視モード（安定性優先）
ENABLE_DEBUG_LOGGING = False  # デバッグログ無効化
```

## 📧 メールテンプレート仕様

### 📄 HTMLテンプレート
- **ファイル名**: `templates/corporate-email-newsletter.html`
- **形式**: HTML形式（マルチパート対応）
- **文字エンコーディング**: UTF-8
- **用途**: 統合送信システム（huganjob_unified_sender.py）

### 📝 テキストテンプレート
- **ファイル名**: `templates/corporate-email-newsletter-text.txt`
- **形式**: プレーンテキスト
- **文字エンコーディング**: UTF-8
- **用途**: テキスト専用送信システム（huganjob_text_only_sender.py）
- **特徴**: 自然で読みやすい文章構成、HTMLタグなし

### 🔄 動的フィールド（共通）
- `{{company_name}}`: 企業名
- `{{job_position}}`: 募集職種（第1職種のみ使用）
- **送信者**: 竹下隼平【株式会社HUGAN】
- **送信元**: contact@huganjob.jp

### 📬 件名テンプレート（共通）
```
【{{job_position}}の人材採用を強化しませんか？】株式会社HUGANからのご提案
```

### 📋 テキストテンプレート構成
```
件名: 【{{job_position}}の人材採用を強化しませんか？】株式会社HUGANからのご提案

{{company_name}} 採用ご担当者様

いつもお疲れ様です。
株式会社HUGANの竹下と申します。

{{company_name}}様の{{job_position}}の採用活動について、
弊社の人材紹介サービスでお手伝いできることがございます。

[サービス詳細・お問い合わせ先]
株式会社HUGAN
担当: 竹下
Email: contact@huganjob.jp
```

## 🔧 システム要件

### Python環境
- Python 3.8+
- 必要パッケージ: pandas, flask, requests, smtplib

### ファイル構造
```
email_marketing_derivative_system/
├── huganjob_email_address_resolver.py
├── huganjob_unified_sender.py          # 🆕 HTMLメール専用送信
├── huganjob_text_only_sender.py        # テキスト専用送信（非推奨）
├── dashboard/
│   ├── derivative_dashboard.py
│   └── templates/huganjob_companies.html
├── data/
│   └── new_input_test.csv
├── templates/
│   ├── corporate-email-newsletter.html      # HTMLテンプレート
│   └── corporate-email-newsletter-text.txt # テキストテンプレート
├── huganjob_email_resolution_results.csv
├── huganjob_text_email_results.csv     # テキスト送信結果
└── logs/
    └── huganjob_*.log
```

## 🚀 基本操作コマンド

### メールアドレス抽出
```bash
# ID範囲指定での抽出
python huganjob_email_address_resolver.py --start-id 1 --end-id 10

# 全企業の抽出
python huganjob_email_address_resolver.py
```

### ダッシュボード起動
```bash
python dashboard/derivative_dashboard.py
# アクセス: http://127.0.0.1:5002/companies
```

### 📧 メール送信コマンド

#### 🔄 統合送信（🆕 HTMLメール専用）- 推奨
```bash
# ID範囲指定での送信（自動データ更新機能付き）
python huganjob_unified_sender.py --start-id 1 --end-id 10

# 大規模送信の例
python huganjob_unified_sender.py --start-id 101 --end-id 200
```

#### 📝 テキスト専用送信
```bash
# HTMLメール表示問題対応、軽量送信
python huganjob_text_only_sender.py --start-id 1 --end-id 10

# 複数回送信可能（配信停止以外）
python huganjob_text_only_sender.py --start-id 1 --end-id 50
```

#### 🎛️ ダッシュボード経由送信
```
1. http://127.0.0.1:5002/control にアクセス
2. 「📧 メール形式選択送信」を選択
3. 送信形式を選択:
   - 🆕 HTMLメール（デフォルト・推奨）
   - HTMLのみ（同上）
   - テキストのみ（非推奨・無効化済み）
4. ID範囲を指定して送信実行
```

### 🆕 バウンス処理（統合管理）
```bash
# バウンスメール検出・企業データベース更新（推奨）
python huganjob_bounce_processor.py

# bounceフォルダ分析
python huganjob_bounce_folder_analyzer.py

# バウンスレポートからの復元
python huganjob_bounce_report_restorer.py

# メールボックス調査
python huganjob_mailbox_investigator.py
```

### 📊 データ整合性確認
```bash
# 送信履歴をCSV形式に変換
python convert_huganjob_history_to_csv.py

# 重複送信チェック（統合送信のみ）
python huganjob_duplicate_prevention.py

# バウンス状態の整合性チェック
python huganjob_bounce_processor.py --verify-only

# テキスト送信結果確認
cat huganjob_text_email_results.csv
```

### 🔍 送信結果ファイル
```bash
# 統合送信結果（JSON形式）
huganjob_email_results.json

# テキスト送信結果（CSV形式）
huganjob_text_email_results.csv

# メールアドレス抽出結果
huganjob_email_resolution_results.csv
```

## 🔒 セキュリティ仕様

### メール認証
- SMTP認証: contact@huganjob.jp
- TLS暗号化通信
- SPF/DKIM設定済み

### データ保護
- ログファイルの定期ローテーション
- 個人情報の適切な管理
- アクセス制限

## 📊 監視・ログ

### ログファイル
- `logs/huganjob_email_resolver.log`: メール抽出ログ
- `logs/huganjob_email_sender.log`: メール送信ログ

### 監視項目
- メール送信成功率
- バウンス率
- システムエラー率

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. ダッシュボードが起動しない
```bash
# ポート確認
netstat -an | findstr :5002

# 強制終了後再起動
taskkill /f /im python.exe
python dashboard/derivative_dashboard.py
```

#### 2. メールアドレス抽出が失敗する
- ネットワーク接続の確認
- ログファイルでエラー詳細を確認
- 対象企業のウェブサイトアクセス可能性確認

#### 3. CSVファイルが破損した場合
- バックアップファイルからの復旧
- 部分的な再抽出実行

### エラーコード一覧
- `HTTP 400`: 不正なリクエスト（ウェブサイトアクセス時）
- `HTTP 403`: アクセス拒否
- `HTTP 404`: ページが見つからない
- `SMTP Error`: メール送信エラー

## 🚨 迷惑メール対策システム（2025年6月26日実装）

### 迷惑メール判定問題の対策

#### 問題の背景
- HUGANJOBシステムからの送信メールが迷惑メールフォルダに分類される問題が発生
- Thunderbird直接送信は正常、ダッシュボード送信は迷惑メール判定
- 技術的要因と送信レピュテーションの複合的問題

#### 実装済み対策

##### A. ヘッダー最適化（huganjob_anti_spam_sender.py）
```python
# 削除されたヘッダー（迷惑メール判定要因）
# ❌ msg['X-Mailer'] = 'HUGAN JOB System v2.0'
# ❌ msg['Authentication-Results'] = 'huganjob.jp; spf=pass; dkim=pass'
# ❌ msg['List-Unsubscribe'] = '<https://forms.gle/49BTNfSgUeNkH7rz5>'

# 最小限のヘッダー（迷惑メール判定回避）
msg['Date'] = formatdate(localtime=True)
msg['Message-ID'] = make_msgid(domain='huganjob.jp')
```

##### B. 追跡機能完全削除
- 開封追跡ピクセル削除
- JavaScript追跡削除
- CSS背景画像追跡削除
- 全ての追跡要素を完全除去

##### C. 配信停止リンク挿入
```html
<div style="margin-top: 15px; padding: 10px;">
    <p style="margin: 0; font-size: 11px;">
        配信停止をご希望の場合は<a href="https://forms.gle/49BTNfSgUeNkH7rz5">こちら</a>からお手続きください。
    </p>
</div>
```

##### D. 件名最適化
```
修正前: 【採用ご担当者様へ】採用工数の削減とミスマッチ防止を実現するご提案｜HUGAN JOB
修正後: システムエンジニア採用について - HUGAN JOB
```

#### 残存する課題
1. **HTMLテンプレートの営業色**: 複雑なデザイン・営業的文言
2. **送信レピュテーション**: 過去の迷惑メール判定履歴
3. **DMARC設定**: 不完全な認証設定
4. **送信パターン**: 大量送信の検出

#### 推奨される次の対策
1. **プレーンテキスト送信**: HTMLを完全に削除
2. **DMARC完全設定**: Xserver DNS設定
3. **送信頻度調整**: より長い送信間隔
4. **送信レピュテーション回復**: 段階的送信再開

### 送信システムの種類と用途

#### 1. huganjob_unified_sender.py（メインシステム）
- **用途**: 通常のHTMLメール送信
- **特徴**: 追跡機能、開封率分析
- **状況**: 迷惑メール判定問題あり

#### 2. huganjob_anti_spam_sender.py（迷惑メール対策版）
- **用途**: 偽装ヘッダー削除版
- **特徴**: 最小限のヘッダー構成
- **状況**: 部分改善、完全解決には至らず

#### 3. huganjob_thunderbird_style_sender.py（Thunderbird方式）
- **用途**: Thunderbird送信の再現
- **特徴**: シンプルなヘッダー構成
- **状況**: 受信トレイ到達確認済み

#### 4. huganjob_unsubscribe_sender.py（配信停止リンク付き）
- **用途**: 法的コンプライアンス対応
- **特徴**: 配信停止リンク、追跡削除
- **状況**: 最新版、テスト中

#### 5. huganjob_clean_sender.py（URL削除版）
- **用途**: URL要因の完全除去
- **特徴**: 全URL・リンク削除
- **状況**: 改善傾向、完全解決には至らず

## 📚 開発者向け情報

### コード構造の重要なポイント

#### メールアドレス検証の優先順位
1. CSV直接取得（最優先）
2. ウェブサイト抽出（高度システム）
3. 機械的生成（info@domain）

#### データ保存の仕組み
- 追記式保存で既存データを保護
- 重複IDの自動更新
- 企業IDによる自動ソート

### 拡張可能な機能
- 新しいメール抽出アルゴリズムの追加
- 送信スケジュール機能
- レポート生成機能
- API連携機能

## 🔄 定期メンテナンス

### 日次作業
- ログファイルの確認
- システム稼働状況の確認

### 週次作業
- **🆕 バウンス処理の実行**: `python huganjob_bounce_processor.py`（推奨）
- データベースの整合性チェック
- バックアップファイルの作成

### 月次作業
- システムパフォーマンスの分析
- セキュリティ更新の確認
- **🆕 バウンス復元システムの検証**: データ整合性の完全チェック

## 🚫 配信停止管理システム（v1.5新機能）

### システム概要
Googleフォームからの配信停止申請を自動検出・処理し、企業データベースを更新するシステム。
**🆕 v1.5では個人メールアドレスからの配信停止申請に対応するドメインベース配信停止機能を追加。**

### 主要コンポーネント
- **`huganjob_unsubscribe_manager.py`**: 配信停止処理エンジン
- **`huganjob_google_sheets_monitor.py`**: Google Sheets監視システム
- **`setup_google_sheets_api.py`**: Google Sheets API設定支援
- **🆕 `manual_unsubscribe_processor.py`**: 手動配信停止処理（ドメインマッチング対応）
- **`data/huganjob_unsubscribe_log.json`**: 配信停止ログ（JSON形式に変更）

### 🆕 ドメインベース配信停止機能

#### 概要
個人メールアドレス（例：`t-hayakawa@media4u.co.jp`）からの配信停止申請に対応するため、メールアドレスのドメインと企業ホームページのドメインを照合して企業を特定する機能。

#### 技術仕様
```python
def check_unsubscribe_status(self, recipient_email, company_data=None):
    """配信停止状況をチェック（ドメインベース対応）"""
    # 1. 完全一致チェック（従来機能）
    if entry.get('メールアドレス', '').lower().strip() == recipient_email_lower:
        return True, entry.get('配信停止理由', '配信停止申請')

    # 2. ドメインベースチェック（新機能）
    if company_data and '@' in recipient_email_lower:
        recipient_domain = recipient_email_lower.split('@')[1]
        # 配信停止ログでドメインマッチングをチェック
        # 企業ホームページのドメインとも照合
```

#### ドメインマッチング処理
1. **申請メールアドレスからドメイン抽出**: `t-hayakawa@media4u.co.jp` → `media4u.co.jp`
2. **企業ホームページURLからドメイン抽出**: `https://www.media4u.co.jp/` → `media4u.co.jp`
3. **正規化処理**: www.プレフィックス除去、大文字小文字統一
4. **ドメイン一致判定**: 一致した場合、該当企業を配信停止対象とする

#### 対応ケース
- **企業メールアドレス**: `info@company.co.jp` → 完全一致処理
- **個人メールアドレス**: `yamada@company.co.jp` → ドメイン一致処理
- **異なるドメイン**: `personal@gmail.com` → 処理対象外

### 処理フロー
```
Googleフォーム入力 → スプレッドシート更新 → 監視システム検出（60秒間隔）
→ 企業データベース照合（完全一致 + ドメイン一致） → 配信停止処理実行
→ 送信システムでの自動ブロック（ドメインベース対応）
```

### 技術仕様
- **監視間隔**: 60秒（設定可能）
- **認証方式**: Google Sheets API（サービスアカウント）
- **🆕 ドメインマッチング**: URLパース処理による正確なドメイン抽出
- **🆕 配信停止ログ形式**: JSON形式（詳細な理由とソース記録）

### 配信停止ログ形式
```json
{
  "company_id": 2117,
  "company_name": "株式会社メディア4u",
  "email": "t-hayakawa@media4u.co.jp",
  "reason": "ドメイン一致による配信停止申請（個人メールアドレス）",
  "timestamp": "2025-06-26T15:30:00.000000",
  "source": "domain_matching_manual"
}
```
- **重複防止**: ハッシュベースの処理済み管理
- **データ整合性**: 送信システムとの完全連携

### 運用要件
- **Google Cloud Console設定**: プロジェクト作成、API有効化、サービスアカウント作成
- **認証情報配置**: `config/google_sheets_credentials.json`
- **スプレッドシート権限**: サービスアカウントに閲覧権限付与

---

**注意**: この仕様書は基幹システムの安定した仕様を記載しています。日々の運用状況や進捗については別途引き継ぎ書を参照してください。

**最終更新**: 2025年6月27日 12:45:00
**バージョン**: 1.6（メール送信アーキテクチャ根本変更・迷惑メール対策）
**作成者**: HUGAN JOB開発チーム

### 🔧 バージョン1.6の主要変更点（2025年6月27日）
- **メール送信アーキテクチャ根本変更**: MIMEMultipart → MIMEText単体構造への変更
- **迷惑メール判定対策**: Thunderbird完全模倣による商用メール特徴の排除
- **MIME構造最適化**: 複雑なマルチパート構造から単純なHTML構造への変更
- **ダッシュボード送信統一**: 全送信機能で`--email-format html_only`を強制指定
- **送信品質向上**: 個人メールクライアント同等の送信方式を実現

#### 技術的詳細
```python
# 変更前（迷惑メール判定される構造）
msg = MIMEMultipart('alternative')
html_part = MIMEText(html_content, 'html', 'utf-8')
msg.attach(html_part)

# 変更後（Thunderbird完全模倣構造）
msg = MIMEText(html_content, 'html', 'utf-8')
```

#### 影響範囲
- **huganjob_unified_sender.py**: メール作成ロジックの根本変更
- **dashboard/derivative_dashboard.py**: 全送信機能での引数統一
- **送信品質**: 迷惑メール判定率の大幅改善（コマンドライン送信で確認済み）

### 🆕 バージョン1.5の主要変更点（2025年6月26日）
- **ドメインベース配信停止機能**: 個人メールアドレスからの配信停止申請に対応
- **即時反映機能**: 送信完了後のダッシュボード即時更新
- **配信停止ログ強化**: JSON形式による詳細な理由とソース記録
- **企業検索機能拡張**: ドメインマッチングによる企業特定

### 🆕 バージョン1.4の主要変更点（2025年6月25日）
- **配信停止管理システム**: Googleフォーム連携による自動配信停止処理
- **Google Sheets監視システム**: リアルタイム配信停止申請検出・処理
- **送信記録修正**: 96社分の欠落記録復元（カバレッジ99.78%達成）
- **統計システム改善**: 送信履歴ベースの正確な統計計算

### 🆕 バージョン1.3の主要変更点（2025年6月24日）
- **多重化開封追跡システム**: 9種類の並行追跡方法を実装
- **企業環境対応強化**: 厳格なセキュリティ環境での追跡精度向上
- **URLクリック追跡削除**: 受信者アクセス阻害問題の解決
- **システムエラー修正**: stats_cacheエラーの完全修正
- **開封率分析強化**: 企業ID 1201-1500の詳細分析実施

### バージョン1.2の変更点（2025年6月24日）
- **バウンス処理統合管理**: バウンスメール検出と企業データベース更新の同時実行
- **企業データベース自動更新**: バウンス状態の自動反映機能
- **バウンス復元システム**: レポートからの完全復元機能
- **送信結果統合処理**: CSV読み込み処理とデータ統合ロジックの改善
- **データ整合性強化**: 送信結果とダッシュボード表示の整合性向上

### バージョン1.3の変更点（2025年6月25日）
- **ダッシュボードパフォーマンス最適化**: 多層キャッシュシステム実装
- **軽量版データ処理**: 高速統計処理機能追加
- **エラーハンドリング強化**: CSVファイル列名変更対応
- **日時解析改善**: マイクロ秒付き形式対応
- **キャッシュ管理**: 期間別データキャッシュ機能

### バージョン1.4の変更点（2025年6月27日）
- **CSVファイル読み込み処理改善**: pandas.read_csv()からcsv.DictReader()への変更
- **企業データ表示問題修正**: ヘッダー認識エラーの解決
- **エラーハンドリング強化**: ID変換エラーの安全処理
- **データクリーニングツール追加**: huganjob_data_cleaner.py実装
- **データ検証機能**: 必須列存在確認とデバッグログ強化
