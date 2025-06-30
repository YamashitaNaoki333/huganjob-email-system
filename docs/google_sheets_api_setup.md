# Google Cloud Console 設定ガイド

## 1. プロジェクト作成
1. Google Cloud Console (https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成
   - プロジェクト名: huganjob-sheets-api (任意)
   - 組織: 個人アカウントの場合は「組織なし」

## 2. Google Sheets API有効化
1. APIとサービス > ライブラリ に移動
2. "Google Sheets API" を検索
3. Google Sheets API を選択して「有効にする」をクリック

## 3. サービスアカウント作成
1. APIとサービス > 認証情報 に移動
2. 「認証情報を作成」> 「サービスアカウント」を選択
3. サービスアカウント詳細:
   - サービスアカウント名: huganjob-sheets-monitor
   - サービスアカウントID: huganjob-sheets-monitor
   - 説明: HUGANJOB配信停止監視システム用
4. 「作成して続行」をクリック
5. ロールは設定不要（「完了」をクリック）

## 4. 認証情報ダウンロード
1. 作成したサービスアカウントをクリック
2. 「キー」タブに移動
3. 「キーを追加」> 「新しいキーを作成」
4. キーのタイプ: JSON を選択
5. 「作成」をクリックしてJSONファイルをダウンロード

## 5. 認証情報ファイル配置
1. ダウンロードしたJSONファイルを以下に配置:
   config/google_sheets_credentials.json
2. ファイル名を正確に合わせてください

## 6. スプレッドシート権限設定
1. 対象スプレッドシートを開く
2. 「共有」ボタンをクリック
3. サービスアカウントのメールアドレスを追加
   - メールアドレス: huganjob-sheets-monitor@[プロジェクトID].iam.gserviceaccount.com
   - 権限: 閲覧者（読み取り専用で十分）
4. 「送信」をクリック

## 7. 必要なPythonライブラリインストール
```bash
pip install google-api-python-client google-auth
```

## 8. 動作テスト
```bash
python huganjob_google_sheets_monitor.py --test
```
