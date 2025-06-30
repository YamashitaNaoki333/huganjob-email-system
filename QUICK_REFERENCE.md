# 派生版システム クイックリファレンス

**対象**: AI開発者  
**用途**: 日常的な開発作業のリファレンス

## 🚀 基本コマンド

### システム起動
```bash
# ダッシュボード起動
start_derivative_dashboard.bat
# または
python dashboard/derivative_dashboard.py --port 5002

# 統合ワークフロー実行
run_derivative_workflow.bat
# または
python core_scripts/derivative_integrated_workflow.py --start-id 1 --end-id 3
```

### システムテスト
```bash
# 全体テスト
python test_derivative_system.py

# 構文チェック
python -m py_compile core_scripts/derivative_*.py
```

## 📁 重要ファイル・ディレクトリ

### 必須ファイル
- `core_scripts/derivative_integrated_workflow.py` - メイン処理
- `dashboard/derivative_dashboard.py` - Webダッシュボード
- `config/derivative_email_config.ini` - 設定ファイル
- `data/derivative_input.csv` - 入力データ

### 結果ファイル
- `data/derivative_email_extraction_results_*.csv` - メール抽出結果
- `data/derivative_website_analysis_results_*.csv` - サイト分析結果
- `data/derivative_email_sending_results.csv` - メール送信結果

### ログファイル
- `logs/derivative_dashboard/derivative_dashboard.log` - ダッシュボードログ
- `logs/derivative_dashboard/derivative_integrated_workflow.log` - ワークフローログ

## 🔧 設定変更

### ポート変更
```python
# dashboard/derivative_dashboard.py
parser.add_argument('--port', type=int, default=5002)  # ここを変更
```

### バッチサイズ変更
```python
# core_scripts/derivative_integrated_workflow.py
DEFAULT_BATCH_SIZE = 3  # ここを変更
```

### タイムアウト変更
```python
# core_scripts/derivative_integrated_workflow.py
self.silent_timeout_minutes = 10  # ここを変更
```

## 🐛 デバッグ

### ログレベル変更
```python
# 各スクリプトの先頭で
logging.basicConfig(level=logging.DEBUG)  # INFO → DEBUG に変更
```

### デバッグモード起動
```bash
python dashboard/derivative_dashboard.py --debug --port 5002
```

### プロセス確認
```bash
# ポート使用状況
netstat -an | findstr :5002

# Pythonプロセス確認
tasklist | findstr python
```

## 📊 データ操作

### 入力データ追加
```csv
# data/derivative_input.csv に行追加
6,新企業,https://example.com,業界,場所,規模,説明
```

### 結果データ確認
```python
import pandas as pd

# メール抽出結果確認
df = pd.read_csv('data/derivative_email_extraction_results_latest.csv')
print(df.head())

# 分析結果確認
df = pd.read_csv('data/derivative_website_analysis_results_latest.csv')
print(df[['company_name', 'total_score', 'rank']])
```

## 🔍 トラブルシューティング

### よくあるエラー

#### ポート競合
```bash
# 解決法1: 別ポートで起動
python dashboard/derivative_dashboard.py --port 5003

# 解決法2: プロセス終了
taskkill /f /im python.exe
```

#### ファイルが見つからない
```bash
# 現在ディレクトリ確認
cd C:\Users\Raxus\Desktop\email_extraction_project\email_marketing_derivative_system
```

#### ChromeDriverエラー
```bash
# ChromeDriverパス確認
where chromedriver

# 最新版ダウンロード
# https://chromedriver.chromium.org/
```

#### メモリ不足
```python
# メモリクリーンアップ
import gc
gc.collect()
```

### ログ確認
```bash
# リアルタイムログ監視
Get-Content logs\derivative_dashboard\derivative_dashboard.log -Wait

# エラーログ検索
findstr "ERROR" logs\derivative_dashboard\*.log
```

## 🛠️ 開発パターン

### 新機能追加テンプレート
```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
派生版新機能: [機能名]
"""

import os
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def new_feature_function():
    """新機能のメイン関数"""
    try:
        # 処理実装
        logger.info("新機能処理開始")
        
        # 結果保存
        result_file = "data/derivative_new_feature_results.csv"
        # save_results(result_file)
        
        logger.info("新機能処理完了")
        return True
        
    except Exception as e:
        logger.error(f"新機能処理エラー: {e}")
        return False

if __name__ == "__main__":
    success = new_feature_function()
    exit(0 if success else 1)
```

### ダッシュボード機能追加
```python
# dashboard/derivative_dashboard.py に追加

@app.route('/api/new-feature')
def api_new_feature():
    """新機能API"""
    try:
        # データ取得・処理
        data = get_new_feature_data()
        return jsonify(data)
    except Exception as e:
        logger.error(f"新機能APIエラー: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/new-feature')
def new_feature_page():
    """新機能ページ"""
    return render_template('new_feature.html')
```

## 📈 パフォーマンス最適化

### メモリ使用量削減
```python
# 大きなデータフレームの処理後
del large_dataframe
gc.collect()

# チャンク処理
for chunk in pd.read_csv('large_file.csv', chunksize=1000):
    process_chunk(chunk)
```

### 処理速度向上
```python
# 並列処理（注意: 1プロセス推奨）
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=2) as executor:
    futures = [executor.submit(process_company, company) for company in companies]
    results = [future.result() for future in futures]
```

## 🔒 セキュリティチェック

### 設定ファイル確認
```bash
# パスワードが平文で保存されていないか確認
type config\derivative_email_config.ini | findstr password
```

### ログ出力確認
```python
# 個人情報がログに出力されていないか確認
def safe_log(message, email=None):
    if email:
        masked_email = email[:3] + "***@" + email.split('@')[1]
        message = message.replace(email, masked_email)
    logger.info(message)
```

## 📋 チェックリスト

### 開発前チェック
- [ ] 正しいディレクトリにいる
- [ ] テストが全て通る
- [ ] ポート5002が利用可能
- [ ] 必要な依存関係がインストール済み

### 開発後チェック
- [ ] 新機能のテストを追加
- [ ] ログ出力が適切
- [ ] メモリリークがない
- [ ] エラーハンドリングが適切
- [ ] ドキュメントを更新

### デプロイ前チェック
- [ ] 全テストが通る
- [ ] パフォーマンステスト実行
- [ ] セキュリティチェック実行
- [ ] バックアップ作成

## 🎯 よく使うコードスニペット

### データ読み込み
```python
import pandas as pd

# 企業データ読み込み
companies = pd.read_csv('data/derivative_input.csv')

# 結果データ読み込み
results = pd.read_csv('data/derivative_email_extraction_results_latest.csv')
```

### ログ出力
```python
import logging

logger = logging.getLogger(__name__)

# 情報ログ
logger.info(f"処理開始: {company_name}")

# エラーログ
logger.error(f"処理失敗: {company_name}, エラー: {str(e)}")

# デバッグログ
logger.debug(f"詳細情報: {debug_info}")
```

### 設定読み込み
```python
import configparser

config = configparser.ConfigParser()
config.read('config/derivative_email_config.ini')

smtp_server = config['SMTP']['server']
smtp_port = config.getint('SMTP', 'port')
```

### WebDriver操作
```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

try:
    driver.get(url)
    # 処理
finally:
    driver.quit()
```

---

**クイックリファレンス v1.0.0**  
**最終更新**: 2025年6月18日
