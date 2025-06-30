# AI後任者向け引き継ぎガイド

**作成日**: 2025年6月18日  
**対象**: 後任AI開発者  
**システム**: 派生版メールマーケティングシステム  
**バージョン**: 1.0.0

## 🎯 このシステムについて

### システムの位置づけ
- **元システム**: `C:\Users\Raxus\Desktop\email_extraction_project\` (ポート5001)
- **派生版システム**: `C:\Users\Raxus\Desktop\email_extraction_project\email_marketing_derivative_system\` (ポート5002)
- **関係性**: 完全独立（元システムに影響なし）

### 目的
- 新機能開発・テスト環境
- 元システムを変更せずに安全な実験が可能
- アルゴリズム改善やUI/UX改善の検証

## 📁 システム構造理解

### ディレクトリ構造
```
email_marketing_derivative_system/
├── 📂 core_scripts/           # メイン処理スクリプト
│   ├── derivative_integrated_workflow.py    # 統合ワークフロー（メイン）
│   ├── derivative_email_extractor.py        # メール抽出
│   ├── derivative_website_analyzer.py       # ウェブサイト分析
│   └── derivative_email_sender.py           # メール送信
├── 📂 dashboard/              # ダッシュボード
│   └── derivative_dashboard.py              # Flask Webアプリ
├── 📂 config/                 # 設定ファイル
│   └── derivative_email_config.ini          # SMTP/IMAP設定
├── 📂 data/                   # データファイル
│   ├── derivative_input.csv                 # 入力データ
│   ├── results/                             # 処理結果
│   └── derivative_consolidated/             # 統合結果
├── 📂 templates/              # HTMLテンプレート（15ファイル）
├── 📂 logs/                   # ログファイル
├── 🚀 start_derivative_dashboard.bat        # ダッシュボード起動
├── 🔄 run_derivative_workflow.bat           # ワークフロー実行
├── 🧪 test_derivative_system.py             # システムテスト
├── 📖 README.md                             # 基本説明
├── 📋 DEPLOYMENT_GUIDE.md                   # デプロイガイド
└── 📝 AI_HANDOVER_GUIDE.md                  # この文書
```

### 重要な命名規則
- **プレフィックス**: 全ファイルに `derivative_` を使用
- **ポート**: 5002番（元システムは5001番）
- **データパス**: `data/` ディレクトリ配下
- **ログパス**: `logs/derivative_dashboard/` 配下

## 🔧 開発環境セットアップ

### 前提条件
- Python 3.8+
- 必要パッケージ: Flask, pandas, selenium, requests
- Chrome/ChromeDriver（ウェブサイト分析用）

### 初回セットアップ
```bash
# 1. ディレクトリ移動
cd C:\Users\Raxus\Desktop\email_extraction_project\email_marketing_derivative_system

# 2. 依存関係確認
pip install flask pandas selenium requests

# 3. システムテスト実行
python test_derivative_system.py

# 4. ダッシュボード起動テスト
python dashboard/derivative_dashboard.py --debug --port 5002
```

## 🚀 基本操作

### 1. ダッシュボード起動
```bash
# バッチファイル使用（推奨）
start_derivative_dashboard.bat

# 直接実行
python dashboard/derivative_dashboard.py --port 5002

# デバッグモード
python dashboard/derivative_dashboard.py --debug --port 5002
```
**アクセス**: http://127.0.0.1:5002/

### 2. 統合ワークフロー実行
```bash
# バッチファイル使用（推奨）
run_derivative_workflow.bat

# 直接実行（ID 1-3の企業を処理）
python core_scripts/derivative_integrated_workflow.py --start-id 1 --end-id 3
```

### 3. 個別スクリプト実行
```bash
# メール抽出のみ
python core_scripts/derivative_email_extractor.py --start-id 1 --end-id 3

# ウェブサイト分析のみ
python core_scripts/derivative_website_analyzer.py --start-id 1 --end-id 3

# メール送信のみ
python core_scripts/derivative_email_sender.py --start-id 1 --end-id 3
```

## 📊 データフロー理解

### 処理の流れ
1. **入力**: `data/derivative_input.csv` から企業データ読み込み
2. **メール抽出**: 企業ウェブサイトからメールアドレス抽出
3. **ウェブサイト分析**: サイト品質を評価してランク付け
4. **メール送信**: ランク別テンプレートでメール送信
5. **結果保存**: `data/results/` に各段階の結果を保存

### データファイル
- **入力**: `data/derivative_input.csv` (5社のサンプルデータ)
- **抽出結果**: `derivative_email_extraction_results_*.csv`
- **分析結果**: `derivative_website_analysis_results_*.csv`
- **送信結果**: `data/derivative_email_sending_results.csv`

## 🔍 トラブルシューティング

### よくある問題と解決法

#### 1. ポート競合エラー
```bash
# 現在の使用状況確認
netstat -an | findstr :5002

# 別ポートで起動
python dashboard/derivative_dashboard.py --port 5003
```

#### 2. ファイルが見つからないエラー
```bash
# 現在のディレクトリ確認
pwd

# 正しいディレクトリに移動
cd C:\Users\Raxus\Desktop\email_extraction_project\email_marketing_derivative_system
```

#### 3. 設定ファイルエラー
```bash
# 設定ファイル確認
type config\derivative_email_config.ini

# 設定ファイルが存在しない場合は元システムからコピー
copy ..\email_config.ini config\derivative_email_config.ini
```

#### 4. ChromeDriverエラー
```bash
# ChromeDriverのパス確認
where chromedriver

# 最新版ダウンロード推奨
# https://chromedriver.chromium.org/
```

### ログ確認方法
```bash
# ダッシュボードログ
type logs\derivative_dashboard\derivative_dashboard.log

# 統合ワークフローログ
type logs\derivative_dashboard\derivative_integrated_workflow.log

# リアルタイムログ監視（PowerShell）
Get-Content logs\derivative_dashboard\derivative_dashboard.log -Wait
```

## 🛠️ 開発ガイド

### 新機能追加手順
1. **スクリプト作成**: `core_scripts/derivative_new_feature.py`
2. **命名規則遵守**: `derivative_` プレフィックス使用
3. **設定参照**: `config/derivative_email_config.ini` を使用
4. **データ保存**: `data/results/` ディレクトリに保存
5. **ダッシュボード統合**: `dashboard/derivative_dashboard.py` に機能追加
6. **テスト追加**: `test_derivative_system.py` にテストケース追加

### コード修正時の注意点
- **元システム非干渉**: 元システムのファイルは絶対に変更しない
- **パス参照**: 相対パスは派生版ディレクトリ基準
- **ポート固定**: 5002番ポート使用を維持
- **ログ出力**: 適切なログレベルで出力

### テスト実行
```bash
# システム全体テスト
python test_derivative_system.py

# 個別機能テスト
python -m pytest tests/ -v  # (テストディレクトリがある場合)
```

## 📈 パフォーマンス最適化

### 推奨設定
- **バッチサイズ**: 3-5社（小規模テスト用）
- **タイムアウト**: 10分
- **メモリ制限**: 2GB
- **同時実行**: 1プロセス

### 監視ポイント
- **メモリ使用量**: ダッシュボードで確認
- **処理時間**: ログファイルで確認
- **エラー率**: ダッシュボードで確認
- **ファイルサイズ**: `data/` ディレクトリ監視

## 🔒 セキュリティ考慮事項

### 機密情報
- **SMTP設定**: `config/derivative_email_config.ini` に保存
- **メールアドレス**: 抽出結果に含まれる
- **企業情報**: 入力データに含まれる

### アクセス制御
- **ローカルアクセスのみ**: 127.0.0.1:5002
- **認証なし**: 開発環境のため
- **ファイル権限**: 適切な権限設定を維持

## 📚 参考資料

### 関連ドキュメント
1. **README.md**: 基本的な使用方法
2. **DEPLOYMENT_GUIDE.md**: 詳細なデプロイ手順
3. **派生版システム作成完了報告書_20250618_1030.md**: 構築経緯

### 元システム参照
- **場所**: `C:\Users\Raxus\Desktop\email_extraction_project\`
- **ダッシュボード**: http://127.0.0.1:5001/
- **注意**: 元システムは変更禁止

### 外部リソース
- **Flask公式**: https://flask.palletsprojects.com/
- **pandas公式**: https://pandas.pydata.org/
- **Selenium公式**: https://selenium-python.readthedocs.io/

## 🎯 開発優先順位

### 高優先度
1. **新機能プロトタイプ**: 安全な実験環境として活用
2. **アルゴリズム改善**: メール抽出・ウェブサイト分析の精度向上
3. **UI/UX改善**: ダッシュボードの使いやすさ向上

### 中優先度
1. **パフォーマンス最適化**: 処理速度の改善
2. **エラーハンドリング強化**: 例外処理の改善
3. **ログ機能拡張**: より詳細な監視機能

### 低優先度
1. **大量データ対応**: 元システムで対応済み
2. **本番環境対応**: 派生版は開発・テスト用途

## 📞 サポート情報

### 緊急時対応
1. **システム停止**: Ctrl+C でプロセス停止
2. **ポート解放**: タスクマネージャーでPythonプロセス終了
3. **データ復旧**: `data/` ディレクトリのバックアップから復元

### 定期メンテナンス
- **ログローテーション**: 月1回ログファイル整理
- **データクリーンアップ**: 不要な結果ファイル削除
- **システムテスト**: 週1回の動作確認

---

## 🎉 最後に

この派生版システムは元システムから完全に独立しており、安全に実験・開発を行うことができます。

**重要**: 元システム（ポート5001）には絶対に影響を与えないよう注意してください。

何か問題が発生した場合は、まず `test_derivative_system.py` を実行して システムの健全性を確認してください。

**Good luck with your development!** 🚀

## 📋 チェックリスト

### 引き継ぎ完了確認
- [ ] システム構造を理解した
- [ ] 基本操作を実行できた
- [ ] テストスクリプトが正常に動作した
- [ ] ダッシュボードにアクセスできた
- [ ] ログファイルの場所を確認した
- [ ] 設定ファイルの内容を理解した
- [ ] 元システムとの違いを把握した

### 開発開始前確認
- [ ] 開発環境が正常に動作している
- [ ] 必要な依存関係がインストールされている
- [ ] ChromeDriverが正常に動作している
- [ ] ポート5002が利用可能である
- [ ] データディレクトリに書き込み権限がある

---

**作成者**: AI Assistant
**最終更新**: 2025年6月18日
**次回更新予定**: 利用開始後のフィードバックに基づく
