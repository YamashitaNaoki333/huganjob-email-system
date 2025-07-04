# HUGAN JOB データ入力方法ガイド

**作成日時**: 2025年6月19日  
**対象**: 新しいインプットデータの追加方法  
**目的**: 複数のデータソースを効率的に統合・管理

---

## 概要

HUGAN JOBメールマーケティングシステムでは、複数の方法で新しいデータを追加・統合できます。このガイドでは、各方法の特徴と使用手順を説明します。

## 📊 **現在のデータ構造**

### 標準データ形式
```csv
ID,企業名,URL,業種,所在地,従業員数,資本金,売上高,メールアドレス
1,司法書士法人中央ライズアクロス,https://riseacross.com/,司法書士事務所,,,,,
2,おばた司法書士事務所,https://ojso.jp/,司法書士事務所,,,,,
```

### 必須カラム
- **企業名**: 送信対象企業の名称
- **URL**: 企業のウェブサイトURL

### オプションカラム
- **業種**: 企業の業界・事業内容
- **所在地**: 企業の所在地
- **従業員数**: 従業員数
- **資本金**: 資本金
- **売上高**: 売上高
- **メールアドレス**: 直接送信用メールアドレス

---

## 🛠️ **データ追加方法**

### 方法1: 対話式データ入力管理システム（推奨）

#### 特徴
- ✅ 最も簡単で安全
- ✅ 自動的なデータ検証・クリーニング
- ✅ 既存データとの重複チェック
- ✅ 複数形式対応（CSV, Excel, JSON）

#### 使用手順
```bash
python data_input_manager.py
```

#### 実行例
```
📊 HUGAN JOB データ追加システム
📁 追加するデータファイルのパスを入力してください:
ファイルパス: osaka_input.csv

📊 ファイル分析: osaka_input.csv
✅ ファイル読み込み成功
📋 データ件数: 50件
📋 カラム数: 6個

🔍 必須カラムチェック:
  ✅ 企業名
  ✅ URL

🔗 既存データとマージしますか？ (y/n): y
✅ データ追加が完了しました！
```

### 方法2: データ形式変換ツール

#### 特徴
- ✅ 様々な形式からCSVに変換
- ✅ カラム名の自動マッピング
- ✅ データクリーニング機能

#### 使用手順
```bash
python data_format_converter.py
```

#### 対応形式
- **CSV**: 各種エンコーディング対応
- **Excel**: .xlsx, .xls形式
- **JSON**: 配列・オブジェクト形式
- **テキスト**: タブ区切り、カンマ区切り等

### 方法3: データ管理ダッシュボード

#### 特徴
- ✅ Webブラウザでの直感的操作
- ✅ ファイル分析・統計表示
- ✅ 複数ファイルの一括マージ
- ✅ リアルタイムプレビュー

#### 使用手順
```bash
python data_management_dashboard.py
```

ブラウザで http://localhost:5003 にアクセス

#### 主な機能
1. **ファイル一覧**: 利用可能なデータファイルの表示
2. **ファイル分析**: データ構造・統計の詳細表示
3. **ファイルマージ**: 複数ファイルの統合
4. **データ統計**: 全体的なデータ状況の把握

---

## 📋 **詳細手順**

### Step 1: データファイルの準備

#### サポートされるファイル形式
- **CSV**: UTF-8, Shift_JIS, CP932対応
- **Excel**: .xlsx, .xls
- **JSON**: 配列またはオブジェクト形式
- **テキスト**: タブ区切り、カンマ区切り

#### データ品質要件
- 企業名は必須（空白不可）
- URLは推奨（自動でhttps://を補完）
- メールアドレスは形式検証あり
- 重複企業は自動検出・処理

### Step 2: データ分析・検証

#### 自動実行される検証項目
1. **ファイル形式チェック**: サポート形式の確認
2. **エンコーディング検出**: 最適なエンコーディングの選択
3. **カラム構造分析**: 必須・オプションカラムの確認
4. **データ品質チェック**: 空白・無効データの検出
5. **重複チェック**: 既存データとの重複確認

#### 分析結果例
```
📋 検出されたカラム:
  1. 企業名 - 例: 株式会社サンプル
  2. URL - 例: https://example.com
  3. 業種 - 例: IT・ソフトウェア

🔍 必須カラムチェック:
  ✅ 企業名
  ✅ URL

🔍 データ品質チェック:
  企業名: 48/50件 (空白: 2件)
  URL: 45/50件 (空白: 5件, http含む: 40件)
```

### Step 3: データ標準化

#### 自動実行される処理
1. **カラム名統一**: 標準カラム名への変換
2. **データクリーニング**: 空白・無効データの除去
3. **URL正規化**: https://プレフィックスの追加
4. **メール検証**: 無効なメールアドレスの除去
5. **ID採番**: 連番IDの自動付与

#### カラム名マッピング例
```
事務所名 → 企業名
会社名 → 企業名
企業URL → URL
ウェブサイト → URL
担当者メールアドレス → メールアドレス
Email → メールアドレス
```

### Step 4: データマージ

#### 重複処理オプション
1. **スキップ**: 重複企業を新規データから除外
2. **上書き**: 既存データを新規データで置換
3. **両方保持**: 重複を許可して両方保持

#### マージ結果例
```
既存データ: 9件
新規データ: 50件
重複企業を検出: 2件
マージ完了: 57件のデータ
```

### Step 5: 保存・確認

#### 自動生成されるファイル
- **メインファイル**: `test_input.csv` (更新)
- **バックアップ**: `test_input_backup_YYYYMMDD_HHMMSS.csv`
- **統合ファイル**: `merged_input_YYYYMMDD_HHMMSS.csv` (オプション)

#### 統計情報表示
```
📊 保存データ統計:
  総件数: 57件
  企業名あり: 57件
  有効URL: 52件
  メールアドレス: 15件
```

---

## 🔄 **実際の使用例**

### 例1: 大阪企業データの追加

```bash
# 1. データ入力管理システムを起動
python data_input_manager.py

# 2. ファイルパス入力
ファイルパス: osaka_input.csv

# 3. 分析結果確認
✅ ファイル読み込み成功
📋 データ件数: 50件
📋 カラム数: 6個

# 4. マージ実行
🔗 既存データとマージしますか？ (y/n): y
重複企業の処理方法を選択してください (1: スキップ, 2: 上書き, 3: 両方保持): 1

# 5. 保存完了
✅ データ追加が完了しました！
📁 保存先: test_input.csv
```

### 例2: Excelファイルの変換・追加

```bash
# 1. 形式変換ツールを起動
python data_format_converter.py

# 2. Excelファイル指定
ファイルパス: company_list.xlsx

# 3. 変換実行
📊 検出された形式: excel
📄 使用シート: Sheet1
✅ 読み込み成功: 100行 × 8列

# 4. 標準化・保存
🎉 変換が完了しました！
📁 出力ファイル: company_list_converted.csv

# 5. データ統合
python data_input_manager.py
ファイルパス: company_list_converted.csv
```

### 例3: Webダッシュボードでの一括管理

```bash
# 1. ダッシュボード起動
python data_management_dashboard.py

# 2. ブラウザアクセス
# http://localhost:5003

# 3. ファイル分析
# 各ファイルの「分析」ボタンをクリック

# 4. 複数ファイルマージ
# マージするファイルを選択
# 出力ファイル名を指定
# 「マージ実行」ボタンをクリック
```

---

## 📋 **次のステップ**

### データ追加後の処理

#### 1. メールアドレス抽出
```bash
python core_scripts/derivative_email_extractor.py
```
- 企業URLからメールアドレスを自動抽出
- 抽出結果は別ファイルに保存

#### 2. ウェブサイト分析
```bash
python core_scripts/derivative_website_analyzer.py
```
- 企業ウェブサイトの品質分析
- UX・デザイン・技術スコアの算出

#### 3. メール送信実行
```bash
python core_scripts/derivative_ad_email_sender.py --start-id 1 --end-id 20
```
- 統合データでのメール送信
- 送信結果の記録・追跡

### 運用上の注意点

#### データ品質管理
- 定期的なデータクリーニング
- 重複データの監視
- 無効URLの確認・更新

#### バックアップ管理
- 自動バックアップの確認
- 定期的な手動バックアップ
- 復旧手順の確認

#### パフォーマンス監視
- 大量データ処理時の監視
- メモリ使用量の確認
- 処理時間の最適化

---

## 🛠️ **トラブルシューティング**

### よくある問題と解決方法

#### 問題1: ファイルが読み込めない
```
原因: エンコーディングの問題
解決: UTF-8で保存し直すか、data_format_converter.pyを使用
```

#### 問題2: カラムが認識されない
```
原因: カラム名の不一致
解決: カラム名マッピング機能を使用、または手動でカラム名を変更
```

#### 問題3: 重複データが多い
```
原因: 既存データとの重複
解決: 重複処理オプションで「スキップ」を選択
```

#### 問題4: メールアドレスが無効
```
原因: 形式が正しくない
解決: 自動検証機能により無効なアドレスは自動除去
```

---

**重要**: データ追加後は必ずメールアドレス抽出とテスト送信を実行して、システムが正常に動作することを確認してください。
