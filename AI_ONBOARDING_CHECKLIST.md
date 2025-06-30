# AI後任者 オンボーディングチェックリスト

**対象**: 新しく担当するAI開発者  
**目的**: スムーズな引き継ぎと作業開始  
**所要時間**: 約30分

## 📋 Phase 1: 環境確認 (5分)

### システム基本情報確認
- [ ] **作業ディレクトリ**: `C:\Users\Raxus\Desktop\email_extraction_project\email_marketing_derivative_system`
- [ ] **システムポート**: 5002番（元システムは5001番）
- [ ] **Python バージョン**: 3.8+ が利用可能
- [ ] **OS**: Windows 10/11

### 必要ツール確認
```bash
# Python確認
python --version

# pip確認
pip --version

# Chrome確認（ウェブサイト分析用）
# Chromeブラウザがインストールされているか確認
```

**確認結果**:
- [ ] Python 3.8+ ✅
- [ ] pip 利用可能 ✅
- [ ] Chrome ブラウザ利用可能 ✅

## 📋 Phase 2: システム理解 (10分)

### ドキュメント読了
- [ ] **README.md** - システム概要理解
- [ ] **AI_HANDOVER_GUIDE.md** - 引き継ぎガイド理解
- [ ] **TECHNICAL_SPECIFICATIONS.md** - 技術仕様理解
- [ ] **QUICK_REFERENCE.md** - 日常作業リファレンス確認

### システム構造確認
```bash
# ディレクトリ構造確認
dir /B

# 主要ファイル確認
dir core_scripts
dir dashboard
dir config
dir data
```

**確認項目**:
- [ ] 6つのメインディレクトリ存在確認
- [ ] 4つのコアスクリプト存在確認
- [ ] ダッシュボードファイル存在確認
- [ ] 設定ファイル存在確認
- [ ] サンプルデータ存在確認

### 元システムとの違い理解
- [ ] **独立性**: 元システム（ポート5001）とは完全分離
- [ ] **命名規則**: `derivative_` プレフィックス使用
- [ ] **データ分離**: `data/` ディレクトリ使用
- [ ] **設定分離**: `config/derivative_email_config.ini` 使用

## 📋 Phase 3: 動作確認 (10分)

### システムテスト実行
```bash
# 作業ディレクトリ移動
cd C:\Users\Raxus\Desktop\email_extraction_project\email_marketing_derivative_system

# システムテスト実行
python test_derivative_system.py
```

**期待結果**:
- [ ] **ディレクトリ構造テスト**: ✅ 合格
- [ ] **設定ファイル独立性テスト**: ✅ 合格
- [ ] **データファイル参照テスト**: ✅ 合格
- [ ] **ポート独立性テスト**: ✅ 合格
- [ ] **スクリプト構文テスト**: ✅ 合格
- [ ] **総合結果**: 🎉 全テスト合格

### ダッシュボード起動テスト
```bash
# ダッシュボード起動
python dashboard/derivative_dashboard.py --port 5002
```

**確認項目**:
- [ ] エラーなく起動
- [ ] http://127.0.0.1:5002/ にアクセス可能
- [ ] ダッシュボード画面表示
- [ ] Ctrl+C で正常停止

### 簡単な処理テスト
```bash
# 小規模テスト実行（ID 1-2の企業のみ）
python core_scripts/derivative_integrated_workflow.py --start-id 1 --end-id 2
```

**確認項目**:
- [ ] エラーなく実行開始
- [ ] ログ出力が正常
- [ ] 処理完了（約3分以内）
- [ ] 結果ファイル生成確認

## 📋 Phase 4: 開発環境準備 (5分)

### 依存関係インストール
```bash
# 必要パッケージインストール
pip install flask pandas selenium requests
```

**確認項目**:
- [ ] Flask インストール完了
- [ ] pandas インストール完了
- [ ] selenium インストール完了
- [ ] requests インストール完了

### ChromeDriver設定
```bash
# ChromeDriverパス確認
where chromedriver
```

**ChromeDriverが見つからない場合**:
1. https://chromedriver.chromium.org/ から最新版ダウンロード
2. PATHの通った場所に配置
3. `where chromedriver` で確認

**確認項目**:
- [ ] ChromeDriver利用可能
- [ ] Selenium + Chrome動作確認

### エディタ・IDE設定
**推奨設定**:
- [ ] Python構文ハイライト有効
- [ ] UTF-8エンコーディング設定
- [ ] タブサイズ4スペース設定
- [ ] 行番号表示有効

## 📋 Phase 5: 実践的理解 (追加時間)

### コード理解
**優先順位順に確認**:
1. [ ] `derivative_integrated_workflow.py` - メイン処理フロー
2. [ ] `derivative_dashboard.py` - ダッシュボード機能
3. [ ] `derivative_email_extractor.py` - メール抽出ロジック
4. [ ] `derivative_website_analyzer.py` - サイト分析ロジック
5. [ ] `derivative_email_sender.py` - メール送信ロジック

### 設定ファイル理解
```ini
# config/derivative_email_config.ini の主要設定確認
[SMTP]
server = f045.sakura.ne.jp
port = 587
# ... その他設定
```

**確認項目**:
- [ ] SMTP設定理解
- [ ] IMAP設定理解
- [ ] 制限値設定理解
- [ ] リトライ設定理解

### ログ分析
```bash
# ログファイル確認
type logs\derivative_dashboard\derivative_dashboard.log
type logs\derivative_dashboard\derivative_integrated_workflow.log
```

**確認項目**:
- [ ] ログ形式理解
- [ ] エラーログ識別方法理解
- [ ] デバッグ情報理解

## 🚨 トラブルシューティング

### よくある問題と解決法

#### テストが失敗する場合
```bash
# 詳細エラー確認
python test_derivative_system.py > test_result.txt 2>&1
type test_result.txt
```

#### ダッシュボードが起動しない場合
```bash
# ポート使用状況確認
netstat -an | findstr :5002

# 別ポートで起動
python dashboard/derivative_dashboard.py --port 5003
```

#### ChromeDriverエラーの場合
```bash
# Chrome バージョン確認
chrome --version

# 対応するChromeDriverダウンロード
# https://chromedriver.chromium.org/
```

#### 権限エラーの場合
```bash
# 管理者権限でコマンドプロンプト起動
# または
# ディレクトリ権限確認・修正
```

## ✅ 完了確認

### 最終チェック
- [ ] **全テスト合格**: システムテストが全て通る
- [ ] **ダッシュボード動作**: 正常に起動・アクセス可能
- [ ] **処理実行**: 小規模テストが正常完了
- [ ] **ログ確認**: ログファイルが正常に生成される
- [ ] **設定理解**: 主要設定項目を理解している
- [ ] **トラブル対応**: 基本的な問題解決方法を理解している

### 引き継ぎ完了宣言
**以下の文章を確認して、準備完了を宣言してください**:

> 「派生版メールマーケティングシステムの引き継ぎを完了しました。
> システムの構造を理解し、基本的な動作確認を行い、
> 開発環境の準備が整いました。
> 元システムとは完全に独立したこのシステムで、
> 安全に新機能開発・テストを行う準備ができています。」

**引き継ぎ完了日時**: _______________  
**担当AI**: _______________

## 🎯 次のステップ

### 開発開始前の推奨事項
1. **小規模実験**: 1-2社のデータで機能テスト
2. **ログ監視**: 処理中のログ出力を確認
3. **バックアップ**: 重要な変更前にデータバックアップ
4. **段階的開発**: 小さな変更から始める

### 開発時の注意事項
- **元システム非干渉**: 絶対に元システムを変更しない
- **ポート固定**: 5002番ポートを維持
- **命名規則**: `derivative_` プレフィックスを維持
- **テスト実行**: 変更後は必ずテスト実行

### サポートリソース
- **技術仕様書**: `TECHNICAL_SPECIFICATIONS.md`
- **クイックリファレンス**: `QUICK_REFERENCE.md`
- **デプロイガイド**: `DEPLOYMENT_GUIDE.md`
- **システムテスト**: `test_derivative_system.py`

---

**オンボーディングチェックリスト v1.0.0**  
**作成日**: 2025年6月18日  
**想定所要時間**: 30分  
**成功率**: 100%（全項目完了で開発開始可能）

---

## 🎉 Welcome to the Team!

このチェックリストを完了すれば、派生版システムでの開発を安全に開始できます。
何か問題が発生した場合は、まず `test_derivative_system.py` を実行して
システムの健全性を確認してください。

**Happy coding!** 🚀
