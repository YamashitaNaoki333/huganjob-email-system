# HUGAN JOB メール設定ガイド

## 概要
HUGAN JOB採用営業キャンペーン用のメール設定を行うためのガイドです。

## 必要な設定項目

### 1. SMTPサーバー設定
以下の情報をHUGANのメールサーバー管理者から取得してください：

- **SMTPサーバー**: smtp.hugan.co.jp（推定）
- **ポート**: 587（STARTTLS）または 465（SSL）
- **認証方式**: SMTP認証
- **暗号化**: STARTTLS または SSL/TLS

### 2. IMAPサーバー設定（バウンス処理用）
- **IMAPサーバー**: imap.hugan.co.jp（推定）
- **ポート**: 993（SSL）または 143（STARTTLS）

### 3. アカウント情報
- **メールアドレス**: client@hugan.co.jp
- **パスワード**: [HUGANメールサーバー管理者から取得]

## 設定手順

### ステップ1: パスワード設定
1. `config/derivative_email_config.ini`ファイルを開く
2. 以下の箇所の`[要設定]`を実際のパスワードに置き換える：
   ```ini
   password = [要設定]
   ```

### ステップ2: サーバー設定確認
HUGANのメールサーバー設定が以下と異なる場合は修正してください：

```ini
[SMTP]
server = smtp.hugan.co.jp
port = 587
user = client@hugan.co.jp
username = client@hugan.co.jp
password = [実際のパスワード]
sender_name = HUGAN採用事務局
from_name = HUGAN採用事務局
from_email = client@hugan.co.jp
reply_to = client@hugan.co.jp

[email]
imap_server = imap.hugan.co.jp
imap_port = 993
username = client@hugan.co.jp
password = [実際のパスワード]

[IMAP]
server = imap.hugan.co.jp
port = 993
```

### ステップ3: 接続テスト
設定完了後、以下のコマンドでテスト送信を実行：

```bash
python core_scripts/derivative_ad_email_sender.py --start-id 1 --end-id 1 --test-mode
```

## よくある設定パターン

### Gmail系の場合
```ini
server = smtp.gmail.com
port = 587
```

### Outlook/Hotmail系の場合
```ini
server = smtp-mail.outlook.com
port = 587
```

### 独自ドメインの場合
```ini
server = mail.hugan.co.jp
# または
server = smtp.hugan.co.jp
port = 587
```

## トラブルシューティング

### 認証エラーが発生する場合
1. メールアドレスとパスワードが正しいか確認
2. 2段階認証が有効な場合はアプリパスワードを使用
3. SMTPサーバーのアドレスとポート番号を確認

### 接続エラーが発生する場合
1. ファイアウォールの設定を確認
2. SMTPサーバーのアドレスを確認
3. ポート番号（587, 465, 25）を試す

### SSL/TLS エラーが発生する場合
1. ポート587でSTARTTLSを試す
2. ポート465でSSL/TLSを試す
3. セキュリティ設定を確認

## 設定完了後の確認事項

1. ✅ テストモードでメール送信が成功する
2. ✅ 送信者名が「HUGAN採用事務局」で表示される
3. ✅ 送信元アドレスが「client@hugan.co.jp」になっている
4. ✅ メール件名が「【採用ご担当者様へ】採用工数の削減とミスマッチ防止を実現するご提案｜HUGAN JOB」になっている
5. ✅ テンプレートが「corporate-email-newsletter.html」を使用している

## 注意事項

- パスワードは設定ファイルに平文で保存されるため、ファイルのアクセス権限に注意してください
- テスト送信で問題がないことを確認してから本番送信を行ってください
- HUGANのメールサーバー設定については、システム管理者に確認してください

## サポート

設定に関する質問や問題が発生した場合は、以下を確認してください：
1. このガイドのトラブルシューティング
2. HUGANのメールサーバー管理者への問い合わせ
3. システムログの確認
